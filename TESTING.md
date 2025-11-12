# QuickCart Testing Guide 🧪

Complete guide to test every feature of your QuickCart bot before going live.

---

## 🎯 Testing Objectives

By the end of this guide, you'll have verified:
- ✅ Bot responds to commands
- ✅ Product catalog works
- ✅ Order flow is complete
- ✅ Payment integration works
- ✅ Stock management is accurate
- ✅ Admin commands function properly
- ✅ Database operations are correct

---

## 📋 Pre-Testing Checklist

Before you start testing:

- [ ] Bot is running (`docker-compose ps` shows all services "Up")
- [ ] You have your bot's Telegram username
- [ ] You have at least 2 Telegram accounts (one admin, one customer)
- [ ] You have small test amount in Pakasir (Rp 1,000 - Rp 5,000)
- [ ] Database is empty (fresh install) or you have backup

---

## 🚀 Part 1: Basic Connectivity Tests

### Test 1.1: Bot Responds to /start

**Steps:**
1. Open Telegram
2. Search for your bot
3. Send `/start`

**Expected Result:**
```
ᯓ Halo **Your Name** 👋🏻
Selamat datang di **QuickCart Store**

⤷ Total Pengguna: 1 Orang
⤷ Total Transaksi: 0x

Dokumentasi: [Baca Disini]
Silakan tombol dibawah ini untuk melihat produk yang tersedia.
```

**Should Display Buttons:**
```
[LIST PRODUK] [STOK]
[AKUN] [KIRIM PESAN]
[1] [2] [3] [4] ... (product buttons if products exist)
```

**✅ Pass Criteria:** Bot responds within 2 seconds with welcome message

**❌ If Failed:**
- Check logs: `docker-compose logs -f app`
- Verify `TELEGRAM_BOT_TOKEN` in `.env`
- Restart bot: `docker-compose restart app`

---

### Test 1.2: Health Check Endpoint

**Steps:**
```bash
curl http://localhost:8000/health
```

**Expected Result:**
```json
{
  "status": "healthy",
  "services": {
    "redis": "ok",
    "main_database": "ok",
    "audit_database": "ok"
  }
}
```

**✅ Pass Criteria:** All services show "ok"

---

### Test 1.3: Database Connection

**Steps:**
```bash
make db
# Then inside PostgreSQL shell:
\dt
```

**Expected Result:**
Should show tables:
- users
- products
- product_stocks
- orders
- order_items
- vouchers
- voucher_usage_cooldown

**✅ Pass Criteria:** All 7 tables exist

---

## 📦 Part 2: Product Management Tests

### Test 2.1: Add Product (Admin Command)

**Steps:**
1. In Telegram, send (replace with your admin account):
```
/add 1|Netflix Premium|Streaming|15000|Akun Netflix premium 1 bulan
```

**Expected Result:**
```
✅ Produk berhasil ditambahkan!

📦 ID: 1
📛 Nama: Netflix Premium
🏷️ Kategori: Streaming
💰 Harga: Rp15,000
📝 Deskripsi: Akun Netflix premium 1 bulan
```

**Verify in Database:**
```bash
make db
SELECT * FROM products WHERE id = 1;
```

**✅ Pass Criteria:** Product appears in database with correct values

---

### Test 2.2: Add Stock to Product

**Steps:**
```
/addstock 1|test@email.com:password123
```

**Expected Result:**
```
✅ Stok berhasil ditambahkan!

📦 Produk: Netflix Premium (ID: 1)
🔢 Total stok: 1
```

**Verify in Database:**
```sql
SELECT * FROM product_stocks WHERE product_id = 1;
```

**✅ Pass Criteria:** 
- Stock record exists
- `is_sold = false`
- Content is stored correctly

---

### Test 2.3: Add Multiple Products

**Add at least 3 products:**
```
/add 2|Spotify Premium|Music|20000|Spotify 1 bulan
/add 3|YouTube Premium|Video|25000|YouTube tanpa iklan
/add 4|Disney+ Hotstar|Streaming|30000|Disney+ 1 bulan
```

