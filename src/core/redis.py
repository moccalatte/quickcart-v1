"""
Redis Client Configuration and Session Management
Reference: docs/05-architecture.md (CR-003: Secure Sessions)

Redis is OPTIONAL - system falls back to in-memory storage if Redis is unavailable.
This makes deployment simpler for beginners while still supporting Redis for production.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from src.core.config import settings

# Try to import Redis, but make it optional
try:
    import redis.asyncio as redis
    from redis.asyncio import Redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None


class InMemoryStorage:
    """Fallback in-memory storage when Redis is not available"""

    def __init__(self):
        self._storage: Dict[str, tuple[Any, Optional[datetime]]] = {}

    async def get(self, key: str) -> Optional[str]:
        """Get value from memory"""
        if key in self._storage:
            value, expiry = self._storage[key]
            if expiry is None or datetime.utcnow() < expiry:
                return value
            else:
                # Expired
                del self._storage[key]
                return None
        return None

    async def setex(self, key: str, ttl: int, value: str) -> None:
        """Set value with TTL in memory"""
        expiry = datetime.utcnow() + timedelta(seconds=ttl)
        self._storage[key] = (value, expiry)

    async def delete(self, *keys: str) -> None:
        """Delete keys from memory"""
        for key in keys:
            self._storage.pop(key, None)

    async def incr(self, key: str) -> int:
        """Increment counter"""
        current = await self.get(key)
        new_value = int(current) + 1 if current else 1
        # Set without expiry for incr
        self._storage[key] = (str(new_value), None)
        return new_value

    async def expire(self, key: str, ttl: int) -> None:
        """Set TTL for existing key"""
        if key in self._storage:
            value, _ = self._storage[key]
            expiry = datetime.utcnow() + timedelta(seconds=ttl)
            self._storage[key] = (value, expiry)

    async def keys(self, pattern: str) -> list:
        """Get keys matching pattern (simple implementation)"""
        # Simple pattern matching for "prefix:*"
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return [k for k in self._storage.keys() if k.startswith(prefix)]
        return [k for k in self._storage.keys() if k == pattern]

    async def zadd(self, key: str, mapping: dict) -> None:
        """Add to sorted set (simplified)"""
        # Store as JSON with scores
        current = await self.get(key)
        data = json.loads(current) if current else {}
        data.update(mapping)
        await self.setex(key, 86400, json.dumps(data))  # 24h default

    async def zrangebyscore(self, key: str, min_score: float, max_score: float) -> list:
        """Get sorted set members by score range"""
        current = await self.get(key)
        if not current:
            return []
        data = json.loads(current)
        return [
            member for member, score in data.items() if min_score <= score <= max_score
        ]

    async def zrem(self, key: str, *members: str) -> None:
        """Remove members from sorted set"""
        current = await self.get(key)
        if current:
            data = json.loads(current)
            for member in members:
                data.pop(member, None)
            await self.setex(key, 86400, json.dumps(data))

    async def zscore(self, key: str, member: str) -> Optional[float]:
        """Get score of member in sorted set"""
        current = await self.get(key)
        if current:
            data = json.loads(current)
            return data.get(member)
        return None

    async def ping(self) -> bool:
        """Always available for in-memory"""
        return True

    def pipeline(self):
        """Return simple pipeline mock"""
        return InMemoryPipeline(self)

    async def close(self) -> None:
        """No-op for in-memory"""
        pass


class InMemoryPipeline:
    """Simple pipeline for in-memory storage"""

    def __init__(self, storage: InMemoryStorage):
        self.storage = storage
        self.commands = []

    def incr(self, key: str):
        self.commands.append(("incr", key))
        return self

    def expire(self, key: str, ttl: int):
        self.commands.append(("expire", key, ttl))
        return self

    async def execute(self):
        results = []
        for cmd in self.commands:
            if cmd[0] == "incr":
                result = await self.storage.incr(cmd[1])
                results.append(result)
            elif cmd[0] == "expire":
                await self.storage.expire(cmd[1], cmd[2])
                results.append(True)
        return results


class RedisClient:
    """Redis client wrapper for QuickCart application - with optional Redis"""

    def __init__(self) -> None:
        self.redis: Optional[Redis] = None
        self.in_memory: Optional[InMemoryStorage] = None
        self.use_redis = REDIS_AVAILABLE and settings.redis_url is not None
        self.session_ttl = settings.session_ttl_seconds

    async def connect(self) -> None:
        """Establish Redis connection or fall back to in-memory"""
        if self.use_redis:
            try:
                self.redis = await redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                )
                # Test connection
                await self.redis.ping()
                print("✓ Redis connected successfully")
            except Exception as e:
                print(f"⚠ Redis connection failed: {e}")
                print("✓ Falling back to in-memory storage")
                self.redis = None
                self.in_memory = InMemoryStorage()
        else:
            print("✓ Using in-memory storage (Redis not configured)")
            self.in_memory = InMemoryStorage()

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()

    async def ping(self) -> bool:
        """Check Redis connectivity"""
        try:
            if self.redis:
                return await self.redis.ping()
            elif self.in_memory:
                return await self.in_memory.ping()
            return False
        except Exception:
            return False

    def get_client(self):
        """Get the active client (Redis or in-memory)"""
        return self.redis if self.redis else self.in_memory


class SecureRedisSession:
    """
    Secure session management with TTL and data protection
    Reference: docs/05-architecture.md (CR-003 Best Practice)
    """

    def __init__(self, client):
        self.client = client
        self.session_ttl = settings.session_ttl_seconds

    async def save_session(self, user_id: int, session_data: dict) -> None:
        """
        Save user session securely

        Best Practice: Don't store sensitive data (order amounts, payment info)
        Only store navigation state and context
        """
        key = f"session:{user_id}"

        # Only store safe navigation data
        safe_data = {
            "current_flow": session_data.get("current_flow"),
            "current_step": session_data.get("current_step"),
            "product_id": session_data.get("product_id"),
            "quantity": session_data.get("quantity", 1),
            "category": session_data.get("category"),
            "last_activity": datetime.utcnow().isoformat(),
        }

        # Save with automatic expiry (24 hours)
        await self.client.setex(key, self.session_ttl, json.dumps(safe_data))

    async def get_session(self, user_id: int) -> Optional[dict]:
        """Get user session safely"""
        key = f"session:{user_id}"
        data = await self.client.get(key)

        if data:
            return json.loads(data)
        return None

    async def clear_session(self, user_id: int) -> None:
        """Clear user session (logout/security/flow reset)"""
        key = f"session:{user_id}"
        await self.client.delete(key)

    async def update_session_field(self, user_id: int, field: str, value: Any) -> None:
        """Update specific field in session without full reload"""
        session = await self.get_session(user_id)
        if session:
            session[field] = value
            session["last_activity"] = datetime.utcnow().isoformat()
            await self.save_session(user_id, session)


class CacheManager:
    """Cache management for product counts, stats, and temporary data"""

    def __init__(self, client):
        self.client = client

    async def get_stock_count(self, product_id: int) -> Optional[int]:
        """Get cached stock count for product"""
        key = f"stock_count:{product_id}"
        count = await self.client.get(key)
        return int(count) if count else None

    async def set_stock_count(
        self, product_id: int, count: int, ttl: int = 300
    ) -> None:
        """Cache stock count (5 minutes default)"""
        key = f"stock_count:{product_id}"
        await self.client.setex(key, ttl, str(count))

    async def invalidate_stock_cache(self, product_id: int) -> None:
        """Invalidate stock count cache after purchase/addition"""
        key = f"stock_count:{product_id}"
        await self.client.delete(key)

    async def get_stats(self, stat_name: str) -> Optional[str]:
        """Get cached statistics (total_users, total_transactions)"""
        key = f"stats:{stat_name}"
        return await self.client.get(key)

    async def set_stats(self, stat_name: str, value: Any, ttl: int = 600) -> None:
        """Cache statistics (10 minutes default)"""
        key = f"stats:{stat_name}"
        await self.client.setex(key, ttl, str(value))

    async def invalidate_stats(self) -> None:
        """Invalidate all stats cache"""
        keys = await self.client.keys("stats:*")
        if keys:
            await self.client.delete(*keys)


class RateLimiter:
    """Rate limiting for user actions and fraud prevention"""

    def __init__(self, client):
        self.client = client

    async def check_rate_limit(
        self, user_id: int, action: str, limit: int = 10, window: int = 60
    ) -> bool:
        """
        Check if user exceeded rate limit

        Args:
            user_id: Telegram user ID
            action: Action type (e.g., "order", "payment_check", "command")
            limit: Max actions allowed in window
            window: Time window in seconds (default 60 = 1 minute)

        Returns:
            True if within limit, False if exceeded
        """
        key = f"rate:{user_id}:{action}"
        current = await self.client.get(key)

        if current and int(current) >= limit:
            return False

        # Increment counter
        pipe = self.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        await pipe.execute()

        return True

    async def get_remaining_attempts(
        self, user_id: int, action: str, limit: int = 10
    ) -> int:
        """Get remaining attempts before rate limit"""
        key = f"rate:{user_id}:{action}"
        current = await self.client.get(key)
        used = int(current) if current else 0
        return max(0, limit - used)


class PaymentExpiryQueue:
    """Queue for payment expiry tracking using sorted sets"""

    def __init__(self, client):
        self.client = client
        self.queue_key = "payment_expiry_queue"

    async def schedule_payment_expiry(
        self, order_id: str, expires_at: datetime
    ) -> None:
        """
        Schedule payment expiry check

        Args:
            order_id: Order invoice ID
            expires_at: When payment expires (10 minutes from creation)
        """
        expiry_timestamp = expires_at.timestamp()
        await self.client.zadd(self.queue_key, {order_id: expiry_timestamp})

    async def get_expired_payments(self) -> list[str]:
        """Get all payments that have expired (for background worker processing)"""
        current_time = datetime.utcnow().timestamp()
        expired_orders = await self.client.zrangebyscore(
            self.queue_key, 0, current_time
        )
        return expired_orders

    async def remove_from_queue(self, order_id: str) -> None:
        """Remove order from expiry queue (payment completed or cancelled)"""
        await self.client.zrem(self.queue_key, order_id)

    async def get_time_until_expiry(self, order_id: str) -> Optional[int]:
        """Get seconds until payment expires"""
        score = await self.client.zscore(self.queue_key, order_id)
        if score:
            expiry_time = datetime.fromtimestamp(score)
            delta = expiry_time - datetime.utcnow()
            return max(0, int(delta.total_seconds()))
        return None


# Global Redis client instance
redis_client = RedisClient()


async def get_redis():
    """Dependency injection for Redis/in-memory client"""
    if not redis_client.redis and not redis_client.in_memory:
        await redis_client.connect()
    return redis_client.get_client()


async def get_session_manager() -> SecureRedisSession:
    """Get session manager instance"""
    client = await get_redis()
    return SecureRedisSession(client)


async def get_cache_manager() -> CacheManager:
    """Get cache manager instance"""
    client = await get_redis()
    return CacheManager(client)


async def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance"""
    client = await get_redis()
    return RateLimiter(client)


async def get_payment_queue() -> PaymentExpiryQueue:
    """Get payment expiry queue instance"""
    client = await get_redis()
    return PaymentExpiryQueue(client)
