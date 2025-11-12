# QuickCart Telegram Bot – Functional & Technical Blueprint

> **Note:**
> All inline/reply keyboard buttons must be in Bahasa Indonesia.
> All bot explanations, notifications, and documentation are in English.
> Backend variables use `snake_case`. Database columns follow schema conventions.
> This document is designed for AI/engineers to implement the system with zero ambiguity.

---

## 1. Introduction

QuickCart is a Telegram auto-order bot for digital products (e.g., tutorials, premium accounts, courses). The system is inspired by Lynk.id: users receive product content after successful payment. The bot supports flexible navigation, robust error handling, and a clear separation between public/admin features.

---

## 2. User Flows

### 2.1. Onboarding & Main Menu

- **/start**:
  - Sends welcome sticker (`sticker="CAACAgIAAxkBAAIDbWkLZHuqPRCqCqmL9flozT9YJdWOAAIZUAAC4KOCB7lIn3OKexieNgQ"`).
  - Prompts for name, WhatsApp number, and email (all can be skipped, defaults: 'Anonymous', 'null', 'null').
  - Shows main menu with user stats and documentation link.

- **Main Menu (Reply Keyboard):**
  ```
  [LIST PRODUK] [STOK]
  [AKUN] [KIRIM PESAN]
  [1] [2] [3] [4] [5] [6] [7] [8]
  [9] [10] [11] [12] [13] [14] [15] [16]
  [17] [18] [19] [20] [21] [22] [23] [24]
  ```
  - Numbers = product_id (only products with stock, sorted ascending).

- **Main Menu Welcome Message Example:**
  ```
  ᯓ Halo **{name}** 👋🏻
  Selamat datang di **{store_name}**

  ⤷ **Total Pengguna: {total_user} Orang**
  ⤷ **Total Transaksi: {total_transaction}x**

  Dokumentasi: [Baca Disini]{https://notion.so/blabla}
  Silakan tombol dibawah ini untuk melihat produk yang tersedia.
  ```
  - Inline buttons: `[Kategori] [Terlaris] [Semua Produk]`

---

### 2.2. Product Browsing & Ordering

- **[Kategori]**: Shows categories as inline buttons (`[Tanpa Kategori] [Kategori 1] ... [Kembali]`).
  - Selecting a category lists products in that category, paginated, with `[KEMBALI] [SELANJUTNYA 1/{total_page}]`.

- **[Terlaris]**: Lists best-selling products, with `[Kembali] [Top Buyers]`.

- **[Semua Produk]**: Lists all products (including out of stock), paginated.

- **Order Flow:**
  1. User sends a product_id (e.g., '1').
  2. Bot responds with product info (name, stock, price, sold, description).
  3. Inline buttons: `[-] [+] [+2] [+5] [+10] [Lanjut ke pembayaran] [Batalkan]`
  4. Quantity is adjusted via buttons.
  5. `[Lanjut ke pembayaran]` shows order summary (product, price, quantity, fee, total), with `[QRIS] [SALDO] [KEMBALI] [BATALKAN]`.

- **Payment Flow:**
  - **[QRIS]**: Shows QR code, payment instructions, invoice ID, and expiry (10 minutes).
    Inline: `[Checkout Page] [Status Pembayaran] [Batalkan]`
    - If unpaid after 10 minutes, bot edits message to show invoice expired and notes refund policy when customer keeps paying while invoice is expired ('jika tetap membayar ketika invoice sudah expired, maka pembayaran akan dibatalkan dan uang akan dikembalikan dan dipotong sesuai fee transaksi.').
    - If paid, bot sends product content.
  - **[SALDO]**: Confirms/cancels payment with account balance.

- **Flexible Navigation:**
  Users can click any button at any time. The bot must context-switch to the new flow, discarding previous state if needed. No need to cancel before starting a new operation.

---

### 2.3. Account Management

- **[AKUN]**: Shows user info (user_id, name, username, email, WhatsApp, saldo, bank_id, member status).
  - Inline: `[Ubah Nama] [Ubah Email] [Ubah Whatsapp] [Riwayat Transaksi] [Deposit]`
    - `[Deposit]`: Starts deposit flow (see 2.5).
    - `[Riwayat Transaksi]`: Lists all user transactions, paginated.

---

### 2.4. Messaging Admins

- **[KIRIM PESAN]**:
  User is prompted to input a message (optionally with 1 image).
  Message is sent to all admins (and whitelisted groups).
  Admins can reply directly via bot or group.

---

### 2.5. Deposit Flow

- **[Deposit]** (from [AKUN]):
  - User chooses amount, bot shows payment QR (same as order flow), with fee applied.
  - If paid, saldo (`account_balance`) is increased (minus fee).
  - If unpaid after 10 minutes, bot edits invoice message to show expired.
  - Example notification:
    - User: "Deposit berhasil. Saldo Anda telah bertambah sebesar Rp{amount} (setelah fee)."
    - Admin: "User {user_name} berhasil deposit Rp{amount}."

