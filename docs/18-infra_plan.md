# 18. Infrastructure Plan
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
Defines comprehensive infrastructure strategy for QuickCart deployment on Digital Ocean, ensuring scalability, security, and reliability for payment processing workloads. Focused on cost-effective, maintainable infrastructure.

---

## Environment Strategy

### Multi-Environment Architecture
```yaml
environments:
  development:
    purpose: "Feature development and initial testing"
    isolation: "Complete isolation from other environments"
    data: "Synthetic test data only"
    access: "Development team only"
    
  staging:
    purpose: "Pre-production validation and integration testing"
    isolation: "Production-like but separate infrastructure"
    data: "Anonymized production data for realistic testing"
    access: "Development team + QA + stakeholders"
    
  production:
    purpose: "Live customer-facing environment"
    isolation: "Completely isolated with enhanced security"
    data: "Real customer and financial data"
    access: "Minimal access, audit-logged"
```

### Environment Configuration Matrix
| Component | Development | Staging | Production |
|-----------|-------------|---------|------------|
| **Digital Ocean Droplet** | Basic (1 vCPU, 1GB RAM) | Standard (2 vCPU, 4GB RAM) | Optimized (4 vCPU, 8GB RAM) |
| **PostgreSQL** | Managed DB Basic | Managed DB Standard | Managed DB Production + Standby |
| **Redis** | Single instance | Single instance | Cluster (3 nodes) |
| **Load Balancer** | None | Basic | Premium with SSL termination |
| **Monitoring** | Basic logs | Full monitoring | Full monitoring + alerting |
| **Backup** | Daily | Daily + weekly | Hourly + daily + weekly |

---

## Digital Ocean Infrastructure Design

### Core Infrastructure Components
```yaml
# Digital Ocean Infrastructure Layout
quickcart_infrastructure:
  region: "sgp1"  # Singapore for low latency to Indonesia
  vpc:
    name: "quickcart-vpc"
    ip_range: "10.0.0.0/16"
    subnets:
      public:
        name: "quickcart-public"
        ip_range: "10.0.1.0/24"
        purpose: "Load balancers, NAT gateway"
      private:
        name: "quickcart-private" 
        ip_range: "10.0.2.0/24"
        purpose: "Application servers, databases"

  compute:
    application_droplets:
      production:
        size: "s-2vcpu-4gb"
        image: "docker-20-04"
        count: 2  # Initial deployment
        auto_scaling:
          min: 2
          max: 10
          cpu_threshold: 70
      staging:
        size: "s-1vcpu-2gb" 
        image: "docker-20-04"
        count: 1
      development:
        size: "s-1vcpu-1gb"
        image: "docker-20-04"
        count: 1

  databases:
    postgresql_main:
      production:
        plan: "db-s-4vcpu-8gb"
        nodes: 2  # Primary + standby
        storage: "100gb"
        backups: "daily"
        region: "sgp1"
      staging:
        plan: "db-s-2vcpu-4gb"
        nodes: 1
        storage: "50gb"
        backups: "daily"

    postgresql_audit:
      production:
        plan: "db-s-2vcpu-4gb"
        nodes: 2  # Primary + standby
        storage: "200gb"  # Larger for permanent audit logs
        backups: "daily"
        
  redis_clusters:
    production:
      plan: "db-redis-s-2vcpu-4gb"
      nodes: 3  # Cluster mode
      eviction_policy: "allkeys-lru"
    staging:
      plan: "db-redis-s-1vcpu-2gb"
      nodes: 1

  load_balancers:
    production:
      type: "lb-small"
      algorithm: "round_robin"
      health_checks: "enabled"
      ssl_termination: "enabled"
      certificate: "lets_encrypt"

  spaces:
    backup_storage:
      name: "quickcart-backups"
      region: "sgp1"
      access: "private"
      lifecycle_rules:
        backup_retention: "90d"
        log_retention: "30d"
```

### Container Orchestration Strategy
```yaml
# Docker deployment configuration
docker_deployment:
  strategy: "docker-compose"  # Simple but effective for initial deployment
  upgrade_path: "kubernetes"  # Future migration when scaling requirements increase

  production_compose:
    version: "3.8"
    services:
      quickcart_app:
        image: "ghcr.io/quickcart/app:latest"
        replicas: 2
        restart_policy: "unless-stopped"
        health_check:
          test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
          interval: "30s"
          timeout: "10s"
          retries: 3
        environment:
          - "DATABASE_URL=${DATABASE_URL}"
          - "REDIS_URL=${REDIS_URL}"
          - "PAKASIR_API_KEY=${PAKASIR_API_KEY}"
          - "TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}"
        ports:
          - "8000:8000"
        deploy:
          resources:
            limits:
              memory: "2G"
              cpus: "1.5"
            reservations:
              memory: "1G"  
              cpus: "0.5"
```

