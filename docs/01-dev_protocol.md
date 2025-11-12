# 01. Development Protocol
**Version:** 1.0  
**Author:** Senior Lead Engineer  
**Last Updated:** 2025-11-12

## Purpose
Defines the development standards, workflows, and tools for QuickCart Telegram bot project, ensuring consistency, quality, and zero-ambiguity implementation throughout the project lifecycle.

---

## 1. Coding Standards

### Primary Technology Stack
- **Backend:** Python 3.11+ with FastAPI framework
- **Database:** PostgreSQL 15+ (main + separate audit database)
- **Cache/Queue:** Redis 7+ for session management and job queues
- **Deployment:** Docker containers on Digital Ocean droplets
- **External APIs:** Telegram Bot API, Pakasir payment gateway

### Code Craftsmanship Standards
- **Philosophy:** Write code like a senior engineer - elegant, intuitive, and inevitable
- **Python Standards:** PEP 8 with Black formatter (line length: 88)
- **Quality Tools:** Flake8, mypy for type checking, bandit for security
- **Import Organization:** isort with profile black
- **Documentation:** Self-explanatory code with strategic comments

#### Senior Engineer Code Principles
```python
# ❌ Bad: AI-like, hardcoded, messy
async def create_order(user_id, product_id, quantity, payment_method="qris"):
    if payment_method == "qris":
        # hardcoded logic here
        result = some_complex_logic()
        return result
    else:
        # more hardcoded stuff
        pass

# ✅ Good: Clean, intentional, maintainable
class OrderCreationService:
    """Handles order creation with clean separation of concerns."""
    
    def __init__(self, stock_service: StockService, fraud_detector: FraudDetector):
        self._stock_service = stock_service
        self._fraud_detector = fraud_detector
    
    async def create_order(
        self,
        customer: Customer,
        product: Product,
        quantity: int,
        payment_method: PaymentMethod
    ) -> OrderResult:
        """Create order with comprehensive validation and fraud detection.
        
        This method orchestrates the entire order creation process:
        1. Validates customer eligibility and product availability
        2. Performs fraud detection checks
        3. Reserves stock atomically
        4. Creates order record with audit trail
        
        Args:
            customer: Validated customer instance
            product: Product to purchase
            quantity: Items to order (must be positive)
            payment_method: How customer will pay
            
        Returns:
            OrderResult containing order details and next actions
            
        Raises:
            OrderCreationError: When order cannot be created
        """
        await self._validate_order_preconditions(customer, product, quantity)
        
        fraud_assessment = await self._fraud_detector.assess_risk(
            customer, product, quantity
        )
        
        if fraud_assessment.requires_review:
            return OrderResult.requiring_manual_review(fraud_assessment)
        
        return await self._execute_order_creation(
            customer, product, quantity, payment_method
        )
    
    async def _validate_order_preconditions(
        self, customer: Customer, product: Product, quantity: int
    ) -> None:
        """Validate that order can be created."""
        if customer.is_banned:
            raise CustomerBannedError(f"Customer {customer.id} is banned")
        
        if not product.is_available:
            raise ProductUnavailableError(f"Product {product.id} not available")
        
        if quantity <= 0:
            raise InvalidQuantityError("Quantity must be positive")
        
        available_stock = await self._stock_service.get_available_count(product.id)
        if quantity > available_stock:
            raise InsufficientStockError(
                f"Requested {quantity}, available {available_stock}"
            )
```

#### Code Organization Principles
1. **Single Responsibility:** Each class/function has one clear purpose
2. **Dependency Injection:** Never hardcode dependencies
3. **Domain-Driven Design:** Code reflects business concepts
4. **Error Handling:** Explicit, typed exceptions with clear messages
5. **Testability:** Every component easily mockable and testable

#### Architecture Patterns for Clean Code

