# Coding Conventions

**Analysis Date:** 2026-08-29

## Language & Runtime

**Python 3.8+**
- All source files require Python 3.8+ type annotations
- Shebang: `#!/usr/bin/env python3` (line 1 of all executable scripts)

## Naming Patterns

**Files:**
- All lowercase with underscores: `ha_context_gen.py`, `ssh_transfer.py`
- Main modules in `bin/` directory: `bin/workflow_orchestrator.py`, `bin/secrets_manager.py`
- Test files: `test_*.py` prefix in `tests/` directory

**Functions & Methods:**
- snake_case: `safe_yaml_load()`, `_ensure_directories()`, `export_from_remote()`
- Private methods: Leading underscore `_init_encryption()`, `_generate_label()`
- Public methods: No underscore prefix

**Variables & Attributes:**
- snake_case: `export_path`, `secrets_map`, `connection_timeout`
- Private attributes: Leading underscore `_secrets`, `_fernet`, `_counter`
- Constants: UPPER_CASE: `MAX_AI_FILE_SIZE`, `CRYPTO_AVAILABLE`

**Classes:**
- PascalCase: `HAContextGenerator`, `SecretsManager`, `WorkflowOrchestrator`
- Descriptive names indicating responsibility: `HARemoteManager`, `ExportVerifier`

**Type Hints:**
- Used for function parameters and return types: `def __init__(self, config_path: Optional[str] = None)`
- Common types: `Optional[str]`, `Dict[str, Any]`, `List[str]`, `Tuple[str, int]`
- File: `bin/workflow_orchestrator.py` lines 30-42 show pattern

## Code Style

**Formatting:**
- Tool: Black
- Line length: 120 characters (configured in `.pre-commit-config.yaml` line 29, `.vscode/settings.json` line 19, `pytest.ini` line 36)
- Format on save: Enabled in VSCode (`.vscode/settings.json` line 22)
- Run with: `make format` or `black --line-length 120 bin/`

**Linting:**
- Tool: Flake8
- Max line length: 120 characters
- Ignored rules: E203 (whitespace before colon), W503 (line break before binary operator)
- Config: `.pre-commit-config.yaml` line 36, `pytest.ini` line 36
- Run with: `make lint`

**Additional Quality:**
- MyPy: Type checking enabled with `warn_return_any = True` (pytest.ini line 48)
- Bandit: Security scanning enabled (`.pre-commit-config.yaml` line 42)
- Pylint: Optional additional checks (Makefile line 59)

## Import Organization

**Order:**
1. Standard library imports (os, sys, json, yaml, pathlib, datetime)
2. Third-party imports (PyYAML, requests, paramiko, cryptography)
3. Local/relative imports (sibling modules in bin/)

**Pattern:**
```python
import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Third-party
import requests
from cryptography.fernet import Fernet

# Local
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from workflow_config import WorkflowConfig
from secrets_manager import SecretsManager
```

See `bin/workflow_orchestrator.py` lines 7-24 for reference.

**Path handling:**
- Add bin directory to path: `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`
- Use `Path` from pathlib: `from pathlib import Path`
- File: `bin/workflow_orchestrator.py` line 16

## Docstrings

**Module Level:**
- Use triple quotes with description
- Example: `bin/ha_diagnostic_export.py` lines 2-15

**Class Level:**
- Triple quotes with one-line description
- Example: `class HAContextGenerator:` followed by docstring explaining purpose

**Method/Function Level:**
- Triple quotes with description, Args, and Returns sections
- Args: List parameter name and type
- Returns: Describe return type and value
- Example from `bin/workflow_orchestrator.py` lines 36-42:
```python
def __init__(
    self,
    config_path: Optional[str] = None,
    ssh_timeout: Optional[int] = None,
    transfer_timeout: Optional[int] = None,
):
    """Initialize orchestrator.

    Args:
        config_path: Optional path to configuration file
        ssh_timeout: Override SSH connection timeout from CLI
        transfer_timeout: Override file transfer timeout from CLI
    """
```

## Error Handling

