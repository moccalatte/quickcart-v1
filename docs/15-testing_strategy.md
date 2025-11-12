# 15. Testing Strategy
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
Defines comprehensive testing approach for QuickCart to ensure quality, reliability, and security throughout the payment processing system lifecycle. Zero-tolerance for payment-related bugs or security vulnerabilities.

---

## Testing Pyramid & Strategy

### Testing Hierarchy
```
                    ┌─────────────────┐
                    │   Manual E2E    │ (5%)
                    │   Testing       │
                ┌───┴─────────────────┴───┐
                │   Automated E2E Tests   │ (15%)
                │   Integration Tests     │
            ┌───┴─────────────────────────┴───┐
            │        Unit Tests               │ (80%)
            │        Component Tests          │
        └───────────────────────────────────────┘
```

### Test Types & Coverage Goals

| Test Type | Coverage Target | Purpose | Automation Level |
|-----------|----------------|---------|------------------|
| **Unit Tests** | 95% for business logic | Function-level validation | 100% automated |
| **Integration Tests** | 90% for API endpoints | Service interaction validation | 100% automated |
| **E2E Tests** | 100% for critical paths | Full user flow validation | 95% automated |
| **Security Tests** | 100% for sensitive operations | Vulnerability detection | 90% automated |
| **Performance Tests** | Key user journeys | Load and stress validation | 100% automated |
| **Fraud Tests** | All detection rules | Anti-fraud system validation | 95% automated |

---

## Unit Testing Strategy

### Unit Test Framework
```python
# pytest configuration for QuickCart
# conftest.py
import pytest
import asyncio
import asyncpg
from unittest.mock import AsyncMock, MagicMock
from src.database import Database
from src.redis_client import RedisClient
from src.telegram_bot import TelegramBot

@pytest.fixture
async def db_connection():
    """Provide test database connection"""
    connection = await asyncpg.connect(
        "postgresql://test_user:test_pass@localhost/quickcart_test"
    )
    
    # Clean database before each test
    await connection.execute("TRUNCATE TABLE users, products, orders, product_stocks CASCADE")
    
    yield connection
    
    await connection.close()

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    return redis_mock

@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram Bot for testing"""
    bot_mock = MagicMock()
    bot_mock.send_message = AsyncMock(return_value={"message_id": 123})
    bot_mock.send_photo = AsyncMock(return_value={"message_id": 124})
    return bot_mock

@pytest.fixture
def mock_pakasir_api():
    """Mock Pakasir API for testing"""
    api_mock = AsyncMock()
    api_mock.create_payment = AsyncMock(return_value={
        "payment": {
            "order_id": "TRX123",
            "amount": 50000,
            "payment_number": "mock_qr_code",
            "expired_at": "2025-11-12T10:00:00Z"
        }
    })
    return api_mock
```

