"""
Product Repository - Data Access for Product and Stock Operations
Reference: docs/06-data_schema.md, docs/01-dev_protocol.md
"""

from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.product import Product, ProductStock


class ProductRepository:
    """Repository for product and stock data access"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_all_active(self) -> List[Product]:
        """Get all active products"""
        result = await self.session.execute(
            select(Product).where(Product.is_active == True).order_by(Product.id)
        )
        return result.scalars().all()

    async def get_by_category(self, category: str) -> List[Product]:
        """Get products by category"""
        result = await self.session.execute(
            select(Product)
            .where(and_(Product.category == category, Product.is_active == True))
            .order_by(Product.id)
        )
        return result.scalars().all()

    async def get_best_sellers(self, limit: int = 10) -> List[Product]:
        """Get top-selling products"""
        result = await self.session.execute(
            select(Product)
            .where(Product.is_active == True)
            .order_by(Product.sold_count.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_all_categories(self) -> List[str]:
        """Get list of unique categories"""
        result = await self.session.execute(
            select(Product.category)
            .where(Product.is_active == True)
            .distinct()
            .order_by(Product.category)
        )
        return result.scalars().all()

    async def create(self, product_data: dict) -> Product:
        """Create new product"""
        product = Product(**product_data)
        self.session.add(product)
        await self.session.flush()
        return product

    async def update(self, product_id: int, updates: dict) -> Optional[Product]:
        """Update product fields"""
        product = await self.get_by_id(product_id)
        if product:
            for key, value in updates.items():
                setattr(product, key, value)
            await self.session.flush()
        return product

    async def delete(self, product_id: int) -> bool:
        """Soft delete product (set is_active to False)"""
        product = await self.get_by_id(product_id)
        if product:
            product.is_active = False
            await self.session.flush()
            return True
        return False

    async def increment_sold_count(self, product_id: int, quantity: int = 1) -> bool:
        """Increment product sold count after successful order"""
        product = await self.get_by_id(product_id)
        if product:
            product.sold_count += quantity
            await self.session.flush()
            return True
        return False

    async def get_available_stock_count(self, product_id: int) -> int:
        """Get count of available (unsold) stock for product"""
        result = await self.session.execute(
            select(func.count(ProductStock.id)).where(
                and_(
                    ProductStock.product_id == product_id, ProductStock.is_sold == False
                )
            )
        )
        return result.scalar() or 0

    async def get_available_stocks(
        self, product_id: int, limit: Optional[int] = None
    ) -> List[ProductStock]:
        """Get available stock items for product"""
        query = select(ProductStock).where(
            and_(ProductStock.product_id == product_id, ProductStock.is_sold == False)
        )

        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def add_stock(self, product_id: int, content: str) -> ProductStock:
        """Add stock item for product"""
        stock = ProductStock(product_id=product_id, content=content, is_sold=False)
        self.session.add(stock)
        await self.session.flush()
        return stock

    async def add_bulk_stock(
        self, product_id: int, contents: List[str]
    ) -> List[ProductStock]:
        """Add multiple stock items at once"""
        stocks = [
            ProductStock(product_id=product_id, content=content, is_sold=False)
            for content in contents
        ]
        self.session.add_all(stocks)
        await self.session.flush()
        return stocks

    async def reserve_stock(
        self, product_id: int, quantity: int, order_id: int
    ) -> List[ProductStock]:
        """
        Reserve stock items for an order (mark as sold and assign order_id)

        Business Rule: Stock reservation must be atomic to prevent overselling
        """
        # Get available stocks
        stocks = await self.get_available_stocks(product_id, limit=quantity)

        if len(stocks) < quantity:
            raise ValueError(
                f"Insufficient stock: requested {quantity}, available {len(stocks)}"
            )

        # Mark as sold and assign to order
        for stock in stocks[:quantity]:
            stock.is_sold = True
            stock.order_id = order_id

        await self.session.flush()
        return stocks[:quantity]

    async def release_stock(self, order_id: int) -> int:
        """
        Release reserved stock (when payment expires or is cancelled)
        Returns number of stock items released
        """
        result = await self.session.execute(
            select(ProductStock).where(ProductStock.order_id == order_id)
        )
        stocks = result.scalars().all()

        released_count = 0
        for stock in stocks:
            stock.is_sold = False
            stock.order_id = None
            released_count += 1

        await self.session.flush()
        return released_count

    async def delete_stock(self, stock_id: str) -> bool:
        """Delete specific stock item (admin operation)"""
        result = await self.session.execute(
            select(ProductStock).where(ProductStock.id == stock_id)
        )
        stock = result.scalar_one_or_none()

        if stock and not stock.is_sold:
            await self.session.delete(stock)
            await self.session.flush()
            return True
        return False

    async def delete_all_stock(self, product_id: int, only_unsold: bool = True) -> int:
        """
        Delete all stock for product

        Args:
            product_id: Product ID
            only_unsold: If True, only delete unsold stock (default: True)

        Returns:
            Number of stock items deleted
        """
        query = select(ProductStock).where(ProductStock.product_id == product_id)

        if only_unsold:
            query = query.where(ProductStock.is_sold == False)

        result = await self.session.execute(query)
        stocks = result.scalars().all()

        deleted_count = len(stocks)
        for stock in stocks:
            await self.session.delete(stock)

        await self.session.flush()
        return deleted_count

    async def get_stock_by_id(self, stock_id: str) -> Optional[ProductStock]:
        """Get specific stock item by ID"""
        result = await self.session.execute(
            select(ProductStock).where(ProductStock.id == stock_id)
        )
        return result.scalar_one_or_none()

    async def get_stocks_for_order(self, order_id: int) -> List[ProductStock]:
        """Get all stock items assigned to an order"""
        result = await self.session.execute(
            select(ProductStock).where(ProductStock.order_id == order_id)
        )
        return result.scalars().all()
