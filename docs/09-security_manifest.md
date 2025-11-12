# 09 — Security Manifest
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
Defines comprehensive security policies, controls, and practices for QuickCart to ensure data protection, compliance, and operational integrity in a high-stakes payment processing environment.

---

## 1. Threat Model

### High-Risk Threats
- **Payment Fraud:** Unauthorized payment manipulation, double-spending, chargebacks
- **Account Takeover:** Admin account compromise leading to system control
- **Stock Manipulation:** Unauthorized product/stock modification
- **Data Breach:** Exposure of user PII, payment details, or audit logs
- **API Abuse:** Rate limit bypass, unauthorized access to admin functions

### Attack Surfaces
- **Telegram Bot API:** Public-facing bot accepting user input
- **Pakasir Webhooks:** External payment notifications requiring validation
- **Admin Commands:** Powerful Telegram commands with system-level access
- **Database Layer:** PostgreSQL instances containing sensitive data
- **Redis Cache:** Session data and temporary payment information

### Attack Vectors
- **Social Engineering:** Fraudulent admin requests, fake payment confirmations
- **Injection Attacks:** SQL injection, command injection via bot inputs
- **Session Hijacking:** Redis session manipulation, unauthorized state changes
- **MITM Attacks:** Webhook spoofing, API response tampering
- **Denial of Service:** Resource exhaustion via bot flooding

---

## 2. Authentication & Authorization

### User Authentication
- **Primary Auth:** Telegram user ID (inherent platform security)
- **Session Management:** Redis-based sessions with 24-hour expiry
- **Multi-Factor:** Telegram's built-in 2FA for admin accounts (recommended)
- **Account Recovery:** No password recovery needed (Telegram handles identity)

### Role-Based Access Control (RBAC)
```python
# Permission matrix
PERMISSIONS = {
    "customer": ["view_products", "create_order", "view_own_orders"],
    "reseller": ["view_products", "create_order", "view_own_orders", "access_reseller_prices"],
    "admin": ["*"]  # All permissions including user management, product management
}

# Role verification for admin commands
def check_admin_permission(user_id: int, command: str) -> bool:
    user = get_user(user_id)
    if user.member_status != "admin":
        return False
    return True  # Admins have all permissions
```

### Admin Command Security
- **Whitelist-based:** Only specific Telegram user IDs can execute admin commands
- **Command Validation:** Strict input validation with format checking
- **Audit Logging:** All admin actions logged to permanent audit database
- **Rate Limiting:** Admin commands limited to prevent abuse
- **Command Visibility:** Admin commands are completely hidden from non-admin users (they cannot see these commands exist)