**Pattern:**
- Use try-except blocks with specific exception types
- Catch narrowly: avoid bare `except:`
- Log warnings for recoverable errors
- Return None or False for graceful failures
- Example from `bin/ha_ai_context_gen.py` lines 61-78:
```python
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.load(f, Loader=HAYAMLLoader)
except yaml.YAMLError as e:
    print(f"  Warning: YAML parsing error in {file_path}: {e}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {'_raw_content': content, '_parse_error': str(e)}
    except:
        return None
except Exception as e:
    print(f"  Warning: Could not read {file_path}: {e}")
    return None
```

**Patterns:**
- Optional fallback imports: `try: import X except ImportError: X_AVAILABLE = False` (secrets_manager.py line 18)
- Graceful degradation: Return status booleans or error dicts
- Always provide user feedback via print statements or logging

## Logging & Output

**Framework:** console print() statements

**Patterns:**
- Success: `print("✓ message")` or `print(f"✓ Loaded {count} items")`
- Warning: `print("⚠ message")`
- Error: `print("✗ message")`
- Info: `print("→ message")` or plain `print("message")`
- Example from `bin/secrets_manager.py` lines 67, 80, 82, 91, 93

**When to use:**
- Every major operation start/completion
- Non-fatal errors and warnings
- Data counts and progress

## Comments

**When to Comment:**
- Complex algorithms or non-obvious logic
- HA-specific behavior (YAML tags, config directives)
- Important assumptions or constraints
- Workarounds for known issues

**Example from `bin/ha_ai_context_gen.py` lines 14-16:**
```python
# Custom YAML loader to handle Home Assistant's !include directives
class HAYAMLLoader(yaml.SafeLoader):
    """Custom YAML loader that handles HA-specific tags"""
```

**Avoid:**
- Obvious comments restating code
- Outdated comments after code changes

## Function Design

**Size:** Methods typically 10-50 lines

**Parameters:**
- Use type hints for all parameters
- Use Optional[] for nullable parameters
- Provide default values for optional parameters
- Example: `def __init__(self, secrets_dir: str = "./secrets", label_prefix: str = "HA_SECRET")` (secrets_manager.py line 31)

**Return Values:**
- Always specify return type hint
- Return tuples for multiple values: `Tuple[bool, str]`
- Return None for optional operations
- Use booleans for success/failure: `success, message = operation()` (workflow_orchestrator.py line 66-69)

**Private Helpers:**
- Prefix with underscore: `_init_encryption()`, `_load_existing()`
- Call from within class only

## Module Design

**Exports:**
- Classes are main exports (no underscore prefix)
- Functions typically internal to classes
- Exception classes for specific errors

**Initialization:**
- Class initialization via `__init__` with clear docstring
- Private initialization methods for setup: `_init_encryption()`, `_ensure_directories()`

**State Management:**
- Minimize mutable class state
- Use attributes for configuration and results
- Example: `self.export_path`, `self.secrets_map`, `self.context`

**Encapsulation:**
- Private: attributes and methods with leading underscore
- Public: everything else
- Docstring documents public interface

## Whitespace & Formatting

**File Endings:**
- Unix line endings (LF)
- Final newline at end of file
- No trailing whitespace (enforced by pre-commit hook)

**Indentation:**
- 4 spaces per indent level (Black standard)
- Never use tabs

**Blank Lines:**
- Two blank lines between class definitions
- One blank line between method definitions
- One blank line before block-level comments

## Conditional Imports

**Pattern:**
Used for optional dependencies that may not be installed

Example from `bin/secrets_manager.py` lines 17-25:
```python
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠ cryptography not installed. Using base64 encoding (not secure for production)")
```

Then check flag before using: `if not CRYPTO_AVAILABLE: return`

## Pre-Commit Hooks

**Enforcement:** Yes, all files must pass before commit

**Checks include:**
- Trailing whitespace
- End of file fixer
- YAML, JSON validation
- Detect private keys
- Mixed line endings
- Black formatting
- Flake8 linting
- Bandit security
- ShellCheck (shell scripts)
- YAMLLint
- MarkdownLint
- Pytest (all tests must pass)

**Setup:**
- Run: `make pre-commit` or `pre-commit install`
- Bypass (not recommended): `git commit --no-verify`

---

*Convention analysis: 2026-08-29*
