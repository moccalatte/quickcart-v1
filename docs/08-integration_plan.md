# 08. Integration Plan
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
Outlines how QuickCart integrates with external services (Pakasir, Telegram) and internal components, ensuring reliable, secure, and maintainable connections with comprehensive error handling.

---

## Integration Points

### Pakasir Payment Gateway
- **Service:** Pakasir QRIS payment processing
- **Purpose:** Automated QRIS payment creation, status checking, webhook processing
- **Key Endpoints:**
  - `POST /api/transactioncreate/qris` - Create payment
  - `GET /api/transactiondetail` - Check payment status
  - `POST /webhooks/pakasir` (incoming) - Payment completion notification
- **Payment Flow:** Order → Create payment → QR display → 10min timer → Webhook → Content delivery
- **Custom Domain:** Uses `https://pots.my.id` for customer-facing payment pages

### Telegram Bot API
- **Service:** Telegram Bot API for all user interactions
- **Library:** python-telegram-bot v22.5 (latest version)
- **Repository:** https://github.com/python-telegram-bot/python-telegram-bot
- **Purpose:** Message handling, file delivery, inline keyboards, notifications
- **Integration Method:** Webhook + long polling fallback
- **Key Features:**
  - Reply keyboards for main navigation
  - Inline keyboards for dynamic interactions
  - File/sticker sending for content delivery
  - Callback query handling for button interactions
  - Async/await support (native in v22.5)
- **Rate Limits:** 30 messages/second with queue management
- **Installation:** `pip install python-telegram-bot --upgrade`

### Internal Components
- **PostgreSQL Main DB:** User data, orders, products, stock
- **PostgreSQL Audit DB:** Permanent audit trail (separate instance)
- **Redis:** Session state, caching, job queues, rate limiting
- **FastAPI Backend:** Business logic orchestration and API handling

---

## Data Mapping & Transformation

### Pakasir → Internal Order Mapping
```python
# Incoming Pakasir webhook → Internal order update
pakasir_webhook = {
    "amount": 99000,
    "order_id": "TRX20241228ABC123", 
    "status": "completed"
}

# Maps to internal order update
internal_order_update = {
    "invoice_id": pakasir_webhook["order_id"],
    "status": "paid" if pakasir_webhook["status"] == "completed" else "failed",
    "payment_method": "qris",
    "updated_at": datetime.utcnow()
}
```

### Telegram User → Internal User Mapping
```python
# Telegram user object → Internal user record
telegram_user = {
    "id": 123456789,
    "username": "johndoe", 
    "first_name": "John"
}

# Maps to internal user creation/update
internal_user = {
    "id": telegram_user["id"],  # Use Telegram ID as primary key
    "name": telegram_user.get("first_name", "Anonymous"),
    "username": telegram_user.get("username"),
    "member_status": "customer",  # Default
    "bank_id": generate_bank_id()  # Auto-generated
}
```

### Product Display Mapping
```python
# Internal product → Telegram message formatting
def format_product_message(product, user_member_status):
    price = product.reseller_price if (
        user_member_status == 'reseller' and product.reseller_price
    ) else product.customer_price
    
    return f"""
📦 **{product.name}**
📝 {product.description}
💰 Harga: Rp{price:,.0f}
📊 Stok: {product.stock_count}
🔥 Terjual: {product.sold_count}x
    """
```

---

## Error Handling & Retries

### Pakasir API Error Handling
```python
# Exponential backoff with maximum retries
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, Timeout))
)
async def create_pakasir_payment(order_data):
    try:
        response = await pakasir_api.create_payment(order_data)
        return response
    except PakasirAPIError as e:
        # Log error with correlation ID
        logger.error(f"Pakasir API error: {e}", extra={
            "correlation_id": order_data.get("order_id"),
            "user_id": order_data.get("user_id")
        })
        raise PaymentCreationError("Failed to create payment") from e
```

### Telegram API Error Handling
```python
# Message sending with fallback
async def send_telegram_message(chat_id, text, **kwargs):
    for attempt in range(3):
        try:
            return await bot.send_message(chat_id, text, **kwargs)
        except TelegramError as e:
            if e.description == "Bot blocked by user":
                # Mark user as unreachable, don't retry
                await mark_user_unreachable(chat_id)
                return None
            elif attempt < 2:  # Retry for other errors
                await asyncio.sleep(2 ** attempt)
            else:
                logger.error(f"Failed to send message after 3 attempts: {e}")
                raise
```

