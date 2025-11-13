# QuickCart Production Deployment Guide

> **Complete guide for deploying QuickCart to production with external PostgreSQL and Redis servers**

**Last Updated:** 2025-01-15  
**Version:** 1.1.0  
**Target:** Production deployment with separate VPS for app, database, and cache

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Server Preparation](#server-preparation)
4. [Database Setup](#database-setup)
5. [Redis Setup](#redis-setup)
6. [Application Deployment](#application-deployment)
7. [Security Hardening](#security-hardening)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Production Checklist](#production-checklist)

---

## 🏗️ Architecture Overview

### Production Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     PRODUCTION SETUP                         │
└──────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│   Application VPS   │      Your main server running the bot
│   - Docker          │      Can be smallest tier (1GB RAM)
│   - QuickCart Bot   │
│   - Port: 8000      │
└─────────┬───────────┘
          │
          ├─────────────────┐
          │                 │
┌─────────▼─────────┐  ┌────▼──────────────┐
│  PostgreSQL VPS   │  │   Redis VPS       │
│  - Main DB        │  │   (Optional)      │
│  - Audit DB       │  │   Session Cache   │
│  - Port: 5432     │  │   Port: 6379      │
│  (2GB+ RAM)       │  │   (512MB+ RAM)    │
└───────────────────┘  └───────────────────┘
```

### Why Separate Servers?

- **Isolation**: Database issues don't affect the bot
- **Security**: Database not exposed to internet
- **Scalability**: Scale each component independently
- **Performance**: Dedicated resources for each service
- **Cost**: Can use managed services or smaller VPS tiers

---

## 📋 Prerequisites

### Required

- ✅ **Application Server** (VPS with Docker)
  - OS: Ubuntu 20.04+ or Debian 11+
  - RAM: 1GB minimum, 2GB recommended
  - Storage: 10GB minimum
  - Docker & Docker Compose installed

- ✅ **PostgreSQL Server** (VPS or managed service)
  - PostgreSQL 15 recommended
  - RAM: 2GB minimum, 4GB recommended
  - Storage: 20GB minimum (depending on data volume)
  - Can host both main and audit databases

- ✅ **Telegram Bot Token**
  - Get from [@BotFather](https://t.me/BotFather)

- ✅ **Pakasir Account**
  - API Key and Project Slug
  - From [app.pakasir.com](https://app.pakasir.com)

### Optional but Recommended

- ⭐ **Redis Server** (VPS or managed service)
  - Redis 7 recommended
  - RAM: 512MB minimum, 1GB recommended
  - For session management and caching

- ⭐ **Domain Name**
  - For webhook setup (better than polling)
  - SSL certificate via Let's Encrypt

- ⭐ **Monitoring Service**
  - Sentry.io for error tracking
  - Or self-hosted monitoring solution

---

## 🖥️ Server Preparation

### 1. Prepare Application Server

**SSH into your application server:**
```bash
ssh root@your-app-server-ip
```

**Install Docker:**
```bash
# Update package list
apt update && apt upgrade -y

# Install required packages
apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

**Create application directory:**
```bash
mkdir -p /opt/quickcart
cd /opt/quickcart
```

---

## 🗄️ Database Setup

### Option A: Self-Managed PostgreSQL on VPS

**SSH into your database server:**
```bash
ssh root@your-db-server-ip
```

#### Install PostgreSQL

```bash
# Install PostgreSQL 15
apt update
apt install -y postgresql-15 postgresql-contrib-15

# Verify installation
sudo -u postgres psql --version
```

#### Configure PostgreSQL for Remote Access

```bash
# Edit postgresql.conf
nano /etc/postgresql/15/main/postgresql.conf

# Find and change this line:
listen_addresses = '*'
# Or for more security, specify your app server IP:
# listen_addresses = 'localhost,YOUR_APP_SERVER_IP'

# Save and exit (Ctrl+X, Y, Enter)
```

```bash
# Edit pg_hba.conf to allow remote connections
nano /etc/postgresql/15/main/pg_hba.conf

# Add this line at the end (replace with your app server IP):
host    all             all             YOUR_APP_SERVER_IP/32    scram-sha-256

# For testing (NOT RECOMMENDED in production):
# host    all             all             0.0.0.0/0               scram-sha-256

# Save and exit
```

```bash
# Restart PostgreSQL
systemctl restart postgresql

# Enable on boot
systemctl enable postgresql

# Check status
systemctl status postgresql
```

#### Create Databases and Users

```bash
sudo -u postgres psql

-- Create main database user with strong password
CREATE USER quickcart WITH PASSWORD 'CHANGE_THIS_TO_STRONG_PASSWORD';

-- Create main database
CREATE DATABASE quickcart OWNER quickcart;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE quickcart TO quickcart;

-- Create audit database user
CREATE USER quickcart_audit WITH PASSWORD 'CHANGE_THIS_TO_STRONG_PASSWORD';

-- Create audit database
CREATE DATABASE quickcart_audit OWNER quickcart_audit;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE quickcart_audit TO quickcart_audit;

-- Exit psql
\q
```

#### Test Connection from Application Server

```bash
# From your application server
apt install -y postgresql-client

# Test main database connection (replace IP and password)
psql "postgresql://quickcart:YOUR_PASSWORD@YOUR_DB_SERVER_IP:5432/quickcart" -c "SELECT version();"

# Should display PostgreSQL version
```

### Option B: Managed PostgreSQL (DigitalOcean, AWS RDS, etc.)

If using managed PostgreSQL:

1. **Create two databases:**
   - `quickcart` (main operational database)
   - `quickcart_audit` (compliance/audit logs)

2. **Note connection strings:**
   - Format: `postgresql+asyncpg://user:password@host:port/database`

3. **Configure firewall:**
   - Allow connections from your application server IP
   - Use managed service's firewall/security group settings

4. **Enable SSL/TLS:**
   - Recommended for production
   - Most managed services enable this by default

---

## 💾 Redis Setup

### Option A: Self-Managed Redis on VPS

**SSH into your Redis server:**
```bash
ssh root@your-redis-server-ip
```

#### Install Redis

```bash
# Install Redis
apt update
apt install -y redis-server

# Verify installation
redis-server --version
```

#### Configure Redis for Remote Access

```bash
# Edit Redis configuration
nano /etc/redis/redis.conf

# Find and change these lines:

# 1. Bind to all interfaces (or specify app server IP)
bind 0.0.0.0
# More secure: bind YOUR_APP_SERVER_IP 127.0.0.1

# 2. Set a strong password
requirepass YOUR_STRONG_REDIS_PASSWORD

# 3. Set max memory (adjust based on your server)
maxmemory 256mb
maxmemory-policy allkeys-lru

# 4. Enable persistence (optional, for session recovery)
save 900 1
save 300 10
save 60 10000

# Save and exit
```

```bash
# Restart Redis
systemctl restart redis-server

# Enable on boot
systemctl enable redis-server

# Check status
systemctl status redis-server
```

#### Test Connection from Application Server

```bash
# From your application server
apt install -y redis-tools

# Test connection (replace IP and password)
redis-cli -h YOUR_REDIS_SERVER_IP -a YOUR_REDIS_PASSWORD ping

# Should return: PONG
```

### Option B: Managed Redis (Redis Cloud, AWS ElastiCache, etc.)

If using managed Redis:

1. **Create Redis instance**
2. **Note connection URL:**
   - Format: `redis://:password@host:port/0`
3. **Configure access:**
   - Allow connections from application server IP
4. **Enable persistence** (if needed for session recovery)

### Option C: Disable Redis (Use In-Memory Fallback)

QuickCart works without Redis for:
- Single bot instance
- Low to medium traffic
- Quick testing/staging

**To disable Redis:** Leave `REDIS_URL` empty in `.env`

⚠️ **Note:** In-memory sessions are lost on bot restart!

---

## 🚀 Application Deployment

### 1. Clone Repository

```bash
cd /opt/quickcart
git clone https://github.com/yourusername/quickcart-v1.git .

# Or download and extract if not using git
```

### 2. Create Environment Configuration

```bash
# Copy template
cp .env.template .env

# Edit configuration
nano .env
```

### 3. Configure Production Environment

**Complete `.env` file for production:**

```bash
# ==============================================================================
# REQUIRED CONFIGURATION
# ==============================================================================

# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Admin Telegram User IDs (comma-separated)
ADMIN_USER_IDS=123456789,987654321

# Pakasir Payment Gateway
PAKASIR_API_KEY=pk_live_your_live_api_key
PAKASIR_PROJECT_SLUG=your-production-store

# Security Keys (generate with: openssl rand -hex 32)
SECRET_KEY=GENERATE_RANDOM_32_BYTE_HEX_STRING
ENCRYPTION_KEY=GENERATE_RANDOM_32_BYTE_HEX_STRING

# ==============================================================================
# STORE CUSTOMIZATION
# ==============================================================================

STORE_NAME="Toko Digital Premium"
BOT_NAME="Premium Store Bot"
BOT_USERNAME="@YourPremiumBot"
DOCUMENTATION_URL="https://docs.yourstore.com"
SUPPORT_CONTACT="@YourSupport"

# ==============================================================================
# EXTERNAL DATABASE CONFIGURATION
# ==============================================================================

# Main Database (replace with your actual PostgreSQL server)
DATABASE_URL=postgresql+asyncpg://quickcart:YOUR_DB_PASSWORD@192.168.1.100:5432/quickcart

# Audit Database (can be same server or different)
AUDIT_DATABASE_URL=postgresql+asyncpg://quickcart_audit:YOUR_DB_PASSWORD@192.168.1.100:5432/quickcart_audit

# ==============================================================================
# EXTERNAL REDIS CONFIGURATION (Optional)
# ==============================================================================

# Option 1: External Redis Server
REDIS_URL=redis://:YOUR_REDIS_PASSWORD@192.168.1.200:6379/0

# Option 2: Disable Redis (use in-memory fallback)
# REDIS_URL=

# ==============================================================================
# PRODUCTION SETTINGS
# ==============================================================================

ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=WARNING

# Pakasir webhook secret (get from Pakasir dashboard)
PAKASIR_WEBHOOK_SECRET=your_webhook_secret_from_pakasir_dashboard

# Sentry error tracking (optional but recommended)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

### 4. Generate Secure Keys

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate ENCRYPTION_KEY  
openssl rand -hex 32

# Copy and paste into .env file
```

### 5. Test Database Connectivity

```bash
# Install PostgreSQL client
apt install -y postgresql-client

# Test main database
psql "postgresql://quickcart:PASSWORD@DB_IP:5432/quickcart" -c "SELECT 1;"

# Test audit database
psql "postgresql://quickcart_audit:PASSWORD@DB_IP:5432/quickcart_audit" -c "SELECT 1;"

# Both should return "1" if successful
```

### 6. Run Database Migrations

```bash
# Build the Docker image first
docker compose -f docker-compose.prod.yml build

# Run migrations
docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# You should see:
# INFO  [alembic.runtime.migration] Running upgrade -> 001_initial_schema
# INFO  [alembic.runtime.migration] Running upgrade 001 -> 002_audit_schema
```

### 7. Start Application

```bash
# Start in detached mode
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f app

# You should see:
# 🚀 Starting YourBot v1.1.0...
# ✓ Redis connected (or ✓ Using in-memory storage)
# ✓ Database status: {'main_db': 'ok', 'audit_db': 'ok'}
# ✓ Bot initialized
# ✅ YourBot is ready!
```

### 8. Verify Bot is Working

1. **Open Telegram** and find your bot
2. **Send `/start`** - should receive welcome message
3. **Test navigation** - click buttons, browse products
4. **Check database** - verify user was created:

```bash
psql "postgresql://quickcart:PASSWORD@DB_IP:5432/quickcart" -c "SELECT id, name FROM users;"
```

---

## 🔒 Security Hardening

### 1. Firewall Configuration

**On Application Server:**
```bash
# Install UFW
apt install -y ufw

# Allow SSH (IMPORTANT: Do this first!)
ufw allow 22/tcp

# Allow bot API port (only if using webhook)
ufw allow 8000/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

**On Database Server:**
```bash
# Install UFW
apt install -y ufw

# Allow SSH
ufw allow 22/tcp

# Allow PostgreSQL ONLY from application server
ufw allow from YOUR_APP_SERVER_IP to any port 5432

# Enable firewall
ufw enable

# Verify
ufw status numbered
```

**On Redis Server:**
```bash
# Install UFW
apt install -y ufw

# Allow SSH
ufw allow 22/tcp

# Allow Redis ONLY from application server
ufw allow from YOUR_APP_SERVER_IP to any port 6379

# Enable firewall
ufw enable
```

### 2. SSL/TLS for Database Connections

**Generate SSL certificate on database server:**
```bash
cd /var/lib/postgresql/15/main

# Generate self-signed certificate (or use Let's Encrypt)
sudo -u postgres openssl req -new -x509 -days 365 -nodes -text \
  -out server.crt -keyout server.key -subj "/CN=dbserver"

# Set permissions
sudo -u postgres chmod og-rwx server.key
```

**Enable SSL in PostgreSQL:**
```bash
nano /etc/postgresql/15/main/postgresql.conf

# Change:
ssl = on
ssl_cert_file = '/var/lib/postgresql/15/main/server.crt'
ssl_key_file = '/var/lib/postgresql/15/main/server.key'

# Restart PostgreSQL
systemctl restart postgresql
```

**Update connection string in `.env`:**
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require
```

### 3. Automated Backups

**Create backup script:**
```bash
nano /root/backup-quickcart.sh
```

```bash
#!/bin/bash
# QuickCart Database Backup Script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backups"
DB_HOST="YOUR_DB_SERVER_IP"
DB_USER="quickcart"
DB_PASS="YOUR_DB_PASSWORD"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup main database
PGPASSWORD=$DB_PASS pg_dump -h $DB_HOST -U $DB_USER quickcart > $BACKUP_DIR/main_$DATE.sql

# Backup audit database
PGPASSWORD=$DB_PASS pg_dump -h $DB_HOST -U quickcart_audit quickcart_audit > $BACKUP_DIR/audit_$DATE.sql

# Compress backups
gzip $BACKUP_DIR/main_$DATE.sql
gzip $BACKUP_DIR/audit_$DATE.sql

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable
chmod +x /root/backup-quickcart.sh

# Add to crontab (run daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * /root/backup-quickcart.sh >> /var/log/quickcart-backup.log 2>&1
```

### 4. Fail2Ban for SSH Protection

```bash
# Install Fail2Ban
apt install -y fail2ban

# Configure
nano /etc/fail2ban/jail.local

# Add:
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

# Restart Fail2Ban
systemctl restart fail2ban
systemctl enable fail2ban
```

---

## 📊 Monitoring & Maintenance

### Health Monitoring

**Check bot health:**
```bash
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","services":{"redis":"ok","main_database":"ok","audit_database":"ok"}}
```

**Check bot logs:**
```bash
# Real-time logs
docker compose -f docker-compose.prod.yml logs -f app

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 app

# Save to file
docker compose -f docker-compose.prod.yml logs app > logs.txt
```

### Regular Maintenance Tasks

**Daily:**
- Check bot is responding (`/start` command)
- Monitor disk space: `df -h`
- Check error logs: `docker compose logs app | grep ERROR`

**Weekly:**
- Review database size: `psql -c "SELECT pg_size_pretty(pg_database_size('quickcart'));"`
- Verify backups are created
- Check Redis memory usage: `redis-cli INFO memory`

**Monthly:**
- Update system packages: `apt update && apt upgrade`
- Review and analyze audit logs
- Check for bot updates: `git pull`
- Review security advisories

### Updating the Bot

```bash
cd /opt/quickcart

# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build

# Run migrations if any
docker compose -f docker-compose.prod.yml exec app alembic upgrade head

# Verify
docker compose -f docker-compose.prod.yml logs --tail=50 app
```

---

## 🔧 Troubleshooting

### Bot Not Starting

**Check logs:**
```bash
docker compose -f docker-compose.prod.yml logs app
```

**Common issues:**

1. **Database connection failed**
   ```
   Solution: Verify DATABASE_URL is correct
   Test: psql "YOUR_DATABASE_URL" -c "SELECT 1;"
   ```

2. **Redis connection timeout**
   ```
   Solution: Check REDIS_URL or disable Redis
   Test: redis-cli -h HOST -a PASSWORD ping
   ```

3. **Invalid bot token**
   ```
   Solution: Verify TELEGRAM_BOT_TOKEN
   Test: curl https://api.telegram.org/bot${TOKEN}/getMe
   ```

### Bot Responds Slowly

**Check resource usage:**
```bash
# CPU and memory
docker stats

# Database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory
redis-cli INFO memory
```

**Optimize:**
- Increase DB pool size in `.env`
- Enable Redis if using in-memory
- Upgrade server resources

### Database Migration Errors

```bash
# Check current version
docker compose -f docker-compose.prod.yml exec app alembic current

# Show migration history
docker compose -f docker-compose.prod.yml exec app alembic history

# Downgrade one version
docker compose -f docker-compose.prod.yml exec app alembic downgrade -1

# Upgrade to latest
docker compose -f docker-compose.prod.yml exec app alembic upgrade head
```

---

## ✅ Production Checklist

### Pre-Deployment

- [ ] Application server prepared with Docker
- [ ] PostgreSQL server installed and configured
- [ ] Redis server installed and configured (or intentionally disabled)
- [ ] Firewall rules configured on all servers
- [ ] SSL/TLS enabled for database connections
- [ ] Backups configured and tested
- [ ] `.env` file created with production values

### Configuration

- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=False`
- [ ] `TELEGRAM_BOT_TOKEN` set correctly
- [ ] `ADMIN_USER_IDS` contains correct IDs
- [ ] `SECRET_KEY` and `ENCRYPTION_KEY` are random (32+ chars)
- [ ] `DATABASE_URL` points to production PostgreSQL
- [ ] `AUDIT_DATABASE_URL` points to audit database
- [ ] `REDIS_URL` configured or intentionally disabled
- [ ] `PAKASIR_API_KEY` and `PAKASIR_PROJECT_SLUG` set
- [ ] `PAKASIR_WEBHOOK_SECRET` configured
- [ ] `STORE_NAME` customized to your brand
- [ ] `BOT_NAME` customized
- [ ] `DOCUMENTATION_URL` updated
- [ ] `SUPPORT_CONTACT` set

### Security

- [ ] Strong database passwords (20+ characters)
- [ ] Firewall rules allow only necessary traffic
- [ ] SSH key authentication enabled (password auth disabled)
- [ ] Fail2Ban installed and configured
- [ ] Regular backups scheduled (cron job)
- [ ] Backup restoration tested
- [ ] HTTPS/SSL enabled for webhook (if using webhooks)

### Testing

- [ ] Database connections tested from app server
- [ ] Redis connection tested (if enabled)
- [ ] Bot responds to `/start` command
- [ ] User registration creates database record
- [ ] Product browsing works
- [ ] Navigation is flexible (can switch flows)
- [ ] Admin commands work for admin users
- [ ] Payments can be created (test mode)
- [ ] Logs are clean (no critical errors)

### Monitoring

- [ ] Sentry or error tracking configured
- [ ] Log monitoring set up
- [ ] Disk space alerts configured
- [ ] Uptime monitoring configured
- [ ] Backup success notifications set up

### Documentation

- [ ] Production credentials documented (securely)
- [ ] Server access details documented
- [ ] Emergency contact list created
- [ ] Runbook created for common issues

---

## 🎓 Best Practices

1. **Use different passwords** for each database and service
2. **Never commit `.env`** to version control
3. **Test backups regularly** - verify you can restore
4. **Monitor logs daily** - catch issues early
5. **Keep software updated** - security patches are critical
6. **Use private networks** between servers when possible
7. **Enable SSL/TLS** for all connections
8. **Document everything** - procedures, credentials (securely), changes
9. **Test changes in staging** before production
10. **Have a rollback plan** for updates

---

## 📞 Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review logs: `docker compose logs app`
3. Check documentation: `docs/` directory
4. Check GitHub issues (if applicable)

---

**Deployment Status:** 🟢 Ready for Production  
**Version:** 1.1.0  
**Last Updated:** 2025-01-15

---

*This guide is maintained as part of the QuickCart project. Please keep it updated when making changes to deployment procedures.*