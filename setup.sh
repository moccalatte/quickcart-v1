#!/bin/bash

# QuickCart Setup Script
# This script helps you set up QuickCart for the first time

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         QuickCart - Telegram Auto-Order Bot Setup           ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check prerequisites
echo "Step 1: Checking prerequisites..."
echo ""

# Check Docker
if command -v docker &> /dev/null; then
    print_success "Docker is installed ($(docker --version | cut -d' ' -f3 | cut -d',' -f1))"
else
    print_error "Docker is not installed"
    echo ""
    echo "Please install Docker first:"
    echo "  Linux: curl -fsSL https://get.docker.com | sh"
    echo "  Mac/Windows: Download from https://www.docker.com/get-started"
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    print_success "Docker Compose is installed ($(docker-compose --version | cut -d' ' -f4 | cut -d',' -f1))"
elif docker compose version &> /dev/null; then
    print_success "Docker Compose (plugin) is installed"
    alias docker-compose='docker compose'
else
    print_error "Docker Compose is not installed"
    echo ""
    echo "Please install Docker Compose:"
    echo "  https://docs.docker.com/compose/install/"
    exit 1
fi

echo ""

# Create .env file if it doesn't exist
echo "Step 2: Creating configuration file..."
echo ""

if [ -f .env ]; then
    print_warning ".env file already exists"
    read -p "Do you want to overwrite it? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Keeping existing .env file"
    else
        cp .env.template .env
        print_success "Created new .env file"
    fi
else
    cp .env.template .env
    print_success "Created .env file"
fi

echo ""

# Generate secret keys
echo "Step 3: Generating security keys..."
echo ""

if command -v python3 &> /dev/null; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

    # Update .env with generated keys
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        sed -i '' "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
    else
        # Linux
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
    fi

    print_success "Generated and saved security keys"
else
    print_warning "Python3 not found - you'll need to generate keys manually"
    echo ""
    echo "Run these commands and update .env file:"
    echo "  python -c \"import secrets; print(secrets.token_urlsafe(32))\""
fi

echo ""

# Prompt for required configuration
echo "Step 4: Required configuration"
echo ""
print_info "Please enter the following required information:"
echo ""

# Telegram Bot Token
read -p "Telegram Bot Token (from @BotFather): " BOT_TOKEN
if [ -n "$BOT_TOKEN" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$BOT_TOKEN|" .env
    else
        sed -i "s|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$BOT_TOKEN|" .env
    fi
    print_success "Saved Telegram Bot Token"
fi

# Admin User IDs
read -p "Your Telegram User ID (from @userinfobot): " USER_ID
if [ -n "$USER_ID" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/ADMIN_USER_IDS=.*/ADMIN_USER_IDS=$USER_ID/" .env
    else
        sed -i "s/ADMIN_USER_IDS=.*/ADMIN_USER_IDS=$USER_ID/" .env
    fi
    print_success "Saved Admin User ID"
fi

# Pakasir API Key
read -p "Pakasir API Key (from pakasir.com): " API_KEY
if [ -n "$API_KEY" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/PAKASIR_API_KEY=.*/PAKASIR_API_KEY=$API_KEY/" .env
    else
        sed -i "s/PAKASIR_API_KEY=.*/PAKASIR_API_KEY=$API_KEY/" .env
    fi
    print_success "Saved Pakasir API Key"
fi

# Pakasir Project Slug
read -p "Pakasir Project Slug: " PROJECT_SLUG
if [ -n "$PROJECT_SLUG" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/PAKASIR_PROJECT_SLUG=.*/PAKASIR_PROJECT_SLUG=$PROJECT_SLUG/" .env
    else
        sed -i "s/PAKASIR_PROJECT_SLUG=.*/PAKASIR_PROJECT_SLUG=$PROJECT_SLUG/" .env
    fi
    print_success "Saved Pakasir Project Slug"
fi

echo ""

# Optional: Store name
read -p "Store Name (optional, press Enter to skip): " STORE_NAME
if [ -n "$STORE_NAME" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/STORE_NAME=.*/STORE_NAME=$STORE_NAME/" .env
    else
        sed -i "s/STORE_NAME=.*/STORE_NAME=$STORE_NAME/" .env
    fi
    print_success "Saved Store Name"
fi

echo ""

# Ask if user wants to start now
echo "Step 5: Ready to launch!"
echo ""
print_info "Configuration complete! Your bot is ready to start."
echo ""
read -p "Do you want to start QuickCart now? [Y/n] " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo "🚀 Starting QuickCart..."
    echo ""

    sudo docker compose up -d

    echo ""
    print_success "QuickCart is starting!"
    echo ""
    echo "Waiting for services to be ready..."
    sleep 10

    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║                    Setup Complete! 🎉                        ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    print_success "QuickCart is running!"
    echo ""
    echo "📝 Next steps:"
    echo ""
    echo "  1. Open Telegram and search for your bot"
    echo "  2. Send /start to your bot"
    echo "  3. You should see the welcome message!"
    echo ""
    echo "📊 Useful commands:"
    echo ""
    echo "  make logs      - View bot logs"
    echo "  make status    - Check service status"
    echo "  make stop      - Stop the bot"
    echo "  make restart   - Restart the bot"
    echo "  make help      - See all commands"
    echo ""
    echo "📚 Documentation: See docs/ folder for detailed guides"
    echo ""
    print_info "View logs with: docker-compose logs -f app"
    echo ""
else
    echo ""
    print_info "Setup complete! Start QuickCart when ready with:"
    echo ""
    echo "  make start"
    echo ""
    echo "Or manually:"
    echo ""
    echo "  docker-compose up -d"
    echo ""
fi

# Create backup directory
mkdir -p backups
print_success "Created backups directory"

echo ""
print_info "Setup script finished!"
echo ""
