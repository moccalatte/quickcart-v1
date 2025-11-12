# 17. Observability Plan
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
Describes comprehensive observability strategy for QuickCart to ensure reliable monitoring, troubleshooting, and performance optimization for the payment processing system. Critical for maintaining 99.5% uptime and rapid incident response.

---

## 1. Metrics Collection & Monitoring

### System Metrics (Infrastructure Level)
```python
SYSTEM_METRICS = {
    "compute": {
        "cpu_usage_percent": {"threshold": 80, "alert_duration": "5m"},
        "memory_usage_percent": {"threshold": 85, "alert_duration": "5m"}, 
        "disk_usage_percent": {"threshold": 90, "alert_duration": "1m"},
        "network_io_mbps": {"threshold": 100, "alert_duration": "10m"}
    },
    "database": {
        "postgresql_connections": {"threshold": 80, "alert_duration": "5m"},
        "postgresql_slow_queries": {"threshold": 10, "alert_duration": "5m"},
        "postgresql_replication_lag": {"threshold": 10, "alert_duration": "1m"},
        "redis_memory_usage": {"threshold": 80, "alert_duration": "5m"}
    },
    "containers": {
        "docker_container_restart_count": {"threshold": 3, "alert_duration": "1h"},
        "docker_image_pull_duration": {"threshold": 300, "alert_duration": "5m"}
    }
}
```

### Application Metrics (PC-001 Best Practice: Bot Stability)
```python
# Simple bot health monitoring (beginner-friendly)
class BotHealthMonitor:
    def __init__(self):
        self.max_response_time = 3.0  # 3 seconds max response
        self.health_check_interval = 60  # Check every minute
    
    async def check_bot_health(self):
        """Simple bot health check"""
        health_status = {
            "bot_responding": False,
            "database_connected": False,
            "redis_connected": False,
            "response_time": None
        }
        
        start_time = time.time()
        
        try:
            # Test bot response time
            test_response = await self.test_bot_response()
            response_time = time.time() - start_time
            
            health_status["bot_responding"] = True
            health_status["response_time"] = response_time
            
            # Alert if too slow
            if response_time > self.max_response_time:
                await self.alert_slow_response(response_time)
            
        except Exception as e:
            await self.alert_bot_down(str(e))
        
        try:
            # Test database
            await database.execute("SELECT 1")
            health_status["database_connected"] = True
        except:
            await self.alert_database_down()
        
        try:
            # Test Redis
            await redis.ping()
            health_status["redis_connected"] = True
        except:
            await self.alert_redis_down()
        
        return health_status
    
    async def alert_slow_response(self, response_time):
        """Alert admin when bot is slow"""
        await notify_admins(f"⚠️ Bot lambat: {response_time:.1f} detik (target: <3 detik)")
    
    async def alert_bot_down(self, error):
        """Alert admin when bot is down"""
        await notify_admins(f"🚨 Bot tidak merespon: {error}")

APPLICATION_METRICS = {
    "api_performance": {
        "http_request_duration_seconds": {"p95_threshold": 2.0, "p99_threshold": 3.0},  # Lowered for stability
        "http_requests_per_second": {"baseline": 10, "spike_threshold": 100},
        "http_error_rate_percent": {"threshold": 1.0, "critical_threshold": 5.0}
    },
    "payment_processing": {
        "pakasir_api_response_time": {"threshold": 30, "alert_duration": "5m"},
        "pakasir_api_error_rate": {"threshold": 5, "alert_duration": "1m"},
        "payment_success_rate": {"threshold": 95, "alert_duration": "5m"},
        "payment_expiry_rate": {"threshold": 10, "alert_duration": "10m"}
    },
    "telegram_integration": {
        "telegram_message_send_duration": {"threshold": 10, "alert_duration": "5m"},
        "telegram_webhook_latency": {"threshold": 5, "alert_duration": "5m"},
        "telegram_rate_limit_hits": {"threshold": 5, "alert_duration": "1m"}
    }
}
```

