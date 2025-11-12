# QuickCart Installation Guide - From Zero to Running 🚀

**Complete step-by-step guide for absolute beginners**

This guide assumes you know NOTHING about servers, Docker, or programming. By the end, you'll have a working auto-order bot!

---

## 📋 What You Need

Before starting, you need:

1. **A Computer** - Windows, Mac, or Linux
2. **Internet Connection** - To download stuff
3. **30 Minutes** - That's all!
4. **A Telegram Account** - To create and test your bot

**That's it!** No programming knowledge needed.

---

## 🎯 What We'll Install

1. **Docker** - Runs the bot in a container (like a virtual box)
2. **QuickCart** - The bot itself
3. **PostgreSQL** - Database (comes with Docker, auto-installed)
4. **Redis** - Cache (optional, comes with Docker)

---

## Part 1: Install Docker

Docker is like a virtual machine that runs your bot. Choose your operating system:

### 🪟 Windows 10/11

1. **Check if you have Windows 10/11 Pro, Enterprise, or Education:**
   - Press `Win + R`
   - Type `winver` and press Enter
   - Look at the version

2. **Download Docker Desktop:**
   - Go to: https://www.docker.com/products/docker-desktop
   - Click "Download for Windows"
   - Wait for download (about 500MB)

3. **Install Docker Desktop:**
   - Double-click the downloaded file
   - Click "OK" when asked about WSL 2
   - Click "Close and restart" when done
   - Computer will restart

4. **Start Docker Desktop:**
   - Find "Docker Desktop" in Start menu
   - Click to open it
   - Wait for "Docker Desktop is running" message (bottom left)

5. **Verify Docker works:**
   - Press `Win + R`
   - Type `cmd` and press Enter
   - In the black window, type: `docker --version`
   - You should see: `Docker version 24.x.x`

✅ **Docker installed!**

---

### 🍎 Mac (Intel or M1/M2)

1. **Download Docker Desktop:**
   - Go to: https://www.docker.com/products/docker-desktop
   - Click "Download for Mac"
   - Choose "Mac with Intel chip" or "Mac with Apple chip" based on your Mac

2. **Install Docker Desktop:**
   - Open the downloaded `.dmg` file
   - Drag Docker icon to Applications folder
   - Open Applications folder
   - Double-click Docker
   - Click "Open" when warned about internet download

3. **Start Docker:**
   - Docker whale icon appears in top menu bar
   - Wait until it says "Docker Desktop is running"

4. **Verify Docker works:**
   - Press `Cmd + Space`
   - Type `terminal` and press Enter
   - In the terminal, type: `docker --version`
   - You should see: `Docker version 24.x.x`

✅ **Docker installed!**

---

### 🐧 Linux (Ubuntu/Debian)

1. **Open Terminal:**
   - Press `Ctrl + Alt + T`

