# 10. Audit Architecture
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
Describes comprehensive audit logging and traceability mechanisms for QuickCart, ensuring complete accountability, compliance, and forensic capabilities for all critical operations in a payment processing environment.

---

## 1. Audit Database Design

### Dedicated Audit Database (db_audits)
- **Separation:** Completely separate PostgreSQL instance from operational data
- **Purpose:** Permanent, tamper-resistant audit trail for compliance
- **Access:** Write-only from application, read-only for authorized personnel
- **Security:** Enhanced encryption, restricted network access, separate backups

### Core Audit Tables

#### audit_logs (Primary audit table)
```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Actor information
    actor_id BIGINT,                    -- User/admin who performed action
    actor_type VARCHAR(20) NOT NULL,    -- 'user', 'admin', 'system', 'external'
    actor_context JSONB,               -- Additional actor details (IP, session, etc.)
    
    -- Action details
    action VARCHAR(50) NOT NULL,        -- 'create', 'update', 'delete', 'login', 'payment'
    entity_type VARCHAR(50) NOT NULL,   -- 'user', 'order', 'product', 'payment'
    entity_id VARCHAR(50) NOT NULL,     -- ID of affected entity
    
    -- State information
    before_state JSONB,                 -- Previous values (for updates/deletes)
    after_state JSONB,                  -- New values (for creates/updates)
    
    -- Context and metadata
    correlation_id UUID,               -- Links related actions
    request_id VARCHAR(100),           -- External request identifier
    metadata JSONB,                    -- Additional context (user agent, etc.)
    
    -- Compliance fields
    regulatory_flag BOOLEAN DEFAULT FALSE,  -- Marks entries requiring special retention
    retention_period INTERVAL,        -- Custom retention for specific entries
    
    -- Integrity protection
    checksum VARCHAR(64),              -- SHA-256 of log entry for tamper detection
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Performance and security indexes
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_id, actor_type);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_correlation ON audit_logs(correlation_id);
```