**1. Service Layer Pattern**
```python
# Clean separation between API, business logic, and data access
class OrderService:
    def __init__(self, repository: OrderRepository, payment_gateway: PaymentGateway):
        self._repository = repository
        self._payment_gateway = payment_gateway

class OrderController:
    def __init__(self, order_service: OrderService):
        self._order_service = order_service
    
    async def create_order(self, request: CreateOrderRequest) -> OrderResponse:
        # Controller only handles HTTP concerns, delegates business logic
        try:
            order = await self._order_service.create_order(request.to_domain())
            return OrderResponse.from_domain(order)
        except OrderCreationError as e:
            return ErrorResponse.from_exception(e)
```

**2. Value Objects for Type Safety**
```python
# ❌ Avoid: Primitive obsession
def calculate_price(user_type: str, base_price: float, quantity: int) -> float:
    # Brittle, error-prone

# ✅ Use: Strong typing with value objects
@dataclass(frozen=True)
class Price:
    amount: Decimal
    currency: str = "IDR"
    
    def multiply(self, quantity: int) -> "Price":
        return Price(self.amount * quantity, self.currency)

@dataclass(frozen=True)  
class Quantity:
    value: int
    
    def __post_init__(self):
        if self.value <= 0:
            raise InvalidQuantityError("Quantity must be positive")

class PricingService:
    def calculate_total(self, customer: Customer, product: Product, quantity: Quantity) -> Price:
        base_price = self._get_customer_price(customer, product)
        return base_price.multiply(quantity.value)
```

**3. Command Pattern for Actions**
```python
# Clean, testable, auditable actions
class CreateOrderCommand:
    def __init__(self, customer_id: int, product_id: int, quantity: int):
        self.customer_id = customer_id
        self.product_id = product_id
        self.quantity = quantity

class CreateOrderHandler:
    async def handle(self, command: CreateOrderCommand) -> OrderResult:
        # Single responsibility: handle this specific command
        customer = await self._customer_service.get_by_id(command.customer_id)
        product = await self._product_service.get_by_id(command.product_id)
        
        return await self._order_service.create_order(
            customer, product, Quantity(command.quantity)
        )
```

**4. Factory Pattern for Complex Object Creation**
```python
class PaymentFactory:
    """Creates appropriate payment strategy based on method."""
    
    def __init__(self, pakasir_service: PakasirService, balance_service: BalanceService):
        self._pakasir_service = pakasir_service
        self._balance_service = balance_service
    
    def create_payment_processor(self, method: PaymentMethod) -> PaymentProcessor:
        match method:
            case PaymentMethod.QRIS:
                return QRISPaymentProcessor(self._pakasir_service)
            case PaymentMethod.ACCOUNT_BALANCE:
                return BalancePaymentProcessor(self._balance_service)
            case _:
                raise UnsupportedPaymentMethodError(f"Method {method} not supported")
```

### Branching Strategy
- **Main Branch:** `main` - production-ready code only
- **Feature Branches:** `feature/payment-integration`, `feature/admin-commands`
- **Hotfix Branches:** `hotfix/security-patch`, `hotfix/payment-bug`
- **No Direct Commits:** All changes via Pull Requests with review

### Commit Message Conventions
```
feat: add QRIS payment integration with Pakasir gateway
fix: resolve stock race condition in concurrent orders
security: implement rate limiting for admin commands
docs: update API contracts for webhook handling
refactor: optimize database queries for product listing
test: add integration tests for payment expiry flow
```

---

## 2. Development Workflow

### Issue Tracking & Project Management
- **Platform:** GitHub Issues with project boards
- **Labels:** `feature`, `bug`, `security`, `documentation`, `technical-debt`
- **Priority:** `P0-critical`, `P1-high`, `P2-medium`, `P3-low`
- **Components:** `payment`, `bot-interface`, `admin`, `database`, `security`

### Ticket Lifecycle
```
Backlog → To Do → In Progress → Code Review → Testing → Done → Deployed
```