2. **Install Docker with one command:**
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```
   - Press Enter
   - Wait 2-3 minutes
   - Enter your password if asked

3. **Add your user to docker group:**
   ```bash
   sudo usermod -aG docker $USER
   ```
   - Log out and log back in

4. **Install Docker Compose:**
   ```bash
   sudo apt-get update
   sudo apt-get install docker-compose-plugin
   ```

5. **Verify Docker works:**
   ```bash
   docker --version
   docker compose version
   ```
   - Both should show version numbers

✅ **Docker installed!**

---

## Part 2: Get Telegram Bot Token

You need a bot token to control your bot.

1. **Open Telegram** on your phone or computer

2. **Find BotFather:**
   - In search, type: `@BotFather`
   - Click on the official BotFather (verified with blue checkmark)

3. **Create your bot:**
   - Send: `/newbot`
   - BotFather asks: "Alright, a new bot. How are we going to call it?"
   - Type your bot name, example: `My Store Bot`
   - BotFather asks: "Now choose a username for your bot"
   - Type username ending in "bot", example: `mystore_bot`

4. **Copy your token:**
   - BotFather sends you a message with a token
   - It looks like: `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ`
   - **COPY THIS TOKEN** - you'll need it soon
   - **KEEP IT SECRET** - anyone with this token controls your bot

✅ **Bot token obtained!**

---

## Part 3: Get Your Telegram User ID

You need your User ID to be admin of the bot.

1. **Find userinfobot:**
   - In Telegram search, type: `@userinfobot`
   - Click on it

2. **Get your ID:**
   - Send: `/start`
   - The bot replies with your user ID
   - It's a number like: `123456789`
   - **COPY THIS NUMBER**

✅ **User ID obtained!**

---

## Part 4: Get Pakasir API Credentials

Pakasir is the payment gateway (for QRIS payments).

1. **Go to Pakasir:**
   - Open browser: https://pakasir.com
   - Click "Daftar" (Register)

2. **Create account:**
   - Fill in your details
   - Verify email
   - Login to dashboard

3. **Get API Key:**
   - In dashboard, click "Settings" or "Pengaturan"
   - Click "API" or "API Keys"
   - Click "Generate API Key"
   - **COPY THE API KEY** - looks like: `pk_live_xxxxxxxxxxxxxxxx`

4. **Get Project Slug:**
   - In dashboard, look at your project name
   - The slug is the URL-friendly version
   - Example: if project name is "My Store", slug might be: `my-store`
   - **COPY THE PROJECT SLUG**

5. **Set Webhook (we'll do this later):**
   - You'll need to add webhook URL after bot is running
   - For now, just have your API key and slug ready

✅ **Pakasir credentials obtained!**

---

## Part 5: Download QuickCart

Now download the bot code.

### If you have Git installed:

```bash
git clone <repository-url>
cd quickcart-v1
```

### If you DON'T have Git:

1. **Go to the repository page** (GitHub/GitLab)
2. **Click "Code" or "Clone"**
3. **Click "Download ZIP"**
4. **Extract the ZIP file** to a folder like `C:\quickcart-v1` or `~/quickcart-v1`
5. **Open terminal/command prompt in that folder:**
   - **Windows:** Right-click folder → "Open in Terminal" or "Command Prompt here"
   - **Mac:** Right-click folder → "New Terminal at Folder"
   - **Linux:** Right-click folder → "Open in Terminal"

✅ **QuickCart downloaded!**

---

## Part 6: Configure QuickCart

Now we'll create the configuration file.

1. **You should be in the quickcart-v1 folder**

2. **Copy the example configuration:**

   **Windows (Command Prompt):**
   ```cmd
   copy .env.example.template .env
   ```

   **Windows (PowerShell):**
   ```powershell
   Copy-Item .env.example.template .env
   ```

   **Mac/Linux:**
   ```bash
   cp .env.example.template .env
   ```

3. **Open the .env file:**
   - **Windows:** Right-click `.env` → "Edit with Notepad"
   - **Mac:** Right-click `.env` → "Open With" → "TextEdit"
   - **Linux:** Use any text editor: `nano .env` or `gedit .env`

4. **Fill in these values** (from what you copied earlier):

   Find these lines and replace the values:

   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   ```
   Replace `your_token_here` with your actual bot token

   ```env
   ADMIN_USER_IDS=123456789
   ```
   Replace `123456789` with your Telegram User ID

   ```env
   PAKASIR_API_KEY=your_api_key_here
   ```
   Replace `your_api_key_here` with your Pakasir API key

   ```env
   PAKASIR_PROJECT_SLUG=your_project_slug
   ```
   Replace `your_project_slug` with your Pakasir project slug

5. **Generate security keys:**

   You need random keys for SECRET_KEY and ENCRYPTION_KEY.

   **Option A - Use Python (if installed):**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Run this TWICE to get two different keys.

   **Option B - Use online generator:**
   - Go to: https://www.random.org/strings/
   - Set length to 32
   - Click "Get Strings"
   - Do this twice for two keys

   **Option C - Make up random strings:**
   - Type random letters, numbers for 32 characters
   - Example: `aB3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3x`
   - Make TWO different random strings

   Paste these into:
   ```env
   SECRET_KEY=paste_first_random_key_here
   ENCRYPTION_KEY=paste_second_random_key_here
   ```