#### payment_audit_logs (Financial transaction specific)
```sql
CREATE TABLE payment_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    audit_log_id BIGINT NOT NULL REFERENCES audit_logs(id),
    
    -- Payment specific fields
    order_id VARCHAR(20) NOT NULL,
    invoice_id VARCHAR(20) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    gateway_response JSONB,            -- Pakasir response data
    
    -- Anti-fraud fields
    risk_score INTEGER,               -- Calculated fraud risk (0-100)
    risk_factors JSONB,               -- Array of risk indicators
    review_required BOOLEAN DEFAULT FALSE,
    
    -- Regulatory compliance
    aml_check_result JSONB,           -- Anti-money laundering check
    pci_compliance_note TEXT,         -- PCI DSS compliance notes
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### admin_action_audit (Admin command tracking)
```sql
CREATE TABLE admin_action_audit (
    id BIGSERIAL PRIMARY KEY,
    audit_log_id BIGINT NOT NULL REFERENCES audit_logs(id),
    
    -- Admin action details
    admin_user_id BIGINT NOT NULL,
    command_executed TEXT NOT NULL,     -- Full command string
    target_user_id BIGINT,             -- User affected by command
    target_entity_type VARCHAR(50),    -- 'product', 'user', 'system'
    target_entity_id VARCHAR(50),
    
    -- Impact assessment
    financial_impact DECIMAL(15,2),    -- Monetary impact if any
    data_sensitivity VARCHAR(20),      -- 'low', 'medium', 'high', 'critical'
    approval_required BOOLEAN DEFAULT FALSE,
    approved_by BIGINT,                -- Admin who approved action
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 2. Log Collection & Storage

### Application-Level Logging Strategy
```python
import asyncio
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any

class AuditLogger:
    """Centralized audit logging with guaranteed delivery"""
    
    def __init__(self, audit_db_pool):
        self.audit_db = audit_db_pool
        self.failed_logs = []  # Store failed logs for retry
        
    async def log_action(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_id: Optional[int] = None,
        actor_type: str = "system",
        before_state: Optional[Dict] = None,
        after_state: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        correlation_id: Optional[str] = None
    ):
        """Log audit event with guaranteed delivery"""
        
        log_entry = {
            "timestamp": datetime.utcnow(),
            "actor_id": actor_id,
            "actor_type": actor_type,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "before_state": before_state,
            "after_state": after_state,
            "correlation_id": correlation_id or self.generate_correlation_id(),
            "metadata": metadata or {}
        }
        
        # Calculate integrity checksum
        log_entry["checksum"] = self.calculate_checksum(log_entry)
        
        # Attempt to write to audit database
        try:
            await self.write_audit_log(log_entry)
        except Exception as e:
            # Store for retry if database write fails
            self.failed_logs.append(log_entry)
            # Log failure to application logs
            logger.error(f"Failed to write audit log: {e}", extra=log_entry)
            
            # Try alternative storage (Redis, file system)
            await self.store_to_backup(log_entry)
    
    async def write_audit_log(self, log_entry: Dict):
        """Write audit log to dedicated audit database"""
        query = """
            INSERT INTO audit_logs (
                timestamp, actor_id, actor_type, action, entity_type, entity_id,
                before_state, after_state, correlation_id, metadata, checksum
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        
        await self.audit_db.execute(
            query,
            log_entry["timestamp"],
            log_entry["actor_id"], 
            log_entry["actor_type"],
            log_entry["action"],
            log_entry["entity_type"],
            log_entry["entity_id"],
            json.dumps(log_entry["before_state"]) if log_entry["before_state"] else None,
            json.dumps(log_entry["after_state"]) if log_entry["after_state"] else None,
            log_entry["correlation_id"],
            json.dumps(log_entry["metadata"]),
            log_entry["checksum"]
        )
```

### Critical Events Requiring Audit Logging
```python
# Comprehensive list of auditable events
AUDIT_EVENTS = {
    # User management
    "user_created": {"entity_type": "user", "sensitivity": "medium"},
    "user_updated": {"entity_type": "user", "sensitivity": "medium"},
    "user_deleted": {"entity_type": "user", "sensitivity": "high"},
    "user_banned": {"entity_type": "user", "sensitivity": "high"},
    "role_changed": {"entity_type": "user", "sensitivity": "high"},
    
    # Financial operations
    "payment_initiated": {"entity_type": "order", "sensitivity": "high"},
    "payment_completed": {"entity_type": "order", "sensitivity": "high"},
    "payment_failed": {"entity_type": "order", "sensitivity": "medium"},
    "refund_issued": {"entity_type": "order", "sensitivity": "high"},
    "balance_modified": {"entity_type": "user", "sensitivity": "critical"},
    
    # Product and inventory
    "product_created": {"entity_type": "product", "sensitivity": "medium"},
    "product_updated": {"entity_type": "product", "sensitivity": "medium"},
    "product_deleted": {"entity_type": "product", "sensitivity": "high"},
    "stock_added": {"entity_type": "product", "sensitivity": "medium"},
    "stock_assigned": {"entity_type": "order", "sensitivity": "high"},
    
    # Security events
    "admin_command_executed": {"entity_type": "system", "sensitivity": "critical"},
    "unauthorized_access_attempt": {"entity_type": "security", "sensitivity": "critical"},
    "rate_limit_exceeded": {"entity_type": "security", "sensitivity": "medium"},
    "session_created": {"entity_type": "user", "sensitivity": "low"},
    "session_expired": {"entity_type": "user", "sensitivity": "low"},
    
    # System operations
    "webhook_received": {"entity_type": "system", "sensitivity": "medium"},
    "webhook_processed": {"entity_type": "system", "sensitivity": "medium"},
    "backup_created": {"entity_type": "system", "sensitivity": "low"},
    "system_maintenance": {"entity_type": "system", "sensitivity": "medium"}
}
```

### Audit Log Triggers (Database Level)
```sql
-- Automatic audit triggers for critical tables
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (
            actor_id, actor_type, action, entity_type, entity_id, before_state
        ) VALUES (
            current_setting('app.user_id', true)::bigint,
            current_setting('app.user_type', true),
            'delete',
            TG_TABLE_NAME,
            OLD.id::text,
            row_to_json(OLD)
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (
            actor_id, actor_type, action, entity_type, entity_id, 
            before_state, after_state
        ) VALUES (
            current_setting('app.user_id', true)::bigint,
            current_setting('app.user_type', true),
            'update',
            TG_TABLE_NAME,
            NEW.id::text,
            row_to_json(OLD),
            row_to_json(NEW)
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (
            actor_id, actor_type, action, entity_type, entity_id, after_state
        ) VALUES (
            current_setting('app.user_id', true)::bigint,
            current_setting('app.user_type', true),
            'create',
            TG_TABLE_NAME,
            NEW.id::text,
            row_to_json(NEW)
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to critical tables
CREATE TRIGGER audit_users_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_orders_trigger
    AFTER INSERT OR UPDATE OR DELETE ON orders
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

---

## 3. Access & Review

### Role-Based Audit Access
```python
class AuditAccessControl:
    ROLES = {
        "audit_viewer": {
            "permissions": ["read_audit_logs"],
            "restrictions": ["no_user_pii", "time_limited"]
        },
        "compliance_officer": {
            "permissions": ["read_audit_logs", "export_audit_data", "generate_reports"],
            "restrictions": ["full_access"]
        },
        "security_admin": {
            "permissions": ["read_audit_logs", "investigate_incidents", "modify_retention"],
            "restrictions": ["security_events_only"]
        },
        "system_admin": {
            "permissions": ["read_audit_logs", "system_maintenance", "backup_restore"],
            "restrictions": ["system_events_only"]
        }
    }
    
    @staticmethod
    def check_audit_access(user_id: int, requested_logs: str, date_range: tuple):
        user_role = get_user_audit_role(user_id)
        
        # Check permissions
        if "read_audit_logs" not in AuditAccessControl.ROLES[user_role]["permissions"]:
            raise PermissionError("No audit access permission")
        
        # Apply role-specific restrictions
        restrictions = AuditAccessControl.ROLES[user_role]["restrictions"]
        
        if "time_limited" in restrictions:
            # Limit to last 30 days for basic viewers
            max_date = datetime.utcnow() - timedelta(days=30)
            if date_range[0] < max_date:
                raise PermissionError("Date range exceeds permission limits")
        
        return True
```

### Automated Review & Alerting
```python
class AuditReviewSystem:
    """Automated audit log analysis and alerting"""
    
    ALERT_RULES = {
        "suspicious_admin_activity": {
            "condition": "admin actions > 50 in 1 hour",
            "severity": "high",
            "notification": ["security_team", "compliance_officer"]
        },
        "mass_data_modification": {
            "condition": "bulk updates/deletes > 100 records",
            "severity": "critical",
            "notification": ["security_team", "system_admin"]
        },
        "payment_anomalies": {
            "condition": "failed payments > 10% in 1 hour",
            "severity": "medium",
            "notification": ["finance_team"]
        },
        "unauthorized_access_pattern": {
            "condition": "failed admin commands > 5 from same user",
            "severity": "high",
            "notification": ["security_team"]
        }
    }
    
    async def run_automated_review(self):
        """Daily automated audit log review"""
        for rule_name, rule_config in self.ALERT_RULES.items():
            try:
                violations = await self.check_rule(rule_config)
                if violations:
                    await self.send_alert(rule_name, violations, rule_config)
            except Exception as e:
                logger.error(f"Failed to check audit rule {rule_name}: {e}")
```

---

## 4. Integration with Other Systems

### Cross-Reference Capabilities
```python
class AuditCrossReference:
    """Link audit logs with operational data and external systems"""
    
    async def trace_order_lifecycle(self, order_id: str):
        """Complete audit trail for an order"""
        query = """
            SELECT al.*, pal.gateway_response, pal.risk_score
            FROM audit_logs al
            LEFT JOIN payment_audit_logs pal ON al.id = pal.audit_log_id
            WHERE al.entity_type = 'order' 
            AND al.entity_id = $1
            ORDER BY al.timestamp
        """
        
        audit_trail = await self.audit_db.fetch_all(query, order_id)
        
        # Enrich with operational data
        order_details = await self.get_order_details(order_id)
        
        return {
            "order": order_details,
            "audit_trail": audit_trail,
            "summary": self.generate_lifecycle_summary(audit_trail)
        }
    
    async def investigate_user_activity(self, user_id: int, date_range: tuple):
        """Complete user activity investigation"""
        user_activities = await self.get_user_audit_logs(user_id, date_range)
        admin_actions = await self.get_admin_actions_on_user(user_id, date_range)
        
        return {
            "user_activities": user_activities,
            "admin_actions": admin_actions,
            "risk_assessment": self.assess_user_risk(user_activities),
            "recommendations": self.generate_recommendations(user_activities)
        }
```

### External System Integration
```python
# Integration with external compliance systems
class ExternalAuditIntegration:
    
    async def export_for_regulatory_compliance(self, start_date: datetime, end_date: datetime):
        """Export audit data for regulatory compliance"""
        
        # Financial transaction logs for tax/AML compliance
        financial_logs = await self.get_financial_audit_logs(start_date, end_date)
        
        # User data handling logs for GDPR compliance
        privacy_logs = await self.get_privacy_audit_logs(start_date, end_date)
        
        # Security incident logs for cybersecurity compliance
        security_logs = await self.get_security_audit_logs(start_date, end_date)
        
        # Format for external systems
        compliance_report = {
            "report_period": {"start": start_date, "end": end_date},
            "financial_transactions": financial_logs,
            "data_privacy_events": privacy_logs,
            "security_incidents": security_logs,
            "integrity_verification": await self.verify_log_integrity(),
            "generated_at": datetime.utcnow()
        }
        
        return compliance_report
```

---

## 5. Compliance & Privacy

### GDPR Audit Considerations
```python
class GDPRAuditCompliance:
    """GDPR-specific audit logging and compliance"""
    
    PII_FIELDS = ["name", "email", "whatsapp_number", "ip_address"]
    
    def anonymize_audit_entry(self, log_entry: Dict) -> Dict:
        """Anonymize PII in audit logs while preserving audit integrity"""
        
        anonymized = log_entry.copy()
        
        # Replace PII with anonymized identifiers
        for field in self.PII_FIELDS:
            if field in anonymized.get("before_state", {}):
                anonymized["before_state"][field] = self.generate_anonymized_id()
            if field in anonymized.get("after_state", {}):
                anonymized["after_state"][field] = self.generate_anonymized_id()
        
        # Mark as anonymized but keep audit trail
        anonymized["metadata"]["gdpr_anonymized"] = True
        anonymized["metadata"]["anonymization_date"] = datetime.utcnow()
        
        return anonymized
    
    async def process_right_to_erasure(self, user_id: int):
        """Process GDPR right to erasure request"""
        
        # 1. Log the erasure request
        await audit_logger.log_action(
            action="gdpr_erasure_requested",
            entity_type="user",
            entity_id=str(user_id),
            metadata={"gdpr_article": "17", "request_type": "right_to_erasure"}
        )
        
        # 2. Anonymize operational data
        await self.anonymize_user_data(user_id)
        
        # 3. Anonymize audit logs (preserve structure, remove PII)
        await self.anonymize_user_audit_logs(user_id)
        
        # 4. Log completion
        await audit_logger.log_action(
            action="gdpr_erasure_completed",
            entity_type="user", 
            entity_id=str(user_id),
            metadata={"completion_date": datetime.utcnow()}
        )
```

### Retention and Archival Policy
```python
class AuditRetentionPolicy:
    """Automated audit log retention and archival"""
    
    RETENTION_RULES = {
        "financial_transactions": timedelta(years=7),  # Legal requirement
        "user_privacy_events": timedelta(years=3),     # GDPR requirement
        "security_incidents": timedelta(years=5),      # Security best practice
        "system_operations": timedelta(years=1),       # Operational needs
        "admin_actions": timedelta(years=10)           # Accountability
    }
    
    async def apply_retention_policy(self):
        """Daily retention policy enforcement"""
        
        for event_category, retention_period in self.RETENTION_RULES.items():
            cutoff_date = datetime.utcnow() - retention_period
            
            # Archive old logs before deletion
            await self.archive_old_logs(event_category, cutoff_date)
            
            # Delete logs past retention period
            await self.delete_expired_logs(event_category, cutoff_date)
            
            # Log retention actions
            await audit_logger.log_action(
                action="retention_policy_applied",
                entity_type="audit_logs",
                entity_id=event_category,
                metadata={
                    "cutoff_date": cutoff_date,
                    "retention_period": str(retention_period)
                }
            )
```

---

## Cross-References

- See [06-data_schema.md](06-data_schema.md) for audit database schema details and table relationships
- See [09-security_manifest.md](09-security_manifest.md) for security event logging requirements and threat detection
- See [11-anti_fraud_policy.md](11-anti_fraud_policy.md) for fraud-specific audit requirements and investigation procedures

---

> Note for AI builders: Audit logging is mandatory for ALL critical operations. Every financial transaction, admin action, and security event must be logged. Audit logs are permanent and tamper-resistant - they cannot be modified or deleted except through automated retention policies. Design all features with audit-first mentality.