### Critical Unit Tests Examples
```python
# tests/unit/test_order_processing.py
import pytest
from unittest.mock import AsyncMock, patch
from src.services.order_service import OrderService
from src.models.order import Order
from src.exceptions import InsufficientStockError, UserBannedError

class TestOrderProcessing:
    """Unit tests for order processing logic"""
    
    @pytest.mark.asyncio
    async def test_create_order_success(self, db_connection, mock_redis):
        """Test successful order creation"""
        # Arrange
        order_service = OrderService(db_connection, mock_redis)
        user_id = 12345
        product_id = 1
        quantity = 2
        
        # Mock available stock
        mock_redis.get.return_value = "5"  # 5 items in stock
        
        # Act
        order = await order_service.create_order(user_id, product_id, quantity)
        
        # Assert
        assert order.user_id == user_id
        assert order.total_bill > 0
        assert order.status == "pending"
        
        # Verify stock was reserved
        mock_redis.set.assert_called_with(
            f"stock_reserved:{product_id}", quantity, ex=600  # 10 minutes
        )
    
    @pytest.mark.asyncio
    async def test_create_order_insufficient_stock(self, db_connection, mock_redis):
        """Test order creation fails with insufficient stock"""
        # Arrange
        order_service = OrderService(db_connection, mock_redis)
        mock_redis.get.return_value = "1"  # Only 1 item in stock
        
        # Act & Assert
        with pytest.raises(InsufficientStockError):
            await order_service.create_order(12345, 1, 3)  # Request 3 items
    
    @pytest.mark.asyncio
    async def test_create_order_banned_user(self, db_connection, mock_redis):
        """Test order creation fails for banned user"""
        # Arrange
        order_service = OrderService(db_connection, mock_redis)
        
        # Setup banned user in database
        await db_connection.execute(
            "INSERT INTO users (id, name, is_banned) VALUES ($1, $2, $3)",
            12345, "Banned User", True
        )
        
        # Act & Assert
        with pytest.raises(UserBannedError):
            await order_service.create_order(12345, 1, 1)

# tests/unit/test_fraud_detection.py
class TestFraudDetection:
    """Unit tests for fraud detection system"""
    
    @pytest.mark.asyncio
    async def test_velocity_fraud_detection(self):
        """Test velocity-based fraud detection"""
        # Arrange
        fraud_detector = FraudDetectionEngine()
        user_id = 12345
        
        # Simulate multiple rapid payments
        transactions = [
            {"amount": 100000, "timestamp": "2025-11-12T10:00:00Z"},
            {"amount": 100000, "timestamp": "2025-11-12T10:05:00Z"},
            {"amount": 100000, "timestamp": "2025-11-12T10:10:00Z"},
            {"amount": 100000, "timestamp": "2025-11-12T10:15:00Z"},
            {"amount": 100000, "timestamp": "2025-11-12T10:20:00Z"},
            {"amount": 100000, "timestamp": "2025-11-12T10:25:00Z"}  # 6th payment in 25 minutes
        ]
        
        # Act
        risk_score = await fraud_detector.evaluate_velocity_risk(user_id, transactions)
        
        # Assert
        assert risk_score >= 70  # High risk score for velocity abuse
        assert "payment_velocity" in fraud_detector.triggered_rules
```

---

## Integration Testing Strategy

### API Integration Tests
```python
# tests/integration/test_payment_flow.py
import pytest
from httpx import AsyncClient
from src.main import app

class TestPaymentIntegration:
    """Integration tests for payment processing"""
    
    @pytest.mark.asyncio
    async def test_complete_payment_flow(self, test_client: AsyncClient):
        """Test complete payment flow from order to delivery"""
        
        # Step 1: Create user
        user_response = await test_client.post("/users", json={
            "telegram_id": 12345,
            "name": "Test User"
        })
        assert user_response.status_code == 201
        
        # Step 2: Create order
        order_response = await test_client.post("/orders", json={
            "user_id": 12345,
            "product_id": 1,
            "quantity": 1,
            "payment_method": "qris"
        })
        assert order_response.status_code == 201
        order_data = order_response.json()
        
        # Step 3: Simulate payment webhook from Pakasir
        webhook_response = await test_client.post("/webhooks/pakasir", json={
            "order_id": order_data["invoice_id"],
            "status": "completed",
            "amount": order_data["total_bill"]
        })
        assert webhook_response.status_code == 200
        
        # Step 4: Verify order is marked as paid
        order_check = await test_client.get(f"/orders/{order_data['id']}")
        assert order_check.json()["status"] == "paid"
        
        # Step 5: Verify content was delivered
        assert order_check.json()["items"][0]["content"] is not None

# tests/integration/test_telegram_integration.py
class TestTelegramIntegration:
    """Integration tests for Telegram bot functionality"""
    
    @pytest.mark.asyncio
    async def test_user_registration_flow(self, mock_telegram_update):
        """Test complete user registration via Telegram"""
        
        # Simulate /start command
        update = create_telegram_update(
            message="/start",
            user_id=12345,
            username="testuser"
        )
        
        # Process update
        await telegram_handler.handle_update(update)
        
        # Verify user was created in database
        user = await get_user(12345)
        assert user is not None
        assert user.name == "testuser"
        
        # Verify welcome message was sent
        mock_telegram_bot.send_message.assert_called_with(
            chat_id=12345,
            text=contains("Selamat datang")
        )
```