6. **Optional settings:**
   
   You can change store name:
   ```env
   STORE_NAME=My Awesome Store
   ```

7. **Save and close the .env file**

✅ **Configuration complete!**

---

## Part 7: Start QuickCart

Now the exciting part - starting your bot!

1. **Make sure you're in the quickcart-v1 folder** in terminal/command prompt

2. **Start everything:**
   ```bash
   docker compose up -d
   ```

3. **What happens:**
   - Downloads required images (first time only, takes 2-5 minutes)
   - Creates database
   - Creates Redis cache
   - Starts your bot
   - Runs database migrations

4. **Wait for completion:**
   - You'll see: `✅ Container quickcart_app Started`
   - This means it's running!

5. **Check if everything is running:**
   ```bash
   docker compose ps
   ```

   You should see 3 services:
   - `quickcart_db` - Status: Up
   - `quickcart_redis` - Status: Up
   - `quickcart_app` - Status: Up

   If all show "Up", you're good! ✅

✅ **Bot is running!**

---

## Part 8: Test Your Bot

Let's make sure it works!

1. **Open Telegram**

2. **Search for your bot:**
   - Type the username you chose earlier (like `@mystore_bot`)
   - Click on your bot

3. **Start the bot:**
   - Send: `/start`
   - You should see a welcome message!

4. **If bot responds:**
   - 🎉 **SUCCESS!** Your bot is working!

5. **If bot doesn't respond:**
   - Check logs: `docker compose logs -f app`
   - Press `Ctrl+C` to exit logs
   - See "Troubleshooting" section below

✅ **Bot is working!**

---

## Part 9: View Logs (Monitoring)

To see what your bot is doing:

```bash
docker compose logs -f app
```

You'll see real-time logs like:
```
✓ Redis connected
✓ Database status: ok
✅ QuickCart is ready!
```

Press `Ctrl+C` to stop viewing logs (bot keeps running).

---

## Part 10: Common Commands

Here are commands you'll use often:

### See if bot is running:
```bash
docker compose ps
```

### Stop the bot:
```bash
docker compose down
```

### Start the bot:
```bash
docker compose up -d
```

### Restart the bot:
```bash
docker compose restart app
```

### View logs:
```bash
docker compose logs -f app
```

### Access database:
```bash
docker compose exec db psql -U quickcart -d quickcart
```
(Type `\q` to exit)

### Update bot (after code changes):
```bash
docker compose down
git pull  # or download new code
docker compose up -d --build
```

---

## 🐛 Troubleshooting

### Problem: "docker: command not found"

**Solution:**
- Docker is not installed or not in PATH
- Reinstall Docker Desktop
- On Mac/Windows: Make sure Docker Desktop is running
- On Linux: Run `sudo systemctl start docker`

---

### Problem: Bot doesn't respond to /start

**Solution 1 - Check logs:**
```bash
docker compose logs -f app
```
Look for errors. Common issues:
- Wrong bot token → Fix in `.env` file
- Database not ready → Wait 30 seconds and try again

**Solution 2 - Restart bot:**
```bash
docker compose restart app
```

**Solution 3 - Check bot token:**
- Go to @BotFather
- Send: `/mybots`
- Select your bot
- Click "API Token"
- Compare with token in `.env` file
- If different, update `.env` and restart

---

### Problem: "Port 5432 already in use"

**Solution:**
- You have PostgreSQL running on your computer
- Stop it, or change port in `docker-compose.yml`
- Change `"5432:5432"` to `"5433:5432"`

---

### Problem: "Port 8000 already in use"

**Solution:**
- Something else is using port 8000
- Change in `docker-compose.yml`
- Change `"8000:8000"` to `"8001:8000"`