**Add stock to each:**
```
/addstock 2|spotify@test.com:pass123
/addstock 3|youtube@test.com:pass456
/addstock 4|disney@test.com:pass789
```

**✅ Pass Criteria:** All products added successfully

---

### Test 2.4: View Stock Status

**Steps:**
```
/stock
```

**Expected Result:**
```
📊 Status Stok Produk:

1. Netflix Premium
   ✅ Stok: 1
   💰 Harga: Rp15,000

2. Spotify Premium
   ✅ Stok: 1
   💰 Harga: Rp20,000

3. YouTube Premium
   ✅ Stok: 1
   💰 Harga: Rp25,000

4. Disney+ Hotstar
   ✅ Stok: 1
   💰 Harga: Rp30,000
```

**✅ Pass Criteria:** All products show correct stock count

---

## 🛒 Part 3: Customer Order Flow Tests

### Test 3.1: Browse Products

**Steps:**
1. Send `/start` (as customer account if you have one)
2. Click `[LIST PRODUK]`

**Expected Result:**
- Should show list of all products with stock
- Each product shows: name, price, stock available, description
- Pagination buttons if > 10 products

**✅ Pass Criteria:** Products display correctly

---

### Test 3.2: Select Product

**Steps:**
1. Send `1` (product ID)

**Expected Result:**
```
📦 Netflix Premium

💰 Harga: Rp15,000
📊 Stok: 1 tersedia
✅ Terjual: 0x

📝 Deskripsi:
Akun Netflix premium 1 bulan

Pilih jumlah yang ingin dibeli:
```

**Buttons:**
```
[-] [1] [+]
[+2] [+5] [+10]
[Lanjut ke pembayaran]
[Batalkan]
```

**✅ Pass Criteria:** Product details show correctly with quantity selector

---

### Test 3.3: Adjust Quantity

**Steps:**
1. Click `[+]` button multiple times
2. Click `[-]` button
3. Click `[+5]`

**Expected Result:**
- Number updates after each click
- Cannot go below 1
- Cannot exceed available stock

**✅ Pass Criteria:** Quantity adjusts correctly, respects limits

---

### Test 3.4: Proceed to Payment

**Steps:**
1. Click `[Lanjut ke pembayaran]`

**Expected Result:**
```
📋 Ringkasan Pesanan:

🛒 Produk: Netflix Premium
🔢 Jumlah: 1
💵 Subtotal: Rp15,000
💳 Biaya Pembayaran: Rp415
━━━━━━━━━━━━━━━━━
💰 Total: Rp15,415

Pilih metode pembayaran:
```

**Buttons:**
```
[QRIS] [SALDO]
[KEMBALI] [BATALKAN]
```

**Verify Fee Calculation:**
- Fee should be: `(15000 * 0.007) + 310 = 105 + 310 = 415`
- Total: `15000 + 415 = 15415` ✓

**✅ Pass Criteria:** 
- Math is correct
- Payment buttons appear
- Can go back or cancel

---

### Test 3.5: QRIS Payment Flow

**Steps:**
1. Click `[QRIS]`

**Expected Result:**
```
💳 Pembayaran QRIS

🧾 Invoice: TRX20250112xxxxxx
💰 Total: Rp15,415
⏰ Berlaku: 10 menit

[QR Code Image]

Cara pembayaran:
1. Buka aplikasi e-wallet Anda
2. Scan QR code di atas
3. Konfirmasi pembayaran
4. Tunggu notifikasi dari bot

⏱️ Invoice akan kadaluarsa dalam 10 menit
```

**Buttons:**
```
[Checkout Page] [Status Pembayaran] [Batalkan]
```

**Verify in Database:**
```sql
SELECT * FROM orders ORDER BY created_at DESC LIMIT 1;
```

