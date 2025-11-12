# 🚀 BUILD AND RUN GUIDE - QuickCart v1.0.0

**Complete step-by-step guide to build Docker image and run QuickCart**

⚠️ **IMPORTANT**: Follow these steps EXACTLY in order!

---

## 📋 Pre-Flight Checklist

Before you start, verify you have:

- [ ] Docker installed (`docker --version` shows 20.10+)
- [ ] Docker Compose installed (`docker compose version` shows 2.0+)
- [ ] Git installed (if cloning from repo)
- [ ] Terminal/Command Prompt open
- [ ] Internet connection (to download images)

**If Docker not installed:** See `INSTALL.md` for installation guide.

---

## 🎯 Quick Start (TL;DR)

```bash
# 1. Navigate to project
cd quickcart-v1

# 2. Create .env file
cp .env.example.template .env

# 3. Edit .env (REQUIRED!)
nano .env  # or any text editor

# 4. Build and run
docker compose up -d --build

# 5. Check logs
docker compose logs -f app

# 6. Test in Telegram
# Send /start to your bot
```

---

## 📝 Detailed Step-by-Step Guide

### Step 1: Navigate to Project Directory

```bash
cd quickcart-v1
```

**Verify you're in the right place:**
```bash
ls -la
# You should see: docker-compose.yml, Dockerfile, requirements.txt, src/, etc.
```

---

### Step 2: Create Environment File

⚠️ **CRITICAL**: This step is REQUIRED!

```bash
# Copy the template
cp .env.example.template .env
```

**Verify file was created:**
```bash
ls -la .env
# Should show: .env file exists
```

---

### Step 3: Edit Environment Variables

Open `.env` file with your favorite editor:

```bash
# Linux/Mac
nano .env
# or
vim .env
# or
code .env  # if you have VS Code

# Windows
notepad .env
# or
code .env
```

**Fill in these 6 REQUIRED values:**

```env
# 1. From @BotFather on Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ

# 2. From @userinfobot on Telegram (YOUR user ID)
ADMIN_USER_IDS=123456789

# 3. From pakasir.com dashboard
PAKASIR_API_KEY=pk_live_xxxxxxxxxxxxxxxx

# 4. From pakasir.com dashboard
PAKASIR_PROJECT_SLUG=your-project-slug

# 5. Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your_random_secret_key_here

# 6. Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
ENCRYPTION_KEY=your_random_encryption_key_here
```

**Generate SECRET_KEY and ENCRYPTION_KEY:**

```bash
# If you have Python installed:
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Run this TWICE to get two different keys

# If no Python, use online generator:
# https://www.random.org/strings/ (32 characters)
```

**Save the file** (Ctrl+O, Enter, Ctrl+X in nano)

---

### Step 4: Verify Configuration

Check your `.env` file:

```bash
cat .env | grep -E "TELEGRAM_BOT_TOKEN|ADMIN_USER_IDS|PAKASIR_API_KEY|SECRET_KEY|ENCRYPTION_KEY"
```

**ALL 5 values should NOT contain "your_" or "generate_"**

If they still have placeholder text, GO BACK TO STEP 3!

---

### Step 5: Build Docker Image

Now build the Docker image:

```bash
docker compose build
```

**What happens:**
- Downloads Python 3.11 base image
- Installs system dependencies
- Installs Python packages from requirements.txt
- Copies application code
- Creates health check

**Time:** 2-5 minutes on first build

**Expected output (last lines):**
```
 => => naming to docker.io/library/quickcart-app
```

**If you see errors:**
- Check your internet connection
- Try: `docker compose build --no-cache`
- See troubleshooting section below

---

### Step 6: Start All Services

Start the database, Redis, and application:

```bash
docker compose up -d
```

**What happens:**
- Creates Docker network
- Starts PostgreSQL database
- Starts Redis cache (optional)
- Starts QuickCart application
- Runs database migrations automatically

**Time:** 10-30 seconds

**Expected output:**
```
✔ Container quickcart_db    Started
✔ Container quickcart_redis Started
✔ Container quickcart_app   Started
```

---

### Step 7: Verify Services are Running

```bash
docker compose ps
```

**Expected output:**
```
NAME                IMAGE           STATUS
quickcart_db        postgres:15     Up (healthy)
quickcart_redis     redis:7         Up (healthy)
quickcart_app       quickcart       Up (healthy)
```

**All should show "Up"**

**If any show "Exit" or "Restarting":**
```bash
docker compose logs <service-name>
# Example: docker compose logs app
```

---

### Step 8: Check Application Logs

View real-time logs:

```bash
docker compose logs -f app
```

