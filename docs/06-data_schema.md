# 06. Data Schema
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
Defines the complete data structure for QuickCart, including main operational database and permanent audit database, ensuring consistency and compliance across all environments.

---

## Main Database Schema (db_store1)

### users
| Column Name        | Data Type      | Constraints                | Description |
|--------------------|---------------|---------------------------|-------------|
| id                 | BIGINT        | PRIMARY KEY               | Telegram User ID |
| name               | VARCHAR(255)  | NOT NULL                  | User display name |
| username           | VARCHAR(255)  | UNIQUE, NULLABLE          | Telegram username |
| email              | VARCHAR(255)  | UNIQUE, NULLABLE          | Email address |
| whatsapp_number    | VARCHAR(20)   | NULLABLE                  | WhatsApp number |
| member_status      | VARCHAR(10)   | NOT NULL, DEFAULT 'customer' | customer/reseller/admin |
| bank_id            | VARCHAR(10)   | UNIQUE, NOT NULL          | 6-digit internal account ID |
| account_balance    | DECIMAL(15,2) | NOT NULL, DEFAULT 0.00    | User balance for purchases |
| is_banned          | BOOLEAN       | NOT NULL, DEFAULT false   | Ban status |
| created_at         | TIMESTAMPTZ   | NOT NULL, DEFAULT NOW()   | Account creation time |
| updated_at         | TIMESTAMPTZ   | NOT NULL, DEFAULT NOW()   | Last update time |

**Indexes:**
- `idx_users_member_status` ON member_status
- `idx_users_bank_id` ON bank_id
- `idx_users_email` ON email WHERE email IS NOT NULL

### products  
| Column Name        | Data Type      | Constraints                | Description |
|--------------------|---------------|---------------------------|-------------|
| id                 | INT           | PRIMARY KEY               | Admin-defined Product ID |
| name               | VARCHAR(255)  | NOT NULL                  | Product name |
| description        | TEXT          | NULLABLE                  | Product description |
| category           | VARCHAR(255)  | NOT NULL, DEFAULT 'Uncategorized' | Product category |
| customer_price     | DECIMAL(15,2) | NOT NULL                  | Regular customer price |
| reseller_price     | DECIMAL(15,2) | NULLABLE                  | Special reseller price |
| sold_count         | INT           | NOT NULL, DEFAULT 0       | Total units sold |
| is_active          | BOOLEAN       | NOT NULL, DEFAULT true    | Product availability |
| created_at         | TIMESTAMPTZ   | NOT NULL, DEFAULT NOW()   | Creation time |
| updated_at         | TIMESTAMPTZ   | NOT NULL, DEFAULT NOW()   | Last update time |

**Indexes:**
- `idx_products_category` ON category
- `idx_products_is_active` ON is_active
- `idx_products_sold_count` ON sold_count DESC

### product_stocks
| Column Name        | Data Type      | Constraints                | Description |
|--------------------|---------------|---------------------------|-------------|
| id                 | UUID          | PRIMARY KEY, DEFAULT gen_random_uuid() | Stock item ID |
| product_id         | INT           | NOT NULL, FK products.id   | Product reference |
| content            | TEXT          | NOT NULL                  | Digital content (keys, accounts) |
| order_id           | INT           | NULLABLE, FK orders.id     | Assigned order (when sold) |
| is_sold            | BOOLEAN       | NOT NULL, DEFAULT false   | Sold status |
| created_at         | TIMESTAMPTZ   | NOT NULL, DEFAULT NOW()   | Stock creation time |
| updated_at         | TIMESTAMPTZ   | NOT NULL, DEFAULT NOW()   | Last update time |

**Indexes:**
- `idx_product_stocks_product_id` ON product_id
- `idx_product_stocks_is_sold` ON is_sold
- `idx_product_stocks_order_id` ON order_id

