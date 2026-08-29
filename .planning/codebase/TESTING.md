# Testing Patterns

**Analysis Date:** 2026-08-29

## Test Framework

**Runner:**
- pytest 7.4.0+
- Config: `pytest.ini`

**Assertion Library:**
- pytest built-in assertions (standard `assert` statements)

**Additional Libraries:**
- pytest-cov (4.1.0+) - Coverage reporting
- pytest-mock (3.11.1+) - Mocking utilities
- pytest-asyncio (0.21.1+) - Async test support
- responses (0.23.3+) - HTTP response mocking
- requests-mock (1.11.0+) - HTTP request mocking

**Run Commands:**

```bash
# Run all tests with verbose output and coverage
pytest -v --cov=bin --cov-report=term-missing

# Run unit tests only
pytest -v -m unit

# Run integration tests only
pytest -v -m integration

# Run with coverage HTML report
pytest -v --cov=bin --cov-report=html

# Run in watch mode (requires pytest-watch)
ptw -- -v

# Run specific test file
pytest tests/test_context_gen.py -v

# Run specific test class
pytest tests/test_context_gen.py::TestHAContextGenerator -v

# Run specific test method
pytest tests/test_context_gen.py::TestHAContextGenerator::test_init -v
```

**Make commands:**
- `make test` - Run all tests with coverage
- `make test-unit` - Run unit tests only
- `make test-integration` - Run integration tests only
- `make coverage` - Generate HTML coverage report
- `make lint` - Run linting checks (including tests must pass)

## Test File Organization

**Location:** `tests/` directory at repository root

**Naming:**
- Test files: `test_*.py` prefix
- Example: `test_context_gen.py`, `test_config_import.py`, `test_ssh_transfer.py`

**Structure:**
```
tests/
├── conftest.py                 # Shared fixtures
├── test_context_gen.py         # Tests for ha_ai_context_gen.py
├── test_config_import.py       # Tests for ha_config_import.py
├── test_diagnostic_export.py   # Tests for ha_diagnostic_export.py
├── test_export_verifier.py     # Tests for ha_export_verifier.py
├── test_ssh_transfer.py        # Tests for ssh_transfer.py
└── __init__.py                 # Package marker
```

**Test Discovery Rules (pytest.ini lines 5-7):**
- `python_files = test_*.py` - Files starting with test_
- `python_classes = Test*` - Classes starting with Test
- `python_functions = test_*` - Methods starting with test_

## Test Structure

**Suite Organization:**

Use class-based organization for related tests. Each test class groups tests for a specific component or method.

```python
"""
Unit tests for ha_ai_context_gen.py
Tests the HAContextGenerator class and related functions.
"""
import pytest
import sys
import os

# Add bin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

from ha_ai_context_gen import HAContextGenerator, HAYAMLLoader


class TestHAContextGenerator:
    """Test HAContextGenerator class"""
    
    def test_init(self, temp_dir):
        """Test initialization of HAContextGenerator"""
        generator = HAContextGenerator(temp_dir)
        assert generator.export_path == temp_dir
        assert 'system_overview' in generator.context


class TestSafeYamlLoad:
    """Test YAML loading functionality"""
    
    def test_safe_yaml_load_valid(self, temp_dir):
        """Test loading valid YAML file"""
        # Test implementation
        pass
```

**Patterns:**

- **Module docstring:** Triple-quoted description of what's being tested
- **Imports:** Place in standard Python order, then add bin/ to path
- **Test classes:** One per major class/component being tested
- **Class docstring:** Describes what functionality is being tested
- **Test methods:** Each method tests one specific behavior
- **Method docstring:** Describes the specific test scenario
- **Fixtures:** Passed as method parameters (from conftest.py)

See `tests/test_context_gen.py` lines 1-49 for complete pattern.

## Mocking

**Framework:** unittest.mock (Python stdlib) with pytest integration

**Patterns:**

**Decorator-based mocking:**
```python
from unittest.mock import Mock, patch, MagicMock, call

@patch('subprocess.run')
def test_connection_success(self, mock_run):
    """Test successful SSH connection."""
    mock_run.return_value = Mock(
        returncode=0, 
        stdout="Connection successful", 
        stderr=""
    )
    
    ssh = SSHTransfer(host="test.host.com")
    success, message = ssh.test_connection()
    
    assert success is True
    assert message == "Connection successful"
    mock_run.assert_called_once()
```

