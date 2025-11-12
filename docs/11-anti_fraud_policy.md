# 11. Anti-Fraud Policy
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
This document outlines comprehensive measures, controls, and response strategies to detect and prevent fraudulent activities within QuickCart's digital product sales and payment processing system.

---

## 1. Fraud Risk Assessment

### High-Risk Fraud Scenarios
- **Payment Fraud:** Stolen payment methods, chargeback abuse, double-spending attempts
- **Account Takeover:** Compromised Telegram accounts used for unauthorized purchases
- **Stock Manipulation:** Attempting to purchase products without payment completion
- **Refund Abuse:** Requesting refunds after consuming digital products
- **Reseller Fraud:** Unauthorized access to reseller pricing, fake reseller applications
- **Admin Impersonation:** Social engineering attempts to gain admin privileges

### Attack Vectors
- **Automated Attacks:** Bot networks attempting bulk purchases or stock depletion
- **Social Engineering:** Fake admin requests, fraudulent payment confirmations
- **Technical Exploitation:** API abuse, session hijacking, webhook manipulation
- **Financial Fraud:** Money laundering through small transactions, structuring
- **Identity Fraud:** Using fake or stolen personal information for accounts

### Fraud Impact Categories
```python
FRAUD_IMPACT = {
    "FINANCIAL": {
        "direct_loss": "Unpaid orders, chargebacks, refund abuse",
        "operational_cost": "Investigation time, manual reviews, customer service",
        "reputation": "Customer trust damage, payment provider penalties"
    },
    "OPERATIONAL": {
        "stock_depletion": "Products unavailable for legitimate customers",
        "system_abuse": "Resource consumption, service degradation",
        "compliance_risk": "Regulatory violations, audit findings"
    },
    "STRATEGIC": {
        "business_continuity": "Payment processor termination",
        "legal_liability": "Regulatory fines, customer lawsuits",
        "market_position": "Competitive disadvantage, customer exodus"
    }
}
```

---

## 2. Fraud Detection Controls

### Automated Detection Rules
```python
class FraudDetectionEngine:
    """Real-time fraud detection and scoring"""
    
    DETECTION_RULES = {
        # Velocity-based rules
        "payment_velocity": {
            "threshold": 5,           # Max payments per hour per user
            "window": 3600,          # 1 hour window
            "action": "flag_review",
            "risk_score": 30
        },
        "amount_velocity": {
            "threshold": 5000000,    # 5M IDR per day per user
            "window": 86400,         # 24 hour window
            "action": "block_payment",
            "risk_score": 70
        },
        
        # Amount-based rules
        "large_transaction": {
            "threshold": 1000000,    # 1M IDR single transaction
            "action": "manual_review",
            "risk_score": 40
        },
        "micro_transaction_pattern": {
            "threshold": 10,         # 10+ transactions under 10k IDR
            "amount_limit": 10000,
            "window": 3600,
            "action": "flag_structuring",
            "risk_score": 60
        },
        
        # Behavioral rules
        "new_user_large_purchase": {
            "user_age_threshold": 86400,  # Account < 24 hours
            "amount_threshold": 500000,   # >500k IDR
            "action": "manual_review",
            "risk_score": 50
        },
        "rapid_role_escalation": {
            "condition": "customer_to_reseller_same_day",
            "action": "flag_review",
            "risk_score": 35
        },
        
        # Technical indicators
        "session_anomaly": {
            "multiple_sessions": True,
            "geographic_mismatch": True,
            "device_fingerprint_change": True,
            "action": "require_verification",
            "risk_score": 45
        }
    }
    
    async def evaluate_transaction(self, user_id: int, order_data: Dict) -> Dict:
        """Evaluate transaction for fraud indicators"""
        
        risk_score = 0
        triggered_rules = []
        recommended_action = "approve"
        
        for rule_name, rule_config in self.DETECTION_RULES.items():
            if await self.check_rule(rule_name, user_id, order_data):
                risk_score += rule_config["risk_score"]
                triggered_rules.append(rule_name)
                
                # Determine most restrictive action
                if rule_config["action"] == "block_payment":
                    recommended_action = "block"
                elif rule_config["action"] == "manual_review" and recommended_action != "block":
                    recommended_action = "review"
                elif rule_config["action"] == "flag_review" and recommended_action == "approve":
                    recommended_action = "flag"
        
        # Risk score thresholds
        if risk_score >= 80:
            recommended_action = "block"
        elif risk_score >= 50:
            recommended_action = "review"
        elif risk_score >= 30:
            recommended_action = "flag"
        
        return {
            "risk_score": min(risk_score, 100),  # Cap at 100
            "triggered_rules": triggered_rules,
            "recommended_action": recommended_action,
            "requires_manual_review": risk_score >= 50
        }
```