### orders (CR-002 Best Practice: One Active Order Per User)
| Column Name        | Data Type      | Constraints                | Description |
|--------------------|---------------|---------------------------|-------------|
| id                 | SERIAL        | PRIMARY KEY               | Order ID |
| invoice_id         | VARCHAR(20)   | UNIQUE, NOT NULL          | External invoice reference |
| user_id            | BIGINT        | NOT NULL, FK users.id     | Customer reference |
| subtotal           | DECIMAL(15,2) | NOT NULL                  | Order amount before fees/discounts |
| voucher_discount   | DECIMAL(15,2) | NOT NULL, DEFAULT 0.00    | Voucher discount applied |
| payment_fee        | DECIMAL(15,2) | NOT NULL, DEFAULT 0.00    | Payment gateway fee (0.7% + 310) |
| total_bill         | DECIMAL(15,2) | NOT NULL                  | Final amount user pays (subtotal - discount + fee) |
| payment_method     | VARCHAR(20)   | NOT NULL                  | qris/account_balance |
| status             | VARCHAR(10)   | NOT NULL, DEFAULT 'pending' | pending/paid/expired/cancelled |
| created_at         | TIMESTAMPTZ   | NOT NULL, DEFAULT NOW()   | Order creation time |
| updated_at         | TIMESTAMPTZ   | NOT NULL, DEFAULT NOW()   | Last status update |

**Business Rule (CR-002):** Only one 'pending' order allowed per user at a time.

**Simple Check Query:**
```sql
-- Check if user has pending order before creating new one
SELECT COUNT(*) FROM orders 
WHERE user_id = $1 AND status = 'pending';
-- If count > 0, user must complete/cancel current order first
```

**Indexes:**
- `idx_orders_invoice_id` ON invoice_id
- `idx_orders_user_id` ON user_id
- `idx_orders_status` ON status
- `idx_orders_created_at` ON created_at DESC

### order_items
| Column Name        | Data Type      | Constraints                | Description |
|--------------------|---------------|---------------------------|-------------|
| id                 | SERIAL        | PRIMARY KEY               | Order item ID |
| order_id           | INT           | NOT NULL, FK orders.id    | Order reference |
| product_id         | INT           | NOT NULL, FK products.id  | Product reference |
| stock_id           | UUID          | NOT NULL, FK product_stocks.id | Specific stock assigned |
| price_per_unit     | DECIMAL(15,2) | NOT NULL                  | Price paid per unit |

**Indexes:**
- `idx_order_items_order_id` ON order_id
- `idx_order_items_stock_id` ON stock_id

### vouchers
| Column Name        | Data Type      | Constraints                | Description |
|--------------------|---------------|---------------------------|-------------|
| id                 | SERIAL        | PRIMARY KEY               | Voucher ID |
| code               | VARCHAR(20)   | UNIQUE, NOT NULL          | Voucher code (auto-generated) |
| amount             | DECIMAL(15,2) | NOT NULL                  | Discount amount in IDR |
| created_by         | BIGINT        | NOT NULL, FK users.id     | Admin who created voucher |
| is_used            | BOOLEAN       | NOT NULL, DEFAULT false   | Usage status |
| used_by            | BIGINT        | NULLABLE, FK users.id     | User who used voucher |
| used_at            | TIMESTAMPTZ   | NULLABLE                  | When voucher was used |
| order_id           | INT           | NULLABLE, FK orders.id    | Order where voucher was applied |
| expires_at         | TIMESTAMPTZ   | NOT NULL                  | Voucher expiry date |
| created_at         | TIMESTAMPTZ   | NOT NULL, DEFAULT NOW()   | Voucher creation time |

**Indexes:**
- `idx_vouchers_code` ON code
- `idx_vouchers_used_by` ON used_by
- `idx_vouchers_is_used` ON is_used
- `idx_vouchers_expires_at` ON expires_at

### voucher_usage_cooldown
| Column Name        | Data Type      | Constraints                | Description |
|--------------------|---------------|---------------------------|-------------|
| id                 | SERIAL        | PRIMARY KEY               | Cooldown record ID |
| user_id            | BIGINT        | NOT NULL, FK users.id     | User in cooldown |
| last_voucher_used  | TIMESTAMPTZ   | NOT NULL                  | Last voucher usage time |
| expires_at         | TIMESTAMPTZ   | NOT NULL                  | When cooldown expires (5 min) |

**Indexes:**
- `idx_voucher_cooldown_user_id` ON user_id
- `idx_voucher_cooldown_expires_at` ON expires_at

---

## Audit Database Schema (db_audits)