#### Admin Command Logic Example
```python
async def handle_command(user_id: int, command: str, args: str = None):
    """Handle all bot commands with proper access control"""
    
    # Get user from database
    user = await get_user(user_id)
    if not user:
        return await send_message(user_id, "Silakan ketik /start untuk memulai.")
    
    # Define admin commands (completely hidden from non-admins)
    ADMIN_COMMANDS = [
        '/add', '/addstock', '/del', '/delstock', '/delallstock', '/editid',
        '/editcategory', '/editsold', '/disc', '/discat', '/priceress',
        '/exportstock', '/info', '/pm', '/transfer', '/editbalance',
        '/ban', '/unban', '/addadmin', '/rmadmin', '/addreseller', '/rmress',
        '/whitelist', '/rm', '/broadcast', '/setformula', '/version', '/giveaway'
    ]
    
    # Public commands (visible to all users)
    PUBLIC_COMMANDS = ['/start', '/stock', '/order', '/refund', '/reff']
    
    # Check if command is admin-only
    if command in ADMIN_COMMANDS:
        if user.member_status != 'admin':
            # Return NOTHING - non-admins cannot see admin commands exist
            return None
        else:
            # Process admin command
            return await process_admin_command(user_id, command, args)
    
    # Check if command is public
    elif command in PUBLIC_COMMANDS:
        return await process_public_command(user_id, command, args)
    
    # Unknown command
    else:
        return await send_message(user_id, "Perintah tidak dikenali. Ketik /start untuk menu utama.")

async def process_admin_command(user_id: int, command: str, args: str):
    """Process admin commands with validation"""
    
    # Validate command format
    if not args and command in ['/add', '/addstock', '/info', '/pm', '/transfer', '/giveaway']:
        return await send_message(user_id, f"""
Format salah. Contoh penggunaan yang benar:
{command} [arguments]
Gunakan format yang sesuai untuk perintah ini.
        """)
    
    # Special validation for giveaway command
    if command == '/giveaway':
        return await handle_giveaway_command(user_id, args)
    
    # Log admin action to audit database
    await audit_logger.log_action(
        action="admin_command_executed",
        entity_type="system",
        entity_id="admin_command",
        actor_id=user_id,
        actor_type="admin",
        metadata={
            "command": command,
            "arguments": args,
            "timestamp": datetime.utcnow()
        }
    )
    
    # Execute specific admin command
    if command == '/add':
        result = await handle_add_product(user_id, args)
    elif command == '/ban':
        result = await handle_ban_user(user_id, args)
    elif command == '/giveaway':
        result = await handle_giveaway_command(user_id, args)
    # ... other admin commands
    else:
        result = await send_message(user_id, "Perintah admin berhasil diproses.")
    
    # PC-003: Simple admin action logging for review
    await log_admin_action_simple(user_id, command, args, result)
    return result

async def log_admin_action_simple(admin_id: int, command: str, args: str, result: any):
    """PC-003: Simple admin action logging (beginner-friendly)"""
    
    log_entry = {
        "admin_id": admin_id,
        "command": command,
        "arguments": args,
        "timestamp": datetime.utcnow().isoformat(),
        "success": "success" if result else "failed"
    }
    
    # Save to audit database for review
    await audit_database.execute("""
        INSERT INTO admin_action_logs (admin_id, command, arguments, timestamp, success)
        VALUES ($1, $2, $3, $4, $5)
    """, admin_id, command, args, log_entry["timestamp"], log_entry["success"])
    
    # Also save to simple log file for easy reading
    with open("admin_actions.log", "a") as f:
        f.write(f"{log_entry['timestamp']} - Admin {admin_id}: {command} {args} - {log_entry['success']}\n")

async def handle_giveaway_command(user_id: int, args: str):
    """Handle giveaway command with format validation and voucher generation"""
    
    # Validate format: nominal|jumlah
    if '|' not in args:
        return await send_message(user_id, """
❌ Format salah!

**Penggunaan yang benar:**
`/giveaway nominal|jumlah`

**Contoh:**
• `/giveaway 10000|10` - Buat 10 voucher senilai Rp10.000
• `/giveaway 25000|5` - Buat 5 voucher senilai Rp25.000

**Aturan:**
• Nominal: 1.000 - 1.000.000 IDR
• Jumlah: 1 - 100 voucher per giveaway
        """)
    
    try:
        parts = args.split('|')
        if len(parts) != 2:
            raise ValueError("Invalid format")
        
        nominal = int(parts[0])
        jumlah = int(parts[1])
        
        # Validate ranges
        if nominal < 1000 or nominal > 1000000:
            return await send_message(user_id, "❌ Nominal harus antara Rp1.000 - Rp1.000.000")
        
        if jumlah < 1 or jumlah > 100:
            return await send_message(user_id, "❌ Jumlah voucher harus antara 1 - 100")
        
        # Generate vouchers
        voucher_codes = await generate_vouchers(
            amount=nominal,
            quantity=jumlah,
            created_by=user_id
        )
        
        # Broadcast to all users
        total_users = await broadcast_vouchers_to_all_users(voucher_codes, nominal)
        
        # Log admin action
        await audit_logger.log_action(
            action="vouchers_created",
            entity_type="voucher_giveaway",
            entity_id=f"giveaway_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            actor_id=user_id,
            actor_type="admin",
            metadata={
                "voucher_amount": nominal,
                "voucher_quantity": jumlah,
                "total_users_notified": total_users,
                "voucher_codes": voucher_codes
            }
        )
        
        return await send_message(user_id, f"""
✅ **Giveaway berhasil dibuat!**

📊 **Detail Giveaway:**
• Voucher senilai: Rp{nominal:,}
• Jumlah voucher: {jumlah}
• Total disebarkan ke: {total_users} pengguna

🎯 **Kode voucher:** `{', '.join(voucher_codes[:3])}{'...' if len(voucher_codes) > 3 else ''}`

Semua pengguna telah menerima notifikasi giveaway! 🎉
        """)
        
    except ValueError:
        return await send_message(user_id, """
❌ Format angka tidak valid!

**Contoh yang benar:**
• `/giveaway 10000|10`
• `/giveaway 25000|5`

Pastikan menggunakan angka bulat tanpa titik atau koma.
        """)
    except Exception as e:
        await send_message(user_id, f"❌ Terjadi kesalahan: {str(e)}")
        # Log error for debugging
        await audit_logger.log_action(
            action="giveaway_command_failed",
            entity_type="admin_command",
            entity_id="giveaway",
            actor_id=user_id,
            metadata={"error": str(e), "args": args}
        )

async def generate_vouchers(amount: int, quantity: int, created_by: int) -> List[str]:
    """Generate voucher codes securely (PC-002 Best Practice)"""
    import secrets
    import string
    
    voucher_codes = []
    expires_at = datetime.utcnow() + timedelta(days=30)  # 30 days expiry
    
    for _ in range(quantity):
        # Generate unique 8-character voucher code (sufficient for small business)
        # Using cryptographically secure random
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        
        # Ensure uniqueness (very unlikely with 8 chars but good practice)
        while await check_voucher_code_exists(code):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        
        # Save to database
        await database.execute("""
            INSERT INTO vouchers (code, amount, created_by, expires_at)
            VALUES ($1, $2, $3, $4)
        """, code, amount, created_by, expires_at)
        
        voucher_codes.append(code)
    
    return voucher_codes

async def validate_voucher_usage(user_id: int, voucher_code: str) -> bool:
    """PC-002: Check voucher cooldown (5 minutes between usage)"""
    
    # Check if user used any voucher in last 5 minutes
    last_usage = await database.fetchval("""
        SELECT MAX(used_at) FROM vouchers 
        WHERE used_by = $1 AND used_at >= NOW() - INTERVAL '5 minutes'
    """, user_id)
    
    if last_usage:
        time_left = 5 - (datetime.utcnow() - last_usage).total_seconds() / 60
        return False, f"⏰ Tunggu {time_left:.0f} menit lagi sebelum menggunakan voucher."
    
    return True, "OK"

async def broadcast_vouchers_to_all_users(voucher_codes: List[str], amount: int) -> int:
    """Broadcast voucher notification to all users"""
    
    # Get all non-banned users
    users = await database.fetch_all("""
        SELECT id, name FROM users WHERE is_banned = FALSE
    """)
    
    message_text = f"""
🎉 **GIVEAWAY VOUCHER!** 🎊

Kami memberikan voucher diskon untuk semua pengguna!

💰 **Nilai Voucher:** Rp{amount:,}
🎫 **Kode Voucher:** `{voucher_codes[0]}`
⏰ **Berlaku sampai:** {(datetime.utcnow() + timedelta(days=30)).strftime('%d-%m-%Y')}

📋 **Cara Pakai:**
1. Pilih produk yang ingin dibeli
2. Saat checkout, pilih [Gunakan Voucher]
3. Masukkan kode voucher di atas
4. Diskon langsung terpotong!

⚠️ **Syarat:** Satu voucher per pesanan, cooldown 5 menit antar pemakaian.

Selamat berbelanja! 🛍️✨
    """
    
    successful_broadcasts = 0
    
    for user in users:
        try:
            await send_message(user['id'], message_text)
            successful_broadcasts += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            # Log failed broadcast but continue
            logger.warning(f"Failed to send voucher to user {user['id']}: {e}")
    
    return successful_broadcasts
```