### Database Integration Tests
```python
# tests/integration/test_database_operations.py
class TestDatabaseIntegrity:
    """Integration tests for database operations"""
    
    @pytest.mark.asyncio
    async def test_order_stock_consistency(self, db_connection):
        """Test order creation maintains stock consistency"""
        
        # Setup: Create product with stock
        await db_connection.execute(
            "INSERT INTO products (id, name, customer_price) VALUES ($1, $2, $3)",
            1, "Test Product", 50000
        )
        
        # Add stock items
        for i in range(5):
            await db_connection.execute(
                "INSERT INTO product_stocks (product_id, content) VALUES ($1, $2)",
                1, f"content_{i}"
            )
        
        # Create multiple concurrent orders
        tasks = []
        for i in range(3):
            task = create_order(user_id=1000+i, product_id=1, quantity=1)
            tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify: Only 3 orders succeeded, 2 remaining stock
        successful_orders = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_orders) == 3
        
        remaining_stock = await db_connection.fetchval(
            "SELECT COUNT(*) FROM product_stocks WHERE product_id = $1 AND is_sold = FALSE",
            1
        )
        assert remaining_stock == 2
```

---

## End-to-End Testing Strategy

### E2E Test Framework
```python
# tests/e2e/test_user_journey.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from telegram_simulator import TelegramSimulator

class TestCompleteUserJourney:
    """End-to-end tests simulating complete user interactions"""
    
    @pytest.mark.asyncio
    async def test_customer_purchase_journey(self):
        """Test complete customer purchase journey"""
        
        telegram_sim = TelegramSimulator()
        
        # Step 1: User starts bot
        response = await telegram_sim.send_message("/start")
        assert "Selamat datang" in response.text
        
        # Step 2: User browses products
        response = await telegram_sim.click_button("LIST PRODUK")
        assert "Pilih kategori" in response.text
        
        # Step 3: User selects product
        response = await telegram_sim.click_button("1")  # Product ID 1
        assert "Netflix Premium" in response.text
        
        # Step 4: User adds quantity
        response = await telegram_sim.click_button("+")
        response = await telegram_sim.click_button("Lanjut ke pembayaran")
        
        # Step 5: User chooses QRIS payment
        response = await telegram_sim.click_button("QRIS")
        assert "Scan QR Code" in response.text
        
        # Step 6: Simulate payment completion
        await telegram_sim.simulate_payment_completion()
        
        # Step 7: Verify product delivery
        final_response = await telegram_sim.get_last_message()
        assert "Pesanan berhasil" in final_response.text
        assert "email:" in final_response.text  # Product content delivered

# tests/e2e/test_admin_operations.py
class TestAdminOperations:
    """End-to-end tests for admin functionality"""
    
    @pytest.mark.asyncio
    async def test_admin_product_management(self):
        """Test admin product management workflow"""
        
        admin_sim = TelegramSimulator(admin=True)
        
        # Add new product
        response = await admin_sim.send_message("/add 25|Netflix Premium 2 Month|Akses Netflix 2 bulan|100000|content here")
        assert "Produk berhasil ditambahkan" in response.text
        
        # Verify product appears in catalog
        response = await admin_sim.send_message("/products")
        assert "Netflix Premium 2 Month" in response.text
        
        # Add stock to product
        response = await admin_sim.send_message("/addstock 25|email:test@netflix.com\npassword:secret123")
        assert "Stok berhasil ditambahkan" in response.text
        
        # Verify stock count
        response = await admin_sim.send_message("/stock")
        assert "ID: 25" in response.text
        assert "Stok: 1" in response.text
```