---

## 3. Command Reference

### 3.1. Public Commands (Accessible to all users)

| Command      | Description                        | Example Format                |
|--------------|------------------------------------|-------------------------------|
| `/start`     | Start the bot and show main menu   | `/start`                      |
| `/stock`     | Show available product stock       | `/stock`                      |
| `/order`     | Guide on how to order              | `/order`                      |
| `/refund`    | Calculate refund for an invoice    | `/refund TRX123456`           |
| `/reff`      | Alias for `/refund`                | `/reff TRX123456`             |

### 3.2. Admin Commands (Admins only)

| Command         | Description                                   | Example Format                       |
|-----------------|-----------------------------------------------|--------------------------------------|
| `/add`          | Add new product                               | `/add 101|Netflix|Streaming|50000|Akun premium.` |
| `/addstock`     | Add stock to product (bulk via newline)       | `/addstock 101|akun1:pass1`          |
| `/del`          | Delete product (soft delete)                  | `/del 101`                           |
| `/delstock`     | Delete specific stock by ID                   | `/delstock 101|STCK5XYZ`             |
| `/delallstock`  | Delete all unsold stock for a product         | `/delallstock 101`                   |
| `/editid`       | Change product ID                             | `/editid 101|102`                    |
| `/editcategory` | Change product category                       | `/editcategory 101|Streaming`        |
| `/editsold`     | Manually add to sold count                    | `/editsold 101|10`                   |
| `/disc`         | Set product discount (percent/nominal)        | `/disc 101|10%` or `/disc 101|5000`  |
| `/discat`       | Set category discount                         | `/discat Streaming|15%`              |
| `/priceress`    | Set reseller price for product                | `/priceress 101|45000`               |
| `/exportstock`  | Export remaining stock for product            | `/exportstock 101`                   |
| `/info`         | Show user account info                        | `/info 123456789`                    |
| `/pm`           | Send private message to user                  | `/pm 123456789|Promo baru!`          |
| `/transfer`     | Add funds to user balance                     | `/transfer 123456789|50000`          |
| `/editbalance`  | Overwrite user balance                        | `/editbalance 123456789|150000`      |
| `/ban`          | Ban user                                      | `/ban 123456789`                     |
| `/unban`        | Unban user                                    | `/unban 123456789`                   |
| `/addadmin`     | Promote user to admin                         | `/addadmin 123456789`                |
| `/rmadmin`      | Remove admin status                           | `/rmadmin 123456789`                 |
| `/addreseller`  | Promote user to reseller                      | `/addreseller 123456789`             |
| `/rmress`       | Remove reseller status                        | `/rmress 123456789`                  |
| `/whitelist`    | Add group to admin notification list          | `/whitelist -100123456789`           |
| `/rm`           | Remove group from notification list           | `/rm -100123456789`                  |
| `/broadcast`    | Broadcast message to all users                | `/broadcast`                         |
| `/setformula`   | Set refund calculation formula                | `/setformula`                        |
| `/version`      | Show current bot version                      | `/version`                           |

#### Command Error Handling

- If a command is sent with missing or wrong format, bot responds with:
  ```
  Format salah. Contoh penggunaan yang benar:
  /add 101|Netflix|Streaming|50000|Akun premium.
  (Gunakan: /add product_id|product_name|category|price|description)
  ```
- If a non-admin tries an admin command:
  ```
  Return nothing.
  ```

---

## 4. Notifications & Bot Responses

- **Order Success:**  
  User: "🎉 Pesanan berhasil!  
  📦 Produk: {product_name}  
  🔢 Jumlah: {jumlah}  
  🧾 Invoice: {invoice_id}  
  Terima kasih telah berbelanja! Silakan cek detail produk di bawah ini. 😊"
  
  Admin: "🆕 Order baru masuk!  
  👤 User: {user_name}  
  📦 Produk: {product_name}  
  🔢 Jumlah: {jumlah}  
  🧾 Invoice: {invoice_id}"

- **Order Failed/Expired:**  
  User: "⏰ Pesanan dibatalkan atau expired.  
  Jika pembayaran sudah dilakukan, dana akan dikembalikan (dipotong biaya).  
  Silakan coba lagi atau hubungi admin jika ada kendala. 🙏"
  
  Admin: "⚠️ Order expired/tidak dibayar  
  🧾 Invoice: {invoice_id}"

