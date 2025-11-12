# QuickCart Dependencies Guide 📦

**Last Updated:** January 12, 2025  
**Python Version:** 3.11+  
**Status:** ✅ All dependencies compatible and tested

---

## 🎯 Critical Dependency Notice

### python-telegram-bot 22.5 Requirements

**IMPORTANT:** `python-telegram-bot==22.5` requires `httpx>=0.27,<0.29`

```
python-telegram-bot==22.5  → requires → httpx>=0.27,<0.29
```

**Do NOT use `httpx==0.25.x`** - This will cause dependency conflicts!

---

## 📋 Production Dependencies

All versions below are **tested and compatible** with each other:

### Web Framework
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
```

### Database
```
asyncpg==0.29.0              # PostgreSQL async driver
psycopg2-binary==2.9.9       # PostgreSQL sync driver (for Alembic)
alembic==1.13.1              # Database migrations
SQLAlchemy==2.0.25           # ORM
```

### Redis (Optional)
```
redis[hiredis]==5.0.1        # Redis client with C parser
```

### Telegram Bot
```
python-telegram-bot==22.5    # Telegram Bot API wrapper
httpx==0.27.2                # HTTP client (MUST be >=0.27,<0.29)
```

**Why httpx==0.27.2?**
- python-telegram-bot 22.5 depends on httpx>=0.27,<0.29
- We use httpx for Pakasir API client as well
- Version 0.27.2 is stable and compatible with both

### Data Validation
```
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.1.0.post1
```

### Security
```
python-dotenv==1.0.0         # Environment variables
cryptography==42.0.0         # Encryption utilities
```

### Utilities
```
python-dateutil==2.8.2       # Date/time utilities
qrcode[pil]==7.4.2          # QR code generation
Pillow==10.2.0              # Image processing
tenacity==8.2.3             # Retry logic
```

---

## 🔄 Dependency Compatibility Matrix

| Package | Version | Compatible With | Notes |
|---------|---------|-----------------|-------|
| python-telegram-bot | 22.5 | httpx 0.27-0.28 | **Requires httpx>=0.27** |
| httpx | 0.27.2 | python-telegram-bot 22.5 | ✅ Perfect match |
| fastapi | 0.109.0 | pydantic 2.5.x | Latest stable |
| SQLAlchemy | 2.0.25 | asyncpg 0.29.0 | Async ORM |
| alembic | 1.13.1 | SQLAlchemy 2.0.x | Migration tool |

---

## 🚨 Common Dependency Conflicts

### ❌ Conflict #1: httpx Version
```bash
ERROR: python-telegram-bot 22.5 depends on httpx<0.29 and >=0.27
```

**Solution:**
```bash
# Use httpx==0.27.2 (NOT 0.25.x)
pip install httpx==0.27.2
```

### ❌ Conflict #2: Pydantic v1 vs v2
```bash
ERROR: pydantic-settings requires pydantic>=2.0
```

**Solution:**
```bash
# Use pydantic 2.x (NOT 1.x)
pip install pydantic==2.5.3
```

### ❌ Conflict #3: SQLAlchemy async
```bash
ImportError: cannot import name 'AsyncSession'
```

**Solution:**
```bash
# Use SQLAlchemy 2.x with asyncpg
pip install sqlalchemy==2.0.25 asyncpg==0.29.0
```

---

## 📦 Installation Methods

### Method 1: Direct Install (Recommended)
```bash
pip install -r requirements.txt
```

### Method 2: Docker (Production)
```bash
docker compose build
docker compose up -d
```

### Method 3: Manual Install
```bash
# Install in specific order to avoid conflicts
pip install pydantic==2.5.3
pip install httpx==0.27.2
pip install python-telegram-bot==22.5
pip install -r requirements.txt
```

---

## 🧪 Testing Dependencies

Testing dependencies are **NOT** in requirements.txt to keep production lean.

Install separately:
```bash
pip install pytest==7.4.4 pytest-asyncio==0.23.3 pytest-cov==4.1.0
```

Or create `requirements-dev.txt`:
```
-r requirements.txt
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
```

Then:
```bash
pip install -r requirements-dev.txt
```

---

## 🔍 Verifying Installation

### Check Installed Versions
```bash
pip list | grep -E "(telegram|httpx|fastapi|sqlalchemy)"
```

Expected output:
```
fastapi                 0.109.0
httpx                   0.27.2
python-telegram-bot     22.5
SQLAlchemy              2.0.25
```

### Run Import Test
```bash
python test_imports.py
```

Should show:
```
✅ All imports successful!
QuickCart code structure is valid! 🚀
```

---

## 🐳 Docker Dependencies

Dependencies are installed automatically in Docker:

```dockerfile
# From Dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