Should show:
- `status = 'pending'`
- `payment_method = 'qris'`
- `total_bill = 15415`

**✅ Pass Criteria:**
- QR code displays
- Invoice ID generated
- Order created in database with pending status
- Timer starts (10 minutes)

---

### Test 3.6: Payment Completion (Webhook Test)

**This requires actual payment or webhook simulation**

**Option A: Make Real Small Payment**
1. Scan QR code with e-wallet
2. Pay the amount
3. Wait for webhook

**Option B: Simulate Webhook (Development)**
```bash
curl -X POST http://localhost:8000/webhooks/pakasir \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "TRX20250112xxxxxx",
    "status": "paid",
    "amount": 15415
  }'
```

**Expected Result (in Telegram):**
```
🎉 Pesanan berhasil!

📦 Produk: Netflix Premium
🔢 Jumlah: 1
🧾 Invoice: TRX20250112xxxxxx

Berikut detail produk Anda:
━━━━━━━━━━━━━━━━━
test@email.com:password123
━━━━━━━━━━━━━━━━━

Terima kasih telah berbelanja! 😊
```

**Verify in Database:**
```sql
-- Order status updated
SELECT status FROM orders WHERE invoice_id = 'TRX20250112xxxxxx';
-- Should be: paid

-- Stock marked as sold
SELECT is_sold FROM product_stocks WHERE content LIKE '%test@email.com%';
-- Should be: true

-- Product sold count increased
SELECT sold_count FROM products WHERE id = 1;
-- Should be: 1
```

**✅ Pass Criteria:**
- User receives product content
- Order status changes to "paid"
- Stock marked as sold
- Sold count incremented
- Audit log created

---

### Test 3.7: Payment Expiry (10 Minutes)

**Steps:**
1. Create a new order (select product, choose QRIS)
2. Don't pay
3. Wait 10 minutes (or change timer for testing)

**Expected Result (after 10 min):**
```
⏰ Invoice Expired

Invoice pembayaran Anda telah kadaluarsa.

🧾 Invoice: TRX20250112xxxxxx

Jika Anda sudah membayar, dana akan dikembalikan (dipotong biaya).
Silakan buat pesanan baru jika masih diperlukan.

[Kembali]
```

**Verify in Database:**
```sql
SELECT status FROM orders WHERE invoice_id = 'TRX20250112xxxxxx';
-- Should be: expired
```

**✅ Pass Criteria:**
- Order automatically expires after 10 min
- Stock released (is_sold = false)
- User notified
- Original QR message edited/deleted

---

## 👤 Part 4: User Account Tests

### Test 4.1: View Account Info

**Steps:**
1. Click `[AKUN]` button

**Expected Result:**
```
👤 Informasi Akun

🆔 User ID: 123456789
📛 Nama: Your Name
👤 Username: @yourusername
📧 Email: -
📱 WhatsApp: -
💰 Saldo: Rp0
🏦 Bank ID: AB1234
⭐ Status: Customer

[Ubah Nama] [Ubah Email]
[Ubah WhatsApp] [Riwayat Transaksi]
[Deposit]
```

**✅ Pass Criteria:** Shows correct user information

---

### Test 4.2: Update Profile

**Steps:**
1. Click `[Ubah Email]`
2. Send email: `test@example.com`

**Expected Result:**
```
✅ Email berhasil diperbarui!

Email Anda: test@example.com
```

**Verify in Database:**
```sql
SELECT email FROM users WHERE id = 123456789;
```

**✅ Pass Criteria:** Email updated in database

---

### Test 4.3: View Transaction History

**Steps:**
1. Click `[Riwayat Transaksi]`

**Expected Result:**
```
📊 Riwayat Transaksi Anda:

1. ✅ Lunas - Netflix Premium
   🧾 TRX20250112xxxxxx
   💰 Rp15,415
   📅 12 Jan 2025, 14:30

[Halaman 1/1]
```

**✅ Pass Criteria:** Shows all completed orders

---

