# 14. Build Plan
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
Outlines the comprehensive build strategy for QuickCart, including development phases, CI/CD pipeline, and deployment processes. Ensures zero-ambiguity implementation and reliable delivery of payment processing functionality.

---

## Development Milestones & Timeline

### Phase 1: Foundation & Core Infrastructure (Weeks 1-4)
| Week | Milestone | Components | Success Criteria |
|------|-----------|------------|------------------|
| 1 | Infrastructure Setup | Docker, PostgreSQL, Redis, Digital Ocean | All services running locally |
| 2 | Database Foundation | Schema creation, migrations, audit setup | All tables created with proper indexes |
| 3 | Basic Bot Framework | Telegram integration, message handling | Bot responds to basic commands |
| 4 | Payment Integration | Pakasir API connection, webhook setup | QR code generation working |

### Phase 2: Core Features Implementation (Weeks 5-8)
| Week | Milestone | Components | Success Criteria |
|------|-----------|------------|------------------|
| 5 | User Management | Registration, profiles, member status | User flows complete |
| 6 | Product Management | Catalog, stock, admin commands | Product CRUD operations working |
| 7 | Order Processing | Order creation, payment flows | End-to-end order completion |
| 8 | Content Delivery | Stock assignment, digital delivery | Products delivered upon payment |

### Phase 3: Advanced Features & Security (Weeks 9-12)
| Week | Milestone | Components | Success Criteria |
|------|-----------|------------|------------------|
| 9 | Account Balance System | Deposits, balance payments | Balance transactions working |
| 10 | Fraud Detection | Risk scoring, manual review | Fraud rules active |
| 11 | Admin Features | User management, notifications | Admin commands complete |
| 12 | Security Hardening | Rate limiting, audit logging | Security tests passing |

### Phase 4: Testing & Production Readiness (Weeks 13-16)
| Week | Milestone | Components | Success Criteria |
|------|-----------|------------|------------------|
| 13 | Load Testing | Performance optimization, scaling | System handles target load |
| 14 | Security Testing | Penetration testing, vulnerability scan | No critical vulnerabilities |
| 15 | UAT & Bug Fixes | User acceptance testing | All critical bugs resolved |
| 16 | Production Deployment | Go-live preparation, monitoring | System live and stable |

---

## Team Structure & Resource Allocation

### Core Development Team
```python
TEAM_STRUCTURE = {
    "senior_lead_engineer": {
        "name": "AI Agent (Primary)",
        "responsibilities": [
            "Architecture decisions",
            "Code review and quality",
            "Security implementation",
            "Documentation maintenance"
        ],
        "time_allocation": "100% development + oversight"
    },
    "devops_engineer": {
        "responsibilities": [
            "Infrastructure setup",
            "CI/CD pipeline",
            "Monitoring and alerting",
            "Backup and recovery"
        ],
        "time_allocation": "50% setup, 30% automation, 20% monitoring"
    },
    "security_specialist": {
        "responsibilities": [
            "Security review",
            "Penetration testing", 
            "Fraud detection tuning",
            "Compliance validation"
        ],
        "time_allocation": "Part-time consultant basis"
    },
    "qa_engineer": {
        "responsibilities": [
            "Test strategy execution",
            "Manual testing",
            "Test automation",
            "Bug tracking"
        ],
        "time_allocation": "Full-time during phases 3-4"
    }
}
```

### External Dependencies
- **Pakasir Support Team:** Payment gateway integration support
- **Digital Ocean Support:** Infrastructure and scaling guidance
- **Security Consultant:** Independent security audit
- **Compliance Advisor:** GDPR and financial regulations

---

## CI/CD Pipeline Architecture

