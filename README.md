# QuickCart - Telegram Auto-Order Bot 🤖

> **Automated digital product sales bot for Telegram with QRIS payment integration.**

QuickCart is an auto-order bot system for selling digital products (courses, accounts, vouchers, etc.) through Telegram. Customers can browse, order, and receive products automatically after payment—all without manual intervention.

> **⚠️ DEVELOPMENT STATUS:** Core infrastructure is complete. Bot handlers and payment integration are currently in development. See [docs/00-project_blueprint.md](docs/00-project_blueprint.md) for detailed status.

**Built with:** `python-telegram-bot` v22.5, `FastAPI`, `PostgreSQL`, `Redis`, `SQLAlchemy`, and `Docker`.

---

## ✨ Features

- 🛍️ **Product Catalog**: Browse products by category, best sellers, or view all *(in development)*
- 💳 **QRIS Payment**: Automatic payment via Pakasir gateway *(in development)*
- ⏱️ **Flexible Navigation**: Users can switch between any flow without canceling
- 👥 **User Roles**: Customer, Reseller, and Admin roles
- 🎫 **Voucher System**: Create and distribute discount codes *(database ready)*
- 📊 **Audit Logging**: Complete transaction history for compliance in a separate database
- 🐳 **Docker Ready**: Simple, fast deployment for local development and production
- 🗄️ **Redis with Fallback**: Session management with optional in-memory fallback

---

## 📋 Prerequisites

Before you start, make sure you have:

1.  **Docker & Docker Compose** installed ([Get Docker](https://docs.docker.com/get-docker/))
2.  **Git** installed
3.  A **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
4.  Your personal **Telegram User ID** from a bot like [@userinfobot](https://t.me/userinfobot)
5.  A **Pakasir Account** for the payment gateway *(for production payment processing)*

---

## 🚀 Getting Started (Local Development)

This setup is recommended for testing, development, and small-scale use. It runs the application, databases, and Redis in Docker containers on your local machine.

### 1. Clone the Repository

```bash
git clone https://github.com/moccalatte/quickcart-v1.git
cd quickcart-v1
```

### 2. Configure Your Environment

Copy the environment variable template and fill in your credentials.

```bash
# 1. Copy the template
cp .env.template .env

# 2. Edit the .env file with a text editor (like nano, vim, or VS Code)
nano .env
```

Inside the `.env` file, you **must** fill in these required values:
- `TELEGRAM_BOT_TOKEN`
- `ADMIN_USER_IDS`
- `PAKASIR_API_KEY`
- `PAKASIR_PROJECT_SLUG`
- `SECRET_KEY` (generate a random string)
- `ENCRYPTION_KEY` (generate a random string)

The database and Redis variables are already pre-configured for the local Docker setup.

### 3. Launch the Application

Build and run the Docker containers in detached mode.

```bash
docker compose up -d --build
```

### 4. Check the Logs

Verify that the application and all services started correctly.

```bash
docker compose logs -f app
```

You should see a message indicating the bot has started successfully. You can now go to Telegram and start a conversation with your bot.

**Current Bot Capabilities:**
- ✅ User onboarding and registration
- ✅ Main menu navigation
- ✅ Product browsing interface
- ✅ Account management
- ✅ Flexible session-based navigation
- 🔧 Order processing (in development)
- 🔧 Payment integration (in development)
- 🔧 Admin commands (in development)

---

## 🌐 Production Deployment

This setup is designed for deploying the application on a server, connecting to **external, managed databases and Redis**.

### 1. Setup Your Server

Clone the repository and create the `.env` file as described in the local setup, but configure it for production:

- Set `ENVIRONMENT=production` and `DEBUG=False`.
- Set `DATABASE_URL` and `AUDIT_DATABASE_URL` to point to your external PostgreSQL servers.
- Set `REDIS_URL` to point to your external Redis server.

### 2. Launch with Production Compose File

Use the `docker-compose.prod.yml` file, which only runs the application container and expects all other services to be external.

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

This setup ensures your application container is lightweight and securely connects to your production infrastructure.

---

## ⚙️ Configuration

All configuration is managed through environment variables listed in `.env.template`. The application uses two separate Docker Compose files:

- `docker-compose.yml`: For **local development**. Includes `app`, `db`, `audit_db`, and `redis` services. Mounts the `src` directory for live-reloading.
- `docker-compose.prod.yml`: For **production**. Includes only the `app` service and is designed to connect to external databases and Redis.

See the `.env.template` file for a complete list of all available configuration variables and their descriptions.

---

## 🛠️ Useful Docker Commands

All commands should be run from the project's root directory.

#### View Logs
```bash
# For local development
docker compose logs -f

# For production
docker compose -f docker-compose.prod.yml logs -f
```

#### Stop Services
```bash
# For local development
docker compose down

# For production
docker compose -f docker-compose.prod.yml down
```

#### Stop Services and Remove Data Volumes
**Warning:** This will delete all your local database data.
```bash
docker compose down -v
```

#### Run Database Migrations Manually
The entrypoint script runs this automatically, but you can run it manually if needed.
```bash
docker compose exec app alembic upgrade head
```

#### Access the Main Database
```bash
docker compose exec db psql -U quickcart -d quickcart
```

---

## 📂 Project Structure

```
quickcart-v1/
├── src/                      # Source code
│   ├── core/                 # Config, database, redis, security
│   ├── models/               # SQLAlchemy database models
│   ├── repositories/         # Data access layer
│   ├── services/             # Business logic layer
│   ├── bot/                  # Telegram bot handlers & keyboards
│   │   ├── handlers/         # Command, callback, message handlers
│   │   ├── keyboards/        # Reply & inline keyboards
│   │   └── utils/            # Bot utilities
│   └── integrations/         # External API clients (Pakasir)
│
├── migrations/               # Alembic database migrations
│   └── versions/             # Migration scripts
├── docs/                     # Comprehensive project documentation
│   ├── 00-20-*.md            # Numbered design documents
│   ├── plans.md              # Original functional blueprint
│   └── *.md                  # Additional guides and references
├── tests/                    # Unit & integration tests
├── docker-compose.yml        # Local development (includes all services)
├── docker-compose.prod.yml   # Production deployment (app only)
├── Dockerfile                # App container image
├── .env.template             # Environment variables template
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```
