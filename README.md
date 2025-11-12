# QuickCart - Telegram Auto-Order Bot 🤖

> **Automated digital product sales bot for Telegram with QRIS payment integration**

QuickCart is a complete auto-order bot system for selling digital products (courses, accounts, vouchers, etc.) through Telegram. Customers can browse, order, and receive products automatically after payment - all without manual intervention.

**Built with python-telegram-bot v22.5** - Latest version with full async/await support  
📚 Library: https://github.com/python-telegram-bot/python-telegram-bot

---

## ✨ Features

- 🛍️ **Product Catalog** - Browse products by category, best sellers, or view all
- 💳 **QRIS Payment** - Automatic payment via Pakasir gateway (0.7% + Rp310 fee)
- ⏱️ **10-Minute Expiry** - Payments automatically expire if not completed
- 👥 **Multi-Tier Users** - Customer, Reseller, and Admin roles
- 🎫 **Voucher System** - Create and distribute discount codes
- 📊 **Audit Logging** - Complete transaction history for compliance
- 🔒 **Secure** - Separate audit database, encrypted sensitive data
- 🌐 **Flexible Deployment** - Works on any server (VPS, cloud, local)
- 🐳 **Docker Ready** - One-command deployment with Docker Compose

---

## 📋 Prerequisites

Before you start, make sure you have:

1. **Docker & Docker Compose** installed ([Get Docker](https://docs.docker.com/get-docker/))
2. **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
3. **Your Telegram User ID** from [@userinfobot](https://t.me/userinfobot)
4. **Pakasir Account** - Sign up at [pakasir.com](https://pakasir.com) for payment gateway

That's it! No programming knowledge needed. Docker handles everything.

**📖 For absolute beginners:** Read `INSTALL.md` for step-by-step guide with screenshots!

---

## 🚀 Quick Start (5 Minutes)

**IMPORTANT:** Never run this before? → Read `INSTALL.md` first for complete guide!

### Method 1: Automatic Setup (Easiest)

```bash
# 1. Download QuickCart
git clone <your-repo-url>
cd quickcart-v1

# 2. Run setup wizard
chmod +x setup.sh
./setup.sh
```

The wizard will ask for your:
- Telegram Bot Token (from @BotFather)
- Telegram User ID (from @userinfobot)
- Pakasir API Key
- Pakasir Project Slug

Then automatically starts everything! ✅

### Method 2: Manual Setup

```bash
# 1. Download QuickCart
git clone <your-repo-url>
cd quickcart-v1

# 2. Create configuration
cp .env.example.template .env

# 3. Edit .env file - fill in 6 REQUIRED values:
nano .env  # or use any text editor

# Required values:
TELEGRAM_BOT_TOKEN=your_token_from_botfather
ADMIN_USER_IDS=your_telegram_user_id
PAKASIR_API_KEY=your_pakasir_api_key
PAKASIR_PROJECT_SLUG=your_pakasir_slug
SECRET_KEY=generate_random_32_chars
ENCRYPTION_KEY=generate_random_32_chars

# Generate keys with:
# python -c "import secrets; print(secrets.token_urlsafe(32))"

# 4. Start the bot
docker compose up -d

# 5. Check logs
docker compose logs -f app
```

### ✅ Verify It Works

1. **Check services are running:**
   ```bash
   docker compose ps
   # All should show "Up"
   ```

2. **Test in Telegram:**
   - Open Telegram
   - Search for your bot
   - Send `/start`
   - You should see welcome message!

🎉 **Success!** Bot is running.

**If anything fails:** See `INSTALL.md` for detailed troubleshooting!

---

## 📱 Using the Bot

### For Customers

1. **Start the bot**: `/start`
2. **Browse products**: Click `[LIST PRODUK]` or use category buttons
3. **Order**: Send product number (1-24), select quantity, choose payment
4. **Pay**: Scan QRIS code or use account balance
5. **Receive**: Product delivered automatically after payment confirmed

### For Admins

All admin commands work directly in Telegram:

```
/add 1|Netflix Premium|Streaming|50000|Akun Netflix 1 bulan
/addstock 1|email:password
/editproduct 1|name|New Product Name
/stock - View all product stock
/orders - View recent orders
/info 123456789 - View user info
/transfer 123456789|50000 - Add balance to user
/broadcast - Send message to all users
/giveaway - Create voucher codes
```

**Full command reference**: See [docs/03-prd.md](docs/03-prd.md) or [plans.md](plans.md)

---

## 🎯 How It Works

```
┌─────────────┐
│   Customer  │ Sends /start
│  (Telegram) │ ──────────────┐
└─────────────┘               │
                              ▼
                    ┌──────────────────┐
                    │  QuickCart Bot   │
                    │   (This App)     │
                    └──────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ┌──────────────┐    ┌──────────────┐
            │  PostgreSQL  │    │   Pakasir    │
            │  (Products,  │    │   (Payment   │
            │   Orders)    │    │   Gateway)   │
            └──────────────┘    └──────────────┘
```

1. Customer browses products via Telegram bot
2. Bot generates QRIS payment via Pakasir API
3. Customer pays using any Indonesian e-wallet
4. Pakasir webhook notifies bot of payment
5. Bot delivers digital product automatically
6. All transactions logged to audit database

---

## 🛠️ Management Commands

```bash
# View logs
docker compose logs -f app

# Restart bot (after code changes)
docker compose restart app

# Stop all services
docker compose down

# Stop and remove all data (CAUTION!)
docker compose down -v

# Enter database
docker compose exec db psql -U quickcart -d quickcart

# Enter bot container
docker compose exec app sh

# Run database migrations manually
docker compose exec app alembic upgrade head

# View database tables
docker compose exec db psql -U quickcart -d quickcart -c "\dt"

# Or use Makefile shortcuts:
make logs      # View logs
make restart   # Restart bot
make db        # Open database
make help      # See all commands
```

---

## 📂 Project Structure

```
quickcart-v1/
├── src/                      # Source code
│   ├── core/                 # Config, database, redis
│   ├── models/               # Database models
│   ├── repositories/         # Database operations
│   ├── services/             # Business logic
│   ├── handlers/             # Telegram command handlers
│   └── integrations/         # Pakasir API client
│
├── migrations/               # Database migrations
│   └── versions/             # Migration files
│
├── docs/                     # Complete documentation (20 files)
│   ├── 01-dev_protocol.md    # Development guidelines
│   ├── 03-prd.md             # Product requirements
│   ├── 04-uiux_flow.md       # User flows
│   ├── 06-data_schema.md     # Database schema
│   └── ...                   # 16 more docs
│
├── tests/                    # Unit & integration tests
├── docker-compose.yml        # Docker services config
├── Dockerfile                # App container image
├── .env                      # Your configuration (create from .env.example.template)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## ⚙️ Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | - | Bot token from @BotFather |
| `ADMIN_USER_IDS` | ✅ Yes | - | Comma-separated admin Telegram IDs |
| `PAKASIR_API_KEY` | ✅ Yes | - | Pakasir API key |
| `PAKASIR_PROJECT_SLUG` | ✅ Yes | - | Pakasir project slug |
| `SECRET_KEY` | ✅ Yes | - | Secret for encryption |
| `ENCRYPTION_KEY` | ✅ Yes | - | Key for sensitive data |
| `DATABASE_URL` | ⚪ No | Auto | PostgreSQL connection string |
| `REDIS_URL` | ⚪ No | Auto | Redis connection (optional) |
| `ENVIRONMENT` | ⚪ No | `development` | Environment mode |
| `DEBUG` | ⚪ No | `true` | Debug mode |
| `STORE_NAME` | ⚪ No | `QuickCart Store` | Your store name |

**See `.env.example.template` for complete list with descriptions.**

### Database Configuration

QuickCart uses **two PostgreSQL databases**:

1. **Main Database** (`quickcart`) - Stores products, orders, users
2. **Audit Database** (`quickcart_audit`) - Permanent compliance logs

Both are created automatically on first run.

### Redis (Optional)

Redis is used for:
- User session management
- Product stock caching
- Rate limiting
- Payment expiry queue

**If Redis is not available**, the system automatically falls back to **in-memory storage**. This works fine for:
- Testing and development
- Low-traffic stores (< 100 concurrent users)
- Single-server deployments

For production with high traffic, Redis is recommended.

---

## 🔧 Troubleshooting

### Bot doesn't respond to /start

**Check logs:**
```bash
docker-compose logs -f app
```

**Common issues:**
- Wrong `TELEGRAM_BOT_TOKEN` - Verify token with @BotFather
- Bot not started - Send any message to wake it up
- Webhook conflicts - Use `/deleteWebhook` via @BotFather

### Database connection error

**Solution:**
```bash
# Restart database
docker-compose restart db

# Wait for it to be healthy
docker-compose ps

# Re-run migrations
docker-compose exec app alembic upgrade head
```

### Payment webhook not working

**Check:**
1. `PAKASIR_WEBHOOK_SECRET` matches Pakasir dashboard
2. Your server is accessible from internet (for webhooks)
3. Webhook URL configured in Pakasir: `https://your-domain.com/webhooks/pakasir`

**For local testing:**
- Use ngrok: `ngrok http 8000`
- Set webhook URL to ngrok URL

### Redis connection error

Redis is **optional**. If you see:
```
⚠ Redis connection failed
✓ Falling back to in-memory storage
```

This is **normal** and the bot will work fine. To disable Redis completely:

**Option 1:** Comment out Redis in `docker-compose.yml`:
```yaml
#  redis:
#    image: redis:7-alpine
#    ...
```

**Option 2:** Remove `REDIS_URL` from `.env`

### Reset everything (clean slate)

```bash
# CAUTION: This deletes all data!
docker-compose down -v
docker-compose up -d
```

---

## 📊 Database Schema

### Main Tables

- **users** - Customer, reseller, and admin accounts
- **products** - Product catalog (ID 1-24)
- **product_stocks** - Individual stock items (digital content)
- **orders** - Order records with payment info
- **order_items** - Products in each order
- **vouchers** - Discount codes
- **voucher_usage_cooldown** - Prevent voucher abuse (5-min cooldown)

### Audit Tables

- **audit_logs** - Master audit log (permanent)
- **payment_audit_logs** - Payment transactions (permanent)
- **admin_action_audit** - Admin commands (permanent)

**View complete schema:** [docs/06-data_schema.md](docs/06-data_schema.md)

---

## 🧪 Testing

```bash
# Run all tests
docker-compose exec app pytest

# Run with coverage
docker-compose exec app pytest --cov=src --cov-report=html

# Run specific test file
docker-compose exec app pytest tests/test_orders.py

# View coverage report
open htmlcov/index.html
```

---

## 📚 Documentation

Complete documentation available in `docs/` folder:

1. **[01-dev_protocol.md](docs/01-dev_protocol.md)** - Development guidelines
2. **[03-prd.md](docs/03-prd.md)** - Product requirements & features
3. **[04-uiux_flow.md](docs/04-uiux_flow.md)** - User flows & UI screens
4. **[06-data_schema.md](docs/06-data_schema.md)** - Database schema
5. **[08-integration_plan.md](docs/08-integration_plan.md)** - Pakasir integration
6. **[09-security_manifest.md](docs/09-security_manifest.md)** - Security best practices
7. **[14-build_plan.md](docs/14-build_plan.md)** - Build & deployment guide
8. ... and 13 more detailed docs

---

## 🌐 Deployment Options

### Option 1: Docker Compose (Recommended for Beginners)

Already covered in Quick Start above. Works on:
- Any VPS (DigitalOcean, Linode, Vultr, etc.)
- AWS EC2, Google Cloud, Azure
- Your own server
- Even your laptop (for testing)

### Option 2: Manual Deployment

```bash
# Install Python 3.11+
python3 --version

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL and Redis
# (Install separately)

# Run migrations
alembic upgrade head

# Start bot
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Option 3: DockerHub (Coming Soon)

We'll publish a ready-to-use Docker image:

```bash
docker pull quickcart/bot:latest
docker run -d --env-file .env quickcart/bot:latest
```

---

## 🔐 Security Best Practices

1. **Never commit `.env` file** - It contains secrets
2. **Use strong SECRET_KEY and ENCRYPTION_KEY** - Generate random 32-char strings
3. **Keep ADMIN_USER_IDS accurate** - Only trusted admins
4. **Enable HTTPS** - Use reverse proxy (nginx) with SSL
5. **Regular backups** - Backup PostgreSQL databases daily
6. **Monitor logs** - Check for suspicious activity
7. **Update regularly** - Pull latest updates from repository

---

## 🤝 Support & Community

- **Issues**: [GitHub Issues](https://github.com/yourrepo/issues)
- **Documentation**: See `docs/` folder (20 detailed guides)
- **Telegram**: Join our support channel (link here)

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

## 🙏 Credits

Built with:
- **Python 3.11** - Core language
- **FastAPI** - Web framework
- **SQLAlchemy 2.0** - Database ORM (async)
- **python-telegram-bot v22.5** - Telegram Bot API (latest)
- **PostgreSQL 15** - Database
- **Redis 7** - Caching (optional)
- **Docker** - Containerization
- **Pakasir** - QRIS payment gateway
- **Alembic** - Database migrations

---

## 📈 Roadmap

- [x] Core order flow
- [x] QRIS payment integration
- [x] Admin commands
- [x] Voucher system
- [x] Audit logging
- [ ] WhatsApp notifications
- [ ] Product images
- [ ] Analytics dashboard
- [ ] Multiple payment gateways
- [ ] Subscription products

---

## 💡 Tips for Success

1. **Read INSTALL.md first** - Complete guide from zero to running
2. **Start small** - Add 1-2 products first, test thoroughly
3. **Test payments** - Use small amounts initially
4. **Set up webhooks** - Critical for automatic order fulfillment
5. **Monitor logs** - First few days, check logs regularly: `docker compose logs -f app`
6. **Backup database** - Run `make backup` before major changes
7. **Read the docs** - Especially [plans.md](plans.md), [03-prd.md](docs/03-prd.md), and [TESTING.md](TESTING.md)

---

## ❓ FAQ

**Q: Do I need programming skills?**  
A: No! If you can copy files and edit a text file, you can deploy this bot. Read `INSTALL.md` for complete beginner guide.

**Q: Does this work outside Indonesia?**  
A: Yes, but you'll need to replace Pakasir with your local payment gateway.

**Q: Can I customize the UI?**  
A: Yes! Edit language files and button layouts in `src/handlers/` folder (when implemented).

**Q: Is Redis required?**  
A: No, it's optional. The bot works fine without Redis using in-memory storage.

**Q: What Telegram library is used?**  
A: python-telegram-bot v22.5 (latest version). Install: `pip install python-telegram-bot --upgrade`

**Q: Can I sell physical products?**  
A: This bot is designed for digital products (instant delivery). For physical products, you'd need to modify the fulfillment logic.

**Q: How do I update the bot?**  
A: `git pull` and `docker compose up -d --build` or just run `make update`

**Q: Where are my databases stored?**  
A: In Docker volumes. Run `docker volume ls` to see them.

**Q: Bot doesn't respond to /start?**  
A: Check logs with `docker compose logs -f app`. Common issues: wrong bot token, database not ready (wait 30s), or webhook conflicts.

**Q: How do I run the CI/CD pipeline?**
A: The CI/CD pipeline is automatically triggered on push and pull requests to the main and develop branches.

---

**Ready to launch your digital store?**

- **Absolute beginner?** → Read `INSTALL.md` (complete step-by-step guide)
- **Have Docker experience?** → Follow Quick Start above
- **Need testing guide?** → Read `TESTING.md` (50+ test cases)
- **Want all details?** → See `docs/` folder (20 comprehensive guides)

**You'll be selling in 5-10 minutes! 🚀**