### Pipeline Overview
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   Git Push  │───▶│  GitHub      │───▶│   Build &   │───▶│   Deploy     │
│             │    │  Actions     │    │   Test      │    │   to Staging │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                                                │
                                                ▼
                                       ┌─────────────┐
                                       │   Security  │
                                       │   Scan      │
                                       └─────────────┘
                                                │
                                                ▼
                                       ┌─────────────┐
                                       │   Manual    │
                                       │   Approval  │
                                       └─────────────┘
                                                │
                                                ▼
                                       ┌─────────────┐
                                       │   Deploy    │
                                       │   to Prod   │
                                       └─────────────┘
```

### GitHub Actions Workflow
```yaml
# .github/workflows/ci-cd.yml
name: QuickCart CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: quickcart_test
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v3
        with:
          python-version: '3.11'
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run database migrations
        run: |
          python manage.py migrate
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/quickcart_test
      
      - name: Run unit tests
        run: |
          pytest tests/unit/ --cov=src/ --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/quickcart_test
          REDIS_URL: redis://localhost:6379
      
      - name: Run integration tests
        run: |
          pytest tests/integration/ --cov=src/ --cov-append --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/quickcart_test
          REDIS_URL: redis://localhost:6379
          PAKASIR_API_KEY: test_key
      
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run security scan
        run: |
          pip install bandit safety
          bandit -r src/ -f json -o bandit-report.json
          safety check --json --output safety-report.json
      
      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json
            safety-report.json

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v3
        with:
          context: .
          push: true
          tags: |
            ghcr.io/quickcart/app:latest
            ghcr.io/quickcart/app:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: [build]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - name: Deploy to staging
        run: |
          # Deploy to Digital Ocean staging environment
          echo "Deploying to staging..."
          # Implementation specific to Digital Ocean setup

  deploy-production:
    needs: [build]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Deploy to production
        run: |
          # Deploy to Digital Ocean production environment
          echo "Deploying to production..."
          # Implementation specific to Digital Ocean setup
```

---

## Build Process Details

### Local Development Build
```python
# build_scripts/local_build.py
"""Local development build script"""

import subprocess
import os
import sys
from pathlib import Path

