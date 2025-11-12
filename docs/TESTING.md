# Testing Guide for QuickCart

This document describes the testing strategy, how to run tests, and what each test suite covers.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [CI/CD Testing](#cicd-testing)
- [Writing Tests](#writing-tests)
- [Troubleshooting](#troubleshooting)

## Overview

QuickCart uses **pytest** for testing with support for async operations via `pytest-asyncio`. Tests are organized into three main categories:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test multiple components working together
- **E2E Tests**: Test complete user workflows

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── unit/                    # Unit tests
│   ├── __init__.py
│   ├── test_models.py       # Database model tests
│   ├── test_config.py       # Configuration tests
│   └── ...
├── integration/             # Integration tests
│   ├── __init__.py
│   └── ...
└── e2e/                     # End-to-end tests
    ├── __init__.py
    └── ...
```

## Running Tests

### Prerequisites

Install dependencies:

```bash
pip install -r requirements.txt
```

Make sure you have the required environment variables set (or create `.env.test`):

```bash
DATABASE_URL=postgresql+asyncpg://quickcart:quickcart123@localhost:5432/quickcart_test
AUDIT_DATABASE_URL=postgresql+asyncpg://quickcart:quickcart123@localhost:5432/quickcart_audit_test
REDIS_URL=redis://localhost:6379/1
BOT_TOKEN=test_token_12345
PAKASIR_API_KEY=test_api_key
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/
```

### Run Specific Test Files

```bash
# Test models only
pytest tests/unit/test_models.py

# Test configuration only
pytest tests/unit/test_config.py
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Verbose Output

```bash
# Show detailed test output
pytest -v

# Show print statements
pytest -s

# Show both
pytest -vs
```

### Fast Fail

```bash
# Stop after first failure
pytest -x

# Stop after N failures
pytest --maxfail=3
```

## Test Categories

### Unit Tests (`tests/unit/`)

Test individual components in isolation without external dependencies.

#### `test_models.py`
- ✅ Verifies all models inherit from Base correctly
- ✅ Checks no reserved SQLAlchemy attributes are used (e.g., `metadata`)
- ✅ Validates all models have proper table names
- ✅ Ensures all models have primary keys
- ✅ Tests model structure and required fields

**Key Tests:**
- `test_no_reserved_column_names()` - **Critical**: Prevents SQLAlchemy errors
- `test_payment_audit_log_has_payment_metadata()` - Ensures proper naming
- `test_all_models_have_tablename()` - Schema validation

#### `test_config.py`
- ✅ Configuration loading and validation
- ✅ Environment-specific settings
- ✅ Database URL format validation
- ✅ Security settings verification
- ✅ Numeric configuration bounds checking

**Key Tests:**
- `test_settings_has_required_attributes()` - Ensures all config present
- `test_database_urls_format()` - Validates connection strings
- `test_no_missing_critical_settings()` - Production readiness

### Integration Tests (`tests/integration/`)

Test multiple components working together with real database connections.

*Coming soon*:
- Repository layer tests with real database
- Service layer tests with mocked external APIs
- Bot handler tests with mocked Telegram API

### E2E Tests (`tests/e2e/`)

Test complete user workflows from start to finish.

*Coming soon*:
- Complete order flow (browse → add to cart → checkout → payment)
- User registration and authentication
- Admin operations
- Payment webhook handling

## CI/CD Testing

### GitHub Actions Workflow

The CI pipeline (`.github/workflows/ci.yml`) runs comprehensive tests:

#### 1. **Lint Job**
- ✅ Python syntax validation
- ✅ Import verification
- ✅ Reserved attribute checking
- ✅ **Unit tests execution**

#### 2. **Build Job**
- ✅ Docker image build
- ✅ Docker Compose configuration validation

#### 3. **Database Job**
- ✅ PostgreSQL service setup
- ✅ Model import verification
- ✅ Alembic migration execution
- ✅ Database schema validation
- ✅ Migration rollback testing
- ✅ Critical table existence checks

#### 4. **Integration Job**
- ✅ Full service stack startup
- ✅ Database connectivity
- ✅ Redis connectivity
- ✅ **Application startup test**
- ✅ Health endpoint verification
- ✅ Webhook endpoint testing
- ✅ Database connectivity from app

#### 5. **Security Job**
- ✅ Trivy vulnerability scanning
- ✅ SARIF upload to GitHub Security

#### 6. **Summary Job**
- ✅ Aggregates all job results
- ✅ Fails if any critical job failed

### Running Tests Locally Like CI

Simulate the CI environment locally:

```bash
# 1. Use CI environment file
cp .env.ci .env

# 2. Start services
docker compose up -d db redis

# 3. Run migrations
export PYTHONPATH=$(pwd)
alembic upgrade head

# 4. Run tests
pytest tests/unit/ -v

# 5. Test application startup
python -c "from src.core.config import settings; print('✓ Config loaded')"

# 6. Cleanup
docker compose down -v
```

## Writing Tests

### Unit Test Template

```python
"""
Unit tests for <module_name>
"""

import pytest
from src.module import YourClass


class TestYourClass:
    """Test YourClass functionality"""

    def test_basic_functionality(self):
        """Test that basic function works"""
        obj = YourClass()
        result = obj.method()
        assert result == expected_value

    def test_edge_case(self):
        """Test edge case handling"""
        obj = YourClass()
        with pytest.raises(ValueError):
            obj.method_that_should_fail()
```

### Async Test Template

```python
import pytest


class TestAsyncFunction:
    """Test async functions"""

    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Test async operation"""
        result = await async_function()
        assert result is not None
```

### Using Fixtures

```python
import pytest


@pytest.fixture
def sample_user():
    """Fixture providing a sample user"""
    return {"id": 1, "username": "testuser"}


class TestWithFixture:
    def test_using_fixture(self, sample_user):
        """Test using fixture"""
        assert sample_user["id"] == 1
```

## Best Practices

### ✅ DO:
- Write descriptive test names: `test_payment_audit_log_uses_payment_metadata_not_metadata()`
- Test one thing per test function
- Use fixtures for common setup
- Clean up resources in tests
- Use parametrize for multiple test cases
- Add docstrings to test classes and methods

### ❌ DON'T:
- Don't test implementation details
- Don't create tests that depend on other tests
- Don't use hard-coded values that might change
- Don't skip cleanup (use `finally` or fixtures)
- Don't commit tests that always skip

## Common Test Patterns

### Testing Exceptions

```python
def test_raises_value_error():
    """Test that function raises ValueError"""
    with pytest.raises(ValueError, match="Invalid input"):
        function_that_raises("bad input")
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test", "TEST"),
    ("hello", "HELLO"),
    ("", ""),
])
def test_uppercase(input, expected):
    """Test uppercase conversion"""
    assert uppercase(input) == expected
```

### Mocking External Services

```python
from unittest.mock import patch, MagicMock


def test_external_api_call():
    """Test function that calls external API"""
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "ok"}
        
        result = call_external_api()
        assert result["status"] == "ok"
```

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError`:

```bash
# Set PYTHONPATH
export PYTHONPATH=$(pwd)
pytest

# Or run with -s to see imports
pytest -s
```

### Database Connection Errors

1. Ensure PostgreSQL is running:
   ```bash
   docker compose up -d db
   ```

2. Check connection string in `.env`:
   ```bash
   DATABASE_URL=postgresql+asyncpg://quickcart:quickcart123@localhost:5432/quickcart_test
   ```

3. Create test database:
   ```bash
   psql -U quickcart -c "CREATE DATABASE quickcart_test;"
   ```

### Redis Connection Errors

1. Start Redis:
   ```bash
   docker compose up -d redis
   ```

2. Verify Redis is accessible:
   ```bash
   docker compose exec redis redis-cli ping
   ```

### Async Test Errors

If async tests fail with "no running event loop":

```python
# Add to conftest.py
import pytest

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

### Reserved Attribute Errors

If you get `InvalidRequestError: Attribute name 'X' is reserved`:

1. Check model definitions in `src/models/`
2. Rename the column (e.g., `metadata` → `payment_metadata`)
3. Update migration files in `migrations/versions/`
4. Run tests to verify fix:
   ```bash
   pytest tests/unit/test_models.py::TestReservedAttributes -v
   ```

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Critical Paths**: 100% coverage (payment, order creation, user auth)
- **Integration Tests**: Cover all major workflows
- **E2E Tests**: Cover top 3 user journeys

## Continuous Improvement

- Review test failures in CI
- Add tests for bugs before fixing
- Update tests when requirements change
- Remove obsolete tests
- Refactor duplicated test code

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [GitHub Actions CI Logs](../../.github/workflows/ci.yml)
- [Testing Strategy](./15-testing_strategy.md)

---

**Last Updated**: January 2025  
**Maintained By**: QuickCart Development Team