# QuickCart Deployment Quick Reference

**TL;DR:** ONE `docker-compose.yml` for everything! Just change URLs in `.env` to use external database.

---

## 1. Deployment Scenarios

### Scenario 1: Everything on One Server (Easiest - Recommended for Beginners)
```bash
# Setup
cp .env.template .env
nano .env  # Fill in bot token, admin ID, Pakasir credentials

# Start everything
docker compose up -d
```
✅ PostgreSQL, Redis, and Bot all run in Docker containers  
✅ No external servers needed  
✅ Perfect for testing and small-scale production

### Scenario 2: Using External Database (Advanced)
```bash
# Setup
cp .env.template .env
nano .env

# In .env, change these lines to your external server:
# DATABASE_URL=postgresql+asyncpg://user:pass@YOUR_DB_IP:5432/quickcart
# REDIS_URL=redis://:pass@YOUR_REDIS_IP:6379/0  (or leave empty)
# ENVIRONMENT=production
# DEBUG=false

# Start with SAME docker-compose.yml
docker compose up -d
```
✅ App connects to your external PostgreSQL/Redis  
✅ Local db container runs but isn't used (can stop it with: docker compose stop db)  
✅ Same commands, same file - just different .env values
✅ App server hanya jalankan aplikasi

**📖 Panduan lengkap:** [docs/DEPLOYMENT_EXTERNAL_DB.md](docs/DEPLOYMENT_EXTERNAL_DB.md)

---

## 📝 Konfigurasi Database URL

### Format Connection String

```bash
# PostgreSQL (asyncpg - untuk async Python)
postgresql+asyncpg://username:password@hostname:port/database

# Redis
redis://:password@hostname:port/database_number
```

### Contoh: Docker Compose (Internal)

```bash
# PostgreSQL menggunakan service name 'db'
DATABASE_URL=postgresql+asyncpg://quickcart:quickcart123@db:5432/quickcart
REDIS_URL=redis://:redis123@redis:6379/0
```

### Contoh: VPS Terpisah (IP Address)

```bash
# PostgreSQL di VPS dengan IP 192.168.1.100
DATABASE_URL=postgresql+asyncpg://quickcart:securepass@192.168.1.100:5432/quickcart
AUDIT_DATABASE_URL=postgresql+asyncpg://quickcart:securepass@192.168.1.100:5432/quickcart_audit

# Redis di VPS dengan IP 192.168.1.101
REDIS_URL=redis://:redispass@192.168.1.101:6379/0
```

### Contoh: VPS Terpisah (Hostname/Domain)

```bash
# PostgreSQL dengan hostname
DATABASE_URL=postgresql+asyncpg://quickcart:securepass@db.yourserver.com:5432/quickcart
AUDIT_DATABASE_URL=postgresql+asyncpg://quickcart:securepass@db.yourserver.com:5432/quickcart_audit

# Redis dengan hostname
REDIS_URL=redis://:redispass@redis.yourserver.com:6379/0
```

### Tanpa Redis (Opsional)

```bash
# Kosongkan atau hapus REDIS_URL
REDIS_URL=

# Atau set ke None
REDIS_URL=None
```

---

## 🚀 Step-by-Step: Deploy dengan Database Eksternal

### 1. Setup PostgreSQL di VPS Database Server

```bash
# Di VPS PostgreSQL
sudo apt update && sudo apt install -y postgresql-15

# Edit config untuk allow remote connection
sudo nano /etc/postgresql/15/main/postgresql.conf
# Set: listen_addresses = '*'

sudo nano /etc/postgresql/15/main/pg_hba.conf
# Tambah: host quickcart quickcart APP_SERVER_IP/32 md5

# Restart PostgreSQL
sudo systemctl restart postgresql

# Buat database dan user
sudo -u postgres psql
CREATE USER quickcart WITH PASSWORD 'your_secure_password';
CREATE DATABASE quickcart OWNER quickcart;
CREATE DATABASE quickcart_audit OWNER quickcart;
\q

# Setup firewall
sudo ufw allow from APP_SERVER_IP to any port 5432
```

### 2. Setup Redis di VPS Redis Server (Opsional)

```bash
# Di VPS Redis
sudo apt update && sudo apt install -y redis-server

# Edit config
sudo nano /etc/redis/redis.conf
# Set: bind 0.0.0.0
# Set: requirepass your_redis_password

# Restart Redis
sudo systemctl restart redis-server

# Setup firewall
sudo ufw allow from APP_SERVER_IP to any port 6379
```

### 3. Setup Aplikasi di VPS App Server