Rebuild after dependency changes:
```bash
docker compose build --no-cache
```

---

## 🔧 Troubleshooting

### Problem: pip install fails with dependency conflict
```bash
ERROR: ResolutionImpossible
```

**Solution:**
1. Clear pip cache: `pip cache purge`
2. Upgrade pip: `pip install --upgrade pip`
3. Install in fresh venv:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

### Problem: Import errors after install
```bash
ModuleNotFoundError: No module named 'telegram'
```

**Solution:**
1. Verify installation: `pip show python-telegram-bot`
2. Check Python version: `python --version` (must be 3.11+)
3. Reinstall: `pip uninstall python-telegram-bot && pip install python-telegram-bot==22.5`

### Problem: httpx version conflict
```bash
ERROR: httpx 0.25.2 is not compatible with python-telegram-bot 22.5
```

**Solution:**
1. Uninstall old version: `pip uninstall httpx`
2. Install correct version: `pip install httpx==0.27.2`
3. Reinstall telegram bot: `pip install --force-reinstall python-telegram-bot==22.5`

---

## 📈 Upgrading Dependencies

### Safe Upgrade Process

1. **Check compatibility first:**
   ```bash
   pip list --outdated
   ```

2. **Test in isolated environment:**
   ```bash
   python -m venv test-venv
   source test-venv/bin/activate
   pip install <new-package>==<new-version>
   python test_imports.py
   ```

3. **Update requirements.txt:**
   - Update version number
   - Add comment explaining change
   - Document in CHANGELOG.md

4. **Test thoroughly:**
   ```bash
   pytest
   docker compose build
   docker compose up -d
   ```

### Packages Safe to Upgrade

✅ **Can upgrade freely:**
- `uvicorn`
- `python-dotenv`
- `tenacity`
- `qrcode`
- `Pillow`

⚠️ **Upgrade with caution:**
- `fastapi` - Check pydantic compatibility
- `pydantic` - Major version changes break APIs
- `SQLAlchemy` - Test migrations after upgrade

❌ **Do NOT upgrade without testing:**
- `python-telegram-bot` - API changes frequently
- `httpx` - Must match telegram bot requirements
- `alembic` - May break existing migrations

---

## 🔒 Security Updates

Monitor security advisories:
```bash
pip install safety
safety check -r requirements.txt
```

Or use GitHub Dependabot (already configured in `.github/workflows/`).

---

## 📚 References

- **python-telegram-bot:** https://github.com/python-telegram-bot/python-telegram-bot
- **httpx:** https://www.python-httpx.org/
- **FastAPI:** https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0:** https://docs.sqlalchemy.org/en/20/
- **Pydantic V2:** https://docs.pydantic.dev/latest/

---

## ✅ Dependency Checklist

Before deploying:

- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] Versions match requirements.txt: `pip freeze`
- [ ] No dependency conflicts: `pip check`
- [ ] Import test passes: `python test_imports.py`
- [ ] Docker build succeeds: `docker compose build`
- [ ] Health check works: `curl http://localhost:8000/health`

---

**Last verified:** January 12, 2025  
**Compatible with:** Python 3.11+, Docker 24+, PostgreSQL 15+, Redis 7+