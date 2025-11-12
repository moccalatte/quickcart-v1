# QuickStart Guide - Get Your Bot Running in 5 Minutes! 🚀

This is the **simplest** guide to get QuickCart running. Perfect for beginners!

---

## 🎯 What You'll Get

After following this guide, you'll have:
- ✅ A fully working Telegram bot
- ✅ Product catalog system
- ✅ Automatic QRIS payment processing
- ✅ Order management system
- ✅ All running on your server/computer

---

## 📋 Before You Start

You need **4 things**:

### 1. Docker Installed
- **Windows/Mac**: Download from [docker.com/get-started](https://www.docker.com/get-started)
- **Linux**: Run `curl -fsSL https://get.docker.com | sh`
- Test it: `docker --version` (should show version number)

### 2. Telegram Bot Token
- Open Telegram, search for `@BotFather`
- Send `/newbot` and follow instructions
- Copy the token (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 3. Your Telegram User ID
- Open Telegram, search for `@userinfobot`
- Send `/start`
- Copy your ID (looks like: `123456789`)

### 4. Pakasir Account
- Go to [pakasir.com](https://pakasir.com)
- Sign up for free account
- Get your API Key and Project Slug from dashboard

That's it! Now let's start...

---

## 🚀 Installation Steps

### Step 1: Download QuickCart

```bash
# Download the code
git clone <your-repo-url>
cd quickcart-v1
```

### Step 2: Run Setup Script

```bash
# Make it executable
chmod +x setup.sh

# Run the setup wizard
./setup.sh
```

The setup wizard will ask you for:
1. Your Telegram Bot Token
2. Your Telegram User ID
3. Your Pakasir API Key
4. Your Pakasir Project Slug

Just paste them when prompted. The script will:
- ✅ Create your `.env` file
- ✅ Generate security keys automatically
- ✅ Start the bot
- ✅ Run database migrations

### Step 3: Test Your Bot

1. Open Telegram
2. Search for your bot (the name you gave @BotFather)
3. Send `/start`
4. You should see a welcome message!

🎉 **Congratulations! Your bot is running!**

---

## 📱 What Can You Do Now?

### As a User (in Telegram):
- `/start` - Start the bot
- Click `[LIST PRODUK]` - Browse products
- Send a product number (1-24) - Order a product

### As Admin (in Telegram):
- `/add 1|Product Name|Category|50000|Description` - Add product
- `/addstock 1|content here` - Add stock to product
- `/stock` - View all stock
- `/info 123456789` - Check user info

---

## 🛠️ Common Commands

### View Logs (see what's happening)
```bash
docker-compose logs -f app
```
Press `Ctrl+C` to exit

### Stop the Bot
```bash
docker-compose down
```

### Start the Bot Again
```bash
docker-compose up -d
```

### Restart After Code Changes
```bash
docker-compose restart app
```

### Reset Everything (DANGER - deletes all data!)
```bash
docker-compose down -v
docker-compose up -d
```

---

## ❓ Troubleshooting

### Bot doesn't respond?

**Check logs:**
```bash
docker-compose logs -f app
```

**Common fixes:**
1. Make sure bot token is correct in `.env`
2. Try restarting: `docker-compose restart app`
3. Check if services are running: `docker-compose ps`

### "Connection refused" error?

Wait 30 seconds and try again. Database might still be starting.

### Can't access the bot?

1. Make sure you sent `/start` to the bot
2. Check your `ADMIN_USER_IDS` in `.env` is correct
3. Try `/deleteWebhook` via @BotFather

---

## 📚 Next Steps

Now that your bot is running:

1. **Add your first product:**
   ```
   /add 1|Netflix Premium|Streaming|50000|Netflix account 1 month
   ```

2. **Add stock:**
   ```
   /addstock 1|email@example.com:password123
   ```

3. **Test ordering:**
   - Send `1` to bot (product ID)
   - Select quantity
   - Try payment flow

4. **Read full documentation:**
   - See `README.md` for complete guide
   - See `docs/03-prd.md` for all features
   - See `docs/06-data_schema.md` for database info

---

## 🎓 Understanding the Setup

### What was installed?

```
📦 Docker Containers:
   ├── quickcart_db    (PostgreSQL - stores your data)
   ├── quickcart_redis (Redis - caching, optional)
   └── quickcart_app   (Your bot - handles everything)

📁 Docker Volumes:
   ├── postgres_data   (your database files)
   └── redis_data      (cache data)
```

### Where is my data?

All your data is in Docker volumes:
```bash
# See volumes
docker volume ls

# Backup your data
make backup
```

### Configuration file

Your `.env` file contains:
- Telegram bot token
- Payment gateway keys
- Database settings
- Security keys

**⚠️ Never share your `.env` file - it contains secrets!**

---

## 🔒 Security Tips

1. **Keep `.env` secret** - Never commit to git
2. **Change default passwords** - Edit `docker-compose.yml` if exposed
3. **Use HTTPS** - Set up nginx with SSL for production
4. **Regular backups** - Run `make backup` daily
5. **Update regularly** - Pull latest code monthly

---

## 💡 Pro Tips

### Use Makefile Commands

Instead of long docker commands, use:
```bash
make start     # Start everything
make stop      # Stop everything
make logs      # View logs
make restart   # Restart bot
make help      # See all commands
```

### Quick Database Access
```bash
make db        # Open database shell
```

### Backup Before Changes
```bash
make backup    # Creates backup in backups/
```

---

## 🆘 Need Help?

1. **Check logs first:**
   ```bash
   make logs
   ```

2. **Read documentation:**
   - `README.md` - Full guide
   - `docs/` folder - 20+ detailed docs

3. **Common issues:**
   - Wrong bot token? Edit `.env` and restart
   - Database errors? Run `make reset` (deletes data!)
   - Port conflicts? Change `8000:8000` in `docker-compose.yml`

4. **Still stuck?**
   - Open an issue on GitHub
   - Join our Telegram support group
   - Read the FAQ in README.md

---

## ✅ Checklist

Before going to production:

- [ ] Changed all default passwords in `docker-compose.yml`
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Set `DEBUG=false` in `.env`
- [ ] Set up HTTPS/SSL
- [ ] Configured Pakasir webhook URL
- [ ] Tested complete order flow
- [ ] Set up automatic backups
- [ ] Added monitoring/alerting

---

## 🎉 You're All Set!

Your QuickCart bot is now running. Happy selling! 🚀

**Quick Reference:**
- Start bot: `make start`
- Stop bot: `make stop`
- View logs: `make logs`
- Add product: `/add` command in Telegram
- Full docs: See `README.md`

---

**Questions? Issues? Ideas?**
- Open an issue on GitHub
- Read the docs in `docs/` folder
- Check `README.md` for FAQ

**Good luck with your digital store! 💪**