### Payment Expiry Handling
```python
# Redis-based job queue for payment expiry
async def schedule_payment_expiry(order_id: str, expires_at: datetime):
    delay = (expires_at - datetime.utcnow()).total_seconds()
    await redis.zadd("payment_expiry_queue", {order_id: time.time() + delay})

# Background worker processes expired payments
async def process_expired_payments():
    while True:
        current_time = time.time()
        expired_orders = await redis.zrangebyscore(
            "payment_expiry_queue", 0, current_time
        )
        for order_id in expired_orders:
            await handle_payment_expiry(order_id)
            await redis.zrem("payment_expiry_queue", order_id)
        await asyncio.sleep(30)  # Check every 30 seconds
```

---

## Security & Compliance

### API Key Management
- **Pakasir API Key:** Stored as environment variable, never logged
- **Telegram Bot Token:** Separate environment variable, access controlled
- **Webhook Signatures:** HMAC validation for incoming Pakasir webhooks
- **Redis Auth:** Password-protected Redis instance

### Data Privacy in Integrations
- **Payment Data:** Never store credit card or bank details locally
- **User PII:** Minimize data sent to external services
- **Audit Logging:** All integration calls logged with sanitized data
- **HTTPS Only:** All external API calls use TLS 1.3

### Rate Limiting Strategy
```python
# User action rate limiting
async def check_rate_limit(user_id: int, action: str, limit: int = 10):
    key = f"rate:{user_id}:{action}"
    current = await redis.get(key)
    if current and int(current) >= limit:
        raise RateLimitExceeded(f"Too many {action} attempts")
    await redis.incr(key)
    await redis.expire(key, 60)  # 1 minute window
```

---

## Testing Integrations

### Pakasir Integration Testing
- **Sandbox Mode:** Use Pakasir sandbox for development/testing
- **Payment Simulation:** `POST /api/paymentsimulation` for testing webhooks
- **Mock Responses:** Local mock server for unit tests
- **E2E Testing:** Complete payment flow in staging environment

### Telegram Bot Testing
- **Test Bot:** Separate bot token for testing environment
- **Mock Updates:** Generate fake Telegram updates for unit tests
- **Integration Tests:** Real Telegram API calls in staging
- **Load Testing:** Simulate high message volume scenarios

### Database Integration Testing
```python
# Test database transaction rollback
@pytest.mark.asyncio
async def test_order_creation_rollback():
    async with database.transaction():
        # Create order
        order = await create_order(user_id=123, product_id=1)
        
        # Simulate payment creation failure
        with pytest.raises(PaymentCreationError):
            await create_payment_for_order(order)
        
        # Verify order was rolled back
        assert await get_order(order.id) is None
        assert await check_stock_reserved(order.id) == 0
```

---

## Monitoring & Maintenance

### Integration Health Checks
```python
# Pakasir API health check
async def check_pakasir_health():
    try:
        # Simple API call to verify connectivity
        response = await pakasir_api.get_project_info()
        return {"status": "ok", "response_time": response.elapsed.total_seconds()}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Telegram API health check  
async def check_telegram_health():
    try:
        response = await bot.get_me()
        return {"status": "ok", "bot_info": response}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### Integration Metrics & Alerts
- **API Response Times:** P95/P99 latency tracking
- **Error Rates:** Failed API calls, timeout percentages  
- **Payment Success Rate:** Successful payment completion rate
- **Message Delivery Rate:** Telegram message success rate
- **Alert Thresholds:**
  - API error rate > 5% for 5 minutes
  - Payment success rate < 90% for 10 minutes
  - Message delivery rate < 95% for 5 minutes

### Maintenance Procedures
- **Weekly:** Review third-party API documentation for changes
- **Monthly:** Update API client libraries and test compatibility
- **Quarterly:** Performance optimization review and load testing
- **As Needed:** Emergency hotfixes for breaking API changes

---

## Cross-References

- See [07-api_contracts.md](07-api_contracts.md) for complete API specifications and data schemas
- See [17-observability.md](17-observability.md) for monitoring, logging, and alerting configuration
- See [09-security_manifest.md](09-security_manifest.md) for security controls and threat mitigation

---

> Note for AI builders: All integrations must implement comprehensive error handling, retry logic, and monitoring. Payment integrations require special attention to idempotency and audit logging. Never assume external services are always available.