### Business Metrics (KPI Level)
```python
BUSINESS_METRICS = {
    "user_engagement": {
        "new_user_registrations_per_hour": {"baseline": 5, "low_threshold": 1},
        "daily_active_users": {"baseline": 100, "low_threshold": 50},
        "user_session_duration_minutes": {"baseline": 10, "low_threshold": 3}
    },
    "financial_performance": {
        "orders_per_hour": {"baseline": 10, "low_threshold": 2},
        "revenue_per_hour_idr": {"baseline": 500000, "low_threshold": 100000},
        "average_order_value_idr": {"baseline": 50000, "low_threshold": 25000}
    },
    "operational_health": {
        "fraud_detection_rate": {"baseline": 95, "low_threshold": 90},
        "customer_support_tickets_per_day": {"baseline": 5, "high_threshold": 20},
        "admin_command_execution_rate": {"baseline": 99, "low_threshold": 95}
    }
}
```

---

## 2. Structured Logging Strategy

### Log Levels & Standards
```python
import structlog
from datetime import datetime

# Structured logging configuration
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(30),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
    context_class=structlog.threadlocal.wrap_dict(dict),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Example structured log entry
async def log_payment_event(event_type: str, user_id: int, order_data: dict):
    """Standard payment event logging"""
    await logger.info(
        "payment_event",
        event_type=event_type,
        user_id=user_id,
        order_id=order_data.get("invoice_id"),
        amount=order_data.get("total_bill"),
        payment_method=order_data.get("payment_method"),
        correlation_id=generate_correlation_id(),
        timestamp=datetime.utcnow().isoformat(),
        service="quickcart",
        environment=get_environment()
    )
```

### Log Categories & Retention
| Log Category | Level | Retention Period | Storage Location | Purpose |
|-------------|--------|------------------|------------------|---------|
| **Application Logs** | INFO+ | 30 days | Digital Ocean Logs | General application behavior |
| **Security Logs** | WARN+ | 90 days | Secure log storage | Security events and threats |
| **Audit Logs** | INFO+ | Permanent | Separate audit DB | Compliance and investigation |
| **Performance Logs** | DEBUG | 7 days | Local + remote | Performance optimization |
| **Error Logs** | ERROR+ | 60 days | Alert system + storage | Error tracking and resolution |

### Centralized Logging Architecture
```python
# Digital Ocean centralized logging setup
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/quickcart/app.log",
            "maxBytes": 104857600,  # 100MB
            "backupCount": 10,
            "formatter": "json"
        }
    },
    "loggers": {
        "quickcart": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        }
    }
}
```

---

## 3. Real-time Dashboards & Visualization

### Primary Operations Dashboard
```python
DASHBOARD_PANELS = {
    "system_health": {
        "metrics": ["cpu_usage", "memory_usage", "disk_usage"],
        "time_range": "last_1h",
        "refresh": "30s",
        "alert_indicators": True
    },
    "payment_performance": {
        "metrics": ["payment_success_rate", "payment_response_time", "pakasir_api_status"],
        "time_range": "last_4h", 
        "refresh": "1m",
        "alert_indicators": True
    },
    "user_activity": {
        "metrics": ["active_users", "orders_per_minute", "telegram_messages_sent"],
        "time_range": "last_24h",
        "refresh": "5m",
        "alert_indicators": False
    },
    "fraud_monitoring": {
        "metrics": ["fraud_detection_rate", "manual_review_queue", "blocked_transactions"],
        "time_range": "last_24h",
        "refresh": "2m", 
        "alert_indicators": True
    }
}
```

### Business Intelligence Dashboard
```python
BI_DASHBOARD_PANELS = {
    "revenue_tracking": {
        "metrics": ["daily_revenue", "monthly_revenue", "revenue_per_user"],
        "time_range": "last_30d",
        "refresh": "1h"
    },
    "product_performance": {
        "metrics": ["top_selling_products", "stock_turnover_rate", "product_conversion_rate"], 
        "time_range": "last_7d",
        "refresh": "30m"
    },
    "user_analytics": {
        "metrics": ["user_growth_rate", "customer_lifetime_value", "retention_rate"],
        "time_range": "last_90d",
        "refresh": "24h"
    }
}
```