### Test 4.4: Balance Deposit

**Steps:**
1. Click `[Deposit]`
2. Enter amount: `50000`

**Expected Result:**
- QR code generated for deposit
- Same 10-minute timer
- After payment: balance increases

**Verify:**
```sql
SELECT account_balance FROM users WHERE id = 123456789;
-- Should be: 50000 (or amount minus fees)
```

**✅ Pass Criteria:**
- Deposit creates order
- Payment increases balance
- Transaction logged

---

## 👑 Part 5: Admin Command Tests

### Test 5.1: Edit Product

**Steps:**
```
/editproduct 1|name|Netflix Premium Family
```

**Expected Result:**
```
✅ Produk berhasil diubah!

📦 Netflix Premium Family
💰 Harga: Rp15,000
```

**✅ Pass Criteria:** Product name updated

---

### Test 5.2: Set Discount

**Steps:**
```
/disc 1|20%
```

**Expected Result:**
```
✅ Diskon berhasil diterapkan!

📦 Produk: Netflix Premium Family
🏷️ Harga Normal: Rp15,000
💥 Diskon: 20%
💰 Harga Sekarang: Rp12,000
```

**✅ Pass Criteria:** Discount calculated and applied

---

### Test 5.3: Set Reseller Price

**Steps:**
```
/priceress 1|12000
```

**Expected Result:**
```
✅ Harga reseller berhasil diset!

📦 Produk: Netflix Premium Family
👥 Harga Customer: Rp15,000
⭐ Harga Reseller: Rp12,000
```

**✅ Pass Criteria:** Reseller price set correctly

---

### Test 5.4: Promote User to Reseller

**Steps:**
```
/addreseller 123456789
```

**Expected Result:**
```
✅ User berhasil diupgrade menjadi reseller!

👤 User: @yourusername
⭐ Status baru: Reseller
```

**Verify User Sees Reseller Price:**
- As that user, check product 1
- Should show Rp12,000 instead of Rp15,000

**✅ Pass Criteria:** User upgraded, sees reseller pricing

---

### Test 5.5: Transfer Balance

**Steps:**
```
/transfer 123456789|25000
```

**Expected Result:**
```
✅ Transfer berhasil!

👤 User: @yourusername
💰 Saldo ditambah: Rp25,000
💳 Saldo sekarang: Rp75,000
```

**✅ Pass Criteria:** Balance transferred correctly

---

### Test 5.6: View User Info (Admin)

**Steps:**
```
/info 123456789
```

**Expected Result:**
```
👤 Informasi User

🆔 ID: 123456789
📛 Nama: Your Name
👤 Username: @yourusername
📧 Email: test@example.com
💰 Saldo: Rp75,000
⭐ Status: Reseller
🛒 Total Order: 1x
```

**✅ Pass Criteria:** Shows complete user info

---

### Test 5.7: Create Giveaway Voucher

**Steps:**
```
/giveaway
```

Follow prompts:
1. Amount: `10000`
2. Quantity: `5`
3. Expiry: `24` (hours)

**Expected Result:**
```
🎉 Giveaway voucher berhasil dibuat!

💰 Nominal: Rp10,000
🎫 Jumlah: 5 voucher
⏰ Berlaku: 24 jam

Kode voucher:
1. GIFT-AB1CD2
2. GIFT-EF3GH4
3. GIFT-IJ5KL6
4. GIFT-MN7OP8
5. GIFT-QR9ST0

Bagikan kode ke pelanggan! 🎁
```

**✅ Pass Criteria:** 
- 5 unique codes generated
- All valid for 24 hours
- Stored in database

---

### Test 5.8: Delete Product Stock

**Steps:**
1. Add some stock: `/addstock 2|dummy@test.com:pass`
2. Get stock ID from database
3. Delete: `/delstock 2|<stock-id-here>`

**Expected Result:**
```
✅ Stok berhasil dihapus!

📦 Produk: Spotify Premium
🆔 Stock ID: xxxxxxxx-xxxx-xxxx...
```