### Real-time Monitoring
```python
class FraudMonitoring:
    """Continuous fraud monitoring and alerting"""
    
    async def monitor_payment_patterns(self):
        """Monitor for suspicious payment patterns"""
        
        # Check for coordinated attacks
        suspicious_patterns = await self.detect_coordinated_fraud()
        
        # Monitor unusual activity spikes
        activity_anomalies = await self.detect_activity_anomalies()
        
        # Check for payment method abuse
        payment_abuse = await self.detect_payment_abuse()
        
        # Generate alerts for investigation
        for pattern in suspicious_patterns + activity_anomalies + payment_abuse:
            await self.generate_fraud_alert(pattern)
    
    async def detect_coordinated_fraud(self):
        """Detect multiple accounts with similar behavior patterns"""
        
        query = """
            SELECT user_id, COUNT(*) as payment_count, 
                   SUM(total_bill) as total_amount,
                   MIN(created_at) as first_payment,
                   MAX(created_at) as last_payment
            FROM orders 
            WHERE created_at >= NOW() - INTERVAL '1 hour'
            AND status = 'paid'
            GROUP BY user_id
            HAVING COUNT(*) >= 5 OR SUM(total_bill) >= 2000000
        """
        
        suspicious_users = await self.database.fetch_all(query)
        
        # Additional analysis for coordination
        coordinated_groups = []
        for user_data in suspicious_users:
            similar_users = await self.find_similar_behavior_patterns(user_data["user_id"])
            if len(similar_users) >= 3:  # 3+ users with similar patterns
                coordinated_groups.append({
                    "primary_user": user_data["user_id"],
                    "related_users": similar_users,
                    "pattern_type": "coordinated_purchasing",
                    "risk_level": "high"
                })
        
        return coordinated_groups
```

### Machine Learning Fraud Detection
```python
class MLFraudDetection:
    """Machine learning based fraud detection"""
    
    def __init__(self):
        self.model = self.load_fraud_model()
        self.feature_extractors = self.setup_feature_extractors()
    
    async def predict_fraud_probability(self, user_id: int, transaction_data: Dict) -> float:
        """ML-based fraud probability prediction"""
        
        # Extract features for ML model
        features = await self.extract_features(user_id, transaction_data)
        
        # Get prediction from trained model
        fraud_probability = self.model.predict_proba([features])[0][1]
        
        # Log prediction for model improvement
        await self.log_prediction(user_id, features, fraud_probability, transaction_data)
        
        return fraud_probability
    
    async def extract_features(self, user_id: int, transaction_data: Dict) -> List[float]:
        """Extract features for fraud detection model"""
        
        features = []
        
        # User history features
        user_stats = await self.get_user_statistics(user_id)
        features.extend([
            user_stats["account_age_days"],
            user_stats["total_transactions"],
            user_stats["total_spent"],
            user_stats["average_transaction_amount"],
            user_stats["days_since_last_transaction"]
        ])
        
        # Transaction features
        features.extend([
            transaction_data["amount"],
            transaction_data["hour_of_day"],
            transaction_data["day_of_week"],
            len(transaction_data.get("items", [])),
            transaction_data.get("product_category_risk_score", 0)
        ])
        
        # Behavioral features
        recent_behavior = await self.analyze_recent_behavior(user_id)
        features.extend([
            recent_behavior["transaction_frequency_change"],
            recent_behavior["amount_pattern_change"],
            recent_behavior["time_pattern_change"]
        ])
        
        return features
```

---

## 3. Manual Review Process

