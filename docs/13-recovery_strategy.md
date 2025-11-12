# 13. Recovery Strategy
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
Describes comprehensive recovery procedures for QuickCart, ensuring business continuity and minimal downtime in the event of failures, disasters, or data loss. Critical for payment processing systems where data integrity and availability are paramount.

---

## 1. Backup & Restore Strategy

### Backup Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Primary DB    │────│   Backup Agent   │────│  Digital Ocean  │
│  (Operations)   │    │   (pg_dump +     │    │   Spaces        │
└─────────────────┘    │   WAL-E)         │    │  (S3-compatible)│
                       └──────────────────┘    └─────────────────┘
┌─────────────────┐                            ┌─────────────────┐
│   Audit DB      │────────────────────────────│  Separate       │
│  (Permanent)    │                            │  Backup Store   │
└─────────────────┘                            └─────────────────┘
```

### Backup Schedule & Retention

| Component | Backup Type | Frequency | Retention | Storage Location |
|-----------|-------------|-----------|-----------|------------------|
| **Main Database** | Full Backup | Daily at 02:00 UTC | 30 days local, 90 days remote | DO Spaces + Local |
| **Main Database** | Incremental (WAL) | Every 15 minutes | 7 days | DO Spaces |
| **Audit Database** | Full Backup | Daily at 03:00 UTC | Permanent (compliance) | DO Spaces + Archive |
| **Redis State** | Snapshot | Every 6 hours | 48 hours | Local + Remote |
| **Application Config** | Full Backup | On each deployment | 10 versions | Git + DO Spaces |
| **File Uploads** | Incremental | Daily at 04:00 UTC | 30 days | DO Spaces |

### Automated Backup Implementation
```python
class BackupManager:
    """Comprehensive backup management system"""
    
    def __init__(self):
        self.backup_storage = "do_spaces://quickcart-backups/"
        self.retention_policies = {
            "main_db_full": timedelta(days=30),
            "main_db_wal": timedelta(days=7),
            "audit_db": None,  # Permanent retention
            "redis_snapshot": timedelta(days=2),
            "config_files": timedelta(days=90)
        }
    
    async def create_database_backup(self, db_type: str = "main"):
        """Create database backup with verification"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{db_type}_backup_{timestamp}.sql.gz"
        
        try:
            # Create backup
            if db_type == "main":
                command = [
                    "pg_dump", 
                    "--host", os.getenv("DB_HOST"),
                    "--port", os.getenv("DB_PORT"),
                    "--username", os.getenv("DB_USER"),
                    "--dbname", "quickcart_main",
                    "--format", "custom",
                    "--compress", "9",
                    "--file", f"/tmp/{backup_filename}"
                ]
            else:  # audit database
                command = [
                    "pg_dump",
                    "--host", os.getenv("AUDIT_DB_HOST"), 
                    "--username", os.getenv("AUDIT_DB_USER"),
                    "--dbname", "quickcart_audit",
                    "--format", "custom",
                    "--compress", "9",
                    "--file", f"/tmp/{backup_filename}"
                ]
            
            # Execute backup
            result = await asyncio.subprocess.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                raise BackupError(f"Backup failed: {stderr.decode()}")
            
            # Verify backup integrity
            await self.verify_backup_integrity(f"/tmp/{backup_filename}")
            
            # Upload to remote storage
            await self.upload_backup_to_storage(f"/tmp/{backup_filename}", backup_filename)
            
            # Log successful backup
            await audit_logger.log_action(
                action="backup_created",
                entity_type="database",
                entity_id=db_type,
                metadata={
                    "backup_file": backup_filename,
                    "backup_size": os.path.getsize(f"/tmp/{backup_filename}"),
                    "timestamp": timestamp
                }
            )
            
            return backup_filename
            
        except Exception as e:
            await audit_logger.log_action(
                action="backup_failed",
                entity_type="database", 
                entity_id=db_type,
                metadata={"error": str(e), "timestamp": timestamp}
            )
            raise
        
        finally:
            # Clean up local backup file
            if os.path.exists(f"/tmp/{backup_filename}"):
                os.remove(f"/tmp/{backup_filename}")
    
    async def verify_backup_integrity(self, backup_file: str):
        """Verify backup file integrity"""
        # Check if file exists and has content
        if not os.path.exists(backup_file) or os.path.getsize(backup_file) == 0:
            raise BackupError("Backup file is empty or missing")
        
        # Verify PostgreSQL backup format
        command = ["pg_restore", "--list", backup_file]
        result = await asyncio.subprocess.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            raise BackupError(f"Backup file appears corrupted: {stderr.decode()}")
        
        # Verify backup contains expected tables
        expected_tables = ["users", "products", "orders", "product_stocks"]
        backup_content = stdout.decode()
        
        for table in expected_tables:
            if table not in backup_content:
                raise BackupError(f"Backup missing expected table: {table}")
```

### Restore Procedures

#### Database Restore Process
```python
class RestoreManager:
    """Database restore management"""
    
    async def restore_database(self, backup_file: str, target_db: str, restore_type: str = "full"):
        """Restore database from backup with validation"""
        
        # Pre-restore validation
        await self.validate_restore_prerequisites(target_db, backup_file)
        
        try:
            # Create restore point before starting
            restore_point = await self.create_restore_point(target_db)
            
            # Stop application connections
            await self.stop_application_connections()
            
            # Execute restore based on type
            if restore_type == "full":
                await self.execute_full_restore(backup_file, target_db)
            elif restore_type == "point_in_time":
                await self.execute_point_in_time_restore(backup_file, target_db)
            
            # Verify restore integrity
            await self.verify_restore_integrity(target_db)
            
            # Re-enable application connections
            await self.start_application_connections()
            
            # Log successful restore
            await audit_logger.log_action(
                action="database_restored",
                entity_type="database",
                entity_id=target_db,
                metadata={
                    "backup_file": backup_file,
                    "restore_type": restore_type,
                    "restore_point": restore_point
                }
            )
            
        except Exception as e:
            # Rollback to restore point if available
            if restore_point:
                await self.rollback_to_restore_point(target_db, restore_point)
            
            await audit_logger.log_action(
                action="database_restore_failed",
                entity_type="database",
                entity_id=target_db,
                metadata={"error": str(e), "backup_file": backup_file}
            )
            raise RestoreError(f"Database restore failed: {e}")
```

---

## 2. Disaster Recovery

### Recovery Objectives
- **RTO (Recovery Time Objective):** 30 minutes for critical payment functions, 2 hours for full system
- **RPO (Recovery Point Objective):** 15 minutes maximum data loss
- **Service Level Targets:**
  - Payment processing: 99.9% availability (8.77 hours downtime/year)
  - User interface: 99.5% availability (43.83 hours downtime/year)
  - Admin functions: 99% availability (87.66 hours downtime/year)

### Disaster Recovery Architecture
```python
class DisasterRecoveryPlan:
    """Comprehensive disaster recovery implementation"""
    
    DISASTER_SCENARIOS = {
        "regional_outage": {
            "trigger": "Primary region completely unavailable",
            "recovery_method": "failover_to_secondary_region",
            "estimated_rto": 30,  # minutes
            "estimated_rpo": 15   # minutes
        },
        "database_corruption": {
            "trigger": "Primary database corrupted or inaccessible", 
            "recovery_method": "restore_from_backup",
            "estimated_rto": 60,  # minutes
            "estimated_rpo": 60   # minutes (last backup)
        },
        "application_failure": {
            "trigger": "Application containers not responding",
            "recovery_method": "restart_containers",
            "estimated_rto": 5,   # minutes
            "estimated_rpo": 0    # no data loss
        },
        "payment_gateway_failure": {
            "trigger": "Pakasir API unavailable",
            "recovery_method": "queue_payments_resume_when_available",
            "estimated_rto": 0,   # immediate degraded service
            "estimated_rpo": 0    # no data loss
        },
        "security_breach": {
            "trigger": "Confirmed security compromise",
            "recovery_method": "isolate_systems_rebuild_from_clean_backup",
            "estimated_rto": 240, # 4 hours
            "estimated_rpo": 60   # last verified clean backup
        }
    }
    
    async def execute_disaster_recovery(self, scenario: str, severity: str = "high"):
        """Execute disaster recovery plan based on scenario"""
        
        if scenario not in self.DISASTER_SCENARIOS:
            raise ValueError(f"Unknown disaster scenario: {scenario}")
        
        plan = self.DISASTER_SCENARIOS[scenario]
        
        # Log disaster recovery initiation
        await audit_logger.log_action(
            action="disaster_recovery_initiated",
            entity_type="system",
            entity_id="disaster_recovery",
            metadata={
                "scenario": scenario,
                "severity": severity,
                "expected_rto": plan["estimated_rto"],
                "expected_rpo": plan["estimated_rpo"]
            }
        )
        
        # Execute recovery method
        recovery_method = getattr(self, plan["recovery_method"])
        await recovery_method()
        
        # Verify system health post-recovery
        await self.verify_system_health_post_recovery()
        
        # Log disaster recovery completion
        await audit_logger.log_action(
            action="disaster_recovery_completed",
            entity_type="system",
            entity_id="disaster_recovery",
            metadata={"scenario": scenario, "actual_duration": "calculated"}
        )
```

### Failover Procedures
```python
async def failover_to_secondary_region():
    """Failover to secondary Digital Ocean region"""
    
    # 1. Verify secondary region health
    secondary_health = await check_secondary_region_health()
    if not secondary_health["healthy"]:
        raise FailoverError("Secondary region not healthy for failover")
    
    # 2. Sync latest data to secondary region
    await sync_data_to_secondary()
    
    # 3. Update DNS to point to secondary region
    await update_dns_records("quickcart.pots.my.id", "secondary_ip")
    
    # 4. Start services in secondary region
    await start_services_in_secondary_region()
    
    # 5. Verify payment processing works
    await verify_payment_system_health()
    
    # 6. Update monitoring to watch secondary region
    await update_monitoring_targets("secondary_region")
    
    # 7. Notify stakeholders of failover
    await notify_failover_completion()
```

---

## 3. Incident Response Framework

### Incident Response Team Structure
```python
class IncidentResponseTeam:
    """Incident response team coordination"""
    
    ROLES = {
        "incident_commander": {
            "responsibilities": ["Overall coordination", "Decision making", "Stakeholder communication"],
            "primary": "Senior Lead Engineer",
            "backup": "CTO"
        },
        "technical_lead": {
            "responsibilities": ["Technical investigation", "Recovery execution", "System analysis"],
            "primary": "DevOps Lead", 
            "backup": "Backend Lead"
        },
        "communications_lead": {
            "responsibilities": ["User communication", "Status updates", "Media liaison"],
            "primary": "Product Manager",
            "backup": "Customer Success Lead"
        },
        "security_lead": {
            "responsibilities": ["Security analysis", "Breach investigation", "Compliance"],
            "primary": "Security Engineer",
            "backup": "Senior Lead Engineer"
        },
        "business_lead": {
            "responsibilities": ["Business impact assessment", "Priority decisions", "Resource allocation"],
            "primary": "CEO",
            "backup": "CTO"
        }
    }
    
    async def activate_incident_response(self, incident_severity: str):
        """Activate incident response team based on severity"""
        
        if incident_severity in ["P0_CRITICAL", "P1_HIGH"]:
            # Activate full incident response team
            await self.notify_all_roles()
            await self.establish_war_room()
            await self.start_incident_bridge()
        else:
            # Activate minimal team for lower severity
            await self.notify_roles(["technical_lead", "incident_commander"])
```

### Communication Templates
```python
INCIDENT_COMMUNICATION_TEMPLATES = {
    "initial_notification": {
        "internal": """