- **IMPORTANT: QR Payment Expiry Logic (10 Minutes):**
  - When a user initiates payment (QRIS or Deposit), the bot sends a message containing the QR code, invoice ID, and expiry timer.
  - If the payment is not completed within 10 minutes, the bot **must** delete the original QR message and send a new message indicating the invoice is expired.
    - This process must use a persistent job queue (e.g., Redis-backed) to schedule expiry tasks, ensuring the operation is retried on failure (with exponential backoff).
    - All failed attempts to delete or send the new message must be logged and operators alerted.
    - If the bot is offline during expiry, the task must resume on restart.
    - If the replacement fails after multiple retries, send a fallback notification to the user.
  - The new message should clearly state:
    - "Invoice expired. Pembayaran tidak diterima lagi untuk invoice ini. Jika Anda sudah membayar, dana akan dikembalikan (dipotong biaya). Silakan buat pesanan/deposit baru jika masih diperlukan."
    - Only show a single [Kembali] button; all payment-related buttons ([Checkout Page], [Status Pembayaran], [Batalkan]) must be removed.
  - The backend must also revoke the payment payload (if possible) and ensure stock is not reduced for expired/unpaid orders.

- **Deposit Success:**  
  User: "💰 Deposit berhasil!  
  Saldo Anda telah bertambah sebesar Rp{amount} (setelah fee).  
  Silakan cek saldo di menu [Akun]. 🎯"
  
  Admin: "💸 User {user_name} berhasil deposit Rp{amount}."

- **Deposit Expired:**  
  User: "⌛️ Invoice deposit expired.  
  Silakan lakukan deposit ulang jika masih diperlukan. 🔄"
  
  Admin: "🚫 Deposit expired  
  🧾 Invoice: {invoice_id}"

- **Reseller Upgrade:**  
  User: "🎊 Selamat! Status Anda telah menjadi reseller.  
  Nikmati harga spesial dan fitur tambahan! 🏅"
  
  Admin: "⭐️ User {user_name} telah diupgrade menjadi reseller."

---

## 5. Database & Caching Architecture

### 5.1. PostgreSQL Schema

#### users
| Column Name        | Data Type      | Notes                                      |
|--------------------|---------------|--------------------------------------------|
| id                 | BIGINT        | Telegram User ID (PK)                      |
| name               | VARCHAR(255)  |                                            |
| username           | VARCHAR(255)  | Nullable                                   |
| email              | VARCHAR(255)  | Nullable, unique                           |
| whatsapp_number    | VARCHAR(20)   | Nullable                                   |
| member_status      | VARCHAR(10)   | 'customer', 'reseller', 'admin'            |
| bank_id            | VARCHAR(10)   | Unique 6-digit internal account ID          |
| account_balance    | DECIMAL(15,2) | Default: 0.00                              |
| is_banned          | BOOLEAN       | Default: false                             |
| created_at         | TIMESTAMPTZ   |                                            |
| updated_at         | TIMESTAMPTZ   |                                            |

#### products
| Column Name        | Data Type      | Notes                                      |
|--------------------|---------------|--------------------------------------------|
| id                 | INT           | Admin-defined Product ID (PK)              |
| name               | VARCHAR(255)  |                                            |
| description        | TEXT          | Nullable                                   |
| category           | VARCHAR(255)  | Default: 'Uncategorized'                   |
| customer_price     | DECIMAL(15,2) |                                            |
| reseller_price     | DECIMAL(15,2) | Nullable                                   |
| sold_count         | INT           | Default: 0                                 |
| is_active          | BOOLEAN       | Default: true                              |
| created_at         | TIMESTAMPTZ   |                                            |
| updated_at         | TIMESTAMPTZ   |                                            |

#### product_stocks
| Column Name        | Data Type      | Notes                                      |
|--------------------|---------------|--------------------------------------------|
| id                 | UUID          | PK, Default: gen_random_uuid()             |
| product_id         | INT           | FK to products.id                          |
| content            | TEXT          | Digital good (e.g., key, account info)     |
| order_id           | INT           | FK to orders.id, nullable                  |
| is_sold            | BOOLEAN       | Default: false                             |
| created_at         | TIMESTAMPTZ   |                                            |
| updated_at         | TIMESTAMPTZ   |                                            |

#### orders
| Column Name        | Data Type      | Notes                                      |
|--------------------|---------------|--------------------------------------------|
| id                 | SERIAL        | PK                                         |
| invoice_id         | VARCHAR(20)   | Unique, Indexed                            |
| user_id            | BIGINT        | FK to users.id                             |
| total_bill         | DECIMAL(15,2) |                                            |
| payment_method     | VARCHAR(20)   | 'qris', 'account_balance'                  |
| status             | VARCHAR(10)   | 'pending', 'paid', 'expired', 'cancelled'  |
| created_at         | TIMESTAMPTZ   |                                            |
| updated_at         | TIMESTAMPTZ   |                                            |