---

## 4. Intelligent Alerting System

### Alert Severity Levels
```python
ALERT_SEVERITY = {
    "CRITICAL": {
        "examples": ["Payment system down", "Database unavailable", "Security breach"],
        "response_time": "immediate",
        "notification_channels": ["telegram", "email", "sms", "slack"],
        "escalation": "automatic_after_5min"
    },
    "HIGH": {
        "examples": ["High error rate", "Performance degradation", "Fraud spike"],
        "response_time": "5_minutes",
        "notification_channels": ["telegram", "slack"],
        "escalation": "manual_review"
    },
    "MEDIUM": {
        "examples": ["Resource usage spike", "Slow response time", "Queue backup"],
        "response_time": "15_minutes",
        "notification_channels": ["slack"],
        "escalation": "business_hours_only"
    },
    "LOW": {
        "examples": ["Informational alerts", "Trend notifications"],
        "response_time": "1_hour",
        "notification_channels": ["email"],
        "escalation": "none"
    }
}
```

### Smart Alert Configuration
```python
class SmartAlerting:
    """Intelligent alerting with noise reduction"""
    
    def __init__(self):
        self.alert_suppression_rules = {
            "duplicate_window": 300,  # 5 minutes
            "escalation_threshold": 3,  # 3 identical alerts
            "maintenance_mode": False
        }
    
    async def evaluate_alert(self, metric: str, value: float, threshold: float):
        """Evaluate if alert should be sent"""
        
        # Check if in maintenance mode
        if self.alert_suppression_rules["maintenance_mode"]:
            return False
        
        # Check for alert suppression
        if await self.is_alert_suppressed(metric):
            return False
        
        # Apply business context
        alert_context = await self.get_business_context()
        
        if alert_context["business_hours"] and metric in ["user_activity_low"]:
            # Suppress low user activity alerts outside business hours
            return False
        
        # Calculate dynamic threshold based on historical data
        dynamic_threshold = await self.calculate_dynamic_threshold(metric)
        
        if value > dynamic_threshold:
            await self.send_alert(metric, value, dynamic_threshold)
            return True
        
        return False
```

### Alert Notification Templates
```python
ALERT_TEMPLATES = {
    "payment_system_down": {
        "title": "🚨 CRITICAL: Payment System Unavailable",
        "message": """
Payment processing is currently unavailable.
- Pakasir API Status: {pakasir_status}
- Last Successful Payment: {last_payment_time}
- Affected Users: {affected_user_count}
- Estimated Impact: {revenue_impact} IDR/hour

Action Required: Immediate investigation and resolution
War Room: {incident_room_link}
        """,
        "channels": ["telegram_critical", "email_critical", "sms_oncall"]
    },
    "fraud_spike_detected": {
        "title": "⚠️ HIGH: Fraud Activity Spike Detected", 
        "message": """
Unusual fraud activity pattern detected.
- Fraud Attempts: {fraud_count} in last hour
- Success Rate: {fraud_success_rate}%
- Affected Products: {affected_products}
- Risk Score: {average_risk_score}

Action Required: Review fraud detection rules and investigate patterns
Dashboard: {fraud_dashboard_link}
        """,
        "channels": ["telegram_security", "slack_fraud_team"]
    }
}
```

---

## 5. Audit & Compliance Logging