🚨 INCIDENT ALERT - {severity}

Incident ID: {incident_id}
Detected: {timestamp}
Impact: {user_impact_summary}
Status: {current_status}

Initial Assessment:
{initial_assessment}

Next Update: {next_update_time}
War Room: {war_room_link}
        """,
        "user_facing": """
⚠️ Kami sedang mengalami gangguan teknis yang dapat mempengaruhi {service_impact}.

Status: {user_friendly_status}
Estimasi pemulihan: {estimated_resolution}

Kami akan memberikan update dalam {update_interval}.
Mohon maaf atas ketidaknyamanan ini.
        """
    },
    "progress_update": {
        "internal": """
📊 INCIDENT UPDATE - {incident_id}

Progress: {progress_description}
Actions Taken: {actions_completed}
Current Focus: {current_activities}
Blockers: {current_blockers}

Next Update: {next_update_time}
        """,
        "user_facing": """
🔄 Update gangguan sistem:

Status: {progress_summary}
{additional_user_info}

Update berikutnya: {next_update_time}
        """
    },
    "resolution": {
        "internal": """
✅ INCIDENT RESOLVED - {incident_id}

Resolution Time: {total_duration}
Root Cause: {root_cause_summary}
Services Affected: {affected_services}

Post-Incident Tasks:
- [ ] Post-mortem scheduled
- [ ] Documentation updated
- [ ] Preventive measures identified