**Expected output (within 30 seconds):**
```
quickcart_app | 🔄 Running migrations...
quickcart_app | ✓ Redis connected successfully
quickcart_app | ✓ Database status: {'main_db': 'ok', 'audit_db': 'ok'}
quickcart_app | ✅ QuickCart is ready!
quickcart_app | INFO:     Application startup complete.
```

**Press Ctrl+C to exit logs** (services keep running)

**If you see errors:** See troubleshooting section below

---

### Step 9: Verify Database Tables

Check that database tables were created:

```bash
docker compose exec db psql -U quickcart -d quickcart -c "\dt"
```

**Expected output:**
```
                List of relations
 Schema |          Name          | Type  |   Owner
--------+------------------------+-------+-----------
 public | users                  | table | quickcart
 public | products               | table | quickcart
 public | product_stocks         | table | quickcart
 public | orders                 | table | quickcart
 public | order_items            | table | quickcart
 public | vouchers               | table | quickcart
 public | voucher_usage_cooldown | table | quickcart
(7 rows)
```

**Should show 7 tables**

---

### Step 10: Test Health Endpoint

```bash
curl http://localhost:8000/health
```

**Expected output:**
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

**All services should be "ok"**

---

### Step 11: Test Your Bot in Telegram

1. Open Telegram
2. Search for your bot (username from @BotFather)
3. Send: `/start`

**Expected response:**
```
ᯓ Halo **Your Name** 👋🏻
Selamat datang di **QuickCart Store**

⤷ Total Pengguna: 1 Orang
⤷ Total Transaksi: 0x

Dokumentasi: [Baca Disini]
Silakan tombol dibawah ini untuk melihat produk yang tersedia.
```

**With buttons:**
```
[LIST PRODUK] [STOK]
[AKUN] [KIRIM PESAN]
```

---

## ✅ Success Checklist

If ALL of these are true, you're READY:

- [x] Docker build completed without errors
- [x] All 3 services show "Up" status
- [x] App logs show "✅ QuickCart is ready!"
- [x] Health endpoint returns all "ok"
- [x] Database has 7 tables
- [x] Bot responds to /start in Telegram

**🎉 Congratulations! Your bot is RUNNING!**

---

## 🛠️ Common Commands

### View Logs
```bash
# All services
docker compose logs -f

# Just app
docker compose logs -f app

# Just database
docker compose logs -f db

# Last 100 lines
docker compose logs --tail=100 app
```

### Restart Services
```bash
# Restart app only
docker compose restart app

# Restart all
docker compose restart

# Stop all
docker compose down

# Start all
docker compose up -d
```

### Database Access
```bash
# Main database
docker compose exec db psql -U quickcart -d quickcart

# Audit database
docker compose exec db psql -U quickcart -d quickcart_audit

# Run SQL command
docker compose exec db psql -U quickcart -d quickcart -c "SELECT * FROM users;"
```

### Rebuild After Code Changes
```bash
# Stop services
docker compose down

# Rebuild and start
docker compose up -d --build

# Or just rebuild app
docker compose build app
docker compose up -d
```

---

## 🐛 Troubleshooting

### Error: "Cannot connect to Docker daemon"

**Solution (Linux):**
```bash
# Start Docker daemon
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in
```

**Solution (Mac/Windows):**
- Make sure Docker Desktop is running
- Check Docker Desktop icon in system tray
- Restart Docker Desktop

---

### Error: "env file .env not found"

**Solution:**
```bash
# You skipped Step 2! Create .env file:
cp .env.example.template .env
# Then edit it with your values
```

---

### Error: "invalid reference format"

**Solution:**
Your .env file has invalid values (spaces, special characters).

```bash
# Check your .env file
cat .env

# Common issues:
# - Spaces around = sign (wrong: KEY = value)
# - Quotes around values (wrong: KEY="value")
# - Special characters not escaped

# Correct format:
KEY=value
```

---

### Error: "port 5432 already allocated"

**Solution:**
PostgreSQL is already running on your computer.

```bash
# Option 1: Stop PostgreSQL
sudo systemctl stop postgresql  # Linux
brew services stop postgresql   # Mac

# Option 2: Change port in docker-compose.yml
# Change "5432:5432" to "5433:5432"
```

---

### Error: "Bot doesn't respond to /start"

**Checklist:**
1. Check TELEGRAM_BOT_TOKEN in .env is correct
2. Check bot logs: `docker compose logs -f app`
3. Verify bot is not already running elsewhere
4. Try: `/deleteWebhook` via @BotFather
5. Restart app: `docker compose restart app`

---

### Error: "Database migration failed"