---

## 3. Data Protection

### Encryption Standards
- **In Transit:** TLS 1.3 for all external communications (Telegram, Pakasir)
- **At Rest:** PostgreSQL transparent data encryption with AES-256
- **Redis:** Password-protected with AUTH command
- **API Keys:** Environment variables, never in code or logs

### Sensitive Data Handling
```python
# PII data minimization
class UserData:
    required = ["id", "name"]  # Telegram ID + display name only
    optional = ["email", "whatsapp_number"]  # User can choose to provide
    prohibited = ["password", "credit_card", "bank_account"]  # Never collect

# Payment data security
class PaymentData:
    store_locally = ["order_id", "amount", "status", "method"]
    never_store = ["qr_code_content", "bank_details", "card_numbers"]
    audit_required = ["amount_changes", "status_changes", "refunds"]
```

### Data Retention Policies
- **User Data:** Retained until user requests deletion (GDPR compliance)
- **Order Data:** 7 years retention for financial compliance
- **Audit Logs:** Permanent retention (compliance requirement)
- **Session Data:** 24-hour TTL in Redis
- **Payment QR Codes:** Deleted immediately after 10-minute expiry

---

## 4. Secure Coding Practices

### Input Validation
```python
# All user inputs validated before processing
def validate_product_command(command: str) -> bool:
    # Only allow specific patterns for admin commands
    if not re.match(r'^/add \d+\|[^|]+\|[^|]+\|\d+\|.+$', command):
        return False
    return True

# SQL injection prevention
async def get_user_orders(user_id: int):
    # Use parameterized queries exclusively
    query = "SELECT * FROM orders WHERE user_id = $1"
    return await database.fetch_all(query, user_id)
```