---

## Security & Network Architecture

### Network Security Design
```python
# Firewall configuration for Digital Ocean
FIREWALL_RULES = {
    "quickcart_app_firewall": {
        "inbound_rules": [
            {
                "protocol": "tcp",
                "ports": "22",
                "sources": {
                    "addresses": ["YOUR_ADMIN_IP/32"]  # SSH access only from admin IPs
                }
            },
            {
                "protocol": "tcp", 
                "ports": "80,443",
                "sources": {
                    "load_balancer_uids": ["lb-xxx"]  # Only from load balancer
                }
            },
            {
                "protocol": "tcp",
                "ports": "8000",
                "sources": {
                    "load_balancer_uids": ["lb-xxx"]  # Application port
                }
            }
        ],
        "outbound_rules": [
            {
                "protocol": "tcp",
                "ports": "443",
                "destinations": {
                    "addresses": ["0.0.0.0/0"]  # HTTPS outbound (Pakasir, Telegram APIs)
                }
            },
            {
                "protocol": "tcp",
                "ports": "25432",  # PostgreSQL
                "destinations": {
                    "database_cluster_uids": ["dbaas-xxx"]
                }
            }
        ]
    },
    
    "quickcart_db_firewall": {
        "inbound_rules": [
            {
                "protocol": "tcp",
                "ports": "25432",
                "sources": {
                    "droplet_tags": ["quickcart-app"]  # Only from app servers
                }
            }
        ]
    }
}
```

### Simple Payment Configuration
```python
# Simple Pakasir configuration
class PaymentConfig:
    """Simple payment gateway configuration for Pakasir"""
    
    PAKASIR_CONFIG = {
        "required_secrets": ["PAKASIR_API_KEY", "PAKASIR_PROJECT"], 
        "base_url": "https://app.pakasir.com",
        "fee_percentage": 0.007,  # 0.7%
        "fee_fixed": 310,         # Rp310
        "payment_expiry": 600     # 10 minutes
    }
    
    # Simple downtime detection
    PAKASIR_HEALTH_CHECK = {
        "endpoint": "/api/health",  # If available
        "timeout": 5,               # seconds
        "retry_attempts": 3,
        "failure_message": "Payment gateway sedang bermasalah. Coba lagi dalam beberapa menit atau hubungi admin."
    }
```

### Secrets Management Strategy
```python
# Environment variable management with multi-gateway support
class SecretsManagement:
    """Secure secrets handling for different environments and gateways"""
    
    SECRET_SOURCES = {
        "development": "local_env_file",  # .env.local
        "staging": "digital_ocean_app_platform",  # DO App Platform secrets
        "production": "digital_ocean_app_platform"  # DO App Platform secrets
    }
    
    # Core system secrets
    REQUIRED_SECRETS = [
        "DATABASE_URL",
        "AUDIT_DATABASE_URL", 
        "REDIS_URL",
        "TELEGRAM_BOT_TOKEN",
        "ENCRYPTION_KEY_FOR_AUDIT_LOGS",
        "WEBHOOK_SECRET_KEY"
    ]
    
    # Simple payment gateway secrets
    PAKASIR_SECRETS = ["PAKASIR_API_KEY", "PAKASIR_PROJECT"]
    
    def get_all_required_secrets(self) -> List[str]:
        """Get all required secrets for QuickCart"""
        return self.REQUIRED_SECRETS + self.PAKASIR_SECRETS
    
    def validate_secrets_presence(self, environment: str):
        """Ensure all required secrets are available"""
        missing_secrets = []
        
        for secret in self.REQUIRED_SECRETS:
            if not os.getenv(secret):
                missing_secrets.append(secret)
        
        if missing_secrets:
            raise SecretsValidationError(f"Missing secrets: {missing_secrets}")
        
        return True
```

---

## Scalability & Performance Architecture

