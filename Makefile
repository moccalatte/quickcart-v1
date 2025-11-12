# QuickCart Makefile
# Simple commands for managing the bot

.PHONY: help start stop restart logs status clean reset migrate db shell test format

help: ## Show this help message
	@echo "QuickCart - Telegram Auto-Order Bot"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

start: ## Start all services (database, redis, bot)
	@echo "🚀 Starting QuickCart..."
	docker-compose up -d
	@echo "✅ QuickCart started!"
	@echo "📝 View logs: make logs"

stop: ## Stop all services
	@echo "🛑 Stopping QuickCart..."
	docker-compose down
	@echo "✅ QuickCart stopped!"

restart: ## Restart the bot (after code changes)
	@echo "🔄 Restarting QuickCart..."
	docker-compose restart app
	@echo "✅ QuickCart restarted!"

rebuild: ## Rebuild and restart (after dependency changes)
	@echo "🔨 Rebuilding QuickCart..."
	docker-compose up -d --build
	@echo "✅ QuickCart rebuilt!"

logs: ## Show bot logs (follow mode)
	docker-compose logs -f app

logs-all: ## Show all services logs
	docker-compose logs -f

status: ## Show status of all services
	docker-compose ps

clean: ## Stop services and remove containers (keeps data)
	@echo "🧹 Cleaning up containers..."
	docker-compose down
	@echo "✅ Cleanup complete! (Data preserved)"

reset: ## DANGER: Remove everything including data
	@echo "⚠️  WARNING: This will delete ALL data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "🗑️  All data deleted!"; \
	else \
		echo "❌ Cancelled."; \
	fi

migrate: ## Run database migrations
	@echo "🔄 Running migrations..."
	docker-compose exec app alembic upgrade head
	@echo "✅ Migrations complete!"

migrate-create: ## Create new migration (usage: make migrate-create MSG="description")
	@if [ -z "$(MSG)" ]; then \
		echo "❌ Error: Please provide MSG parameter"; \
		echo "Usage: make migrate-create MSG=\"add new column\""; \
		exit 1; \
	fi
	docker-compose exec app alembic revision --autogenerate -m "$(MSG)"

db: ## Open PostgreSQL shell
	docker-compose exec db psql -U quickcart -d quickcart

db-audit: ## Open audit database shell
	docker-compose exec db psql -U quickcart -d quickcart_audit

shell: ## Open bot container shell
	docker-compose exec app sh

test: ## Run tests
	@echo "🧪 Running tests..."
	docker-compose exec app pytest
	@echo "✅ Tests complete!"

test-cov: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	docker-compose exec app pytest --cov=src --cov-report=term --cov-report=html
	@echo "✅ Coverage report generated in htmlcov/"

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	docker-compose exec app black src/ tests/
	docker-compose exec app isort src/ tests/
	@echo "✅ Code formatted!"

lint: ## Run code quality checks
	@echo "🔍 Running linters..."
	docker-compose exec app flake8 src/
	docker-compose exec app mypy src/
	@echo "✅ Linting complete!"

backup: ## Backup databases
	@echo "💾 Backing up databases..."
	@mkdir -p backups
	@docker-compose exec -T db pg_dump -U quickcart quickcart > backups/quickcart_$(shell date +%Y%m%d_%H%M%S).sql
	@docker-compose exec -T db pg_dump -U quickcart quickcart_audit > backups/quickcart_audit_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backups saved to backups/"

restore: ## Restore database from backup (usage: make restore FILE=backups/quickcart_20240101.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Error: Please provide FILE parameter"; \
		echo "Usage: make restore FILE=backups/quickcart_20240101.sql"; \
		exit 1; \
	fi
	@echo "🔄 Restoring database from $(FILE)..."
	@docker-compose exec -T db psql -U quickcart -d quickcart < $(FILE)
	@echo "✅ Database restored!"

setup: ## Initial setup (copy env, generate keys)
	@echo "🔧 Setting up QuickCart..."
	@if [ ! -f .env ]; then \
		cp .env.example.template .env; \
		echo "✅ Created .env file"; \
		echo "⚠️  Please edit .env and fill in required values!"; \
	else \
		echo "⚠️  .env already exists, skipping..."; \
	fi
	@echo ""
	@echo "📝 Next steps:"
	@echo "1. Edit .env file with your values"
	@echo "2. Run: make start"
	@echo "3. Test your bot in Telegram!"

gen-keys: ## Generate random keys for .env
	@echo "SECRET_KEY=$(shell python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
	@echo "ENCRYPTION_KEY=$(shell python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

health: ## Check health status of all services
	@echo "🏥 Health Check:"
	@echo ""
	@echo "Database:"
	@docker-compose exec db pg_isready -U quickcart || echo "❌ Database not ready"
	@echo ""
	@echo "Redis:"
	@docker-compose exec redis redis-cli ping || echo "❌ Redis not ready"
	@echo ""
	@echo "Bot API:"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Bot not ready"

install: setup ## Alias for setup
	@echo "✅ Setup complete!"

dev: ## Start in development mode with hot reload
	docker-compose up

prod: ## Start in production mode
	@echo "🚀 Starting in production mode..."
	@export ENVIRONMENT=production DEBUG=false && docker-compose up -d
	@echo "✅ QuickCart running in production!"

update: ## Update codebase and restart
	@echo "🔄 Updating QuickCart..."
	git pull
	docker-compose up -d --build
	@echo "✅ QuickCart updated!"