### audit_logs
| Column Name        | Data Type      | Constraints                | Description |
|--------------------|---------------|---------------------------|-------------|
| id                 | BIGSERIAL     | PRIMARY KEY               | Audit log entry ID |
| timestamp          | TIMESTAMPTZ   | NOT NULL, DEFAULT NOW()   | Event timestamp |
| actor_id           | BIGINT        | NULLABLE                  | User who performed action |
| actor_type         | VARCHAR(20)   | NOT NULL                  | user/admin/system |
| entity_type        | VARCHAR(50)   | NOT NULL                  | Table/entity affected |
| entity_id          | VARCHAR(50)   | NOT NULL                  | Record ID affected |
| action             | VARCHAR(50)   | NOT NULL                  | create/update/delete/login |
| before_state       | JSONB         | NULLABLE                  | Previous values |
| after_state        | JSONB         | NULLABLE                  | New values |
| context            | JSONB         | NULLABLE                  | Additional context |
| ip_address         | INET          | NULLABLE                  | Source IP (if available) |

**Indexes:**
- `idx_audit_logs_timestamp` ON timestamp
- `idx_audit_logs_entity` ON entity_type, entity_id
- `idx_audit_logs_actor` ON actor_id
- `idx_audit_logs_action` ON action

---

## Key Relationships

```sql
-- Users have orders
orders.user_id → users.id (many-to-one)

-- Orders contain multiple products
order_items.order_id → orders.id (many-to-one)
order_items.product_id → products.id (many-to-one)

-- Each order item gets specific stock
order_items.stock_id → product_stocks.id (one-to-one)
product_stocks.order_id → orders.id (many-to-one)

-- Audit logs reference any entity
audit_logs.entity_type + entity_id → any table.id (polymorphic)
```

---

## Data Integrity Constraints

### Business Rules Enforced by DB
1. **Stock Assignment:** Each `product_stocks` record can only be assigned to one order
2. **Balance Validation:** Account balance cannot go negative
3. **Order Consistency:** Order total must match sum of order_items
4. **Status Transitions:** Order status changes must follow valid state machine

### Triggers & Functions
```sql
-- Auto-update timestamps
CREATE TRIGGER update_timestamp BEFORE UPDATE ON users, products, orders, product_stocks
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Audit log triggers for all main tables
CREATE TRIGGER audit_trigger AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION log_audit_event();
```

---

## Redis Schema Patterns

### Session Management
```
session:{user_id} → {
  "flow": "ordering|deposit|account_edit",
  "state": "selecting_quantity|awaiting_payment",
  "context": { product_id, quantity, ... },
  "expires": timestamp
}
```

### Caching
```
stock_count:{product_id} → integer (available stock count)
stats:total_users → integer
stats:total_transactions → integer
pagination:{user_id}:{context} → { page, total_pages, items[] }
```

### Rate Limiting
```
rate:{user_id}:{action} → counter with TTL
queue:payment_expiry → sorted set with expiry timestamps
```

---

## Data Retention & Privacy

### Personal Data Handling
- **PII Fields:** name, email, whatsapp_number (all optional except name)
- **Minimal Collection:** Only collect what's necessary for order fulfillment
- **User Control:** Users can update/clear optional fields via bot commands

### Compliance Considerations
- **GDPR Article 17:** Right to erasure implementation via soft delete + anonymization
- **Data Export:** User can request their complete transaction history
- **Audit Integrity:** Audit logs cannot be deleted, only anonymized if user requests erasure

### Retention Policies
- **Operational Data:** 7 years retention for financial records
- **Audit Logs:** Permanent retention for compliance
- **Session Data:** 24-hour TTL in Redis
- **Cache Data:** Variable TTL based on update frequency

---

## Cross-References

- See [05-architecture.md](05-architecture.md) for database deployment and scaling strategy.
- Reference [07-api_contracts.md](07-api_contracts.md) for API payload structures that map to these schemas.
- Use [10-audit_architecture.md](10-audit_architecture.md) for audit log implementation details and compliance requirements.

---

> Note for AI builders: This schema is designed for zero data loss and maximum audit compliance. All critical operations must be logged, all financial data must be preserved, and all state changes must be atomic.