#### order_items
| Column Name        | Data Type      | Notes                                      |
|--------------------|---------------|--------------------------------------------|
| id                 | SERIAL        | PK                                         |
| order_id           | INT           | FK to orders.id                            |
| product_id         | INT           | FK to products.id                          |
| stock_id           | UUID          | FK to product_stocks.id                    |
| price_per_unit     | DECIMAL(15,2) |                                            |

### 5.2. Redis Usage

- **User Sessions:** `session:{user_id}` – stores current state for multi-step flows.
- **Product Stock Counts:** `stock_count:{product_id}` – cache available stock.
- **Aggregate Counts:** `stats:total_users`, `stats:total_transactions`.
- **Pagination Caches:** `pagination:{user_id}:{context}`.
- **Rate Limiting:** `rate:{user_id}`.

---

## 6. Business Logic

### 6.1. Refund Calculation

- Formula:  
  ```
  refund_amount = (purchase_price * (30 - days_used) / 30) * fee_multiplier
  ```
  - `fee_multiplier` rules:
    - 0.8 = days_used < 7
    - 0.7 = days_used >= 7
    - 0.6 = 1-2 warranty claims
    - 0.5 = 3 claims
    - 0.4 = >3 claims

### 6.2. Reseller Pricing

- If `member_status == 'reseller'` and `reseller_price` is set, show reseller price.
- Otherwise, show customer price.

---

### 6.3. Session State Management (Flexible Navigation)

- All user session state (multi-step flows, e.g., ordering, deposit) must be stored in Redis using atomic operations.
- Each user has a single session key (e.g., `session:{user_id}`) that tracks the current flow and context.
- When a user clicks any button or sends a new command, the bot must:
  - Atomically clear or update the session state to reflect the new flow.
  - Validate the current state before processing input; if ambiguous, provide a contextual help or fallback message.
  - Use Redis transactions (MULTI/EXEC) to prevent race conditions and state corruption.
- All session transitions and unexpected state changes must be logged for monitoring and debugging.

---

### 6.4. Stock Consistency & Race Condition Prevention

- Stock deduction and assignment must be performed within a database transaction using row-level locking (e.g., `SELECT ... FOR UPDATE` in PostgreSQL).
- When an order is initiated, reserve stock items but do not mark as sold until payment is confirmed.
- If payment expires or fails, release the reserved stock atomically.
- All payment and order processing logic must be idempotent to prevent double-selling or inconsistent stock.
- For high concurrency, consider using a distributed lock (e.g., Redis Redlock) around critical stock update sections.

---

## 7. Access Control Logic

- Public commands: visible and accessible to all users.
- Admin commands: only visible and accessible to users with `member_status = 'admin'`.
- Logic:
 ```
 if command in admin_commands and user.member_status != 'admin':
     return "Command ini hanya bisa diakses oleh admin."
 ```

---

## 8. UI & Language Policy

- All inline/reply keyboard buttons: Bahasa Indonesia (e.g., `[Kirim Pesan]`, `[Akun]`, `[Deposit]`, `[Kembali]`, `[Batalkan]`)
- All bot explanations, notifications, and documentation: English

---

## 9. Operational Monitoring & Audit Logging (Best Practice)

- **Raw Monitoring:**  
 - Use simple logging (to file or stdout) for errors, warnings, and key events (e.g., failed message delivery, retries, suspicious activity).
 - No heavy tools (e.g., Prometheus, Grafana) are required at this stage.
 - Regularly review logs for anomalies and operational issues.

- **Audit Logs:**  
 - All critical admin and user activities (e.g., balance changes, bans, product edits, order status changes) must be recorded in an audit log.
 - **Permanent audit logs** must be stored in a separate database (e.g., `db_audits`), distinct from the main store database (e.g., `db_store1`).
   - `db_store1` contains all operational data and logs that can be cleaned/routinely purged.
   - `db_audits` is for permanent, non-deletable logs for compliance and traceability.
 - Each audit log entry should include: timestamp, actor (user/admin id), action, target (if any), before/after values (if applicable), and context (IP, device, etc. if available).
 - Provide a simple query interface for admins to review audit logs as needed.

---

## 10. Miscellaneous

- All flows must be robust to unexpected user input.  
- Never require users to cancel before starting a new operation.  
- All error messages must include the correct format and an example.

---
## 11. Scalability & High-Volume Scenarios (Best Practice)

- Plan for high-volume usage by:
  - Implementing rate limits for user commands and actions (using Redis or similar).
  - Batching notifications to admins if order volume is high, to avoid notification overload.
  - Using cache invalidation strategies for Redis (e.g., expire keys, invalidate on stock/payment changes).
  - Ensuring paginated queries are efficient and can handle large datasets.
  - Monitoring for Telegram API rate limits and gracefully degrading or retrying as needed.
  - Designing all flows to be stateless where possible, except for necessary session state.
  - Regularly reviewing and optimizing database queries and indexes for performance.

---