### Review Queue Management
```python
class FraudReviewQueue:
    """Management of manual fraud review queue"""
    
    PRIORITY_LEVELS = {
        "CRITICAL": {"max_age_hours": 1, "risk_threshold": 80},
        "HIGH": {"max_age_hours": 4, "risk_threshold": 60},
        "MEDIUM": {"max_age_hours": 12, "risk_threshold": 40},
        "LOW": {"max_age_hours": 24, "risk_threshold": 20}
    }
    
    async def add_to_review_queue(self, order_id: str, risk_assessment: Dict):
        """Add transaction to manual review queue"""
        
        priority = self.calculate_priority(risk_assessment)
        
        review_item = {
            "order_id": order_id,
            "risk_score": risk_assessment["risk_score"],
            "triggered_rules": risk_assessment["triggered_rules"],
            "priority": priority,
            "created_at": datetime.utcnow(),
            "status": "pending",
            "assigned_reviewer": None
        }
        
        await self.database.execute(
            "INSERT INTO fraud_review_queue (order_id, risk_data, priority, created_at, status) "
            "VALUES ($1, $2, $3, $4, $5)",
            order_id, json.dumps(risk_assessment), priority, 
            review_item["created_at"], "pending"
        )
        
        # Send alert to review team
        await self.notify_review_team(review_item)
    
    async def process_review_decision(self, review_id: int, decision: str, reviewer_id: int, notes: str):
        """Process manual review decision"""
        
        valid_decisions = ["approve", "decline", "require_additional_verification", "escalate"]
        if decision not in valid_decisions:
            raise ValueError(f"Invalid decision: {decision}")
        
        # Update review record
        await self.database.execute(
            "UPDATE fraud_review_queue SET status = $1, reviewer_id = $2, "
            "decision = $3, review_notes = $4, reviewed_at = $5 WHERE id = $6",
            "completed", reviewer_id, decision, notes, datetime.utcnow(), review_id
        )
        
        # Execute decision
        review_item = await self.get_review_item(review_id)
        await self.execute_review_decision(review_item["order_id"], decision)
        
        # Log decision for audit
        await audit_logger.log_action(
            action="fraud_review_completed",
            entity_type="order",
            entity_id=review_item["order_id"],
            actor_id=reviewer_id,
            actor_type="admin",
            metadata={
                "decision": decision,
                "risk_score": review_item["risk_score"],
                "review_notes": notes
            }
        )
```

### Investigation Tools
```python
class FraudInvestigationTools:
    """Tools for investigating suspicious activities"""
    
    async def investigate_user(self, user_id: int) -> Dict:
        """Comprehensive user investigation"""
        
        investigation_report = {
            "user_profile": await self.get_user_profile(user_id),
            "transaction_history": await self.get_transaction_history(user_id),
            "behavioral_analysis": await self.analyze_user_behavior(user_id),
            "network_analysis": await self.analyze_user_network(user_id),
            "risk_indicators": await self.identify_risk_indicators(user_id),
            "similar_users": await self.find_similar_users(user_id),
            "investigation_timestamp": datetime.utcnow()
        }
        
        # Calculate overall risk assessment
        investigation_report["overall_risk"] = self.calculate_overall_risk(investigation_report)
        
        return investigation_report
    
    async def trace_related_accounts(self, user_id: int) -> List[int]:
        """Find potentially related accounts"""
        
        user_data = await self.get_user_data(user_id)
        related_accounts = []
        
        # Search by shared email
        if user_data.get("email"):
            email_matches = await self.find_users_by_email_pattern(user_data["email"])
            related_accounts.extend(email_matches)
        
        # Search by shared WhatsApp number
        if user_data.get("whatsapp_number"):
            phone_matches = await self.find_users_by_phone(user_data["whatsapp_number"])
            related_accounts.extend(phone_matches)
        
        # Search by behavioral patterns
        behavior_matches = await self.find_users_by_behavior_similarity(user_id)
        related_accounts.extend(behavior_matches)
        
        # Remove duplicates and original user
        return list(set(related_accounts) - {user_id})
```

---

## 4. Incident Response

