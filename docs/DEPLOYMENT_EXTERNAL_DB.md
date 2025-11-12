# Deployment Guide: External PostgreSQL & Redis Servers

This guide covers deploying QuickCart with PostgreSQL and Redis on **separate VPS servers**.

**Note:** QuickCart uses ONE `docker-compose.yml` for all scenarios. Just change the database URLs in `.env` to use external servers!

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [PostgreSQL VPS Setup](#postgresql-vps-setup)
- [Redis VPS Setup](#redis-vps-setup)
- [Application Server Setup](#application-server-setup)
- [Network Configuration](#network-configuration)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Recommended Setup

```
┌─────────────────────┐
│   Application VPS   │
│   (QuickCart App)   │
│   - FastAPI         │
│   - Telegram Bot    │
│   Port: 8000        │
└──────────┬──────────┘
           │
           ├─────────────────┐
           │                 │
           ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│ PostgreSQL VPS   │  │   Redis VPS      │
│ - Main DB        │  │   (Optional)     │
│ - Audit DB       │  │   - Caching      │
│ Port: 5432       │  │   Port: 6379     │
└──────────────────┘  └──────────────────┘
```

### Why Separate Servers?

✅ **Better Performance** - Dedicated resources for each service  
✅ **Scalability** - Scale database and app independently  
✅ **Isolation** - Issues in one server don't affect others  
✅ **Security** - Better network isolation and firewall rules  
✅ **Backup** - Easier to backup database separately

---

## Prerequisites

### Required VPS Servers

1. **Application Server** (minimum specs):
   - 1 vCPU, 1GB RAM
   - Ubuntu 22.04 LTS or newer
   - Docker & Docker Compose installed

2. **PostgreSQL Server** (minimum specs):
   - 1 vCPU, 2GB RAM
   - Ubuntu 22.04 LTS or newer
   - SSD storage recommended

3. **Redis Server** (optional, minimum specs):
   - 1 vCPU, 512MB RAM
   - Ubuntu 22.04 LTS or newer

### Network Requirements

- Servers can communicate (same datacenter/region recommended)
- Low latency between servers (<10ms ideal)
- Private network support (highly recommended)

---

## PostgreSQL VPS Setup

### Step 1: Install PostgreSQL

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL 15
sudo apt install -y postgresql-15 postgresql-contrib-15

# Start and enable service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
psql --version
```

### Step 2: Configure PostgreSQL for Remote Access

```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/15/main/postgresql.conf
```

Update these settings:

```conf
# Listen on all interfaces (or specific IP)
listen_addresses = '*'

# Connection limits (adjust based on your needs)
max_connections = 100

# Memory settings (adjust based on your RAM)
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
```

### Step 3: Configure Client Authentication

```bash
# Edit pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

Add these lines (replace with your app server IP):

```conf
# Allow app server to connect
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    quickcart       quickcart       YOUR_APP_SERVER_IP/32   md5
host    quickcart_audit quickcart       YOUR_APP_SERVER_IP/32   md5

# For private network (recommended)
host    all             all             10.0.0.0/8              md5
```

### Step 4: Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
```

```sql
-- Create user with strong password
CREATE USER quickcart WITH PASSWORD 'your_very_secure_password_here';

-- Create main database
CREATE DATABASE quickcart OWNER quickcart;

-- Create audit database
CREATE DATABASE quickcart_audit OWNER quickcart;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE quickcart TO quickcart;
GRANT ALL PRIVILEGES ON DATABASE quickcart_audit TO quickcart;

-- Enable extensions
\c quickcart
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c quickcart_audit
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify
\l
\q
```

### Step 5: Configure Firewall

```bash
# Allow PostgreSQL port from app server only
sudo ufw allow from YOUR_APP_SERVER_IP to any port 5432

# Enable firewall
sudo ufw enable

# Verify rules
sudo ufw status
```

### Step 6: Restart PostgreSQL

```bash
sudo systemctl restart postgresql

# Check status
sudo systemctl status postgresql

# Test connection from app server (run this on app server)
psql -h POSTGRES_SERVER_IP -U quickcart -d quickcart
```

---

## Redis VPS Setup

### Step 1: Install Redis

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Redis
sudo apt install -y redis-server

# Start and enable service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify installation
redis-cli --version
```

### Step 2: Configure Redis for Remote Access

```bash
# Edit Redis configuration
sudo nano /etc/redis/redis.conf
```

Update these settings:

```conf
# Bind to all interfaces (or specific IP)
bind 0.0.0.0

# Set strong password
requirepass your_very_secure_redis_password_here

# Disable protected mode (since we're using password)
protected-mode no

# Set max memory (adjust based on your RAM)
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence settings (optional)
save 900 1
save 300 10
save 60 10000
```

### Step 3: Configure Firewall

```bash
# Allow Redis port from app server only
sudo ufw allow from YOUR_APP_SERVER_IP to any port 6379

# Enable firewall
sudo ufw enable

# Verify rules
sudo ufw status
```

### Step 4: Restart Redis

```bash
sudo systemctl restart redis-server

# Check status
sudo systemctl status redis-server

# Test connection from app server (run this on app server)
redis-cli -h REDIS_SERVER_IP -a your_password ping
```

---

## Application Server Setup

### Step 1: Clone Repository

```bash
# Install git
sudo apt update
sudo apt install -y git

# Clone repository
cd /opt
sudo git clone https://github.com/moccalatte/quickcart-v1.git
cd quickcart-v1
```

### Step 2: Configure Environment Variables

```bash
# Copy environment template
cp .env.template .env

# Edit configuration
nano .env
```

Update these critical values in `.env`:

```bash
# Database URLs - REPLACE WITH YOUR POSTGRESQL SERVER
DATABASE_URL=postgresql+asyncpg://quickcart:your_secure_password@POSTGRES_SERVER_IP:5432/quickcart
AUDIT_DATABASE_URL=postgresql+asyncpg://quickcart:your_secure_password@POSTGRES_SERVER_IP:5432/quickcart_audit

# Redis URL - REPLACE WITH YOUR REDIS SERVER (or leave empty if not using)
REDIS_URL=redis://:your_redis_password@REDIS_SERVER_IP:6379/0

# Telegram & Payment settings
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_USER_IDS=your_telegram_user_id
PAKASIR_API_KEY=your_pakasir_key
PAKASIR_PROJECT_SLUG=your_project_slug

# Security keys (generate unique values)
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

**💡 That's it!** The same `docker-compose.yml` works for both local and external databases. The URLs in `.env` control everything.

### Step 3: Test Database Connection

```bash
# Install PostgreSQL client
sudo apt install -y postgresql-client

# Test connection to PostgreSQL server
psql -h POSTGRES_SERVER_IP -U quickcart -d quickcart

# If successful, you'll see PostgreSQL prompt
# Type \q to exit
```

### Step 4: Run Database Migrations

```bash
# Install Python and dependencies
sudo apt install -y python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Verify tables created
psql -h POSTGRES_SERVER_IP -U quickcart -d quickcart -c "\dt"
psql -h POSTGRES_SERVER_IP -U quickcart -d quickcart_audit -c "\dt"
```

### Step 5: Deploy with Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install -y docker-compose
### Step 5: Deploy Application

Start the application with the standard docker-compose.yml:

```bash
# Build and start application
docker compose up -d

# Check logs
docker compose logs -f app
```

**Note:** The local `db` and `redis` containers will start but won't be used (your app connects to external servers via URLs in `.env`). 

Optional - stop local database containers if you don't need them:

```bash
docker compose stop db redis
```

---

## Network Configuration

### Option 1: Public Internet (Basic)

```
App Server (Public IP) → PostgreSQL Server (Public IP)
                      ↓
                      Redis Server (Public IP)
```

**Pros:** Simple setup  
**Cons:** Less secure, requires strong passwords and firewall rules

### Option 2: Private Network (Recommended)

```
App Server (Private: 10.0.1.10) → PostgreSQL (Private: 10.0.1.20)
                                ↓
                                Redis (Private: 10.0.1.30)
```

**Pros:** More secure, better performance, lower latency  
**Cons:** Requires VPS provider support for private networking

**Setup for Private Network:**

```bash
# On each server, configure private network interface
# Example for DigitalOcean/Hetzner:

# Edit netplan configuration
sudo nano /etc/netplan/50-cloud-init.yaml

# Add private network interface
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
    eth1:  # Private interface
      addresses:
        - 10.0.1.10/24  # Replace with your private IP

# Apply configuration
sudo netplan apply

# Update .env with private IPs
DATABASE_URL=postgresql+asyncpg://quickcart:pass@10.0.1.20:5432/quickcart
REDIS_URL=redis://:pass@10.0.1.30:6379/0
```

### Option 3: VPN Tunnel (Most Secure)

Use WireGuard or OpenVPN to create encrypted tunnel between servers.

```bash
# Install WireGuard (Ubuntu)
sudo apt install -y wireguard

# Configure WireGuard (details depend on your setup)
# Refer to WireGuard documentation
```

---

## Security Best Practices

### 1. Database Security

✅ **Use strong passwords** (minimum 32 characters, random)
```bash
# Generate strong password
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

✅ **Restrict IP access** (only app server can connect)
```conf
# pg_hba.conf
host    quickcart    quickcart    10.0.1.10/32    md5
```

✅ **Enable SSL/TLS** (for production)
```conf
# postgresql.conf
ssl = on
ssl_cert_file = '/path/to/server.crt'
ssl_key_file = '/path/to/server.key'
```

✅ **Regular backups**
```bash
# Automated backup script
#!/bin/bash
pg_dump -h localhost -U quickcart quickcart | gzip > /backup/quickcart_$(date +%F).sql.gz
pg_dump -h localhost -U quickcart quickcart_audit | gzip > /backup/quickcart_audit_$(date +%F).sql.gz
```

### 2. Redis Security

✅ **Use strong password**
✅ **Bind to private IP only**
✅ **Rename dangerous commands**

```conf
# redis.conf
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG "CONFIG_asjdh123kjh"
```

### 3. Firewall Rules

```bash
# PostgreSQL Server - Only allow from app server
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.0.1.10 to any port 5432
sudo ufw allow 22/tcp  # SSH
sudo ufw enable

# Redis Server - Only allow from app server
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.0.1.10 to any port 6379
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

### 4. Monitoring

Set up monitoring for:
- Database connections and performance
- Redis memory usage
- Network latency between servers
- Disk space on database server

---

## Troubleshooting

### Cannot Connect to PostgreSQL

```bash
# 1. Check PostgreSQL is running
sudo systemctl status postgresql

# 2. Check PostgreSQL is listening on correct interface
sudo netstat -tulpn | grep 5432

# 3. Test from app server
telnet POSTGRES_SERVER_IP 5432

# 4. Check firewall
sudo ufw status

# 5. Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# 6. Verify pg_hba.conf allows your app server IP
sudo cat /etc/postgresql/15/main/pg_hba.conf | grep quickcart
```

### Cannot Connect to Redis

```bash
# 1. Check Redis is running
sudo systemctl status redis-server

# 2. Check Redis is listening on correct interface
sudo netstat -tulpn | grep 6379

# 3. Test from app server
redis-cli -h REDIS_SERVER_IP -a your_password ping

# 4. Check firewall
sudo ufw status

# 5. Check Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

### Migration Fails

```bash
# 1. Check database exists
psql -h POSTGRES_SERVER_IP -U quickcart -l

# 2. Check user permissions
psql -h POSTGRES_SERVER_IP -U quickcart -d quickcart -c "\du"

# 3. Run migrations with verbose output
alembic upgrade head --verbose

# 4. Check alembic version
psql -h POSTGRES_SERVER_IP -U quickcart -d quickcart -c "SELECT * FROM alembic_version;"
```

### Slow Performance

```bash
# 1. Check network latency
ping -c 10 POSTGRES_SERVER_IP

# 2. Check database connections
psql -h POSTGRES_SERVER_IP -U quickcart -d quickcart -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Monitor queries
psql -h POSTGRES_SERVER_IP -U quickcart -d quickcart -c "SELECT pid, query, state FROM pg_stat_activity WHERE state = 'active';"

# 4. Check Redis latency
redis-cli -h REDIS_SERVER_IP -a your_password --latency
```

---

## Maintenance

### Regular Tasks

**Daily:**
- Monitor application logs
- Check disk space on database server

**Weekly:**
- Review database performance metrics
- Check for slow queries
- Verify backups are working

**Monthly:**
- Update system packages
- Review and rotate logs
- Test backup restoration
- Review security settings

### Backup Strategy

```bash
# Automated daily backup script
#!/bin/bash
# /opt/scripts/backup-databases.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/postgresql"

# Backup main database
pg_dump -h localhost -U quickcart quickcart | \
  gzip > "$BACKUP_DIR/quickcart_$DATE.sql.gz"

# Backup audit database
pg_dump -h localhost -U quickcart quickcart_audit | \
  gzip > "$BACKUP_DIR/quickcart_audit_$DATE.sql.gz"

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

# Upload to cloud storage (optional)
# rclone copy "$BACKUP_DIR" remote:backups/
```

Add to crontab:
```bash
# Run backup daily at 2 AM
0 2 * * * /opt/scripts/backup-databases.sh
```

---

## Quick Reference

### Connection Strings

```bash
# PostgreSQL (asyncpg for Python)
postgresql+asyncpg://user:pass@host:5432/database

# PostgreSQL (psycopg2 for sync)
postgresql://user:pass@host:5432/database

# Redis
redis://:password@host:6379/0
```

### Common Commands

```bash
# Check PostgreSQL connection
psql -h HOST -U quickcart -d quickcart

# Check Redis connection
redis-cli -h HOST -a PASSWORD ping

# Run migrations
alembic upgrade head

# Check application logs
docker-compose logs -f app

# Restart application
docker-compose restart app
```

---

## Additional Resources

- [PostgreSQL Official Documentation](https://www.postgresql.org/docs/)
- [Redis Official Documentation](https://redis.io/documentation)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

---

**Last Updated:** January 2025  
**Maintained By:** QuickCart Development Team