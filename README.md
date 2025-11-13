# QuickCart - Telegram Auto-Order Bot 🤖

> **Automated digital product sales bot for Telegram with QRIS payment integration.**

QuickCart is an auto-order bot system for selling digital products (courses, accounts, vouchers, etc.) through Telegram. Customers can browse, order, and receive products automatically after payment—all without manual intervention.

> **⚠️ DEVELOPMENT STATUS:** Core infrastructure is complete. Bot handlers and payment integration are currently in development. See [docs/00-project_blueprint.md](docs/00-project_blueprint.md) for detailed status.

**Built with:** `python-telegram-bot` v22.5, `FastAPI`, `PostgreSQL`, `Redis`, `SQLAlchemy`, and `Docker`.

---

## ✨ Features

- 🛍️ **Product Catalog**: Browse products by category, best sellers, or view all *(in development)*
- 💳 **QRIS Payment**: Automatic payment via Pakasir gateway *(in development)*
- ⏱️ **Flexible Navigation**: Users can switch between any flow without canceling
- 👥 **User Roles**: Customer, Reseller, and Admin roles
- 🎫 **Voucher System**: Create and distribute discount codes *(database ready)*
- 📊 **Audit Logging**: Complete transaction history for compliance in a separate database
- 🐳 **Docker Ready**: Simple, fast deployment for local development and production
- 🗄️ **Redis with Fallback**: Session management with optional in-memory fallback

---

## 📋 Prerequisites

Before you start, make sure you have:

1.  **Docker & Docker Compose** installed ([Get Docker](https://docs.docker.com/get-docker/))
2.  **Git** installed
3.  A **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
4.  Your personal **Telegram User ID** from a bot like [@userinfobot](https://t.me/userinfobot)
5.  A **Pakasir Account** for the payment gateway *(for production payment processing)*

---

## 🚀 Getting Started (Local Development)

This setup is recommended for testing, development, and small-scale use. It runs the application, databases, and Redis in Docker containers on your local machine.

### 1. Clone the Repository

```bash
git clone https://github.com/moccalatte/quickcart-v1.git
cd quickcart-v1
```

### 2. Configure Your Environment

Copy the environment variable template and fill in your credentials.

```bash
# 1. Copy the template
cp .env.template .env

# 2. Edit the .env file with a text editor (like nano, vim, or VS Code)
nano .env
```

Inside the `.env` file, you **must** fill in these required values:
- `TELEGRAM_BOT_TOKEN`
- `ADMIN_USER_IDS`
- `PAKASIR_API_KEY`
- `PAKASIR_PROJECT_SLUG`
- `SECRET_KEY` (generate a random string)
- `ENCRYPTION_KEY` (generate a random string)

The database and Redis variables are already pre-configured for the local Docker setup.

### 3. Launch the Application

Build and run the Docker containers in detached mode.

```bash
docker compose up -d --build
```

### 4. Check the Logs

Verify that the application and all services started correctly.

```bash
docker compose logs -f app
```

You should see a message indicating the bot has started successfully. You can now go to Telegram and start a conversation with your bot.

**Current Bot Capabilities:**
- ✅ User onboarding and registration
- ✅ Main menu navigation
- ✅ Product browsing interface
- ✅ Account management
- ✅ Flexible session-based navigation
- 🔧 Order processing (in development)
- 🔧 Payment integration (in development)
- 🔧 Admin commands (in development)

---

## 🌐 Production Deployment

This guide covers deploying QuickCart to production with **external PostgreSQL and Redis servers** (e.g., on separate VPS instances).

### Prerequisites

- **Application Server**: VPS/server for running the bot (Docker installed)
- **PostgreSQL Server**: VPS/managed service for databases (can be same or different servers for main + audit DB)
- **Redis Server** (Optional but recommended): VPS/managed service for session storage
- **Domain/IP**: For webhook configuration (optional, bot works with polling)

### Architecture Overview

```
┌─────────────────────┐
│   Application VPS   │
│   (Docker + Bot)    │
│   Port: 8000        │
└─────────┬───────────┘
          │
          ├──────────────┐
          │              │
┌─────────▼─────────┐  ┌─▼─────────────────┐
│  PostgreSQL VPS   │  │   Redis VPS       │
│  - Main DB        │  │   (Optional)      │
│  - Audit DB       │  │   Port: 6379      │
│  Port: 5432       │  └───────────────────┘
└───────────────────┘
```

---

## 📝 Step-by-Step Production Deployment

### Step 1: Prepare PostgreSQL Server

#### Option A: Separate VPS for PostgreSQL

**1.1. Install PostgreSQL on your DB server:**
```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**1.2. Configure PostgreSQL for remote access:**
```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf

# Change listen_addresses:
listen_addresses = '*'  # or specify your app server IP

# Edit pg_hba.conf to allow remote connections
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Add this line (replace with your app server IP):
host    all             all             YOUR_APP_SERVER_IP/32    md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

**1.3. Create databases and users:**
```bash
sudo -u postgres psql

-- Create main database user and database
CREATE USER quickcart WITH PASSWORD 'YOUR_STRONG_PASSWORD';
CREATE DATABASE quickcart OWNER quickcart;
GRANT ALL PRIVILEGES ON DATABASE quickcart TO quickcart;

-- Create audit database user and database
CREATE USER quickcart_audit WITH PASSWORD 'YOUR_STRONG_PASSWORD';
CREATE DATABASE quickcart_audit OWNER quickcart_audit;
GRANT ALL PRIVILEGES ON DATABASE quickcart_audit TO quickcart_audit;

\q
```

#### Option B: Managed PostgreSQL (e.g., DigitalOcean, AWS RDS)

- Create two databases: `quickcart` and `quickcart_audit`
- Note the connection strings provided
- Ensure firewall allows connections from your app server

---

### Step 2: Prepare Redis Server (Optional)

#### Option A: VPS Redis Installation

**2.1. Install Redis:**
```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# Configure Redis for remote access
sudo nano /etc/redis/redis.conf

# Change bind address:
bind 0.0.0.0  # or specify your app server IP

# Set password:
requirepass YOUR_REDIS_PASSWORD

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

**2.2. Test Redis connection:**
```bash
redis-cli -h YOUR_REDIS_IP -a YOUR_REDIS_PASSWORD ping
# Should return: PONG
```

#### Option B: Managed Redis (e.g., Redis Cloud, AWS ElastiCache)

- Create Redis instance
- Note the connection URL
- Ensure firewall allows connections from your app server

#### Option C: Skip Redis (Use In-Memory Fallback)

QuickCart works without Redis using in-memory session storage. This is fine for:
- Single bot instance
- Low to medium traffic
- Development/testing

To disable Redis, leave `REDIS_URL` empty in `.env`

---

### Step 3: Setup Application Server

**3.1. Clone repository on your app server:**
```bash
ssh user@your-app-server
cd /opt  # or your preferred directory
git clone https://github.com/yourusername/quickcart-v1.git
cd quickcart-v1
```

**3.2. Create production environment file:

```bash
cp .env.template .env
nano .env  # or use your preferred editor
```

**3.3. Configure production environment:**

Edit `.env` with your production settings:

```bash
# === REQUIRED ===
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
ADMIN_USER_IDS=123456789,987654321
PAKASIR_API_KEY=pk_live_your_api_key
PAKASIR_PROJECT_SLUG=your-production-store
SECRET_KEY=generate_with_openssl_rand_hex_32
ENCRYPTION_KEY=generate_with_openssl_rand_hex_32

# === STORE CUSTOMIZATION ===
STORE_NAME="Your Store Name"
BOT_NAME="Your Bot Name"
DOCUMENTATION_URL="https://your-docs.com"
SUPPORT_CONTACT="@YourSupport"

# === DATABASE (External PostgreSQL) ===
DATABASE_URL=postgresql+asyncpg://quickcart:YOUR_DB_PASSWORD@YOUR_DB_SERVER_IP:5432/quickcart
AUDIT_DATABASE_URL=postgresql+asyncpg://quickcart_audit:YOUR_DB_PASSWORD@YOUR_DB_SERVER_IP:5432/quickcart_audit

# === REDIS (External or disabled) ===
# Option 1: External Redis
REDIS_URL=redis://:YOUR_REDIS_PASSWORD@YOUR_REDIS_SERVER_IP:6379/0
# Option 2: Disable Redis (use in-memory)
# REDIS_URL=

# === PRODUCTION SETTINGS ===
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=WARNING
PAKASIR_WEBHOOK_SECRET=your_webhook_secret_from_pakasir
```

**Generate secure keys:**
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate ENCRYPTION_KEY
openssl rand -hex 32
```

**3.4. Test database connectivity:**
```bash
# Install PostgreSQL client
sudo apt install postgresql-client

# Test main database connection
psql "postgresql://quickcart:YOUR_PASSWORD@YOUR_DB_IP:5432/quickcart" -c "SELECT version();"

# Test audit database connection
psql "postgresql://quickcart_audit:YOUR_PASSWORD@YOUR_DB_IP:5432/quickcart_audit" -c "SELECT version();"
```

**3.5. Run database migrations:**
```bash
# Using Docker (recommended)
docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# Or manually if you have Python environment
pip install -r requirements.txt
alembic upgrade head
```

**3.6. Launch application:**
```bash
# Build and start in production mode
docker compose -f docker-compose.prod.yml up -d --build

# Check logs
docker compose -f docker-compose.prod.yml logs -f app

# You should see:
# ✅ Starting QuickCart v1.1.0...
# ✓ Redis connected (or ✓ Using in-memory storage)
# ✓ Database status: {'main_db': 'ok', 'audit_db': 'ok'}
# ✓ Bot initialized
# ✅ QuickCart is ready!
```

**3.7. Verify bot is working:**
- Open Telegram and find your bot
- Send `/start` - should get welcome message
- Test navigation - all buttons should work
- Check database for new user record

---

### Step 4: Security Hardening (Production)

**4.1. Firewall Configuration:**
```bash
# On application server - allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # Bot API (if using webhook)
sudo ufw enable

# On database server - allow only from app server
sudo ufw allow from YOUR_APP_SERVER_IP to any port 5432
sudo ufw enable

# On Redis server - allow only from app server
sudo ufw allow from YOUR_APP_SERVER_IP to any port 6379
sudo ufw enable
```

**4.2. SSL/TLS for Database (Recommended):**
```bash
# Add to your DATABASE_URL:
# ?ssl=require
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require
```

**4.3. Regular Backups:**
```bash
# PostgreSQL backup script (run daily via cron)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h YOUR_DB_IP -U quickcart quickcart > backup_main_$DATE.sql
pg_dump -h YOUR_DB_IP -U quickcart_audit quickcart_audit > backup_audit_$DATE.sql

# Add to crontab
0 2 * * * /path/to/backup-script.sh
```

**4.4. Monitoring:**
```bash
# Install monitoring (optional but recommended)
# Add Sentry DSN to .env:
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project

# Or use simple log monitoring:
docker compose -f docker-compose.prod.yml logs -f app | grep ERROR
```

---

### Step 5: Webhook Setup (Optional - For Better Performance)

Instead of polling, use webhooks for faster message delivery:

**5.1. Configure webhook URL:**
```bash
# Your webhook URL format:
https://your-domain.com/webhooks/telegram

# Set webhook via Telegram API:
curl -X POST \
  "https://api.telegram.org/bot${YOUR_BOT_TOKEN}/setWebhook" \
  -d "url=https://your-domain.com/webhooks/telegram"
```

**5.2. Configure reverse proxy (Nginx):**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /webhooks/telegram {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🔧 Production Maintenance

### Updating the Bot

```bash
cd /opt/quickcart-v1
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```

### Viewing Logs

```bash
# Follow logs in real-time
docker compose -f docker-compose.prod.yml logs -f app

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 app

# Save logs to file
docker compose -f docker-compose.prod.yml logs app > bot-logs.txt
```

### Restarting the Bot

```bash
docker compose -f docker-compose.prod.yml restart app
```

### Database Backup & Restore

```bash
# Backup
pg_dump -h YOUR_DB_IP -U quickcart quickcart > backup.sql

# Restore
psql -h YOUR_DB_IP -U quickcart quickcart < backup.sql
```

---

## 🚨 Troubleshooting Production Issues

### Bot Not Connecting to Database

```bash
# Check database is accessible
psql "postgresql://quickcart:PASSWORD@DB_IP:5432/quickcart"

# Check firewall rules
sudo ufw status

# Check logs
docker compose -f docker-compose.prod.yml logs app | grep -i database
```

### Redis Connection Issues

```bash
# Test Redis connection
redis-cli -h YOUR_REDIS_IP -a YOUR_PASSWORD ping

# Check if bot is using in-memory fallback
docker compose -f docker-compose.prod.yml logs app | grep -i redis

# If you see "Using in-memory storage", Redis is disabled or unreachable
```

### Bot Not Responding

```bash
# Check if container is running
docker ps

# Check bot logs for errors
docker compose -f docker-compose.prod.yml logs --tail=100 app

# Restart bot
docker compose -f docker-compose.prod.yml restart app
```

---

## 📊 Production Checklist

Before going live, verify:

- [ ] `ENVIRONMENT=production` in `.env`
- [ ] `DEBUG=False` in `.env`
- [ ] Strong passwords for all databases
- [ ] `SECRET_KEY` and `ENCRYPTION_KEY` are random and unique
- [ ] Database URLs point to production servers
- [ ] Redis URL configured (or intentionally disabled)
- [ ] Firewall rules configured on all servers
- [ ] Database backups configured and tested
- [ ] Bot tested with `/start` command
- [ ] Product catalog populated
- [ ] Admin user IDs are correct
- [ ] Pakasir integration tested (test payment)
- [ ] SSL/TLS enabled for database connections
- [ ] Monitoring/alerting configured (Sentry or logs)
- [ ] Documentation URL updated to your docs
- [ ] Store name and bot name customized
- [ ] Support contact configured

---

## ⚙️ Configuration

All configuration is managed through environment variables listed in `.env.template`. The application uses two separate Docker Compose files:

- `docker-compose.yml`: For **local development**. Includes `app`, `db`, `audit_db`, and `redis` services. Mounts the `src` directory for live-reloading.
- `docker-compose.prod.yml`: For **production**. Includes only the `app` service and is designed to connect to external databases and Redis.

See the `.env.template` file for a complete list of all available configuration variables and their descriptions.

---

## 🛠️ Useful Docker Commands

All commands should be run from the project's root directory.

#### View Logs
```bash
# For local development
docker compose logs -f

# For production
docker compose -f docker-compose.prod.yml logs -f
```

#### Stop Services
```bash
# For local development
docker compose down

# For production
docker compose -f docker-compose.prod.yml down
```

#### Stop Services and Remove Data Volumes
**Warning:** This will delete all your local database data.
```bash
docker compose down -v
```

#### Run Database Migrations Manually
The entrypoint script runs this automatically, but you can run it manually if needed.
```bash
docker compose exec app alembic upgrade head
```

#### Access the Main Database
```bash
docker compose exec db psql -U quickcart -d quickcart
```

---

## 📂 Project Structure

```
quickcart-v1/
├── src/                      # Source code
│   ├── core/                 # Config, database, redis, security
│   ├── models/               # SQLAlchemy database models
│   ├── repositories/         # Data access layer
│   ├── services/             # Business logic layer
│   ├── bot/                  # Telegram bot handlers & keyboards
│   │   ├── handlers/         # Command, callback, message handlers
│   │   ├── keyboards/        # Reply & inline keyboards
│   │   └── utils/            # Bot utilities
│   └── integrations/         # External API clients (Pakasir)
│
├── migrations/               # Alembic database migrations
│   └── versions/             # Migration scripts
├── docs/                     # Comprehensive project documentation
│   ├── 00-20-*.md            # Numbered design documents
│   ├── plans.md              # Original functional blueprint
│   └── *.md                  # Additional guides and references
├── tests/                    # Unit & integration tests
├── docker-compose.yml        # Local development (includes all services)
├── docker-compose.prod.yml   # Production deployment (app only)
├── Dockerfile                # App container image
├── .env.template             # Environment variables template
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```