class LocalBuild:
    """Local development build automation"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.required_services = ["postgresql", "redis", "docker"]
    
    async def setup_development_environment(self):
        """Complete development environment setup"""
        
        print("🔧 Setting up QuickCart development environment...")
        
        # Check prerequisites
        await self.check_prerequisites()
        
        # Setup Python environment
        await self.setup_python_environment()
        
        # Setup databases
        await self.setup_databases()
        
        # Install dependencies
        await self.install_dependencies()
        
        # Run migrations
        await self.run_migrations()
        
        # Setup git hooks
        await self.setup_git_hooks()
        
        print("✅ Development environment ready!")
    
    async def check_prerequisites(self):
        """Verify all required tools are installed"""
        
        for service in self.required_services:
            if not self.is_service_available(service):
                raise EnvironmentError(f"{service} is required but not available")
        
        print("✅ All prerequisites available")
    
    def is_service_available(self, service: str) -> bool:
        """Check if required service is available"""
        try:
            result = subprocess.run(
                ["which", service], 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
```

### Production Build Process
```dockerfile
# Multi-stage production Dockerfile
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-prod.txt ./
RUN pip install --user --no-cache-dir -r requirements-prod.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /root/.local

# Create non-root user
RUN groupadd -r quickcart && useradd -r -g quickcart quickcart

# Set up application directory
WORKDIR /app
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY scripts/ ./scripts/

# Set proper permissions
RUN chown -R quickcart:quickcart /app
USER quickcart

# Add Python user packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Application startup
EXPOSE 8000
CMD ["python", "src/main.py"]
```

---

## Dependencies & Version Management

### Core Dependencies
```python
# requirements.txt - Production dependencies only
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-telegram-bot==22.5  # Latest version with async/await support
asyncpg==0.29.0
psycopg2-binary==2.9.9
alembic==1.12.1
SQLAlchemy==2.0.23
redis[hiredis]==5.0.1  # Optional - system works without it
httpx==0.25.2
pydantic==2.5.2
pydantic-settings==2.1.0
email-validator==2.1.0
python-dotenv==1.0.0
cryptography==41.0.7
python-multipart==0.0.6
python-dateutil==2.8.2
qrcode[pil]==7.4.2
Pillow==10.1.0
tenacity==8.2.3

# Installation
# pip install -r requirements.txt
# Or for latest python-telegram-bot: pip install python-telegram-bot --upgrade

# Testing (install separately)
# pytest==7.4.3
# pytest-asyncio==0.21.1
# pytest-cov==4.1.0
```

### Service Dependencies
```python
EXTERNAL_DEPENDENCIES = {
    "pakasir_api": {
        "version": "v1",
        "documentation": "https://app.pakasir.com/docs",
        "rate_limits": "1000 req/min",
        "health_check": "GET /api/health"
    },
    "telegram_bot_api": {
        "version": "Bot API 7.0+ (python-telegram-bot v22.5)",
        "library": "https://github.com/python-telegram-bot/python-telegram-bot",
        "documentation": "https://core.telegram.org/bots/api",
        "rate_limits": "30 msg/sec",
        "health_check": "GET /bot{token}/getMe"
    },
    "postgresql": {
        "min_version": "15.0",
        "extensions": ["uuid-ossp", "pg_trgm"],
        "connection_pooling": "required"
    },
    "redis": {
        "min_version": "7.0",
        "optional": True,  # System works without Redis (in-memory fallback)
        "persistence": "RDB + AOF"
    }
}
```

---

## Build Artifacts & Versioning

### Artifact Naming Convention
```python
ARTIFACT_NAMING = {
    "docker_images": "ghcr.io/quickcart/app:{version}",
    "database_migrations": "migrations/V{timestamp}_{description}.sql",
    "backup_files": "backup_{db_type}_{timestamp}.sql.gz", 
    "config_files": "config/{environment}.env",
    "deployment_manifests": "deploy/{environment}/docker-compose.yml"
}

# Version format: MAJOR.MINOR.PATCH-BUILD
# Example: 1.0.0-20251112.1
VERSION_FORMAT = "{major}.{minor}.{patch}-{date}.{build_number}"
```

### Deployment Artifacts
```python
class BuildArtifacts:
    """Manage build artifacts and deployment packages"""
    
    ARTIFACTS = {
        "application": {
            "type": "docker_image",
            "registry": "ghcr.io/quickcart/app",
            "tags": ["latest", "version", "commit_sha"]
        },
        "migrations": {
            "type": "sql_scripts",
            "location": "migrations/",
            "validation": "required"
        },
        "configuration": {
            "type": "environment_files",
            "location": "config/",
            "encryption": "required_for_production"
        },
        "monitoring": {
            "type": "dashboard_configs",
            "location": "monitoring/",
            "auto_import": "grafana_prometheus"
        }
    }
    
    async def create_deployment_package(self, environment: str, version: str):
        """Create complete deployment package for environment"""
        
        package = {
            "version": version,
            "environment": environment,
            "timestamp": datetime.utcnow().isoformat(),
            "artifacts": {}
        }
        
        for artifact_name, config in self.ARTIFACTS.items():
            artifact_info = await self.package_artifact(artifact_name, config, environment)
            package["artifacts"][artifact_name] = artifact_info
        
        # Create deployment manifest
        manifest = await self.create_deployment_manifest(package)
        
        return {
            "package": package,
            "manifest": manifest,
            "checksum": self.calculate_package_checksum(package)
        }
```

---

## Cross-References

- See [15-testing_strategy.md](15-testing_strategy.md) for comprehensive testing integration in build pipeline
- See [18-infra_plan.md](18-infra_plan.md) for deployment target infrastructure and scaling requirements
- See [01-dev_protocol.md](01-dev_protocol.md) for coding standards and development workflow
- See [17-observability.md](17-observability.md) for monitoring and logging configuration

---

> Note for AI builders: This build plan ensures reliable, secure, and traceable deployment of QuickCart. All build steps must be automated, tested, and auditable. Payment processing systems require extra validation at each build stage.