### Dependency Management
- **Automated Scanning:** Weekly dependency vulnerability scans
- **Version Pinning:** Lock dependency versions in requirements.txt
- **Security Updates:** Priority patching for critical vulnerabilities
- **Minimal Dependencies:** Only include necessary packages

### Error Handling Security
```python
# Secure error responses - no sensitive data exposure
def handle_payment_error(error: Exception, user_id: int):
    # Log detailed error internally
    logger.error(f"Payment error for user {user_id}: {error}")
    
    # Return generic message to user
    return "Payment processing failed. Please try again or contact support."

# No stack traces in production responses
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return {"error": "Internal server error", "code": 500}
```

---

## 5. Logging & Monitoring

### Security Event Logging
```python
# Critical security events requiring immediate logging
SECURITY_EVENTS = [
    "admin_login",           # Admin user executing commands
    "payment_status_change", # Order status modifications  
    "balance_modification",  # User balance changes
    "role_assignment",       # Member status changes
    "failed_payment",        # Payment failures (potential fraud)
    "rate_limit_exceeded",   # Potential abuse attempts
    "unauthorized_access"    # Invalid admin command attempts
]

# Audit log format for security events
def log_security_event(event_type: str, actor_id: int, **context):
    audit_entry = {
        "timestamp": datetime.utcnow(),
        "event_type": event_type,
        "actor_id": actor_id,
        "actor_type": get_user_role(actor_id),
        "context": context,
        "ip_address": get_user_ip(actor_id),  # If available
        "correlation_id": generate_correlation_id()
    }
    audit_database.insert("security_events", audit_entry)
```

### Anomaly Detection
```python
# Automated fraud detection rules
async def check_payment_anomalies(user_id: int, amount: float):
    # Check for suspicious patterns
    recent_payments = await get_recent_payments(user_id, hours=1)
    
    if len(recent_payments) > 5:  # Too many payments
        await flag_suspicious_activity(user_id, "high_frequency_payments")
    
    if amount > 1000000:  # Large payment amount
        await flag_suspicious_activity(user_id, "large_payment_amount")
    
    # Check velocity limits
    total_recent = sum(p.amount for p in recent_payments)
    if total_recent > 5000000:  # 5M IDR per hour limit
        await flag_suspicious_activity(user_id, "payment_velocity_exceeded")
```

### Alert Thresholds
- **Failed Login Attempts:** > 10 failed admin commands per user per hour
- **Payment Anomalies:** Large amounts (>1M IDR) or high frequency (>5/hour)
- **API Errors:** > 5% error rate for 5+ minutes
- **Database Anomalies:** Unauthorized table access, mass data changes
- **System Anomalies:** High CPU/memory usage, unusual network activity

---

## 6. Compliance & Privacy