---

### Problem: Database connection error

**Solution 1 - Reset database:**
```bash
docker compose down -v
docker compose up -d
```
**WARNING:** This deletes all data!

**Solution 2 - Check database status:**
```bash
docker compose exec db pg_isready -U quickcart
```
Should say: "accepting connections"

---

### Problem: Redis connection failed

**Solution:**
- This is OK! Bot works without Redis
- You should see: "✓ Falling back to in-memory storage"
- If you want Redis, check: `docker compose ps redis`

---

### Problem: Can't access bot from outside server

**Solution:**
- If bot is on VPS/cloud server:
  1. Make sure firewall allows port 8000
  2. Use public IP, not localhost
  3. Set up webhook instead of polling

---

### Problem: "permission denied" errors

**Solution on Linux:**
```bash
sudo usermod -aG docker $USER
```
Then log out and log back in.

---

## 🎓 Next Steps

Now that your bot is running:

### 1. Add Your First Product

In Telegram, send to your bot:
```
/add 1|Test Product|Category|10000|This is a test product
```

### 2. Add Stock

```
/addstock 1|test_content_here
```

### 3. Test Ordering

As a regular user (different Telegram account):
- Send `/start`
- Send `1` (product number)
- Try ordering

### 4. Configure Webhook (for payments)

1. Get your server's public URL (if on VPS)
2. Go to Pakasir dashboard
3. Set webhook URL to: `https://your-domain.com/webhooks/pakasir`
4. If testing locally, use ngrok: https://ngrok.com

### 5. Read Documentation

- `README.md` - Complete features guide
- `TESTING.md` - How to test everything
- `docs/03-prd.md` - All commands and features

---

## 🔒 Security Checklist

Before making bot public:

- [ ] Changed all default passwords in `docker-compose.yml`
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Set `DEBUG=false` in `.env`
- [ ] Never shared your `.env` file
- [ ] Set up HTTPS/SSL (use nginx + Let's Encrypt)
- [ ] Configured Pakasir webhook
- [ ] Tested complete order flow
- [ ] Set up automatic backups

---

## 💾 Backup Your Data

### Backup database:
```bash
docker compose exec db pg_dump -U quickcart quickcart > backup.sql
```

### Restore database:
```bash
docker compose exec -T db psql -U quickcart quickcart < backup.sql
```

### Backup everything (including config):
```bash
# Backup .env file
cp .env .env.backup

# Backup database
docker compose exec db pg_dump -U quickcart quickcart > backup_$(date +%Y%m%d).sql
```

---

## 📞 Getting Help

If you're stuck:

1. **Check logs first:**
   ```bash
   docker compose logs -f app
   ```

2. **Read error messages carefully** - they usually tell you what's wrong

3. **Search documentation:**
   - `README.md` for features
   - `TESTING.md` for testing
   - `docs/` folder for technical details

4. **Check GitHub Issues:**
   - Someone might have same problem

5. **Ask for help:**
   - Open GitHub issue
   - Include: error message, what you did, logs

---

## ✅ Installation Complete!

Congratulations! 🎉 You now have:

- ✅ Docker installed
- ✅ QuickCart running
- ✅ Database ready
- ✅ Bot responding in Telegram
- ✅ Ready to sell digital products!

**What's next?**
- Add products with `/add` command
- Add stock with `/addstock`
- Test ordering
- Configure payments
- Start selling!

---

## 📊 Quick Reference Card

Save this for later:

```
Start bot:     docker compose up -d
Stop bot:      docker compose down
Restart:       docker compose restart app
Logs:          docker compose logs -f app
Status:        docker compose ps
Database:      docker compose exec db psql -U quickcart -d quickcart

Add product:   /add 1|Name|Cat|Price|Desc
Add stock:     /addstock 1|content
View stock:    /stock
User info:     /info <user_id>
```

---

**Good luck with your digital store! 💪**

Need help? Read the docs or open an issue on GitHub.