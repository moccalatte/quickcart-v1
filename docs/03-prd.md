# 03 — Product Requirements Document (PRD)
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

---

## Purpose
This document captures all functional and non-functional requirements for QuickCart, serving as the single source of truth for what will be built and why.

---

## 1. Problem Statement
- **Problem:** Digital product sellers need an automated, user-friendly system to sell tutorials, premium accounts, and courses through Telegram without manual intervention
- **Target Users:** 
  - Digital product sellers who want to automate their Telegram-based business
  - End customers purchasing digital products via Telegram
  - Resellers who get special pricing for bulk purchases

## 2. Goals & Success Metrics
- **Primary Goals:**
  - Fully automated order processing from product selection to content delivery
  - Zero manual intervention for standard transactions
  - Robust fraud prevention and audit trail
  - Seamless payment experience with 10-minute expiry handling
- **KPIs:**
  - Order completion rate > 95%
  - Payment success rate > 90%
  - Average order processing time < 30 seconds
  - Zero data loss or corruption incidents
  - 99.5% uptime for critical flows

## 3. Features

### 3.1. Core User Features (Priority: Critical)
- **Product Browsing:** Category-based navigation, best-sellers, search by product ID
  - *Acceptance:* Users can navigate products via keyboard buttons, view stock and pricing
- **Order Processing:** Multi-step flow with quantity selection and payment options
  - *Acceptance:* Support flexible navigation, users can switch flows anytime without errors
- **QRIS Payment:** Integration with Pakasir gateway, QR code display, 10-minute expiry
  - *Acceptance:* Payment expires automatically, stock released, user notified appropriately
  - **Payment Fee Handling:** Pakasir charges 0.7% + Rp310, automatically added to user's total bill
  - **Fee Display:** Bot shows breakdown: "Total pesanan: Rp30,000 + Biaya pembayaran: Rp520 = **Total tagihan: Rp30,520**"
  - **Business Logic:** `payment_fee = (subtotal * 0.007) + 310` where subtotal is after voucher discount applied
- **Account Balance:** Deposit system, balance-based purchases
  - *Acceptance:* Real-time balance updates, transaction history tracking

### 3.2. Admin Management Features (Priority: Critical)
- **Admin Management:** Complete admin command suite (hidden from non-admins)
  - *Acceptance:* All admin commands work via Telegram with proper error handling
  - *Admin Commands:* `/add`, `/addstock`, `/del`, `/delstock`, `/delallstock`, `/editid`, `/editcategory`, `/editsold`, `/disc`, `/discat`, `/priceress`, `/exportstock`, `/info`, `/pm`, `/transfer`, `/editbalance`, `/ban`, `/unban`, `/addadmin`, `/rmadmin`, `/addreseller`, `/rmress`, `/whitelist`, `/rm`, `/broadcast`, `/setformula`, `/version`, `/giveaway`
  - *Access Control:* Commands completely invisible to non-admin users (return nothing for unauthorized access)

- **User Management:** Ban/unban, balance transfers, role assignments (reseller/admin)
  - *Acceptance:* Role changes take effect immediately, audit logged
- **Notification System:** Real-time order alerts to admins and whitelisted groups
  - *Acceptance:* All critical events trigger appropriate notifications

### 3.3. Advanced Features (Priority: High)
- **Reseller System:** Special pricing tier, automated role management
  - *Acceptance:* Resellers see different pricing automatically based on role
- **Flexible Navigation:** Users can switch between any flow without canceling
  - *Acceptance:* No broken states, session management handles all transitions
- **Voucher/Giveaway System:** Admin-created discount vouchers for promotional campaigns
  - *Acceptance:* Vouchers apply correctly at checkout, one-time use, 5-minute cooldown between usage
  - **Admin Command:** `/giveaway nominal|jumlah` (e.g., `/giveaway 10000|10` creates 10 vouchers worth 10,000 IDR each)
  - **Distribution:** Auto-broadcast to all registered users in database
  - **Usage Rules:** One voucher per user per order, 5-minute cooldown between redemptions
  - **Payment Integration:** Voucher option appears during checkout flow, deducted before payment processing
  - **Error Handling:** Failed payments don't consume voucher, expired vouchers automatically cleaned up
- **Refund System:** Automated refund calculation with configurable formulas (from plans.md)
  - *Acceptance:* Refunds calculated correctly based on usage time and claim history
  - **Refund Formula:** `refund_amount = (purchase_price * (30 - days_used) / 30) * fee_multiplier`
  - **Fee Multiplier Rules:**
    - 0.8 = days_used < 7
    - 0.7 = days_used >= 7  
    - 0.6 = 1-2 warranty claims
    - 0.5 = 3 claims
    - 0.4 = >3 claims

## 4. Non-Functional Requirements

### Performance
- Response time: < 2 seconds for all user interactions
- Concurrent users: Support 1000+ simultaneous users
- Payment processing: < 30 seconds from initiation to QR display

### Security
- All payment data encrypted in transit and at rest
- Role-based access control for admin functions
- Session management with Redis for state consistency
- Separate audit database for permanent logging

### Compliance
- Audit trail for all financial transactions
- Anti-fraud detection and logging
- Data retention policies for different data types
- GDPR considerations for user data handling

### Usability
- Indonesian language for all UI elements
- English for technical documentation and logs
- Intuitive keyboard navigation
- Clear error messages with examples

## 5. Constraints & Assumptions

### Technical Constraints
- Telegram Bot API rate limits (30 messages/second)
- QRIS-only payment method (via Pakasir)
- Docker deployment on Digital Ocean droplets
- PostgreSQL + Redis technology stack

### Business Constraints
- 10-minute payment expiry (non-negotiable)
- Indonesian UI language requirement
- Telegram-only interface (no web admin panel)

### Key Assumptions
- Users have smartphones capable of scanning QR codes
- Stable internet connection for real-time payment processing
- Pakasir gateway maintains 99%+ uptime
- Digital products are text-based deliverables

## 6. Out of Scope
- Payment methods other than QRIS and account balance
- Multi-language support beyond Indonesian/English
- Physical product fulfillment
- Web-based admin interface
- Integration with external inventory systems
- Cryptocurrency payments
- Subscription-based pricing models

## 7. Dependencies
- **Pakasir Payment Gateway:** QRIS processing, webhook notifications
- **Telegram Bot API:** All user interactions and file delivery
- **Digital Ocean:** Infrastructure hosting and scaling
- **Docker Registry:** Container deployment and updates

---

## Cross-References
- See [04-uiux_flow.md](04-uiux_flow.md) for detailed user journeys and interaction flows.
- See [06-data_schema.md](06-data_schema.md) for complete data model and relationships.
- See [07-api_contracts.md](07-api_contracts.md) for Pakasir integration and internal API specifications.

---

> Note for AI builders: This PRD defines the complete scope for QuickCart. Any feature not explicitly listed here should be considered out of scope unless critical for core functionality.