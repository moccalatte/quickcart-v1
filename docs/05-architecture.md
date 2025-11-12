# 05 — Solution Architecture
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
Describes the high-level technical architecture, core components, and their interactions for QuickCart. This document ensures all contributors and AI builders understand the system's structure and integration points for zero-ambiguity implementation.

---

## System Overview
- **System type:** Telegram bot-based digital product sales platform with automated order fulfillment
- **Architecture style:** Containerized monolith with clear separation of concerns and external service integrations
- **Key components:** FastAPI backend, PostgreSQL databases, Redis cache/queue, Pakasir payment integration, Docker deployment

### Architecture Diagram
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram      │    │   Digital Ocean  │    │   Pakasir       │
│   Bot API       │◄──►│   Droplet        │◄──►│   Payment       │
└─────────────────┘    └──────────────────┘    │   Gateway       │
                                 │              └─────────────────┘
                                 ▼
                        ┌─────────────────┐
                        │   FastAPI       │
                        │   Application   │
                        │   (Docker)      │
                        └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
            ┌─────────────┐ ┌──────────┐ ┌────────────┐
            │ PostgreSQL  │ │  Redis   │ │PostgreSQL  │
            │ Main DB     │ │ Cache/   │ │ Audit DB   │
            │ (Store)     │ │ Queue    │ │(Permanent) │
            └─────────────┘ └──────────┘ └────────────┘
```

---

## Component Descriptions

### FastAPI Backend Service
- **Technology:** Python FastAPI with async/await for high concurrency
- **Responsibilities:** 
  - Telegram webhook processing and response generation
  - Business logic orchestration (orders, payments, stock management)
  - Session state management via Redis
  - Payment processing coordination with Pakasir
  - Admin command execution and validation
- **Deployment:** Docker container on Digital Ocean droplet
- **Scalability:** Stateless design enables horizontal scaling behind load balancer

### Database Layer

#### PostgreSQL Main Database (db_store1)
- **Purpose:** Operational data storage for users, products, orders, stock
- **Schema:** Users, products, product_stocks, orders, order_items tables
- **Features:** ACID transactions, row-level locking for stock consistency
- **Backup:** Daily full + hourly incremental backups with 30-day retention

#### PostgreSQL Audit Database (db_audits) 
- **Purpose:** Permanent, immutable audit trail for compliance
- **Schema:** Audit logs with timestamp, actor, action, entity, before/after state
- **Features:** Write-only access, separate from operational DB for security
- **Retention:** Permanent storage, never deleted for regulatory compliance

#### Redis Cache & Job Queue (CR-003 Best Practice: Secure Sessions)
- **Session Management:** Secure sessions with TTL and encryption
- **Caching:** Product stock counts, user stats, pagination data  
- **Job Queue:** Payment expiry tasks, notification queues, retry mechanisms
- **Rate Limiting:** User action throttling and abuse prevention

**Session Security Implementation:**
```python
# Simple but secure session management
class SecureRedisSession:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.session_ttl = 86400  # 24 hours (beginner-friendly: 1 day)
    
    async def save_session(self, user_id: int, session_data: dict):
        """Save user session securely"""
        key = f"session:{user_id}"
        
        # Don't store sensitive data (order amounts, payment info)
        safe_data = {
            "current_flow": session_data.get("current_flow"),  # "ordering", "deposit"
            "current_step": session_data.get("current_step"),  # "selecting_product"
            "product_id": session_data.get("product_id"),      # Which product user viewing
            "last_activity": datetime.utcnow().isoformat()
        }
        
        # Save with automatic expiry (24 hours)
        await self.redis.setex(key, self.session_ttl, json.dumps(safe_data))
    
    async def get_session(self, user_id: int):
        """Get user session safely"""
        key = f"session:{user_id}"
        data = await self.redis.get(key)
        
        if data:
            return json.loads(data)
        return None  # Session expired or doesn't exist
    
    async def clear_session(self, user_id: int):
        """Clear user session (logout/security)"""
        key = f"session:{user_id}"
        await self.redis.delete(key)
```

**Redis Security Config:**
```bash
# Set Redis password (environment variable)
REDIS_PASSWORD=your_strong_password_here