```bash
# Clone repository
git clone <your-repo-url>
cd quickcart-v1

# Copy environment template
cp .env.template .env

# Edit .env - set ENVIRONMENT=production dan ganti dengan IP/hostname server Anda
nano .env

# WAJIB ISI:
DATABASE_URL=postgresql+asyncpg://quickcart:password@POSTGRES_IP:5432/quickcart
AUDIT_DATABASE_URL=postgresql+asyncpg://quickcart:password@POSTGRES_IP:5432/quickcart_audit
REDIS_URL=redis://:password@REDIS_IP:6379/0  # atau kosongkan jika tidak pakai Redis

TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_USER_IDS=your_telegram_id
PAKASIR_API_KEY=your_api_key
PAKASIR_PROJECT_SLUG=your_slug
SECRET_KEY=generate_random_32_chars
ENCRYPTION_KEY=generate_random_32_chars

# Test koneksi database
psql -h POSTGRES_IP -U quickcart -d quickcart

# Install Python dan jalankan migrasi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Deploy dengan Docker
docker compose up -d

# Cek logs
docker compose logs -f app
```

---

## 🔍 Troubleshooting Cepat

### Error: Cannot connect to PostgreSQL

```bash
# 1. Cek PostgreSQL running
sudo systemctl status postgresql

# 2. Cek listen address
sudo netstat -tulpn | grep 5432

# 3. Test dari app server
telnet POSTGRES_IP 5432
# atau
psql -h POSTGRES_IP -U quickcart -d quickcart

# 4. Cek firewall
sudo ufw status

# 5. Cek pg_hba.conf
sudo cat /etc/postgresql/15/main/pg_hba.conf | grep quickcart
```

### Error: Cannot connect to Redis

```bash
# 1. Cek Redis running
sudo systemctl status redis-server

# 2. Test dari app server
redis-cli -h REDIS_IP -a password ping

# 3. Cek Redis config
sudo cat /etc/redis/redis.conf | grep bind
sudo cat /etc/redis/redis.conf | grep requirepass

# 4. Cek firewall
sudo ufw status
```

### Migration Error

```bash
# 1. Pastikan database exists
psql -h POSTGRES_IP -U quickcart -l

# 2. Cek alembic version
psql -h POSTGRES_IP -U quickcart -d quickcart -c "SELECT * FROM alembic_version;"

# 3. Run migration dengan verbose
alembic upgrade head --verbose

# 4. Jika stuck, reset
alembic downgrade base
alembic upgrade head
```

---

## 📊 Network Latency Check

```bash
# Cek latency dari app server ke database server
ping -c 10 POSTGRES_IP

# Ideal: < 10ms (same datacenter)
# Acceptable: < 50ms (same region)
# Slow: > 100ms (consider using private network)
```

---

## 🔐 Security Checklist

- [ ] Gunakan strong password (32+ chars)
- [ ] Restrict firewall (hanya allow IP app server)
- [ ] Gunakan private network jika tersedia
- [ ] Enable SSL/TLS untuk PostgreSQL di production
- [ ] Ganti default passwords
- [ ] Setup automated backups
- [ ] Monitor disk space database server
- [ ] Setup log rotation

---

## 📦 Backup Database (Jalankan di PostgreSQL Server)

```bash
# Manual backup
pg_dump -U quickcart quickcart | gzip > quickcart_$(date +%F).sql.gz
pg_dump -U quickcart quickcart_audit | gzip > quickcart_audit_$(date +%F).sql.gz

# Restore
gunzip < quickcart_2025-01-12.sql.gz | psql -U quickcart quickcart

# Automated backup (crontab)
0 2 * * * pg_dump -U quickcart quickcart | gzip > /backup/quickcart_$(date +\%F).sql.gz
```

---

## 🎯 Quick Commands Reference

```bash
# Start application
docker compose up -d

# Stop application
docker compose down

# View logs
docker compose logs -f app

# Restart application
docker compose restart app

# Run migrations
docker compose exec app alembic upgrade head

# View database
docker compose exec app alembic current
# Check application health
curl http://localhost:8000/health

# Connect to PostgreSQL
psql -h POSTGRES_IP -U quickcart -d quickcart

# Connect to Redis
redis-cli -h REDIS_IP -a password

# Check database size
psql -h POSTGRES_IP -U quickcart -d quickcart -c "SELECT pg_size_pretty(pg_database_size('quickcart'));"
```

---

## 📚 Full Documentation

- **Development Setup:** `README.md`
- **External Database Guide:** `docs/DEPLOYMENT_EXTERNAL_DB.md`
- **Environment Variables:** `.env.template`
- **Testing Guide:** `docs/TESTING.md`

---

**Last Updated:** January 2025  
**For Support:** Check GitHub Issues or Documentation