Post-mortem: {postmortem_link}
        """,
        "user_facing": """
✅ Gangguan sistem telah teratasi.

Durasi gangguan: {user_friendly_duration}
Semua layanan telah pulih normal.

Terima kasih atas kesabaran Anda.
Kami akan terus meningkatkan sistem untuk mencegah gangguan serupa.
        """
    }
}
```

---

## 4. Recovery Testing & Validation

### Automated Recovery Testing
```python
class RecoveryTesting:
    """Automated recovery procedure testing"""
    
    async def run_quarterly_disaster_drill(self):
        """Comprehensive quarterly disaster recovery drill"""
        
        drill_scenarios = [
            "database_backup_restore",
            "application_failover",
            "payment_system_recovery",
            "security_incident_response"
        ]
        
        drill_results = {}
        
        for scenario in drill_scenarios:
            try:
                start_time = time.time()
                
                # Execute drill scenario
                drill_result = await self.execute_drill_scenario(scenario)
                
                duration = time.time() - start_time
                
                drill_results[scenario] = {
                    "status": "passed",
                    "duration": duration,
                    "details": drill_result
                }
                
            except Exception as e:
                drill_results[scenario] = {
                    "status": "failed", 
                    "error": str(e),
                    "duration": time.time() - start_time
                }
        
        # Generate drill report
        await self.generate_drill_report(drill_results)
        
        # Update recovery procedures based on findings
        await self.update_procedures_from_drill_results(drill_results)
        
        return drill_results
    
    async def validate_backup_restore_capability(self):
        """Test backup and restore procedures monthly"""
        
        # Test backup creation
        backup_file = await backup_manager.create_database_backup("main")
        
        # Test restore to staging environment
        await restore_manager.restore_database(
            backup_file, 
            "quickcart_staging",
            "full"
        )
        
        # Validate data integrity post-restore
        integrity_check = await self.validate_data_integrity("quickcart_staging")
        
        if not integrity_check["passed"]:
            raise ValidationError(f"Data integrity check failed: {integrity_check['errors']}")
        
        return {"status": "passed", "backup_file": backup_file}
```

### Recovery Metrics & KPIs
```python
RECOVERY_METRICS = {
    "backup_success_rate": {
        "target": 99.9,
        "measurement": "percentage of successful daily backups",
        "alert_threshold": 95.0
    },
    "restore_test_success_rate": {
        "target": 100.0,
        "measurement": "percentage of successful monthly restore tests",
        "alert_threshold": 90.0
    },
    "actual_rto": {
        "target": 30,  # minutes
        "measurement": "actual recovery time during incidents",
        "alert_threshold": 60
    },
    "actual_rpo": {
        "target": 15,  # minutes
        "measurement": "actual data loss during incidents", 
        "alert_threshold": 30
    },
    "drill_success_rate": {
        "target": 100.0,
        "measurement": "percentage of successful quarterly drills",
        "alert_threshold": 80.0
    }
}
```

---

## 5. Business Continuity Planning

### Critical Business Functions Priority
```python
BUSINESS_FUNCTION_PRIORITY = {
    "tier_1_critical": {
        "functions": ["Payment processing", "Order fulfillment", "Fraud detection"],
        "max_downtime": 15,  # minutes
        "recovery_order": 1
    },
    "tier_2_important": {
        "functions": ["User registration", "Product catalog", "Admin commands"],
        "max_downtime": 60,  # minutes
        "recovery_order": 2
    },
    "tier_3_standard": {
        "functions": ["Statistics", "Reporting", "Non-critical admin tools"],
        "max_downtime": 240,  # minutes
        "recovery_order": 3
    }
}
```

---

## Cross-References

- See [12-maintenance_plan.md](12-maintenance_plan.md) for routine backup tasks and maintenance procedures
- See [10-audit_architecture.md](10-audit_architecture.md) for audit log backup and recovery requirements
- See [18-infra_plan.md](18-infra_plan.md) for infrastructure redundancy and failover architecture
- See [17-observability.md](17-observability.md) for monitoring during recovery operations

---

> Note for AI builders: Recovery procedures are critical for payment systems. All recovery operations must be tested regularly, fully documented, and executable under stress. Data integrity is paramount - never compromise audit logs or financial transaction data during recovery.