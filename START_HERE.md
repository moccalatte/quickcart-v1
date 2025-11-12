# 🚀 START HERE - QuickCart Quick Guide

**First time using QuickCart? Read this first!**

---

## ⚡ Super Quick Start (For Experienced Users)

```bash
# 1. Download
git clone <repo-url>
cd quickcart-v1

# 2. Setup
./setup.sh

# 3. Done!
# Bot is running, test in Telegram with /start
```

---

## 📖 For Beginners (Step-by-Step)

**→ Read: `INSTALL.md`**

Complete guide from absolute zero to running bot:
- Install Docker (Windows/Mac/Linux)
- Get Telegram bot token
- Configure QuickCart
- Start the bot
- Test everything

**Time needed:** 30 minutes (includes Docker installation)

---

## 📚 Documentation Map

Choose your path:

### 🆕 I'm a complete beginner
1. Read `INSTALL.md` - Complete installation guide
2. Read `README.md` - Features overview
3. Read `TESTING.md` - How to verify everything works

### 💻 I have Docker experience
1. Read `README.md` - Complete guide
2. Read `QUICKSTART.md` - 5-minute setup
3. Run `./setup.sh` or `docker compose up -d`

### 🔧 I'm a developer
1. Read `plans.md` - Complete specifications
2. Read `PROJECT_STATUS.md` - What's done/pending
3. Read `docs/` - 20 technical documents
4. Check `IMPLEMENTATION_SUMMARY.md` - All changes

### 🧪 I want to test
1. Read `TESTING.md` - 50+ test procedures
2. Run `python test_imports.py` - Check dependencies
3. Follow test-by-test guide

### 📦 I want to deploy to production
1. Read `INSTALL.md` - Complete setup
2. Read security section in `README.md`
3. Set `ENVIRONMENT=production` in `.env`
4. Follow production checklist

---

## ⚙️ Quick Commands

```bash
# Start bot
docker compose up -d

# Stop bot
docker compose down

# View logs
docker compose logs -f app

# Check status
docker compose ps

# Restart after changes
docker compose restart app

# Access database
docker compose exec db psql -U quickcart -d quickcart

# Run tests
python test_imports.py
```

**Or use Makefile:**
```bash
make help      # See all commands
make start     # Start bot
make logs      # View logs
make restart   # Restart bot
make backup    # Backup database
```

---

## ✅ Pre-Flight Checklist

Before starting:

- [ ] Docker installed (`docker --version`)
- [ ] docker-compose installed (`docker compose version`)
- [ ] Telegram bot token ready (from @BotFather)
- [ ] Your Telegram user ID ready (from @userinfobot)
- [ ] Pakasir account created (pakasir.com)
- [ ] 30 minutes available

---

## 🎯 What You'll Get

After setup, you'll have:

✅ Fully working Telegram bot  
✅ Product catalog system  
✅ QRIS payment integration  
✅ Admin command panel  
✅ Database with all tables  
✅ Automatic order fulfillment  
✅ Complete audit logging  

---

## 📞 Need Help?

1. **Check documentation first:**
   - `INSTALL.md` - Installation issues
   - `TESTING.md` - Verification issues
   - `README.md` - Features and FAQ

2. **Check logs:**
   ```bash
   docker compose logs -f app
   ```

3. **Common issues:**
   - Bot doesn't respond? → Check bot token in `.env`
   - Database error? → Wait 30 seconds, try again
   - Port conflict? → Change ports in `docker-compose.yml`
   - Permission denied? → Add user to docker group

4. **Still stuck?**
   - Read troubleshooting in `INSTALL.md`
   - Open GitHub issue
   - Include error logs

---

## 🚦 Quick Health Check

After starting, verify everything works:

```bash
# 1. Check services
docker compose ps
# Should show: db, redis, app (all "Up")

# 2. Check logs
docker compose logs -f app
# Should show: "✅ QuickCart is ready!"

# 3. Check health API
curl http://localhost:8000/health
# Should return: all services "ok"

# 4. Test in Telegram
# Send /start to your bot
# Should see: Welcome message
```

All green? **You're ready! 🎉**

---

## 📊 File Structure Quick Reference

```
quickcart-v1/
├── START_HERE.md          ← You are here
├── INSTALL.md             ← Beginner guide
├── README.md              ← Main documentation
├── QUICKSTART.md          ← 5-min guide
├── TESTING.md             ← Test procedures
├── PROJECT_STATUS.md      ← What's done/pending
├── CHANGELOG.md           ← Version history
├── plans.md               ← Complete specs
│
├── src/                   ← Source code
├── migrations/            ← Database migrations
├── docs/                  ← 20 detailed docs
├── docker-compose.yml     ← Deployment config
├── requirements.txt       ← Dependencies
└── setup.sh               ← Auto setup script
```

---

## 🎓 Learning Path

**Day 1:** Install and run
- Follow `INSTALL.md`
- Get bot running
- Send `/start` command

**Day 2:** Add products
- Use `/add` command
- Add stock with `/addstock`
- Test ordering

**Day 3:** Configure payments
- Set up Pakasir webhook
- Test small payment
- Verify auto-delivery

**Week 1:** Production ready
- SSL/HTTPS setup
- Backup configuration
- Monitoring setup
- Go live!

---

## 💡 Pro Tips

1. **Start with test mode** - Use small amounts
2. **Read logs often** - Especially first few days
3. **Backup before changes** - Run `make backup`
4. **Test payments first** - Small amounts only
5. **Monitor for a week** - Before going full production

---

## 🚀 Ready to Start?

**Choose your path:**

→ **Total beginner?** Go to `INSTALL.md`  
→ **Have Docker?** Go to `README.md` or run `./setup.sh`  
→ **Developer?** Go to `plans.md` and `PROJECT_STATUS.md`  

**Let's build your digital store! 💪**

---

_QuickCart v1.0.0 - Built with python-telegram-bot v22.5_
