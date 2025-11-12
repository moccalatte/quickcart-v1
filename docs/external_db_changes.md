# Perubahan untuk Support External PostgreSQL & Redis

## Ringkasan

QuickCart sekarang mendukung deployment dengan PostgreSQL dan Redis di **VPS terpisah**. Semua konfigurasi sudah disesuaikan untuk produksi.

---

## Files yang Diubah/Dibuat

### 1. Core Configuration
- ✅ **`src/core/config.py`**
  - Default `database_url` dan `redis_url` diganti dari Docker hostname (`db:5432`, `redis:6379`) ke `localhost` (lebih fleksibel)
  - Ditambahkan description untuk setiap field
  - `redis_url` sekarang Optional, bisa `None`

### 2. Environment Templates
- ✅ **`.env.template`** (UPDATED)
  - Template terpadu untuk development dan production
  - Contoh lengkap dengan IP/hostname VPS untuk production
  - Instruksi deployment step-by-step
  - Security checklist
  - Support ENVIRONMENT=development atau ENVIRONMENT=production

### 3. Docker Compose
- ✅ **Simplified `docker-compose.yml`** (UPDATED)
  - ONE docker-compose file for all scenarios
  - Just change DATABASE_URL in .env to use external database
  - Local db/redis containers run but aren't used when external URLs are configured
  - Can optionally stop local containers: `docker compose stop db redis`

### 4. Documentation
- ✅ **`docs/DEPLOYMENT_EXTERNAL_DB.md`** (BARU)
  - Panduan lengkap 700+ baris
  - Setup PostgreSQL di VPS terpisah
  - Setup Redis di VPS terpisah
  - Network configuration (private network, VPN)
  - Security best practices
  - Troubleshooting guide
  - Backup strategy
  - Maintenance checklist

- ✅ **`DEPLOYMENT_QUICKREF.md`** (BARU)
  - Quick reference card
  - Contoh connection strings
  - Step-by-step deployment
  - Troubleshooting cepat
  - Command reference

- ✅ **`README.md`** (UPDATED)
  - Added section untuk production deployment
  - Diagram arsitektur
  - Link ke dokumentasi lengkap

---

## Cara Menggunakan

### Development (Semua di Docker)
```bash
cp .env.template .env
# Edit .env: set ENVIRONMENT=development
docker-compose up -d
```

### Production (Database di VPS Terpisah)
```bash
# 1. Setup PostgreSQL di VPS database server
# 2. Setup Redis di VPS redis server (optional)
# 3. Di VPS aplikasi:
cp .env.template .env
# Edit .env: set ENVIRONMENT=production, update DATABASE_URL to external server
docker compose up -d
# Optional: stop local db if not needed
docker compose stop db redis
```

---

## Contoh Konfigurasi

### Development (Local Docker)
```bash
# In .env:
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://quickcart:pass@db:5432/quickcart
REDIS_URL=redis://:pass@redis:6379/0
```

### Production (External Database)
```bash
# In .env:
ENVIRONMENT=production
DEBUG=false

# PostgreSQL di VPS 192.168.1.100
DATABASE_URL=postgresql+asyncpg://quickcart:securepass@192.168.1.100:5432/quickcart

# Redis di VPS 192.168.1.101 (optional)
REDIS_URL=redis://:securepass@192.168.1.101:6379/0
```

**💡 Key Point:** Same `docker compose up -d` command for both! The `.env` values control everything.

# Atau dengan hostname
DATABASE_URL=postgresql+asyncpg://quickcart:pass@db.yourserver.com:5432/quickcart
REDIS_URL=redis://:pass@redis.yourserver.com:6379/0
```

---

## Keuntungan Setup Ini

1. **Skalabilitas** - Scale database dan aplikasi secara terpisah
2. **Performance** - Dedicated resources untuk setiap service
3. **Reliability** - Isolasi - masalah di satu server tidak affect yang lain
4. **Security** - Better network isolation dan firewall rules
5. **Backup** - Lebih mudah backup database secara terpisah
6. **Maintenance** - Update database tanpa restart aplikasi

---

## Testing Checklist

- [ ] Connection string format benar
- [ ] Firewall allow koneksi dari app server
- [ ] PostgreSQL listen di interface yang benar
- [ ] Redis requirepass diset
- [ ] pg_hba.conf allow app server IP
- [ ] Migrations berhasil dijalankan
- [ ] Application dapat connect ke database
- [ ] Healthcheck endpoint respond
- [ ] Logs tidak ada error connection

---

## Support & Documentation
## 📚 Documentation Links

- **Quick Reference:** `docs/deployment_quickref.md`
- **Full Guide:** `docs/DEPLOYMENT_EXTERNAL_DB.md`
- **Environment Template:** `.env.template`
- **Main README:** `README.md`
- **Docker Compose:** `docker-compose.yml` (ONE file for all scenarios!)

---

Semua sudah siap untuk deployment production dengan PostgreSQL dan Redis di VPS terpisah! 🚀