### Code Review Process
- **Minimum 1 Reviewer:** Senior developer or tech lead approval required
- **Automated Checks:** All CI/CD checks must pass before merge
- **Review Checklist:**
  - [ ] Code follows senior engineering standards (not AI-generated patterns)
  - [ ] No hardcoded values, magic numbers, or string literals
  - [ ] Clean architecture with proper separation of concerns
  - [ ] All functions have single responsibility and clear naming
  - [ ] Proper error handling with typed exceptions
  - [ ] Tests cover new functionality (unit + integration)
  - [ ] Database changes include migration scripts
  - [ ] API changes documented in relevant files
  - [ ] Security implications reviewed (especially for payment/admin features)
  - [ ] Audit logging implemented for all critical operations

#### Anti-Patterns to Avoid (Common in AI-Generated Code)

**❌ Avoid These Patterns:**
```python
# 1. God functions that do everything
async def handle_telegram_update(update):
    if update.message.text == "/start":
        # 50 lines of hardcoded logic
    elif update.message.text == "/order":
        # 50 more lines of hardcoded logic
    # ... endless elif chain

# 2. Magic strings and numbers everywhere
if user.status == "customer":  # What other statuses exist?
    price = base_price * 1.0  # Why 1.0?
elif user.status == "reseller":
    price = base_price * 0.9  # Where does 0.9 come from?

# 3. Primitive obsession
def create_user(user_id: int, name: str, status: str, balance: float):
    # What's a valid status? What currency is balance?

# 4. No error handling strategy
async def process_payment():
    result = await payment_api.charge()
    return result  # What if API fails?
```

**✅ Senior Engineer Patterns:**
```python
# 1. Single-responsibility handlers with clear delegation
class TelegramUpdateRouter:
    def __init__(self, command_handlers: Dict[str, CommandHandler]):
        self._handlers = command_handlers
    
    async def route_update(self, update: TelegramUpdate) -> None:
        command = self._extract_command(update)
        handler = self._handlers.get(command.type)
        
        if not handler:
            await self._handle_unknown_command(update, command)
            return
        
        await handler.handle(command)

# 2. Configuration-driven, explicit constants
class PricingConfig:
    CUSTOMER_MULTIPLIER = Decimal("1.0")
    RESELLER_DISCOUNT = Decimal("0.1")  # 10% discount for resellers
    
    @classmethod
    def get_multiplier_for_customer_type(cls, customer_type: CustomerType) -> Decimal:
        match customer_type:
            case CustomerType.CUSTOMER:
                return cls.CUSTOMER_MULTIPLIER
            case CustomerType.RESELLER:
                return cls.CUSTOMER_MULTIPLIER - cls.RESELLER_DISCOUNT
            case _:
                raise UnsupportedCustomerTypeError(f"Unknown type: {customer_type}")

# 3. Strong typing with domain objects
class CustomerCreationRequest:
    def __init__(self, telegram_id: TelegramId, name: CustomerName, 
                 member_status: MemberStatus, initial_balance: Money):
        self.telegram_id = telegram_id
        self.name = name
        self.member_status = member_status
        self.initial_balance = initial_balance

# 4. Comprehensive error handling with recovery strategies
class PaymentProcessor:
    async def process_payment(self, payment_request: PaymentRequest) -> PaymentResult:
        try:
            result = await self._payment_gateway.charge(payment_request)
            return PaymentResult.success(result)
        except PaymentGatewayUnavailableError as e:
            await self._metrics.increment("payment_gateway_unavailable")
            return PaymentResult.retry_later("Gateway temporarily unavailable")
        except InsufficientFundsError as e:
            return PaymentResult.failure("Insufficient funds", recoverable=False)
        except PaymentGatewayError as e:
            await self._alert_service.notify_ops(f"Payment gateway error: {e}")
            return PaymentResult.failure("Payment processing error", recoverable=True)
```