### GDPR Compliance
```python
# Right to erasure implementation
async def process_gdpr_deletion(user_id: int):
    # 1. Anonymize personal data in operational database
    await anonymize_user_data(user_id)
    
    # 2. Preserve audit logs but anonymize PII
    await anonymize_audit_logs(user_id)
    
    # 3. Remove from cache/sessions
    await clear_user_sessions(user_id)
    
    # 4. Note: Financial records retained per legal requirements
    await mark_user_deleted(user_id)
```

### Data Subject Rights
- **Access:** Users can request their complete data via bot command
- **Rectification:** Users can update optional fields (email, WhatsApp)
- **Erasure:** Anonymization process while preserving audit integrity
- **Portability:** Export user data in JSON format
- **Objection:** Users can opt out of optional data collection

### Financial Compliance
- **Record Keeping:** 7-year retention for all financial transactions
- **Anti-Money Laundering:** Transaction monitoring and reporting thresholds
- **Tax Compliance:** Detailed transaction records for tax authorities
- **Audit Trail:** Immutable audit logs for financial audits

---

## 7. Security Testing

### Automated Security Testing
```bash
# Static code analysis
bandit -r src/ -f json -o security_report.json

# Dependency vulnerability scanning  
safety check --json

# SQL injection testing
sqlmap -u "http://localhost:8000/api" --batch

# OWASP ZAP baseline scan
zap-baseline.py -t http://localhost:8000
```

### Manual Security Testing
- **Monthly:** Penetration testing of bot commands and API endpoints
- **Quarterly:** Social engineering simulation for admin accounts
- **Semi-Annual:** Full security audit by external firm
- **Ad-hoc:** Security review for all major feature releases

### Testing Checklist
- [ ] Input validation bypass attempts
- [ ] Authentication/authorization circumvention
- [ ] SQL injection and NoSQL injection testing
- [ ] Cross-site scripting (XSS) in message content
- [ ] API rate limiting and abuse testing
- [ ] Session management and fixation testing
- [ ] Privilege escalation attempts
- [ ] Data exposure in error messages

---

## 8. Incident Response

### Detection & Alerting
```python
# Security incident detection
class SecurityIncident:
    SEVERITY_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    @staticmethod
    async def detect_and_alert(event_type: str, severity: str, details: dict):
        incident = {
            "id": generate_incident_id(),
            "timestamp": datetime.utcnow(),
            "type": event_type,
            "severity": severity,
            "details": details,
            "status": "DETECTED"
        }
        
        # Log to audit database
        await log_security_incident(incident)
        
        # Alert based on severity
        if severity in ["HIGH", "CRITICAL"]:
            await notify_security_team(incident)
            await escalate_to_admin(incident)
```

### Response Procedures
1. **Immediate Response (0-15 minutes)**
   - Detect and classify incident severity
   - Isolate affected systems if needed
   - Notify incident response team

2. **Investigation (15-60 minutes)**
   - Analyze audit logs and system state
   - Identify attack vectors and impact scope
   - Document findings and evidence

3. **Containment (60-240 minutes)**
   - Block malicious activity
   - Patch vulnerabilities if identified
   - Implement temporary protective measures

4. **Recovery (4-24 hours)**
   - Restore normal operations
   - Verify system integrity
   - Monitor for recurring issues

5. **Post-Incident (24-72 hours)**
   - Complete incident analysis report
   - Update security procedures
   - Implement prevention measures

### Escalation Contacts
- **Security Team Lead:** Primary contact for all incidents
- **System Administrator:** Infrastructure and database issues  
- **Legal/Compliance:** Data breach or regulatory issues
- **External Support:** Pakasir support, Telegram support if needed

---

## Cross-References

- See [10-audit_architecture.md](10-audit_architecture.md) for detailed audit logging implementation and compliance requirements
- See [11-anti_fraud_policy.md](11-anti_fraud_policy.md) for fraud detection rules and response procedures
- See [13-recovery_strategy.md](13-recovery_strategy.md) for disaster recovery and business continuity planning

---

> Note for AI builders: Security is non-negotiable in payment processing systems. Every feature must be designed with security-first principles. All user inputs must be validated, all sensitive operations must be logged, and all failures must be handled gracefully without exposing system internals.