See `tests/test_ssh_transfer.py` lines 54-68 for reference.

**Side effect mocking (multiple return values):**
```python
@patch('subprocess.run')
def test_connection_retry_logic(self, mock_run):
    """Test retry logic for transient failures."""
    # First two attempts fail, third succeeds
    mock_run.side_effect = [
        Mock(returncode=255, stdout="", stderr="Network error"),
        Mock(returncode=255, stdout="", stderr="Network error"),
        Mock(returncode=0, stdout="Connection successful", stderr="")
    ]
    
    ssh = SSHTransfer(host="test.host.com", retry_attempts=3)
    success, message = ssh.test_connection()
    
    assert success is True
```

See `tests/test_ssh_transfer.py` lines 117-120 for reference.

**Exception mocking:**
```python
@patch('subprocess.run')
def test_connection_timeout(self, mock_run):
    """Test connection timeout."""
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=30)
    
    ssh = SSHTransfer(host="test.host.com", retry_attempts=1)
    success, message = ssh.test_connection()
    
    assert success is False
    assert "timeout" in message.lower()
```

See `tests/test_ssh_transfer.py` lines 101-110 for reference.

**Assertion on mock calls:**
```python
# Check function was called once
mock_run.assert_called_once()

# Check it was called with specific arguments
mock_run.assert_called_with(expected_args)

# Check multiple calls
assert mock_run.call_count == 3
```

**What to Mock:**
- External I/O (file operations, HTTP requests, SSH connections)
- Third-party libraries (subprocess, requests)
- Time-dependent operations (sleep, datetime, time)
- Non-deterministic operations

**What NOT to Mock:**
- Code under test
- Simple data structures (dicts, lists)
- Built-in Python functions (json.dumps, yaml.load)
- The actual logic you're testing

## Fixtures and Factories

**Test Data:**

Fixtures defined in `tests/conftest.py` provide reusable test data:

```python
@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_ha_config(temp_dir):
    """Create a mock Home Assistant configuration"""
    config_dir = Path(temp_dir) / "config"
    config_dir.mkdir(parents=True)
    
    config = {
        'homeassistant': {
            'name': 'Test Home',
            'latitude': '!secret latitude',
            'longitude': '!secret longitude',
            'unit_system': 'metric',
            'time_zone': 'Europe/Berlin'
        },
        'automation': '!include automations.yaml',
    }
    
    with open(config_dir / 'configuration.yaml', 'w') as f:
        yaml.dump(config, f)
    
    return config_dir
```

**Fixtures defined in conftest.py:**
- `temp_dir` - Temporary directory that's cleaned up after test
- `mock_ha_config` - Mock Home Assistant configuration directory
- `mock_export_data` - Sample entity and device data
- `mock_diagnostic_data` - Sample HA diagnostic data
- `mock_secrets` - Sample secrets dictionary

See `tests/conftest.py` lines 13-133 for all fixtures.

**Location:** `tests/conftest.py` - Shared by all test files

**Usage:** Pass fixture name as parameter to test method:
```python
def test_init(self, temp_dir):
    """Test initialization"""
    generator = HAContextGenerator(temp_dir)
    assert generator.export_path == temp_dir
```

## Coverage

**Requirements:** No minimum enforced, but coverage reports generated

**Target:** Aim for >80% for critical modules

**View Coverage:**
```bash
# HTML report (opens in browser)
make coverage
# Then open htmlcov/index.html

# Terminal report
pytest --cov=bin --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=bin --cov-report=xml
```

**Configuration (pytest.ini lines 23-32):**
- Source: `bin/` directory only
- Omit: test files themselves
- Report missing: Show lines not covered
- Precision: 2 decimal places

**In VSCode:**
- Coverage Gutters extension shows coverage in editor
- Green: covered, red: uncovered, yellow: partial
- Config in `.vscode/settings.json` lines 56-61

## Test Types

**Unit Tests:**

Test individual functions or methods in isolation.

```python
class TestHAContextGenerator:
    """Test HAContextGenerator class"""
    
    def test_init(self, temp_dir):
        """Test initialization of HAContextGenerator"""
        generator = HAContextGenerator(temp_dir)
        assert generator.export_path == temp_dir
        assert 'system_overview' in generator.context
```

- Scope: Single method or class
- Setup: Use fixtures for data
- Mocking: Mock external dependencies
- Speed: Fast (< 100ms per test)
- Marker: `@pytest.mark.unit`