**✅ Pass Criteria:** Stock deleted from database

---

## 🎫 Part 6: Voucher System Tests

### Test 6.1: Apply Voucher to Order

**Steps:**
1. Start order for product (e.g., product 2 = Rp20,000)
2. Enter voucher code: `GIFT-AB1CD2`

**Expected Result:**
```
✅ Voucher berhasil diterapkan!

🎫 Kode: GIFT-AB1CD2
💰 Diskon: Rp10,000

📋 Ringkasan:
💵 Subtotal: Rp20,000
🎫 Diskon: -Rp10,000
💳 Biaya: Rp380
━━━━━━━━━━━━━━━━━
💰 Total: Rp10,380
```

**✅ Pass Criteria:**
- Discount applied correctly
- Total calculated properly
- Voucher marked as used after payment

---

### Test 6.2: Voucher Cooldown

**Steps:**
1. Use voucher `GIFT-AB1CD2`
2. Immediately try to use another voucher `GIFT-EF3GH4`

**Expected Result:**
```
⏰ Cooldown Aktif

Anda baru saja menggunakan voucher.
Silakan tunggu 5 menit sebelum menggunakan voucher lagi.

Waktu tersisa: 4 menit 58 detik
```

**✅ Pass Criteria:** Cooldown enforced (5 minutes)

---

### Test 6.3: Expired Voucher

**Steps:**
1. Create voucher that expires in 1 minute
2. Wait 2 minutes
3. Try to use it

**Expected Result:**
```
❌ Voucher tidak valid

Kode: GIFT-XXXXX
Alasan: Voucher telah kadaluarsa
```

**✅ Pass Criteria:** Expired voucher rejected

---

## 🔒 Part 7: Security & Edge Case Tests

### Test 7.1: Non-Admin Command Rejection

**Steps:**
1. Use non-admin Telegram account
2. Try: `/add 99|Hack|Test|1|Test`

**Expected Result:**
- No response OR error message
- Command not executed

**✅ Pass Criteria:** Non-admin cannot use admin commands

---

### Test 7.2: Order Out-of-Stock Product

**Steps:**
1. Sell all stock of product 1
2. Try to order product 1 again

**Expected Result:**
```
❌ Stok Habis

Maaf, produk ini sedang tidak tersedia.
Silakan pilih produk lain atau coba lagi nanti.
```

**✅ Pass Criteria:** Cannot order products with no stock

---

### Test 7.3: Concurrent Order Prevention

