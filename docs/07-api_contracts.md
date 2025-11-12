# 07. API Contracts
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
Documents all API contracts for QuickCart, including Pakasir payment gateway integration, Telegram Bot API usage, and internal webhook handling. This ensures consistent integration and zero-ambiguity implementation.

---

## API Overview
- **Primary Integration:** Pakasir REST API for QRIS payment processing
- **Bot Interface:** Telegram Bot API for all user interactions
- **Internal APIs:** FastAPI webhooks and health endpoints
- **Authentication:** API keys for Pakasir, Bot token for Telegram
- **Rate Limiting:** Telegram (30 msg/sec), Pakasir (per account limits)

---

## Pakasir Payment Gateway API (Simple & Reliable)

### Create Payment Transaction (CR-001 Best Practice)
**Endpoint:** `POST https://app.pakasir.com/api/transactioncreate/qris`

**Pakasir Downtime Detection (Customer Satisfaction First):**
```python
async def check_pakasir_health():
    """Check if Pakasir is working before showing payment option"""
    try:
        # Simple test call to Pakasir
        test_response = await httpx.get("https://app.pakasir.com", timeout=5)
        if test_response.status_code == 200:
            return True
        else:
            return False
    except:
        return False  # If any error, assume Pakasir is down

async def create_payment_with_health_check(order_amount: int, order_id: str):
    """Create payment only if Pakasir is healthy"""
    
    # Step 1: Check if Pakasir is working
    if not await check_pakasir_health():
        # Notify admins immediately
        await notify_admins("🚨 Pakasir payment gateway sedang bermasalah!")
        
        # Tell user in friendly way
        return {
            "success": False,
            "message": "💔 Maaf, sistem pembayaran sedang bermasalah.\n\n🔄 Silakan coba lagi dalam beberapa menit atau hubungi admin untuk bantuan.\n\nTerima kasih atas pengertiannya! 🙏"
        }
    
    # Step 2: Calculate fees (only if Pakasir is healthy)
    payment_fee = int(order_amount * 0.007) + 310  # 0.7% + Rp310
    final_amount = order_amount + payment_fee
    
    # Step 3: Create payment
    try:
        response = await create_pakasir_payment(final_amount, order_id)
        return {"success": True, "data": response}
    except Exception as e:
        # Log error for debugging
        logger.error(f"Pakasir payment creation failed: {e}")
        
        # Notify admins
        await notify_admins(f"🚨 Pakasir error: {str(e)}")
        
        # User-friendly message
        return {
            "success": False, 
            "message": "💔 Terjadi kendala teknis saat membuat pembayaran.\n\n🔄 Silakan coba lagi atau hubungi admin.\n\nMaaf atas ketidaknyamanan ini! 🙏"
        }
```

**Request Body:**
```json
{
  "project": "string",        // Pakasir project slug
  "order_id": "string",       // Format: TRX{timestamp}{random}
  "amount": 30520,            // Final amount including fee (base_amount + fee)
  "api_key": "string"         // Pakasir API key
}
```

**Success Response (200):**
```json
{
  "payment": {
    "project": "depodomain",
    "order_id": "TRX20241228ABC123",
    "amount": 99000,
    "fee": 1003,
    "total_payment": 100003,
    "payment_method": "qris",
    "payment_number": "00020101021226610016...", // QR code string
    "expired_at": "2024-12-28T01:18:49.678Z"
  }
}
```

**Error Response (400/500):**
```json
{
  "error": "Invalid project or insufficient balance",
  "code": 400
}
```

### Check Payment Status
**Endpoint:** `GET https://app.pakasir.com/api/transactiondetail`

**Query Parameters:**
- `project`: Pakasir project slug
- `amount`: Payment amount
- `order_id`: Transaction ID
- `api_key`: Pakasir API key

**Success Response:**
```json
{
  "transaction": {
    "amount": 99000,
    "order_id": "TRX20241228ABC123",
    "project": "depodomain", 
    "status": "completed",
    "payment_method": "qris",
    "completed_at": "2024-12-28T08:07:02.819+07:00"
  }
}
```

### Payment Webhook (Incoming)
**Endpoint:** `POST /webhooks/pakasir` (Our FastAPI endpoint)

**Headers:**
- `X-Pakasir-Signature`: HMAC signature for verification
- `Content-Type`: application/json

**Payload:**
```json
{
  "amount": 99000,
  "order_id": "TRX20241228ABC123", 
  "project": "depodomain",
  "status": "completed",
  "payment_method": "qris",
  "completed_at": "2024-12-28T08:07:02.819+07:00",
  "metadata": {
    "telegram_id": 123456789,
    "telegram_username": "customer_user"
  }
}
```

---

## Telegram Bot API Integration

### Send Message
**Endpoint:** `POST https://api.telegram.org/bot{token}/sendMessage`

**Request Body:**
```json
{
  "chat_id": 123456789,
  "text": "🎉 Pesanan berhasil!\n📦 Produk: Netflix Premium\n🧾 Invoice: TRX123",
  "parse_mode": "Markdown",
  "reply_markup": {
    "inline_keyboard": [
      [{"text": "Kembali", "callback_data": "back_to_menu"}]
    ]
  }
}
```

### Send Welcome Sticker
**Endpoint:** `POST https://api.telegram.org/bot{token}/sendSticker`