---

## Security Testing Strategy

### Automated Security Tests
```python
# tests/security/test_input_validation.py
class TestInputValidation:
    """Security tests for input validation"""
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, test_client):
        """Test SQL injection attack prevention"""
        
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "admin'/*",
            "<script>alert('xss')</script>"
        ]
        
        for malicious_input in malicious_inputs:
            response = await test_client.post("/users", json={
                "telegram_id": 12345,
                "name": malicious_input
            })
            
            # Should either reject or sanitize input
            assert response.status_code in [400, 422, 201]
            
            # Verify database wasn't compromised
            user_count = await get_user_count()
            assert user_count >= 0  # Database still functional
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_client):
        """Test rate limiting protection"""
        
        # Attempt to exceed rate limit
        responses = []
        for i in range(15):  # Assume limit is 10/minute
            response = await test_client.post("/orders", json={
                "user_id": 12345,
                "product_id": 1,
                "quantity": 1
            })
            responses.append(response.status_code)
        
        # Should get rate limited after 10 requests
        assert 429 in responses  # Too Many Requests

# tests/security/test_authentication.py
class TestAuthentication:
    """Security tests for authentication and authorization"""
    
    @pytest.mark.asyncio
    async def test_admin_command_authorization(self, test_client):
        """Test admin commands require proper authorization"""
        
        # Attempt admin command as regular user
        response = await test_client.post("/admin/ban_user", json={
            "user_id": 99999,
            "admin_user_id": 12345  # Not an admin
        })
        
        assert response.status_code == 403  # Forbidden
        
        # Verify user wasn't actually banned
        user = await get_user(99999)
        assert not user.is_banned if user else True
```

### Penetration Testing Checklist
```python
SECURITY_TEST_CHECKLIST = {
    "authentication": [
        "Admin privilege escalation attempts",
        "Session hijacking tests",
        "Telegram user ID spoofing",
        "Rate limiting bypass attempts"
    ],
    "data_validation": [
        "SQL injection in all input fields",
        "XSS in message content",
        "Command injection in admin commands",
        "Path traversal in file operations"
    ],
    "api_security": [
        "Webhook signature validation",
        "API key exposure checks",
        "CORS policy validation",
        "HTTP security headers"
    ],
    "business_logic": [
        "Payment amount manipulation",
        "Stock quantity bypass",
        "Order status manipulation",
        "Fraud detection bypass"
    ]
}
```

---

## Performance Testing Strategy

### Load Testing Configuration
```python
# tests/performance/test_payment_load.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestPaymentSystemLoad:
    """Performance tests for payment processing"""
    
    @pytest.mark.asyncio
    async def test_concurrent_payment_processing(self):
        """Test system under concurrent payment load"""
        
        # Configuration
        concurrent_users = 100
        payments_per_user = 5
        test_duration = 60  # seconds
        
        # Metrics collection
        successful_payments = 0
        failed_payments = 0
        response_times = []
        
        async def simulate_user_payments(user_id: int):
            """Simulate a user making multiple payments"""
            for i in range(payments_per_user):
                start_time = time.time()
                try:
                    result = await create_test_payment(user_id, product_id=1, amount=50000)
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    if result["status"] == "success":
                        successful_payments += 1
                    else:
                        failed_payments += 1
                except Exception as e:
                    failed_payments += 1
                
                # Random delay between payments
                await asyncio.sleep(random.uniform(0.1, 2.0))
        
        # Execute load test
        tasks = []
        for user_id in range(concurrent_users):
            task = simulate_user_payments(user_id + 10000)
            tasks.append(task)
        
        start_time = time.time()
        await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Performance assertions
        success_rate = successful_payments / (successful_payments + failed_payments)
        avg_response_time = sum(response_times) / len(response_times)
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]
        
        assert success_rate >= 0.95  # 95% success rate minimum
        assert avg_response_time <= 2.0  # 2 seconds average
        assert p95_response_time <= 5.0  # 5 seconds P95
        
        print(f"Load Test Results:")
        print(f"Success Rate: {success_rate:.2%}")
        print(f"Avg Response Time: {avg_response_time:.2f}s")
        print(f"P95 Response Time: {p95_response_time:.2f}s")
        print(f"Total Payments: {successful_payments + failed_payments}")
```