#### Code Quality Gates
1. **No TODO comments in production code** - Convert to tracked issues
2. **No commented-out code** - Use version control instead
3. **No print() statements** - Use proper logging
4. **No global variables** - Use dependency injection
5. **No deep nesting** - Extract functions, use guard clauses
6. **No long parameter lists** - Use value objects or builders

---

## 🔥 Senior Lead Engineer Review Criteria

> **WARNING:** The senior lead engineer will review ALL code and has ZERO tolerance for:
> - AI-generated boilerplate code
> - Hardcoded magic numbers or strings  
> - Overly complex solutions to simple problems
> - Copy-paste programming
> - Code that "just works" without elegance

### **Instant Rejection Triggers:**

**❌ These Will Get Your PR Rejected Immediately:**
```python
# 1. Hardcoded configuration
TELEGRAM_TOKEN = "123456789:ABCDEFGH..."  # NEVER!
DATABASE_URL = "postgresql://user:pass@localhost/db"  # NEVER!

# 2. AI-style verbose comments explaining obvious things
def add_numbers(a: int, b: int) -> int:
    """
    This function takes two integer parameters a and b
    and returns their sum by adding them together using
    the + operator in Python programming language.
    """
    return a + b  # Return the sum of a and b

# 3. Overkill patterns for simple operations
class NumberAdderFactory:
    def create_number_adder(self) -> INumberAdder:
        return ConcreteNumberAdder()
        
class INumberAdder(ABC):
    @abstractmethod
    def add(self, a: int, b: int) -> int: pass
        
class ConcreteNumberAdder(INumberAdder):
    def add(self, a: int, b: int) -> int:
        return a + b

# 4. God objects that do everything
class TelegramBotHandler:
    def handle_everything(self, update):
        # 200 lines doing user management, payment processing,
        # stock management, notifications, etc.
```

### **What the Senior Lead Engineer Expects:**

**✅ Clean, Purposeful Code:**
```python
# 1. Configuration through environment with validation
class Config:
    TELEGRAM_TOKEN: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    DATABASE_URL: PostgresDsn = Field(..., env="DATABASE_URL")
    
    @validator("TELEGRAM_TOKEN")
    def validate_telegram_token(cls, v):
        if not v.startswith(('1', '2', '5', '6')):
            raise ValueError("Invalid Telegram bot token format")
        return v

# 2. Self-explanatory code with strategic comments only
def calculate_reseller_discount(base_price: Money, discount_rate: Decimal) -> Money:
    # Business rule: Resellers get percentage discount, minimum 1000 IDR off
    discount_amount = max(
        base_price * discount_rate,
        Money(1000, Currency.IDR)
    )
    return discount_amount

# 3. Right-sized abstractions
@dataclass(frozen=True)
class PaymentRequest:
    amount: Money
    customer_id: CustomerId
    payment_method: PaymentMethod

class PaymentService:
    def __init__(self, gateway: PaymentGateway):
        self._gateway = gateway
    
    async def process_payment(self, request: PaymentRequest) -> PaymentResult:
        return await self._gateway.charge(request)

# 4. Single responsibility with clear boundaries
class OrderCreationHandler:
    async def handle(self, command: CreateOrderCommand) -> OrderResult:
        # Only creates orders, delegates everything else
        
class StockReservationService:
    async def reserve(self, product_id: ProductId, quantity: int) -> Reservation:
        # Only handles stock reservation logic
```

### **Senior Lead Engineer's Mental Checklist:**

**When reviewing your code, they're asking:**

1. **"Can I understand this in 30 seconds?"** 
   - If not, it's too complex or poorly named

2. **"Is this solving the right problem?"**
   - No over-engineering, no premature optimization

3. **"Will this break when requirements change?"**
   - Code should be flexible, not brittle

4. **"Can this be tested easily?"**
   - If it's hard to test, it's poorly designed