**Steps:**
1. Start order for product 1 (don't complete)
2. Try to start another order for product 2

**Expected Result:**
```
⚠️ Order Aktif

Anda masih memiliki order yang belum selesai.
Silakan selesaikan atau batalkan order tersebut terlebih dahulu.

[Lanjutkan Order] [Batalkan Order]
```

**✅ Pass Criteria:** Only one pending order allowed per user

---

### Test 7.4: Invalid Input Handling

**Steps:**
```
/add invalid|format|test
/addstock 999|content
/transfer abc|def
```

**Expected Result:**
```
❌ Format salah

Contoh yang benar:
/add 1|Produk|Kategori|50000|Deskripsi
```

**✅ Pass Criteria:** Clear error messages with examples

---

### Test 7.5: Rate Limiting

**Steps:**
1. Send `/start` 20 times rapidly

**Expected Result (after ~10 requests):**
```
⏰ Terlalu Cepat

Silakan tunggu beberapa detik sebelum mencoba lagi.
```

**✅ Pass Criteria:** Rate limiting active

---

## 📊 Part 8: Database Integrity Tests

### Test 8.1: Audit Log Verification

**Steps:**
```bash
# Connect to audit database
docker-compose exec db psql -U quickcart -d quickcart_audit

# Check audit logs
SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 10;
```

**Expected Result:**
- All major actions logged (user creation, orders, payments, admin commands)
- Timestamps accurate
- Actor IDs correct

**✅ Pass Criteria:** Audit trail complete

---

### Test 8.2: Payment Audit Logs

**Steps:**
```sql
SELECT * FROM payment_audit_logs ORDER BY timestamp DESC;
```

**Expected Result:**
- All payment attempts logged
- Status transitions recorded
- Gateway responses stored

**✅ Pass Criteria:** Complete payment history

---

### Test 8.3: Data Consistency

**Steps:**
```sql
-- Check sold count matches actual sales
SELECT 
  p.id,
  p.sold_count,
  (SELECT COUNT(*) FROM product_stocks WHERE product_id = p.id AND is_sold = true) as actual_sold
FROM products p;
```

**Expected Result:**
- `sold_count` = `actual_sold` for all products

**✅ Pass Criteria:** Counts match

---

## ⚡ Part 9: Performance Tests

### Test 9.1: Response Time

**Steps:**
```bash
# Send /start command, measure response time
time curl -X POST http://localhost:8000/webhooks/telegram \
  -d '{"message":{"text":"/start"}}'
```

**Expected Result:**
- Response < 2 seconds

**✅ Pass Criteria:** Fast response times

---

### Test 9.2: Concurrent Users

**Steps:**
- Simulate 10 users ordering simultaneously
- Use testing tool or scripts

**Expected Result:**
- All orders processed
- No stock overselling
- No database deadlocks

**✅ Pass Criteria:** Handles concurrent load

---

## 📋 Testing Checklist Summary

Copy this checklist and mark as you complete each test:

### Basic Tests
- [ ] Bot responds to /start
- [ ] Health check passes
- [ ] Database tables exist

### Product Tests
- [ ] Add product works
- [ ] Add stock works
- [ ] View stock shows correct data
- [ ] Multiple products handled

### Order Flow Tests
- [ ] Browse products works
- [ ] Select product works
- [ ] Quantity adjustment works
- [ ] Payment summary correct
- [ ] QRIS generation works
- [ ] Payment completion works
- [ ] Payment expiry works

### User Tests
- [ ] View account info
- [ ] Update profile
- [ ] Transaction history
- [ ] Balance deposit

### Admin Tests
- [ ] Edit product
- [ ] Set discount
- [ ] Set reseller price
- [ ] Promote to reseller
- [ ] Transfer balance
- [ ] View user info
- [ ] Create vouchers
- [ ] Delete stock

### Voucher Tests
- [ ] Apply voucher
- [ ] Cooldown enforcement
- [ ] Expired voucher rejection

### Security Tests
- [ ] Non-admin rejection
- [ ] Out of stock prevention
- [ ] Concurrent order prevention
- [ ] Invalid input handling
- [ ] Rate limiting

### Database Tests
- [ ] Audit logs complete
- [ ] Payment logs accurate
- [ ] Data consistency verified

### Performance Tests
- [ ] Response time acceptable
- [ ] Concurrent users handled

---

## 🎉 All Tests Passed?

Congratulations! Your QuickCart bot is ready for production.

**Next Steps:**
1. Set up SSL/HTTPS
2. Configure production environment
3. Set up automatic backups
4. Configure monitoring/alerts
5. Add real products and stock
6. Announce your store!

**Before Going Live:**
- [ ] Change all default passwords
- [ ] Set ENVIRONMENT=production
- [ ] Set DEBUG=false
- [ ] Configure Pakasir webhook
- [ ] Test with real small payment
- [ ] Set up backup schedule
- [ ] Document your procedures

---

## 🐛 Found Issues?

1. **Document the issue:**
   - What test failed?
   - What was the error message?
   - What were you doing?

2. **Check logs:**
   ```bash
   make logs
   ```

3. **Check database:**
   ```bash
   make db
   ```

4. **Report issue:**
   - Open GitHub issue
   - Include logs and error messages
   - Describe expected vs actual behavior

---

**Happy testing! 🚀**