**Integration Tests:**

Test interactions between multiple components.

- Scope: Multiple modules working together
- Setup: May use real files/data (in temp directories)
- Mocking: Mock only external services
- Speed: Slower, but still < 1 second per test
- Marker: `@pytest.mark.integration`

**Test Markers (pytest.ini lines 17-21):**
- `@pytest.mark.slow` - Tests that take >1 second
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.security` - Security-related tests

**Run specific marker:**
```bash
pytest -m unit              # Only unit tests
pytest -m "not slow"        # Exclude slow tests
pytest -m integration       # Only integration tests
```

## Common Patterns

**Async Testing:**

```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async function"""
    result = await async_function()
    assert result == expected_value
```

Requires: pytest-asyncio (in requirements-test.txt)

**Error Testing:**

Test that exceptions are raised appropriately:

```python
def test_safe_yaml_load_invalid_yaml(self, temp_dir):
    """Test loading invalid YAML returns structure with error info"""
    yaml_file = Path(temp_dir) / 'invalid.yaml'
    yaml_file.write_text('key: value\n  invalid: indentation\n- broken')
    
    generator = HAContextGenerator(temp_dir)
    result = generator.safe_yaml_load(str(yaml_file))
    
    # Should return a dict with _parse_error or None
    if result is not None:
        assert '_parse_error' in result or '_raw_content' in result
```

Or use pytest.raises():
```python
def test_invalid_config():
    """Test that invalid config raises ValueError"""
    with pytest.raises(ValueError, match="invalid config"):
        parse_config("invalid")
```

**State Assertions:**

Test object state changes:

```python
def test_restore_secrets_basic(self, temp_dir):
    """Test basic secret restoration"""
    secrets_file = Path(temp_dir) / 'secrets_map.json'
    secrets_data = {
        'secrets': {
            '<<PASSWORD_1>>': 'my_secret_password',
            '<<IP_1>>': '192.168.1.100'
        }
    }
    secrets_file.write_text(json.dumps(secrets_data))
    
    importer = HAConfigImporter(temp_dir, str(secrets_file))
    importer.load_secrets()
    
    text = 'password: <<PASSWORD_1>>\nhost: <<IP_1>>'
    result = importer.restore_secrets(text)
    
    assert result == 'password: my_secret_password\nhost: 192.168.1.100'
    assert len(importer.changes_log) == 2  # Check state changed
```

See `tests/test_config_import.py` lines 102-120 for complete example.

## Pre-Commit Hook

**Hook behavior (`.pre-commit-config.yaml` lines 69-76):**
- Runs pytest on every commit
- Runs with `-v --tb=short -x` (verbose, short traceback, stop on first failure)
- Blocks commit if any tests fail
- Bypass with `git commit --no-verify` (not recommended)

**Pytest execution:**
```bash
pytest -v --tb=short -x
```

## Test Conventions

**Test Method Naming:**
- Always start with `test_`
- Descriptive: `test_safe_yaml_load_valid`, `test_connection_retry_logic`
- Pattern: `test_<function>_<scenario>` or `test_<scenario>`

**Assertions:**
- One logical assertion per test (can have multiple `assert` statements)
- Use descriptive assertion messages if needed:
```python
assert result == expected, f"Expected {expected}, got {result}"
```

**Docstrings:**
- Every test method needs a docstring
- One-line description of what's being tested
- Example: `"""Test initialization of HAContextGenerator"""`

**Test Independence:**
- Each test should be independent
- Use fixtures for setup/teardown
- Don't depend on test execution order
- Cleanup happens automatically (fixture teardown)

**Example complete test (tests/test_config_import.py lines 21-39):**
```python
def test_init(self, temp_dir):
    """Test initialization with correct constructor signature"""
    import_path = Path(temp_dir) / 'imports'
    secrets_file = Path(temp_dir) / 'secrets_map.json'
    
    # Create a valid secrets file
    secrets_file.write_text(json.dumps({'secrets': {}}))
    
    importer = HAConfigImporter(
        import_path=str(import_path),
        secrets_file=str(secrets_file)
    )
    
    assert importer.import_path == str(import_path)
    assert importer.secrets_file == str(secrets_file)
    assert importer.secrets_map == {}
    assert importer.reverse_map == {}
    assert importer.dry_run == True
    assert importer.changes_log == []
```

---

*Testing analysis: 2026-08-29*