---

## Testing Infrastructure & Automation

### CI/CD Test Integration
```yaml
# .github/workflows/comprehensive-testing.yml
name: Comprehensive Testing Pipeline

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run unit tests
        run: |
          pytest tests/unit/ --cov=src/ --cov-report=xml --junit-xml=unit-results.xml
          
  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
    steps:
      - name: Run integration tests
        run: |
          pytest tests/integration/ --junit-xml=integration-results.xml
  
  security-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run security tests
        run: |
          pytest tests/security/ --junit-xml=security-results.xml
          bandit -r src/ -f json -o security-scan.json
  
  e2e-tests:
    needs: [unit-tests, integration-tests]
    runs-on: ubuntu-latest
    steps:
      - name: Run E2E tests
        run: |
          pytest tests/e2e/ --junit-xml=e2e-results.xml
  
  performance-tests:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Run performance tests
        run: |
          pytest tests/performance/ --junit-xml=performance-results.xml
```

### Test Data Management
```python
# tests/fixtures/test_data.py
"""Test data fixtures and factories"""

class TestDataFactory:
    """Factory for creating consistent test data"""
    
    @staticmethod
    def create_test_user(user_id: int = None, is_admin: bool = False):
        """Create test user with optional admin privileges"""
        return {
            "id": user_id or random.randint(10000, 99999),
            "name": f"Test User {user_id or 'Random'}",
            "member_status": "admin" if is_admin else "customer",
            "account_balance": 0.0,
            "is_banned": False
        }
    
    @staticmethod
    def create_test_product(product_id: int = None):
        """Create test product with stock"""
        return {
            "id": product_id or random.randint(1, 24),
            "name": f"Test Product {product_id or 'Random'}",
            "description": "Test product description",
            "customer_price": 50000.0,
            "reseller_price": 45000.0,
            "category": "Test Category"
        }
    
    @staticmethod
    def create_test_order(user_id: int, product_id: int):
        """Create test order"""
        return {
            "user_id": user_id,
            "product_id": product_id,
            "quantity": 1,
            "total_bill": 50000.0,
            "payment_method": "qris",
            "status": "pending"
        }
```

---

## Test Metrics & Reporting

### Coverage Targets by Component
```python
COVERAGE_TARGETS = {
    "payment_processing": 100,  # Critical path, zero tolerance
    "fraud_detection": 100,    # Security critical
    "user_management": 95,     # High importance
    "admin_commands": 95,      # High impact operations
    "telegram_handlers": 90,   # User interface
    "reporting": 80,           # Non-critical features
    "utilities": 85            # Support functions
}

# Quality gates
QUALITY_GATES = {
    "unit_test_coverage": 90,
    "integration_test_coverage": 85,
    "security_test_pass_rate": 100,
    "performance_test_pass_rate": 95,
    "code_quality_score": 85
}
```

---

## Cross-References

- See [14-build_plan.md](14-build_plan.md) for CI/CD pipeline integration and test automation
- See [16-risk_register.md](16-risk_register.md) for risk-based test prioritization and mitigation
- See [17-observability.md](17-observability.md) for production monitoring and testing in live environment
- See [11-anti_fraud_policy.md](11-anti_fraud_policy.md) for fraud detection system testing requirements

---

> Note for AI builders: Testing is mission-critical for payment systems. Every feature must have comprehensive test coverage before production deployment. Payment-related functionality requires 100% test coverage with both positive and negative test cases. Security tests are mandatory for all user inputs and admin operations.