5. **"Is this code expressing business intent?"**
   - Technical details shouldn't obscure business logic

6. **"Would I be comfortable maintaining this at 2 AM?"**
   - Code should be debuggable under pressure

### **Pro Tips to Pass Senior Review:**

1. **Write code like you're writing a story** - Clear beginning, middle, end
2. **Name things so well that comments are unnecessary** 
3. **Extract small functions with clear single purposes**
4. **Use types to make invalid states unrepresentable**
5. **Handle errors explicitly, never silently**
6. **Show, don't tell** - Let the code demonstrate its correctness

### **Final Warning:**

> **The senior lead engineer has seen thousands of codebases.** They can spot AI-generated code, lazy copy-paste jobs, and over-engineered solutions from a mile away. They value **elegance over cleverness**, **clarity over brevity**, and **maintainability over performance premature optimization**.
>
> **Your code is your professional signature.** Make sure it reflects the craftsmanship of a senior engineer, not the output of an AI assistant.

---

### Pull Request Requirements
```markdown
## Summary
Brief description of changes and motivation

## Changes Made
- [ ] Feature implementation
- [ ] Database migrations
- [ ] API updates
- [ ] Documentation updates

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Security Review
- [ ] No sensitive data in logs
- [ ] Proper input validation
- [ ] Audit logging implemented

## Related Issues
Fixes #123, Addresses #456
```

---

## 3. Development Tooling

### Source Control & Collaboration
- **Repository:** GitHub with protected main branch
- **CI/CD:** GitHub Actions for automated testing and deployment
- **Code Quality:** SonarQube integration for continuous quality monitoring
- **Dependencies:** Dependabot for automated security updates

### Local Development Setup
```bash
# Required tools for all developers
python3.11+
docker & docker-compose
postgresql-client
redis-cli
git
pre-commit hooks

# Environment setup
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
```

### Communication Channels
- **Daily Updates:** Telegram group for quick coordination
- **Technical Discussions:** GitHub Discussions for architecture decisions
- **Documentation:** All decisions recorded in appropriate `/docs` files
- **Emergency Contact:** Dedicated Telegram channel for critical issues

### Development Environment
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  app:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/quickcart_dev
      - REDIS_URL=redis://redis:6379
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - PAKASIR_API_KEY=${PAKASIR_API_KEY}
    volumes:
      - .:/app
    ports:
      - "8000:8000"
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: quickcart_dev
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

---

## 4. Documentation Requirements

### Mandatory Documentation Updates
- **Feature Changes:** Update relevant docs in `/docs` before PR merge
- **API Changes:** Must be reflected in `07-api_contracts.md`
- **Database Changes:** Update `06-data_schema.md` with schema modifications
- **Security Changes:** Document in `09-security_manifest.md`
- **Integration Changes:** Update `08-integration_plan.md`

### Documentation Standards
- **Format:** Markdown with consistent heading structure
- **Code Examples:** Include working code snippets with explanations
- **Cross-References:** Link related documents using relative paths
- **Version Control:** Update version and date in document headers
- **Language:** English for technical docs, Indonesian for user-facing content

### Required Documentation for New Features
1. **Feature Description** in relevant doc (e.g., PRD, Architecture)
2. **API Specification** if exposing new endpoints
3. **Database Schema** if adding/modifying tables
4. **Security Review** documenting security implications
5. **Integration Details** if involving external services
6. **Testing Strategy** for the new functionality

---

## 5. Code Quality & Security

### Automated Quality Checks
```yaml
# .github/workflows/quality.yml
name: Code Quality
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      
      - name: Lint with flake8
        run: flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
      
      - name: Type check with mypy
        run: mypy src/
      
      - name: Security check with bandit
        run: bandit -r src/ -f json
      
      - name: Run tests
        run: pytest --cov=src/ --cov-report=xml
      
      - name: SonarQube Scan
        uses: sonarqube-quality-gate-action@master
```