# Redis connection with auth
redis://username:password@localhost:6379
```

### External Integrations

#### Pakasir Payment Gateway Integration
- **Method:** QRIS-only payment processing (simple and reliable)
- **Integration:** REST API for payment creation, webhook for completion
- **Fee Structure:** 0.7% + Rp310 (auto-calculated and shown to users)
- **Features:** 10-minute payment expiry, automatic QR generation
- **Security:** API key authentication, webhook signature validation
- **Downtime Handling:** Bot detects Pakasir down, notifies admins, shows user-friendly message

#### Telegram Bot API
- **Communication:** Bi-directional messaging, file delivery, notification broadcasting
- **Rate Limits:** 30 messages/second, handled with queuing
- **Features:** Inline keyboards, reply keyboards, sticker support
- **Error Handling:** Exponential backoff for failed messages

---

## Data Flow

### Order Processing Flow
```
User Input → Session Validation → Business Logic → Database Transaction → 
External API Call → Response Generation → Telegram Response
```

### Payment Flow
```
Payment Initiation → Pakasir API → QR Code Display → 10-min Timer Setup → 
Webhook Receipt → Payment Validation → Stock Assignment → Content Delivery
```

### Audit Flow
```
Critical Action → Audit Log Entry → Separate DB Write → 
(Parallel to main operation, never blocks user flow)
```

---

## Security Considerations

### Authentication & Authorization
- **User Auth:** Telegram user ID-based authentication (built-in security)
- **Role-based Access:** Member status (customer/reseller/admin) controls feature access
- **Admin Commands:** Telegram user ID whitelist validation
- **API Security:** Pakasir webhook signature validation

### Data Protection
- **Encryption in Transit:** TLS 1.3 for all external communications
- **Encryption at Rest:** PostgreSQL transparent data encryption
- **Secrets Management:** Environment variables with Docker secrets
- **PII Handling:** Minimal data collection, user consent for optional fields

### Session Security
- **State Management:** Redis with TTL expiration for abandoned sessions
- **Race Condition Prevention:** Atomic Redis operations with MULTI/EXEC
- **Input Validation:** All user input sanitized and validated before processing

---

## Scalability & Reliability

### Horizontal Scaling Strategy
- **Stateless Backend:** FastAPI instances can be load-balanced
- **Database Scaling:** PostgreSQL read replicas for read-heavy operations
- **Cache Distribution:** Redis Cluster for high-availability caching
- **Queue Processing:** Multiple workers for background job processing

### High Availability Design
- **Health Checks:** `/health` endpoint for container orchestration
- **Graceful Degradation:** Core functions continue if non-critical services fail
- **Circuit Breakers:** Pakasir API calls with fallback mechanisms
- **Retry Logic:** Exponential backoff for transient failures

### Performance Optimization
- **Database Indexing:** Strategic indexes on high-query columns
- **Connection Pooling:** PostgreSQL and Redis connection pools
- **Async Processing:** Non-blocking I/O for all external API calls
- **Caching Strategy:** Multi-layer caching (Redis + application level)

---

## Monitoring & Observability

### Application Metrics
- **Response Time:** P95/P99 latency tracking for all endpoints
- **Error Rates:** Failed API calls, database errors, payment failures
- **Business Metrics:** Orders/hour, conversion rates, payment success rates
- **System Metrics:** CPU/memory usage, database connections, queue lengths

### Logging Strategy
- **Structured Logs:** JSON format with correlation IDs
- **Log Levels:** ERROR for failures, WARN for retries, INFO for business events
- **Audit Logs:** Separate permanent logging for all critical operations
- **Performance Logs:** Slow query detection and optimization

---

## Cross-References
- See [06-data_schema.md](06-data_schema.md) for complete database entity definitions and relationships.
- See [07-api_contracts.md](07-api_contracts.md) for Pakasir integration details and internal API specifications.
- See [09-security_manifest.md](09-security_manifest.md) for comprehensive security controls and threat mitigation.
- See [10-audit_architecture.md](10-audit_architecture.md) for detailed audit log design and compliance requirements.

---

> Note for AI builders: This architecture prioritizes reliability and audit compliance over complexity. Every critical operation must be logged, every external dependency must have fallback handling, and every user interaction must be consistent regardless of system load.