### Compliance Logging Requirements
```python
COMPLIANCE_LOGS = {
    "financial_transactions": {
        "required_fields": ["user_id", "amount", "payment_method", "timestamp", "order_id"],
        "retention": "permanent",
        "encryption": "aes_256",
        "access_control": "compliance_officer_only"
    },
    "data_privacy_events": {
        "required_fields": ["user_id", "data_type", "action", "consent_status"],
        "retention": "7_years",
        "encryption": "aes_256", 
        "access_control": "privacy_officer_only"
    },
    "security_events": {
        "required_fields": ["event_type", "source_ip", "user_id", "outcome"],
        "retention": "5_years",
        "encryption": "aes_256",
        "access_control": "security_team_only"
    }
}
```

### Audit Log Integration
```python
class AuditLogging:
    """Integration with audit database for compliance"""
    
    async def log_compliance_event(self, event_type: str, **kwargs):
        """Log events requiring compliance tracking"""
        
        compliance_entry = {
            "timestamp": datetime.utcnow(),
            "event_type": event_type,
            "service": "quickcart",
            "environment": get_environment(),
            "correlation_id": kwargs.get("correlation_id"),
            "compliance_category": self.get_compliance_category(event_type),
            **kwargs
        }
        
        # Write to audit database
        await self.audit_db.insert("compliance_logs", compliance_entry)
        
        # Also log to operational logs for visibility
        await logger.info("compliance_event", **compliance_entry)
```

---

## 6. Observability in Development & CI/CD

### Pre-Deployment Observability Checks
```python
# CI/CD observability validation
class ObservabilityValidator:
    """Ensure observability hooks in all code"""
    
    REQUIRED_METRICS = [
        "http_request_duration",
        "http_request_count", 
        "database_query_duration",
        "external_api_call_duration"
    ]
    
    REQUIRED_LOG_EVENTS = [
        "user_action",
        "payment_event", 
        "security_event",
        "error_event"
    ]
    
    def validate_code_observability(self, code_changes: list):
        """Validate that new code includes observability"""
        
        validation_results = {}
        
        for file_change in code_changes:
            # Check for metric instrumentation
            has_metrics = self.check_metrics_instrumentation(file_change)
            
            # Check for structured logging
            has_logging = self.check_logging_instrumentation(file_change)
            
            # Check for error handling
            has_error_handling = self.check_error_handling(file_change)
            
            validation_results[file_change.filename] = {
                "metrics": has_metrics,
                "logging": has_logging,
                "error_handling": has_error_handling,
                "overall_pass": has_metrics and has_logging and has_error_handling
            }
        
        return validation_results
```

### Automated Testing for Observability
```python
# Test that observability works correctly
import pytest

class TestObservabilityInstrumentation:
    """Test observability instrumentation"""
    
    @pytest.mark.asyncio
    async def test_payment_metrics_emitted(self, mock_payment_flow):
        """Ensure payment flow emits required metrics"""
        
        # Execute payment flow
        result = await mock_payment_flow.create_payment(
            user_id=12345, 
            product_id=1,
            amount=50000
        )
        
        # Check metrics were emitted
        metrics = await get_emitted_metrics()
        
        assert "payment_request_duration" in metrics
        assert "pakasir_api_call_duration" in metrics
        assert "payment_success_count" in metrics
        
        # Check logs were emitted
        logs = await get_emitted_logs()
        payment_logs = [log for log in logs if log.event_type == "payment_event"]
        
        assert len(payment_logs) >= 2  # Start and completion events
        assert all("correlation_id" in log for log in payment_logs)
```

---

## Cross-References

- See [10-audit_architecture.md](10-audit_architecture.md) for audit database design and compliance requirements
- See [18-infra_plan.md](18-infra_plan.md) for infrastructure monitoring and Digital Ocean observability setup
- See [12-maintenance_plan.md](12-maintenance_plan.md) for operational monitoring procedures and health checks
- See [16-risk_register.md](16-risk_register.md) for risk-based monitoring priorities and alert configuration

---

> Note for AI builders: Observability is critical for payment systems. All payment flows, security events, and system health must be comprehensively monitored. Implement observability-first development practices - if it's not monitored, it doesn't exist. Alert fatigue is dangerous - use intelligent alerting with proper context and noise reduction.