### Security Requirements for All Code
- **Input Validation:** All user inputs validated before processing
- **SQL Injection Prevention:** Use parameterized queries exclusively
- **Secrets Management:** Environment variables, never hard-coded
- **Error Handling:** No sensitive data in error messages
- **Audit Logging:** All critical operations logged to audit database
- **Rate Limiting:** Prevent abuse of bot commands and API endpoints

### Testing Requirements
- **Unit Tests:** 90%+ coverage for business logic
- **Integration Tests:** All external API interactions
- **Security Tests:** Input validation and authentication flows
- **Load Tests:** Payment processing under concurrent load
- **E2E Tests:** Complete user flows via Telegram bot

---

## 6. Deployment & Operations

### Environment Management
```python
# Environment configurations
ENVIRONMENTS = {
    "development": {
        "database_url": "postgresql://localhost/quickcart_dev",
        "redis_url": "redis://localhost:6379",
        "log_level": "DEBUG",
        "telegram_webhook": False  # Use polling for development
    },
    "staging": {
        "database_url": "${DATABASE_URL}",
        "redis_url": "${REDIS_URL}",
        "log_level": "INFO",
        "telegram_webhook": True,
        "pakasir_sandbox": True
    },
    "production": {
        "database_url": "${DATABASE_URL}",
        "redis_url": "${REDIS_URL}", 
        "log_level": "INFO",
        "telegram_webhook": True,
        "pakasir_sandbox": False
    }
}
```

### Deployment Process
1. **Code Review:** All changes reviewed and approved
2. **Automated Testing:** Full test suite passes
3. **Security Scan:** No critical vulnerabilities detected
4. **Staging Deployment:** Deploy to staging environment first
5. **Manual Testing:** Critical flows tested in staging
6. **Production Deployment:** Blue-green deployment to minimize downtime
7. **Post-Deployment:** Monitor logs and metrics for issues

### Rollback Procedures
- **Database Migrations:** Reversible migrations with down scripts
- **Code Rollback:** Previous Docker image available for instant rollback
- **Configuration Rollback:** Version-controlled configuration files
- **Monitoring:** Automated alerts trigger rollback procedures if needed

---

## 7. Onboarding & Knowledge Sharing

### New Developer Onboarding
1. **Read Core Documentation:** `02-context.md`, `03-prd.md`, `05-architecture.md`
2. **Setup Local Environment:** Follow development setup guide
3. **Review Security Policies:** `09-security_manifest.md`, `11-anti_fraud_policy.md`
4. **Complete Training Tasks:** Build simple feature end-to-end
5. **Code Review Observation:** Shadow experienced developer reviews

### Knowledge Sharing Practices
- **Weekly Tech Talks:** Share learnings, discuss architecture decisions
- **Documentation Review:** Monthly review and update of all docs
- **Post-Incident Reviews:** Document lessons learned from any issues
- **Best Practices Sharing:** Regular updates to development protocols

### Critical Knowledge Areas
- **Payment Processing:** Understanding Pakasir integration and fraud prevention
- **Bot Architecture:** Telegram API limitations and session management
- **Security:** Audit logging requirements and access control
- **Database Design:** Separation of operational and audit data
- **Error Handling:** Graceful degradation and user communication

---

## Cross-References

- See [03-prd.md](03-prd.md) for complete feature requirements and acceptance criteria
- See [05-architecture.md](05-architecture.md) for technical architecture and deployment details
- See [09-security_manifest.md](09-security_manifest.md) for security requirements and code review criteria
- See [15-testing_strategy.md](15-testing_strategy.md) for comprehensive testing approach
- See [20-docs_index.md](20-docs_index.md) for complete documentation structure and maintenance

---

> Note for AI builders: This development protocol ensures zero-ambiguity implementation. Every developer must follow these standards religiously. Payment processing requires extra care in testing and security review. All critical operations must be auditable and reversible.