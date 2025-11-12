# Pakasir QRIS Integration - Usage Example

Panduan lengkap penggunaan Pakasir payment gateway (QRIS only) di QuickCart.

**Reference:** `docs/pakasir.md` (Official API Documentation)

---

## 📋 Table of Contents

1. [Setup](#setup)
2. [Creating QRIS Payment](#creating-qris-payment)
3. [Checking Payment Status](#checking-payment-status)
4. [Webhook Handling](#webhook-handling)
5. [Complete Flow Example](#complete-flow-example)

---

## Setup

### Environment Variables

Di `.env`, pastikan konfigurasi Pakasir sudah benar:

```bash
# Required
PAKASIR_API_KEY=your_api_key_from_pakasir_dashboard
PAKASIR_PROJECT_SLUG=your_project_slug

# Optional (recommended)
PAKASIR_BASE_URL=https://app.pakasir.com
PAKASIR_PAYMENT_CUSTOM_DOMAIN=https://pots.my.id
PAKASIR_WEBHOOK_SECRET=your_webhook_secret_if_any
```

### Import Client

```python
from src.integrations.pakasir import pakasir_client
```

---

## Creating QRIS Payment

### Basic Usage

```python
# Create QRIS payment
order_id = f"tg{telegram_user_id}-{unique_suffix}"
amount = 10000  # Rp 10,000 (integer, no decimals)

payment_data = await pakasir_client.create_qris_payment(
    order_id=order_id,
    amount=amount
)

if payment_data:
    print("Payment created successfully!")
    print(f"Order ID: {payment_data['payment']['order_id']}")
    print(f"Total: Rp {payment_data['payment']['total_payment']:,}")
    print(f"Fee: Rp {payment_data['payment']['fee']:,}")
else:
    print("Failed to create payment")
```

### With Metadata (Recommended)

```python
# Include telegram info for easier webhook processing
payment_data = await pakasir_client.create_qris_payment(
    order_id=f"tg{user.telegram_id}-ORDER123",
    amount=50000,
    metadata={
        "telegram_id": user.telegram_id,
        "telegram_username": user.username,
        "product_id": product.id,
        "quantity": 1
    }
)
```

### Response Structure

```json
{
  "payment": {
    "project": "your-project",
    "order_id": "tg12345-ORDER123",
    "amount": 50000,
    "fee": 660,
    "total_payment": 50660,
    "payment_method": "qris",
    "payment_number": "00020101021226610016ID.CO.SHOPEE.WWW...",
    "expired_at": "2025-09-19T01:18:49.678622564Z"
  }
}
```

---

## Extracting QR Code

### Get QRIS String

```python
payment_data = await pakasir_client.create_qris_payment(order_id, amount)

# Extract QRIS code string
qris_code = pakasir_client.extract_qris_code(payment_data)

if qris_code:
    print(f"QRIS Code: {qris_code[:50]}...")  # Very long string
```

### Generate QR Image (Example using qrcode library)

```python
import qrcode
from io import BytesIO

# Generate QR code image
qris_code = pakasir_client.extract_qris_code(payment_data)

qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data(qris_code)
qr.make(fit=True)

# Create image
img = qr.make_image(fill_color="black", back_color="white")

# Save to BytesIO for sending via Telegram
bio = BytesIO()
img.save(bio, 'PNG')
bio.seek(0)

# Send to user
await context.bot.send_photo(
    chat_id=user.telegram_id,
    photo=bio,
    caption=f"💳 Scan QR untuk bayar Rp {amount:,}\n"
            f"⏰ Berlaku 10 menit"
)
```

---

## Getting Checkout URL

### Generate Payment Link

```python
# Generate checkout URL (auto-redirect to QRIS)
checkout_url = pakasir_client.get_checkout_url(
    order_id="tg12345-ORDER123",
    amount=50000
)

print(checkout_url)
# Output: https://pots.my.id/pay/projectslug/50000?order_id=tg12345-ORDER123&qris_only=1
```

### Send to User

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Create button with checkout URL
keyboard = [
    [InlineKeyboardButton("💳 Bayar via Browser", url=checkout_url)]
]
reply_markup = InlineKeyboardMarkup(keyboard)

await context.bot.send_message(
    chat_id=user.telegram_id,
    text=f"Total: Rp {total_payment:,}\n"
         f"Klik tombol di bawah untuk membayar:",
    reply_markup=reply_markup
)
```

---

## Checking Payment Status

### Check Status

```python
# Check if payment has been completed
status_data = await pakasir_client.get_payment_status(
    order_id="tg12345-ORDER123",
    amount=50000  # Amount is required
)

if status_data:
    transaction = status_data.get("transaction", {})
    status = transaction.get("status")
    
    if status == "completed":
        print("✅ Payment successful!")
        print(f"Completed at: {transaction.get('completed_at')}")
    elif status == "pending":
        print("⏳ Payment still pending")
    elif status == "expired":
        print("❌ Payment expired")
```

### Polling Example

```python
import asyncio

async def wait_for_payment(order_id: str, amount: int, max_wait: int = 600):
    """
    Poll payment status every 10 seconds
    max_wait: Maximum wait time in seconds (default: 10 minutes)
    """
    elapsed = 0
    interval = 10
    
    while elapsed < max_wait:
        status_data = await pakasir_client.get_payment_status(order_id, amount)
        
        if status_data:
            status = status_data.get("transaction", {}).get("status")
            
            if status == "completed":
                return True
            elif status == "expired":
                return False
        
        await asyncio.sleep(interval)
        elapsed += interval
    
    return False  # Timeout

# Usage
paid = await wait_for_payment("tg12345-ORDER123", 50000)
if paid:
    print("Payment received!")
```

---

## Webhook Handling

### Webhook Endpoint

Webhook handler sudah ada di `src/main.py`:

```python
@app.post("/webhooks/pakasir")
async def pakasir_webhook(request: Request):
    """
    Receives payment notifications from Pakasir
    """
    # Automatically handles:
    # - Signature validation (if PAKASIR_WEBHOOK_SECRET is set)
    # - Payment status processing
    # - Logging
```

### Expected Webhook Payload

```json
{
  "amount": 50000,
  "order_id": "tg12345-ORDER123",
  "project": "your-project",
  "status": "completed",
  "payment_method": "qris",
  "completed_at": "2025-09-10T08:07:02.819+07:00",
  "metadata": {
    "telegram_id": 12345,
    "telegram_username": "user123",
    "product_id": 5,
    "quantity": 1
  }
}
```

### Processing Webhook

Di `src/main.py`, tambahkan logic di bagian `# TODO: Process successful payment`:

```python
if status == "completed":
    # Extract user info
    telegram_id = metadata.get("telegram_id")
    
    # If not in metadata, extract from order_id (format: tg{id}-{suffix})
    if not telegram_id and order_id.startswith("tg"):
        telegram_id = int(order_id.split("-")[0][2:])
    
    # Update order in database
    async with get_db_session() as session:
        order = await session.get(Order, order_id)
        if order:
            order.status = "paid"
            order.paid_at = completed_at
            order.payment_method = payment_method
            await session.commit()
            
            # Deliver product to user
            await deliver_product_to_user(telegram_id, order)
            
            # Send confirmation
            await send_payment_confirmation(telegram_id, order)
            
            # Log to audit database
            await log_payment_audit(order, amount, "completed")
```

### Configure Webhook in Pakasir Dashboard

1. Login ke Pakasir dashboard
2. Pilih project Anda
3. Masuk ke Settings → Webhooks
4. Set Webhook URL: `https://yourdomain.com/webhooks/pakasir`
5. (Optional) Set webhook secret untuk security

---

## Complete Flow Example

### Full Payment Flow (Bot Handler)

```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.integrations.pakasir import pakasir_client
from src.models.order import Order
from src.core.database import get_db_session

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle payment creation and display
    """
    user = update.effective_user
    
    # Get order details from context
    product_id = context.user_data.get("selected_product_id")
    quantity = context.user_data.get("quantity", 1)
    
    # Calculate amount (from database)
    async with get_db_session() as session:
        product = await session.get(Product, product_id)
        amount = product.price * quantity
        fee = calculate_pakasir_fee(amount)  # 0.7% + Rp310
        total = amount + fee
    
    # Create order in database
    order_id = f"tg{user.id}-{generate_random_suffix()}"
    
    async with get_db_session() as session:
        order = Order(
            order_id=order_id,
            user_id=user.id,
            product_id=product_id,
            quantity=quantity,
            amount=amount,
            fee=fee,
            total=total,
            status="pending"
        )
        session.add(order)
        await session.commit()
    
    # Create QRIS payment
    payment_data = await pakasir_client.create_qris_payment(
        order_id=order_id,
        amount=total,
        metadata={
            "telegram_id": user.id,
            "telegram_username": user.username,
            "product_id": product_id,
            "quantity": quantity
        }
    )
    
    if not payment_data:
        await update.message.reply_text(
            "❌ Gagal membuat pembayaran. Silakan coba lagi."
        )
        return
    
    # Extract QRIS code and generate QR image
    qris_code = pakasir_client.extract_qris_code(payment_data)
    qr_image = generate_qr_image(qris_code)  # Your QR generator
    
    # Get checkout URL
    checkout_url = pakasir_client.get_checkout_url(order_id, total)
    
    # Get expiry time
    expiry = pakasir_client.get_expiry_time(payment_data)
    
    # Send QR code to user
    keyboard = [
        [InlineKeyboardButton("💳 Bayar via Browser", url=checkout_url)],
        [InlineKeyboardButton("🔄 Cek Status", callback_data=f"check_payment:{order_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=qr_image,
        caption=f"💰 Total Pembayaran: Rp {total:,}\n"
                f"📦 Produk: {product.name}\n"
                f"🔢 Order ID: {order_id}\n\n"
                f"⏰ Berlaku hingga {expiry.strftime('%H:%M')}\n\n"
                f"Scan QR atau klik tombol di bawah untuk membayar.",
        reply_markup=reply_markup
    )
    
    # Start background task to monitor payment
    context.application.create_task(
        monitor_payment(user.id, order_id, total, context)
    )

async def monitor_payment(user_id: int, order_id: str, amount: int, context):
    """
    Background task to monitor payment status
    """
    paid = await wait_for_payment(order_id, amount, max_wait=600)
    
    if paid:
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Pembayaran berhasil! Produk sedang dikirim..."
        )
        # Delivery akan dihandle oleh webhook
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Pembayaran expired. Silakan order ulang."
        )

def calculate_pakasir_fee(amount: int) -> int:
    """
    Calculate Pakasir fee: 0.7% + Rp310
    """
    percentage_fee = int(amount * 0.007)
    fixed_fee = 310
    return percentage_fee + fixed_fee

def generate_random_suffix(length: int = 8) -> str:
    """Generate random suffix for order_id"""
    import secrets
    import string
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))
```

---

## Testing with Sandbox

### Payment Simulation (Sandbox Mode Only)

```python
# Only works if your project is in Sandbox mode
result = await pakasir_client.simulate_payment(
    order_id="tg12345-TEST123",
    amount=10000
)

if result:
    print("✅ Payment simulated, webhook should be triggered")
```

### Testing Webhook Locally

Use ngrok or similar tool:

```bash
# Terminal 1: Start your app
docker compose up -d

# Terminal 2: Start ngrok
ngrok http 8000

# Configure webhook URL in Pakasir dashboard:
# https://abc123.ngrok.io/webhooks/pakasir
```

---

## Best Practices

### 1. Always Include Metadata

```python
# ✅ Good - easy to identify user from webhook
payment_data = await pakasir_client.create_qris_payment(
    order_id=f"tg{user_id}-{suffix}",
    amount=amount,
    metadata={"telegram_id": user_id, "telegram_username": username}
)

# ❌ Bad - hard to track user
payment_data = await pakasir_client.create_qris_payment(
    order_id="ORDER123",
    amount=amount
)
```

### 2. Use Descriptive Order IDs

```python
# ✅ Good - contains user info
order_id = f"tg{telegram_id}-{timestamp}-{product_id}"

# ❌ Bad - no context
order_id = str(uuid.uuid4())
```

### 3. Handle All Payment Statuses

```python
status = webhook_data.get("status")

if status == "completed":
    # Deliver product
    pass
elif status == "expired":
    # Clean up, notify user
    pass
elif status == "pending":
    # Wait or remind user
    pass
```

### 4. Log Everything

```python
from src.models.audit import PaymentAuditLog

# Log to audit database
await log_payment_event(
    order_id=order_id,
    event_type="payment_created",
    amount=amount,
    status="pending",
    payment_metadata=payment_data
)
```

### 5. Validate Webhook Signature

```python
# In production, always set PAKASIR_WEBHOOK_SECRET
# The webhook handler will automatically validate signature
```

---

## Troubleshooting

### Payment Creation Failed

```python
payment_data = await pakasir_client.create_qris_payment(order_id, amount)

if not payment_data:
    # Check logs for errors
    # Common issues:
    # - Invalid API key
    # - Invalid project slug
    # - Network timeout
    # - Pakasir service down
    pass
```

### Webhook Not Received

1. Check webhook URL is publicly accessible
2. Verify webhook URL in Pakasir dashboard
3. Check firewall allows incoming from Pakasir IPs
4. Test with ngrok for local development
5. Check application logs for errors

### QR Code Not Scanning

```python
# Ensure you're using the payment_number field
qris_code = payment_data.get("payment", {}).get("payment_number")

# Generate QR with proper version/size
qr = qrcode.QRCode(version=1, box_size=10, border=5)
```

---

## Additional Resources

- **Official Docs:** `docs/pakasir.md`
- **Integration Code:** `src/integrations/pakasir.py`
- **Webhook Handler:** `src/main.py` (POST `/webhooks/pakasir`)
- **Config:** `src/core/config.py`

---

**Last Updated:** January 2025  
**API Version:** Pakasir v1  
**Payment Method:** QRIS Only