**Request Body:**
```json
{
  "chat_id": 123456789,
  "sticker": "CAACAgIAAxkBAAIDbWkLZHuqPRCqCqmL9flozT9YJdWOAAIZUAAC4KOCB7lIn3OKexieNgQ"
}
```

### Send Photo with QR Code
**Endpoint:** `POST https://api.telegram.org/bot{token}/sendPhoto`

**Request Body:**
```json
{
  "chat_id": 123456789,
  "photo": "data:image/png;base64,iVBOR...", // Base64 QR code
  "caption": "💳 Scan QR Code untuk pembayaran\n⏰ Berlaku 10 menit",
  "reply_markup": {
    "inline_keyboard": [
      [
        {"text": "Checkout Page", "url": "https://app.pakasir.com/pay/..."},
        {"text": "Status Pembayaran", "callback_data": "check_payment_status"}
      ],
      [{"text": "Batalkan", "callback_data": "cancel_payment"}]
    ]
  }
}
```

### Handle Callback Query
**Incoming from Telegram:**
```json
{
  "update_id": 12345,
  "callback_query": {
    "id": "callback_id",
    "from": {"id": 123456789, "username": "user"},
    "data": "product_1_quantity_plus",
    "message": {"message_id": 456, "chat": {"id": 123456789}}
  }
}
```

---

## Internal API Endpoints

### Health Check
**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-28T10:30:00Z",
  "services": {
    "database": "ok",
    "redis": "ok", 
    "pakasir_api": "ok"
  }
}
```

### Admin Statistics 
**Endpoint:** `GET /admin/stats` (Internal use)

**Response:**
```json
{
  "total_users": 1250,
  "total_transactions": 3456,
  "active_orders": 12,
  "revenue_today": 2500000,
  "top_products": [
    {"id": 1, "name": "Netflix Premium", "sold": 45},
    {"id": 2, "name": "Spotify Premium", "sold": 32}
  ]
}
```

---

## Data Object Schemas

### User Object
```json
{
  "id": 123456789,
  "name": "John Doe", 
  "username": "johndoe",
  "email": "john@example.com",
  "whatsapp_number": "+62812345678",
  "member_status": "customer",
  "bank_id": "USR001",
  "account_balance": 150000.00,
  "is_banned": false,
  "created_at": "2024-12-28T10:00:00Z"
}
```

### Product Object
```json
{
  "id": 1,
  "name": "Netflix Premium 1 Month",
  "description": "Access to Netflix premium content for 1 month",
  "category": "Streaming",
  "customer_price": 50000.00,
  "reseller_price": 45000.00,
  "sold_count": 234,
  "stock_count": 15,
  "is_active": true
}
```

### Order Object
```json
{
  "id": 123,
  "invoice_id": "TRX20241228ABC123",
  "user_id": 123456789,
  "total_bill": 50000.00,
  "payment_method": "qris",
  "status": "paid",
  "items": [
    {
      "product_id": 1,
      "product_name": "Netflix Premium",
      "quantity": 1,
      "price_per_unit": 50000.00,
      "content": "email:test@netflix.com\npassword:secret123"
    }
  ],
  "created_at": "2024-12-28T10:00:00Z",
  "updated_at": "2024-12-28T10:05:00Z"
}
```

---

## Error Handling

### Standard Error Codes
- **400 Bad Request:** Invalid input data, malformed JSON
- **401 Unauthorized:** Invalid API key, expired session
- **403 Forbidden:** Insufficient permissions, banned user
- **404 Not Found:** Resource doesn't exist, invalid product ID
- **409 Conflict:** Stock unavailable, duplicate order
- **429 Too Many Requests:** Rate limit exceeded
- **500 Internal Server Error:** Database error, external API failure
- **502 Bad Gateway:** Pakasir API unreachable
- **503 Service Unavailable:** System maintenance mode

### Error Response Format
```json
{
  "error": "Insufficient stock for product ID 5",
  "code": 409,
  "details": {
    "product_id": 5,
    "requested": 3,
    "available": 1
  },
  "timestamp": "2024-12-28T10:30:00Z"
}
```

---

## Rate Limiting & Quotas

### Telegram Bot API
- **Message Sending:** 30 messages per second
- **File Upload:** 20 MB per file, 50 files per minute
- **Callback Queries:** Must respond within 30 seconds

### Pakasir API
- **Transaction Creation:** 100 requests per minute per project
- **Status Check:** 1000 requests per minute per project
- **Webhook Delivery:** 3 retry attempts with exponential backoff

### Internal Rate Limits
- **User Actions:** 10 commands per minute per user
- **Admin Commands:** 100 commands per minute per admin
- **Payment Checks:** 5 status checks per minute per order

---

## Security Considerations

### Authentication Methods
- **Pakasir:** API key in request body (HTTPS only)
- **Telegram:** Bot token in URL path
- **Webhooks:** HMAC signature validation

### Data Protection
- **Sensitive Data:** Never log payment details or API keys
- **PII Handling:** Mask user data in logs except user ID
- **Audit Logging:** All API calls logged with correlation IDs

---

## Cross-References

- See [06-data_schema.md](06-data_schema.md) for database schema that maps to these API objects.
- See [08-integration_plan.md](08-integration_plan.md) for detailed Pakasir integration workflow and error handling.
- See [09-security_manifest.md](09-security_manifest.md) for API security requirements and threat mitigation.

---

> Note for AI builders: All API integrations must implement exponential backoff retry logic and comprehensive error logging. Payment-related APIs require idempotency to prevent double-charging or stock assignment.