### Auto-scaling Configuration
```python
# Digital Ocean auto-scaling setup
AUTO_SCALING_CONFIG = {
    "horizontal_scaling": {
        "triggers": [
            {
                "metric": "cpu_usage",
                "threshold": 70,  # 70% CPU
                "duration": 300,  # 5 minutes
                "action": "scale_up",
                "cooldown": 600   # 10 minutes
            },
            {
                "metric": "memory_usage", 
                "threshold": 80,  # 80% memory
                "duration": 180,  # 3 minutes
                "action": "scale_up",
                "cooldown": 600
            },
            {
                "metric": "active_connections",
                "threshold": 1000,  # 1000 concurrent connections
                "duration": 60,     # 1 minute
                "action": "scale_up",
                "cooldown": 300
            }
        ],
        "scale_down_triggers": [
            {
                "metric": "cpu_usage",
                "threshold": 30,  # 30% CPU
                "duration": 1800, # 30 minutes (conservative)
                "action": "scale_down",
                "cooldown": 1800
            }
        ],
        "limits": {
            "min_instances": 2,   # Always maintain 2 instances for HA
            "max_instances": 10,  # Cost control limit
            "scale_up_step": 2,   # Add 2 instances at a time
            "scale_down_step": 1  # Remove 1 instance at a time
        }
    }
}
```

### Database Scaling Strategy
```python
DATABASE_SCALING = {
    "read_replicas": {
        "production": {
            "primary_region": "sgp1",
            "read_replica_regions": ["sgp1"],  # Same region initially
            "replica_count": 1,
            "automatic_failover": True,
            "connection_pooling": {
                "max_connections": 100,
                "pool_size": 20,
                "pool_timeout": 30
            }
        }
    },
    "vertical_scaling": {
        "triggers": [
            {
                "metric": "connection_utilization",
                "threshold": 80,
                "action": "recommend_upgrade"
            },
            {
                "metric": "cpu_usage",
                "threshold": 80,
                "action": "recommend_upgrade" 
            },
            {
                "metric": "memory_usage",
                "threshold": 85,
                "action": "recommend_upgrade"
            }
        ]
    }
}
```

---

## Cost Management & Optimization

### Cost Budgets & Monitoring
```python
COST_MANAGEMENT = {
    "monthly_budgets": {
        "development": 50,    # USD
        "staging": 150,       # USD  
        "production": 800,    # USD
        "total": 1000        # USD
    },
    "cost_alerts": [
        {
            "threshold": 80,   # 80% of budget
            "action": "email_alert",
            "recipients": ["devops@company.com"]
        },
        {
            "threshold": 95,   # 95% of budget
            "action": "emergency_alert",
            "recipients": ["devops@company.com", "cto@company.com"]
        },
        {
            "threshold": 100,  # Budget exceeded
            "action": "auto_scale_down",
            "safety_limits": {
                "min_production_instances": 1,
                "preserve_databases": True
            }
        }
    ],
    "optimization_strategies": [
        {
            "resource": "compute",
            "strategy": "right_sizing",
            "schedule": "weekly"
        },
        {
            "resource": "storage",
            "strategy": "lifecycle_management",
            "schedule": "daily"
        },
        {
            "resource": "networking",
            "strategy": "traffic_optimization",
            "schedule": "monthly"
        }
    ]
}
```

### Resource Optimization
```python
class ResourceOptimization:
    """Automated resource optimization"""
    
    async def optimize_compute_resources(self):
        """Right-size compute instances based on usage"""
        
        # Analyze CPU/memory usage over the last 7 days
        usage_stats = await self.get_usage_statistics(days=7)
        
        recommendations = []
        
        for droplet in usage_stats:
            avg_cpu = droplet["cpu_usage_avg"]
            avg_memory = droplet["memory_usage_avg"]
            
            # Recommend downsizing if consistently underutilized
            if avg_cpu < 30 and avg_memory < 50:
                smaller_size = self.get_smaller_droplet_size(droplet["size"])
                if smaller_size:
                    recommendations.append({
                        "droplet_id": droplet["id"],
                        "current_size": droplet["size"], 
                        "recommended_size": smaller_size,
                        "estimated_savings": self.calculate_savings(droplet["size"], smaller_size)
                    })
            
            # Recommend upsizing if consistently over-utilized
            elif avg_cpu > 80 or avg_memory > 85:
                larger_size = self.get_larger_droplet_size(droplet["size"])
                if larger_size:
                    recommendations.append({
                        "droplet_id": droplet["id"],
                        "current_size": droplet["size"],
                        "recommended_size": larger_size,
                        "reason": "performance_optimization"
                    })
        
        return recommendations
```

---

## Infrastructure as Code Implementation