### Fraud Incident Classification
```python
class FraudIncidentResponse:
    
    INCIDENT_TYPES = {
        "CONFIRMED_FRAUD": {
            "immediate_actions": ["freeze_account", "block_ip", "alert_payment_processor"],
            "investigation_required": True,
            "law_enforcement_threshold": 10000000  # 10M IDR
        },
        "SUSPECTED_FRAUD": {
            "immediate_actions": ["flag_account", "manual_review_all"],
            "investigation_required": True,
            "escalation_time": 24  # hours
        },
        "POLICY_VIOLATION": {
            "immediate_actions": ["warn_user", "temporary_restriction"],
            "investigation_required": False,
            "auto_resolve_time": 72  # hours
        },
        "FALSE_POSITIVE": {
            "immediate_actions": ["remove_flags", "compensate_if_needed"],
            "investigation_required": False,
            "process_improvement": True
        }
    }
    
    async def handle_fraud_incident(self, incident_type: str, incident_data: Dict):
        """Handle fraud incident according to severity"""
        
        incident_config = self.INCIDENT_TYPES.get(incident_type)
        if not incident_config:
            raise ValueError(f"Unknown incident type: {incident_type}")
        
        incident_id = await self.create_incident_record(incident_type, incident_data)
        
        # Execute immediate actions
        for action in incident_config["immediate_actions"]:
            await self.execute_incident_action(action, incident_data)
        
        # Start investigation if required
        if incident_config["investigation_required"]:
            await self.initiate_investigation(incident_id, incident_data)
        
        # Check law enforcement reporting threshold
        if (incident_type == "CONFIRMED_FRAUD" and 
            incident_data.get("financial_impact", 0) >= incident_config["law_enforcement_threshold"]):
            await self.report_to_authorities(incident_id, incident_data)
        
        # Log incident for compliance
        await audit_logger.log_action(
            action="fraud_incident_created",
            entity_type="security_incident",
            entity_id=str(incident_id),
            metadata=incident_data
        )
```

### Communication Protocols
```python
class FraudCommunication:
    """Communication protocols for fraud incidents"""
    
    async def notify_stakeholders(self, incident_id: str, incident_type: str, severity: str):
        """Notify relevant stakeholders of fraud incident"""
        
        notification_config = {
            "CRITICAL": {
                "immediate": ["security_team", "management", "legal"],
                "within_1hr": ["payment_processor", "compliance_officer"],
                "within_24hr": ["all_staff"]
            },
            "HIGH": {
                "immediate": ["security_team", "fraud_analyst"],
                "within_4hr": ["management", "compliance_officer"],
                "within_24hr": ["relevant_staff"]
            },
            "MEDIUM": {
                "immediate": ["fraud_analyst"],
                "within_8hr": ["security_team"],
                "within_48hr": ["management"]
            }
        }
        
        notifications = notification_config.get(severity, notification_config["MEDIUM"])
        
        # Send immediate notifications
        for recipient in notifications.get("immediate", []):
            await self.send_fraud_alert(recipient, incident_id, incident_type, "immediate")
        
        # Schedule delayed notifications
        for delay, recipients in [("within_1hr", "within_1hr"), ("within_4hr", "within_4hr")]:
            if delay in notifications:
                await self.schedule_fraud_notification(
                    recipients=notifications[delay],
                    incident_id=incident_id,
                    delay=delay
                )
    
    async def communicate_with_customer(self, user_id: int, incident_type: str, action_taken: str):
        """Communicate fraud response to affected customer"""
        
        if incident_type == "FALSE_POSITIVE":
            message = "Kami telah meninjau transaksi Anda dan menghapus pembatasan yang salah diterapkan. Mohon maaf atas ketidaknyamanan ini."
        elif action_taken == "account_frozen":
            message = "Akun Anda telah dibekukan sementara karena aktivitas mencurigakan. Tim keamanan akan menghubungi Anda dalam 24 jam."
        elif action_taken == "manual_review":
            message = "Transaksi Anda sedang dalam peninjauan keamanan. Proses akan diselesaikan dalam 1x24 jam."
        else:
            message = "Transaksi Anda telah ditinjau oleh tim keamanan. Terima kasih atas kesabaran Anda."
        
        await self.send_user_notification(user_id, message)
        
        # Log customer communication
        await audit_logger.log_action(
            action="fraud_customer_communication",
            entity_type="user",
            entity_id=str(user_id),
            metadata={
                "incident_type": incident_type,
                "action_taken": action_taken,
                "message_sent": message
            }
        )
```

---

## 5. Reporting & Metrics

