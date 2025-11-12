# 04 — UI/UX Flow
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
This document outlines the user journey, key screens, and interaction flows for QuickCart. It serves as a reference for developers to ensure a consistent, user-friendly Telegram bot experience with flexible navigation.

---

## User Personas

### Persona 1: Digital Product Customer
- **Profile:** Telegram users purchasing tutorials, premium accounts, or courses
- **Goals:** Quick product discovery, secure payment, immediate content delivery
- **Pain Points:** Complex payment flows, unclear product information, expired payments
- **Behavior:** Expects instant gratification, mobile-first experience, Indonesian interface

### Persona 2: Reseller
- **Profile:** Users who purchase in bulk for resale with special pricing
- **Goals:** Access to wholesale prices, bulk ordering, account management
- **Pain Points:** Manual price negotiations, unclear reseller benefits
- **Behavior:** Price-sensitive, relationship-focused, requires account balance management

### Persona 3: Bot Administrator
- **Profile:** Digital product seller managing inventory and users via Telegram
- **Goals:** Efficient product/user management, sales monitoring, fraud prevention
- **Pain Points:** Manual stock updates, customer support overflow, payment disputes
- **Behavior:** Command-line comfortable, efficiency-focused, requires audit visibility

---

## Main User Flows

### 1. Onboarding Flow (/start)
```
/start → Welcome Sticker → Name Input (skippable) → WhatsApp Input (skippable) → 
Email Input (skippable) → Main Menu Display
```
- **Welcome Sticker ID:** `CAACAgIAAxkBAAIDbWkLZHuqPRCqCqmL9flozT9YJdWOAAIZUAAC4KOCB7lIn3OKexieNgQ`
- **Default Values:** Name: 'Anonymous', Phone: 'null', Email: 'null'
- **Welcome Message Format (from plans.md):**
  ```
  ᯓ Halo **{name}** 👋🏻
  Selamat datang di **{store_name}**

  ⤷ **Total Pengguna: {total_user} Orang**
  ⤷ **Total Transaksi: {total_transaction}x**

  Dokumentasi: [Baca Disini]{https://notion.so/blabla}
  Silakan tombol dibawah ini untuk melihat produk yang tersedia.
  ```
- **Inline Buttons:** `[Kategori] [Terlaris] [Semua Produk]`

### 2. Product Discovery Flow
```
Main Menu → [Kategori]/[Terlaris]/[Semua Produk] → Category/Product List → 
Product Selection (1-24) → Product Details → Quantity Selection → Payment Options
```
- **Navigation Options:** 
  - `[Kategori]` → Category buttons → Products in category (paginated)
  - `[Terlaris]` → Best-selling products + `[Top Buyers]` feature
  - `[Semua Produk]` → All products including out-of-stock (paginated)
  - Direct product ID (1-24) → Product details immediately

### 3. Order & Payment Flow
```
Product Selection → Product Info Display → Quantity Adjustment (-, +, +2, +5, +10) →
[Lanjut ke pembayaran] → Order Summary → Voucher Option ([Gunakan Voucher]/[Skip]) →
Payment Method Selection ([QRIS]/[SALDO]) → Payment Processing → Content Delivery
```

#### 3a. QRIS Payment Sub-flow
```
[QRIS] → Fee Calculation → QR Code Display + 10-minute Timer → 
Payment Status Monitoring → Success/Expiry Handling
```
- **Payment Fee:** Pakasir charges 0.7% + Rp310 (automatically added to total)
- **Fee Calculation Example:** 
  - Order total: Rp30,000
  - Payment fee: (30,000 × 0.7%) + 310 = 210 + 310 = Rp520
  - **Final amount shown:** Rp30,520 (what user pays via QR)
- **User Message:** "Total pesanan: Rp30,000\nBiaya pembayaran: Rp520\n**Total tagihan: Rp30,520**"
- **Buttons During Payment:** `[Checkout Page]` `[Status Pembayaran]` `[Batalkan]`
- **Expiry Behavior:** Auto-message replacement, stock release, refund policy notice
- **Expiry Message (from plans.md):** "Invoice expired. Pembayaran tidak diterima lagi untuk invoice ini. Jika Anda sudah membayar, dana akan dikembalikan (dipotong biaya). Silakan buat pesanan/deposit baru jika masih diperlukan."
- **Post-Expiry:** Only `[Kembali]` button visible, all payment buttons removed

#### 3b. Balance Payment Sub-flow
```
[SALDO] → Balance Verification → Instant Deduction → Content Delivery
```

### 4. Account Management Flow
```
[AKUN] → Account Info Display → Action Selection:
- [Ubah Nama] → Name Update Flow
- [Ubah Email] → Email Update Flow  
- [Ubah Whatsapp] → WhatsApp Update Flow
- [Riwayat Transaksi] → Transaction History (paginated)
- [Deposit] → Deposit Flow
```