**Solution:**
```bash
# Reset database
docker compose down -v
docker compose up -d

# Or run migrations manually
docker compose exec app alembic upgrade head
```

---

### Error: "Redis connection failed"

**This is OK!** System will use in-memory storage.

You should see:
```
⚠ Redis connection failed
✓ Falling back to in-memory storage
```

Bot will work fine without Redis.

**To fix Redis:**
```bash
# Check Redis status
docker compose ps redis

# Restart Redis
docker compose restart redis
```

---

### Error: "Exec format error" or "no matching manifest"

**Solution:**
Your CPU architecture doesn't match the image.

```bash
# Check your architecture
uname -m

# If ARM (Apple M1/M2):
# Add to docker-compose.yml under app service:
platform: linux/amd64

# Or rebuild for ARM:
docker compose build --platform linux/arm64
```

---

## 🔧 Advanced: Manual Testing

### Test Imports
```bash
docker compose exec app python test_imports.py
```

### Run Python Shell
```bash
docker compose exec app python
>>> from src.core.config import settings
>>> print(settings.admin_ids)
>>> exit()
```

### Test Database Connection
```bash
docker compose exec app python -c "
from src.core.database import db_manager
import asyncio
asyncio.run(db_manager.check_connection())
"
```

---

## 📊 Performance Check

### Check Resource Usage
```bash
docker stats
```

**Expected (idle):**
- DB: ~50MB RAM
- Redis: ~10MB RAM  
- App: ~100MB RAM

### Check Disk Space
```bash
docker system df
```

---

## 🧹 Cleanup

### Stop Services (keep data)
```bash
docker compose down
```

### Remove Everything (DELETE ALL DATA!)
```bash
docker compose down -v
docker system prune -a
```

**⚠️ WARNING: This deletes ALL Docker data!**

---

## 📝 Environment Variables Reference

All environment variables you can set in `.env`:

### Required (6 variables)
```env
TELEGRAM_BOT_TOKEN=     # From @BotFather
ADMIN_USER_IDS=         # Your Telegram user ID
PAKASIR_API_KEY=        # From pakasir.com
PAKASIR_PROJECT_SLUG=   # From pakasir.com
SECRET_KEY=             # Random 32+ characters
ENCRYPTION_KEY=         # Random 32+ characters
```

### Optional (with defaults)
```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

DATABASE_URL=postgresql+asyncpg://quickcart:quickcart123@db:5432/quickcart
AUDIT_DATABASE_URL=postgresql+asyncpg://quickcart:quickcart123@db:5432/quickcart_audit

REDIS_URL=redis://:redis123@redis:6379/0

STORE_NAME=QuickCart Store
PAYMENT_FEE_PERCENTAGE=0.007
PAYMENT_FEE_FIXED=310
PAYMENT_EXPIRY_MINUTES=10
```

**See `.env.example.template` for complete list**

---

## 🎓 Next Steps

After successful build and run:

1. **Add Products**: See `README.md` for `/add` command
2. **Add Stock**: Use `/addstock` command
3. **Test Ordering**: Order as customer
4. **Configure Webhook**: Set up Pakasir webhook
5. **Production Setup**: SSL, monitoring, backups

---

## 📚 Additional Documentation

- `INSTALL.md` - Complete installation from zero
- `README.md` - Features and commands
- `TESTING.md` - Complete testing guide
- `plans.md` - Full specifications
- `docs/` - 20 technical documents

---

## ✅ Final Verification Checklist

Before considering deployment complete:

- [ ] `.env` file created with real values
- [ ] Docker build completed: `docker compose build`
- [ ] Services started: `docker compose up -d`
- [ ] All services healthy: `docker compose ps`
- [ ] Logs show ready: `docker compose logs app`
- [ ] Database tables exist: 7 tables
- [ ] Health endpoint responds: `curl localhost:8000/health`
- [ ] Bot responds in Telegram: `/start` works

---

## 🆘 Getting Help

**Still having issues?**

1. Check logs: `docker compose logs -f app`
2. Read `INSTALL.md` for detailed setup
3. See `TESTING.md` for verification steps
4. Check GitHub issues
5. Include in your issue:
   - Error message
   - Docker version
   - OS version
   - Steps to reproduce
   - Logs output

---

## 📞 Support Resources

- Documentation: `docs/` folder
- Installation: `INSTALL.md`
- Testing: `TESTING.md`
- Issues: GitHub Issues
- python-telegram-bot: https://github.com/python-telegram-bot/python-telegram-bot

---

**Status**: ✅ Ready to Build and Run  
**Version**: 1.0.0  
**Last Updated**: 2025-01-12

**Good luck! Your QuickCart bot will be running in minutes! 🚀**