### Fraud KPIs and Monitoring
```python
class FraudMetrics:
    """Fraud detection and prevention metrics"""
    
    KEY_METRICS = {
        "detection_rate": "Percentage of fraudulent transactions detected",
        "false_positive_rate": "Percentage of legitimate transactions flagged",
        "response_time": "Average time from detection to resolution",
        "financial_impact": "Total monetary loss due to fraud",
        "prevention_savings": "Estimated losses prevented by detection systems"
    }
    
    async def generate_fraud_dashboard(self, time_period: str = "last_30_days") -> Dict:
        """Generate comprehensive fraud metrics dashboard"""
        
        metrics = {}
        
        # Detection effectiveness
        metrics["detection_stats"] = await self.calculate_detection_stats(time_period)
        
        # Financial impact
        metrics["financial_impact"] = await self.calculate_financial_impact(time_period)
        
        # Response efficiency
        metrics["response_metrics"] = await self.calculate_response_metrics(time_period)
        
        # Trend analysis
        metrics["trends"] = await self.analyze_fraud_trends(time_period)
        
        # Top fraud patterns
        metrics["top_patterns"] = await self.identify_top_fraud_patterns(time_period)
        
        return metrics
    
    async def calculate_detection_stats(self, time_period: str) -> Dict:
        """Calculate fraud detection effectiveness statistics"""
        
        query = """
            SELECT 
                COUNT(*) FILTER (WHERE is_fraud = TRUE) as total_fraud,
                COUNT(*) FILTER (WHERE is_fraud = TRUE AND detected = TRUE) as detected_fraud,
                COUNT(*) FILTER (WHERE is_fraud = FALSE AND detected = TRUE) as false_positives,
                COUNT(*) FILTER (WHERE is_fraud = FALSE) as total_legitimate
            FROM fraud_cases 
            WHERE created_at >= NOW() - INTERVAL '{}'
        """.format(time_period)
        
        result = await self.database.fetch_one(query)
        
        detection_rate = (result["detected_fraud"] / result["total_fraud"] * 100) if result["total_fraud"] > 0 else 0
        false_positive_rate = (result["false_positives"] / result["total_legitimate"] * 100) if result["total_legitimate"] > 0 else 0
        
        return {
            "detection_rate": round(detection_rate, 2),
            "false_positive_rate": round(false_positive_rate, 2),
            "total_fraud_attempts": result["total_fraud"],
            "successful_detections": result["detected_fraud"],
            "false_positives": result["false_positives"]
        }
```

### Continuous Improvement
```python
class FraudPrevention Improvement:
    """Continuous improvement of fraud prevention systems"""
    
    async def analyze_missed_fraud(self) -> List[Dict]:
        """Analyze fraud cases that weren't detected"""
        
        missed_cases = await self.get_missed_fraud_cases()
        
        analysis_results = []
        for case in missed_cases:
            analysis = {
                "case_id": case["id"],
                "why_missed": await self.analyze_why_missed(case),
                "rule_gaps": await self.identify_rule_gaps(case),
                "proposed_improvements": await self.suggest_improvements(case)
            }
            analysis_results.append(analysis)
        
        return analysis_results
    
    async def update_detection_rules(self, improvement_suggestions: List[Dict]):
        """Update fraud detection rules based on analysis"""
        
        for suggestion in improvement_suggestions:
            if suggestion["confidence_score"] >= 0.8:  # High confidence improvements
                await self.implement_rule_update(suggestion)
                await audit_logger.log_action(
                    action="fraud_rule_updated",
                    entity_type="system",
                    entity_id="fraud_detection_engine",
                    metadata=suggestion
                )
            else:
                await self.queue_for_manual_review(suggestion)
```

---

## Cross-References

- See [09-security_manifest.md](09-security_manifest.md) for security controls and threat detection integration
- See [10-audit_architecture.md](10-audit_architecture.md) for fraud investigation audit logging requirements
- See [16-risk_register.md](16-risk_register.md) for fraud-related business risk management

---

> Note for AI builders: Anti-fraud measures must be integrated into every payment flow and admin operation. All fraud-related events must be logged for investigation and compliance. The system should err on the side of caution - it's better to flag a legitimate transaction for review than to miss actual fraud.