### 5. Deposit Flow
```
[Deposit] → Amount Input → Fee Calculation → QRIS Payment → 
Balance Credit (success) / Expiry Handling (timeout)
```

### 6. Admin Communication Flow
```
[KIRIM PESAN] → Message Input Prompt → Optional Image Attachment → 
Message Broadcast to Admins → Admin Response Capability
```

### 7. Voucher/Discount Flow
```
Order Summary → [Gunakan Voucher] → Voucher Code Input → 
Voucher Validation → Discount Applied → Updated Order Total → Payment Method Selection
```
- **Voucher Input:** User enters voucher code manually
- **Validation:** Real-time validation with cooldown check (5-minute between usage)
- **Error Messages:** 
  - "Kode voucher tidak valid atau sudah digunakan."
  - "Anda baru saja menggunakan voucher. Tunggu 5 menit untuk menggunakan voucher lagi."
  - "Voucher sudah expired atau tidak berlaku."
- **Success Message:** "Voucher berhasil diterapkan! Diskon Rp{amount} telah dipotong dari total pesanan."
- **Order Summary Update:** Shows original price, discount amount, and final total

### 8. Flexible Navigation Principle
- **Core Rule:** Users can click ANY button at ANY time
- **State Management:** Bot discards previous state and switches to new flow
- **No Cancellation Required:** Seamless flow switching without explicit cancellation
- **Session Consistency:** Redis-backed state management prevents corruption

---

## Key Interface Elements

### Reply Keyboard Layout
```
[LIST PRODUK] [STOK]
[AKUN] [KIRIM PESAN]
[1] [2] [3] [4] [5] [6] [7] [8]
[9] [10] [11] [12] [13] [14] [15] [16]  
[17] [18] [19] [20] [21] [22] [23] [24]
```
- Numbers represent product IDs (only shown if in stock)
- Sorted in ascending order for consistency

### Inline Button Patterns
- **Navigation:** `[Kembali]` `[Selanjutnya 1/3]` (pagination)
- **Quantity Control:** `[-] [+] [+2] [+5] [+10]`
- **Payment Actions:** `[QRIS] [SALDO] [KEMBALI] [BATALKAN]`
- **Account Management:** `[Ubah Nama] [Ubah Email] [Riwayat Transaksi]`

## Language & Localization
- **UI Buttons:** Indonesian (e.g., "Lanjut ke pembayaran", "Batalkan")
- **Bot Messages:** Indonesian for user-facing content
- **Technical Logs:** English for debugging and audit
- **Error Messages:** Indonesian with English examples in admin context

## Notification Templates (from plans.md)

### Order Success Notifications
**User Message:**
```
🎉 Pesanan berhasil!
📦 Produk: {product_name}
🔢 Jumlah: {jumlah}
🧾 Invoice: {invoice_id}
Terima kasih telah berbelanja! Silakan cek detail produk di bawah ini. 😊
```

**Admin Message:**
```
🆕 Order baru masuk!
👤 User: {user_name}
📦 Produk: {product_name}
🔢 Jumlah: {jumlah}
🧾 Invoice: {invoice_id}
```

### Order Failed/Expired Notifications
**User Message:**
```
⏰ Pesanan dibatalkan atau expired.
Jika pembayaran sudah dilakukan, dana akan dikembalikan (dipotong biaya).
Silakan coba lagi atau hubungi admin jika ada kendala. 🙏
```

**Admin Message:**
```
⚠️ Order expired/tidak dibayar
🧾 Invoice: {invoice_id}
```

### Deposit Success Notifications
**User Message:**
```
💰 Deposit berhasil!
Saldo Anda telah bertambah sebesar Rp{amount} (setelah fee).
Silakan cek saldo di menu [Akun]. 🎯
```

**Admin Message:**
```
💸 User {user_name} berhasil deposit Rp{amount}.
```

### Reseller Upgrade Notifications
**User Message:**
```
🎊 Selamat! Status Anda telah menjadi reseller.
Nikmati harga spesial dan fitur tambahan! 🏅
```

**Admin Message:**
```
⭐️ User {user_name} telah diupgrade menjadi reseller.
```

## Error Handling & Recovery
- **Invalid Commands:** Show correct format with examples
- **Expired Payments:** Clear expiry message, new order guidance
- **Out of Stock:** Immediate notification, alternative suggestions
- **Network Issues:** Retry logic with user feedback
- **State Corruption:** Graceful fallback to main menu

## Cross-References
- Refer to [03-prd.md](03-prd.md) for complete feature requirements and acceptance criteria
- Refer to [05-architecture.md](05-architecture.md) for session management and Redis implementation
- Refer to [07-api_contracts.md](07-api_contracts.md) for Pakasir integration and webhook handling

---

> Note for AI builders: This flow document defines the complete user experience for QuickCart. All navigation must support flexible flow switching. Session state management is critical for preventing user confusion and data corruption.