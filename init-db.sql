-- QuickCart initial database bootstrap
-- Source of truth: SQLAlchemy models in src/models and Alembic migrations/versions/*
-- This script is idempotent and can be safely re-run.

------------------------------------------------------------
-- 1. Create roles (if they do not already exist)
------------------------------------------------------------
DO
$$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'quickcart') THEN
        CREATE ROLE quickcart WITH LOGIN PASSWORD 'quickcart';
    END IF;
END;
$$;

DO
$$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'quickcart_audit') THEN
        CREATE ROLE quickcart_audit WITH LOGIN PASSWORD 'quickcart_audit';
    END IF;
END;
$$;

------------------------------------------------------------
-- 2. Create databases (owned by respective roles)
------------------------------------------------------------
DO
$$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'quickcart') THEN
        CREATE DATABASE quickcart OWNER quickcart;
    END IF;
END;
$$;

DO
$$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'quickcart_audit') THEN
        CREATE DATABASE quickcart_audit OWNER quickcart_audit;
    END IF;
END;
$$;

GRANT ALL PRIVILEGES ON DATABASE quickcart TO quickcart;
GRANT TEMPORARY, CONNECT ON DATABASE quickcart TO quickcart;
GRANT ALL PRIVILEGES ON DATABASE quickcart_audit TO quickcart_audit;
GRANT TEMPORARY, CONNECT ON DATABASE quickcart_audit TO quickcart_audit;

------------------------------------------------------------
-- 3. Main Operational Database (quickcart)
------------------------------------------------------------
\connect quickcart

SET search_path TO public;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id               BIGINT PRIMARY KEY,
    name             VARCHAR(255) NOT NULL,
    username         VARCHAR(255) UNIQUE,
    email            VARCHAR(255) UNIQUE,
    whatsapp_number  VARCHAR(20),
    member_status    VARCHAR(10) NOT NULL DEFAULT 'customer',
    bank_id          VARCHAR(10) NOT NULL UNIQUE,
    account_balance  NUMERIC(15,2) NOT NULL DEFAULT 0.00 CHECK (account_balance >= 0),
    is_banned        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_member_status ON users (member_status);
CREATE INDEX IF NOT EXISTS idx_users_bank_id ON users (bank_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email) WHERE email IS NOT NULL;

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id              INTEGER PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    category        VARCHAR(255) NOT NULL DEFAULT 'Uncategorized',
    customer_price  NUMERIC(15,2) NOT NULL,
    reseller_price  NUMERIC(15,2),
    sold_count      INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_products_is_active ON products (is_active);
CREATE INDEX IF NOT EXISTS idx_products_sold_count ON products (sold_count DESC);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id               SERIAL PRIMARY KEY,
    invoice_id       VARCHAR(20) NOT NULL UNIQUE,
    user_id          BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subtotal         NUMERIC(15,2) NOT NULL,
    voucher_discount NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    payment_fee      NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    total_bill       NUMERIC(15,2) NOT NULL,
    payment_method   VARCHAR(20) NOT NULL,
    status           VARCHAR(10) NOT NULL DEFAULT 'pending',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_invoice_id ON orders (invoice_id);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders (user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders (created_at DESC);

-- Product stocks table
CREATE TABLE IF NOT EXISTS product_stocks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    order_id    INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    is_sold     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_product_stocks_product_id ON product_stocks (product_id);
CREATE INDEX IF NOT EXISTS idx_product_stocks_is_sold ON product_stocks (is_sold);
CREATE INDEX IF NOT EXISTS idx_product_stocks_order_id ON product_stocks (order_id);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    id             SERIAL PRIMARY KEY,
    order_id       INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id     INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    stock_id       UUID NOT NULL REFERENCES product_stocks(id) ON DELETE RESTRICT,
    price_per_unit NUMERIC(15,2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items (order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_stock_id ON order_items (stock_id);

-- Vouchers table
CREATE TABLE IF NOT EXISTS vouchers (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20) NOT NULL UNIQUE,
    amount      NUMERIC(15,2) NOT NULL,
    created_by  BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_used     BOOLEAN NOT NULL DEFAULT FALSE,
    used_by     BIGINT REFERENCES users(id) ON DELETE SET NULL,
    used_at     TIMESTAMPTZ,
    order_id    INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vouchers_code ON vouchers (code);
CREATE INDEX IF NOT EXISTS idx_vouchers_used_by ON vouchers (used_by);
CREATE INDEX IF NOT EXISTS idx_vouchers_is_used ON vouchers (is_used);
CREATE INDEX IF NOT EXISTS idx_vouchers_expires_at ON vouchers (expires_at);

-- Voucher usage cooldown table
CREATE TABLE IF NOT EXISTS voucher_usage_cooldown (
    id                SERIAL PRIMARY KEY,
    user_id           BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    last_voucher_used TIMESTAMPTZ NOT NULL,
    expires_at        TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_voucher_cooldown_user_id ON voucher_usage_cooldown (user_id);
CREATE INDEX IF NOT EXISTS idx_voucher_cooldown_expires_at ON voucher_usage_cooldown (expires_at);

------------------------------------------------------------
-- 4. Helper functions and triggers
------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS
$$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$
LANGUAGE plpgsql;

DO
$$
DECLARE
    tbl text;
BEGIN
    FOREACH tbl IN ARRAY ARRAY['users','products','product_stocks','orders']
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%1$s_updated_at ON %1$s', tbl);
        EXECUTE format($f$
            CREATE TRIGGER update_%1$s_updated_at
            BEFORE UPDATE ON %1$s
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        $f$, tbl);
    END LOOP;
END;
$$;

-- Grant privileges on schema objects to the application role
GRANT USAGE ON SCHEMA public TO quickcart;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO quickcart;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO quickcart;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO quickcart;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO quickcart;

------------------------------------------------------------
-- 5. Audit Database (quickcart_audit)
------------------------------------------------------------
\connect quickcart_audit

SET search_path TO public;

CREATE TABLE IF NOT EXISTS audit_logs (
    id           BIGSERIAL PRIMARY KEY,
    timestamp    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_id     BIGINT,
    actor_type   VARCHAR(20) NOT NULL,
    entity_type  VARCHAR(50) NOT NULL,
    entity_id    VARCHAR(50) NOT NULL,
    action       VARCHAR(50) NOT NULL,
    before_state JSONB,
    after_state  JSONB,
    context      JSONB,
    ip_address   INET
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs (actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs (action);

CREATE TABLE IF NOT EXISTS payment_audit_logs (
    id                BIGSERIAL PRIMARY KEY,
    timestamp         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    order_id          VARCHAR(20) NOT NULL,
    user_id           BIGINT NOT NULL,
    amount            VARCHAR(20) NOT NULL,
    payment_method    VARCHAR(20) NOT NULL,
    status            VARCHAR(20) NOT NULL,
    gateway_response  JSONB,
    payment_metadata  JSONB
);

CREATE INDEX IF NOT EXISTS idx_payment_audit_timestamp ON payment_audit_logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_payment_audit_order_id ON payment_audit_logs (order_id);
CREATE INDEX IF NOT EXISTS idx_payment_audit_user_id ON payment_audit_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_payment_audit_status ON payment_audit_logs (status);

CREATE TABLE IF NOT EXISTS admin_action_audit (
    id           BIGSERIAL PRIMARY KEY,
    timestamp    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    admin_id     BIGINT NOT NULL,
    command      VARCHAR(50) NOT NULL,
    target_entity VARCHAR(50),
    target_id    VARCHAR(50),
    parameters   JSONB,
    result       TEXT NOT NULL,
    ip_address   INET
);

CREATE INDEX IF NOT EXISTS idx_admin_action_timestamp ON admin_action_audit (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_admin_action_admin_id ON admin_action_audit (admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_action_command ON admin_action_audit (command);
CREATE INDEX IF NOT EXISTS idx_admin_action_target ON admin_action_audit (target_entity, target_id);

COMMENT ON TABLE audit_logs IS 'Master audit log - permanent retention';
COMMENT ON TABLE payment_audit_logs IS 'Payment audit log - permanent retention';
COMMENT ON TABLE admin_action_audit IS 'Admin command audit - permanent retention';

GRANT USAGE ON SCHEMA public TO quickcart_audit;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO quickcart_audit;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO quickcart_audit;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO quickcart_audit;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO quickcart_audit;

-- End of script