### Terraform Configuration Structure
```hcl
# terraform/main.tf - Infrastructure definition
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
  
  backend "s3" {
    # Using DO Spaces as Terraform backend
    endpoint = "https://sgp1.digitaloceanspaces.com"
    bucket   = "quickcart-terraform-state"
    key      = "infrastructure/terraform.tfstate"
    region   = "sgp1"
    
    skip_credentials_validation = true
    skip_metadata_api_check     = true
  }
}

# Variables
variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
}

variable "droplet_size" {
  description = "Droplet size for the environment"
  type        = map(string)
  default = {
    development = "s-1vcpu-1gb"
    staging     = "s-2vcpu-4gb"
    production  = "s-4vcpu-8gb"
  }
}

# Main application droplets
resource "digitalocean_droplet" "quickcart_app" {
  count    = var.environment == "production" ? 2 : 1
  image    = "docker-20-04"
  name     = "quickcart-app-${var.environment}-${count.index + 1}"
  region   = "sgp1"
  size     = var.droplet_size[var.environment]
  vpc_uuid = digitalocean_vpc.quickcart_vpc.id
  
  ssh_keys = [digitalocean_ssh_key.quickcart_key.id]
  
  tags = [
    "quickcart",
    "app",
    var.environment
  ]
  
  user_data = templatefile("${path.module}/user_data.sh", {
    environment = var.environment
  })
}

# Managed PostgreSQL database
resource "digitalocean_database_cluster" "quickcart_main" {
  name       = "quickcart-main-${var.environment}"
  engine     = "pg"
  version    = "15"
  size       = var.environment == "production" ? "db-s-4vcpu-8gb" : "db-s-2vcpu-4gb"
  region     = "sgp1"
  node_count = var.environment == "production" ? 2 : 1
  
  tags = [
    "quickcart",
    "database", 
    "main",
    var.environment
  ]
}
```

### Deployment Automation
```yaml
# .github/workflows/infrastructure.yml
name: Infrastructure Deployment

on:
  push:
    branches: [main]
    paths: ['terraform/**']
  pull_request:
    paths: ['terraform/**']

jobs:
  terraform:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        environment: [development, staging, production]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.0
      
      - name: Terraform Init
        run: terraform init
        working-directory: ./terraform
        env:
          SPACES_ACCESS_KEY_ID: ${{ secrets.SPACES_ACCESS_KEY_ID }}
          SPACES_SECRET_ACCESS_KEY: ${{ secrets.SPACES_SECRET_ACCESS_KEY }}
      
      - name: Terraform Plan
        run: terraform plan -var="environment=${{ matrix.environment }}"
        working-directory: ./terraform
        env:
          DIGITALOCEAN_TOKEN: ${{ secrets.DIGITALOCEAN_TOKEN }}
      
      - name: Terraform Apply
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: terraform apply -auto-approve -var="environment=${{ matrix.environment }}"
        working-directory: ./terraform
        env:
          DIGITALOCEAN_TOKEN: ${{ secrets.DIGITALOCEAN_TOKEN }}
```

---

## Disaster Recovery Infrastructure

### Multi-Region Strategy
```python
DISASTER_RECOVERY_INFRASTRUCTURE = {
    "primary_region": "sgp1",  # Singapore
    "backup_region": "fra1",   # Frankfurt (for geographic diversity)
    
    "replication_strategy": {
        "databases": {
            "method": "streaming_replication",
            "rpo": "< 1 minute",
            "rto": "< 30 minutes"
        },
        "application_data": {
            "method": "cross_region_backup",
            "frequency": "daily", 
            "retention": "90 days"
        },
        "configuration": {
            "method": "infrastructure_as_code",
            "sync": "real_time"
        }
    },
    
    "failover_procedures": {
        "automatic_triggers": [
            "primary_region_outage > 15 minutes",
            "database_unavailable > 10 minutes",
            "application_error_rate > 50% for 5 minutes"
        ],
        "manual_triggers": [
            "security_incident",
            "planned_maintenance",
            "performance_degradation"
        ]
    }
}
```

---

## Cross-References

- See [09-security_manifest.md](09-security_manifest.md) for detailed security controls implementation and firewall configurations
- See [06-data_schema.md](06-data_schema.md) for database sizing and performance requirements
- See [17-observability.md](17-observability.md) for infrastructure monitoring setup and alerting integration
- See [13-recovery_strategy.md](13-recovery_strategy.md) for backup infrastructure and disaster recovery procedures

---

> Note for AI builders: This infrastructure plan prioritizes reliability and cost-effectiveness over complexity. Start with simple, proven solutions and scale gradually. Every infrastructure component must be monitored, backed up, and easily replaceable. Security must be built into every layer, not added as an afterthought.