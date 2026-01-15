# AI Agent Instructions for HA AI Gen Workflow

## Overview
This document provides comprehensive instructions for AI coding agents (like GitHub Copilot, ChatGPT, Claude) to work effectively with the HA AI Gen Workflow codebase.

## Project Structure
```
HA_AI_Gen_Workflow/
├── bin/                          # Python scripts
│   ├── ha_ai_context_gen.py     # AI context generator
│   ├── ha_config_import.py       # Configuration importer
│   ├── ha_diagnostic_export.py   # Diagnostic data exporter
│   └── ha_export_verifier.py     # Export verification
├── tests/                        # Test suite
│   ├── conftest.py              # Pytest fixtures
│   ├── test_*.py                # Unit tests
│   └── validate_shell_scripts.sh # Shell validation
├── docs/                         # Documentation
├── templates/                    # Templates
├── .github/workflows/            # CI/CD pipelines
├── ha_ai_master_script.sh       # Main orchestrator
├── setup.sh                      # Installation script
└── pytest.ini                    # Test configuration
```

## Core Principles

### 1. Security First
- **NEVER** commit secrets, tokens, passwords, or API keys
- Always sanitize sensitive data (IPs, emails, tokens)
- Use pattern matching to detect and redact sensitive information
- All exports must be verified for data leakage

### 2. Code Quality Standards
- **Python**: Follow PEP 8, use type hints where appropriate
- **Bash**: Use `set -e`, quote variables, handle errors gracefully
- **Documentation**: Update docs when changing functionality
- **Tests**: Write tests for new features and bug fixes

### 3. Testing Requirements
All code changes must include:
- Unit tests for new functions/methods
- Integration tests for workflows
- Validation tests for bash scripts
- Security checks for sanitization

## Development Workflow

### Step 1: Understanding the Request
1. **Read the issue/request carefully**
2. **Check existing code** for similar implementations
3. **Review tests** to understand expected behavior
4. **Identify dependencies** and potential impacts

### Step 2: Planning
1. **Break down the task** into smaller components
2. **Identify files to modify** (Python, Bash, docs, tests)
3. **Plan test cases** before writing code
4. **Consider security implications**

### Step 3: Implementation
1. **Write code** following project conventions
2. **Add error handling** and logging
3. **Update documentation** inline and in docs/
4. **Write tests** alongside implementation

### Step 4: Validation
1. **Run unit tests**: `pytest -v`
2. **Run shell validation**: `./tests/validate_shell_scripts.sh`
3. **Check coverage**: `pytest --cov=bin --cov-report=term`
4. **Run security checks**: `bandit -r bin/`
5. **Validate formatting**: `black --check bin/`

### Step 5: Pre-Commit Checklist
- [ ] All tests pass
- [ ] Code is formatted (black for Python)
- [ ] No linting errors (flake8, shellcheck)
- [ ] Documentation updated
- [ ] Security checks pass
- [ ] No secrets in code
- [ ] Git commit message follows conventions

## Common Tasks

### Adding a New Python Module
```python
#!/usr/bin/env python3
"""
Module description
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional

class NewModule:
    """
    Class description
    
    Args:
        param1: Description
        param2: Description
    """
    
    def __init__(self, param1: str, param2: Optional[int] = None):
        self.param1 = param1
        self.param2 = param2
    
    def method_name(self) -> Dict:
        """
        Method description
        
        Returns:
            Description of return value
        
        Raises:
            ValueError: When X happens
        """
        pass

# Tests should be in tests/test_new_module.py
```

### Adding a New Bash Function
```bash
#!/bin/bash
# Function description
# Args:
#   $1 - Description
#   $2 - Description
# Returns:
#   0 on success, 1 on failure

function_name() {
    local param1="$1"
    local param2="${2:-default}"
    
    # Validate inputs
    if [ -z "$param1" ]; then
        error "Parameter 1 is required"
        return 1
    fi
    
    # Implementation
    # ...
    
    success "Operation completed"
    return 0
}
```

### Writing Tests
```python
# tests/test_new_module.py
import pytest
from bin.new_module import NewModule

class TestNewModule:
    """Test suite for NewModule"""
    
    def test_initialization(self):
        """Test module initialization"""
        module = NewModule("test")
        assert module.param1 == "test"
    
    def test_method_behavior(self, temp_dir):
        """Test method behavior"""
        module = NewModule("test")
        result = module.method_name()
        assert result is not None
    
    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            module = NewModule("")
            module.method_name()
```

## Sanitization Patterns

### Sensitive Data Patterns to Redact
```python
SENSITIVE_PATTERNS = {
    'passwords': r'(password|passwd|pwd)[\s:=]+\S+',
    'tokens': r'(token|bearer|auth)[\s:=]+\S+',
    'api_keys': r'(api[_-]?key|apikey)[\s:=]+\S+',
    'secrets': r'(secret)[\s:=]+\S+',
    'ip_addresses': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
    'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'urls_with_auth': r'https?://[^/]+:[^/]+@',
}

# Replacement strings
REPLACEMENTS = {
    'passwords': '***REDACTED***',
    'tokens': '***REDACTED***',
    'api_keys': '***REDACTED***',
    'ip_addresses': 'xxx.xxx.xxx.xxx',
    'emails': '***EMAIL***',
}
```

## Error Handling Guidelines

### Python
```python
import logging

logger = logging.getLogger(__name__)

try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Validation error: {e}")
    raise
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    return None
finally:
    cleanup_resources()
```

### Bash
```bash
set -e  # Exit on error
set -u  # Error on undefined variable
set -o pipefail  # Pipe failures propagate

# Error handling function
handle_error() {
    error "Command failed: $1"
    cleanup
    exit 1
}

# Use trap for cleanup
trap 'handle_error "Line $LINENO"' ERR
```

## Debugging Workflow

### When Tests Fail
1. **Read the error message** carefully
2. **Run specific test**: `pytest tests/test_file.py::TestClass::test_method -v`
3. **Add debug output**: Use `print()` or `logger.debug()`
4. **Check fixtures**: Verify test setup in `conftest.py`
5. **Isolate the issue**: Create minimal reproduction case

### When Shell Scripts Fail
1. **Run with debug**: `bash -x script.sh`
2. **Check permissions**: `ls -la script.sh`
3. **Validate syntax**: `bash -n script.sh`
4. **Use shellcheck**: `shellcheck script.sh`

## Git Workflow

### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

### Commit Message Format
```
type(scope): Short description

Longer description if needed

Closes #123
```

**Types**: feat, fix, docs, style, refactor, test, chore

### Example Commits
```
feat(context-gen): Add device grouping by manufacturer

- Group devices by manufacturer for better AI context
- Add unit tests for device grouping
- Update documentation

Closes #45
```

## CI/CD Pipeline

### Pipeline Stages
1. **Lint**: Code quality checks (black, flake8, shellcheck)
2. **Test**: Unit and integration tests (pytest)
3. **Security**: Security scanning (bandit, trivy)
4. **Build**: Package creation
5. **Validate**: Pre-merge validation

### Running Locally
```bash
# Full validation before commit
pytest -v
./tests/validate_shell_scripts.sh
black --check bin/
flake8 bin/
bandit -r bin/
```

## Agent Best Practices

### DO
✅ Read existing code before making changes
✅ Write tests for new functionality
✅ Update documentation when changing behavior
✅ Use type hints in Python code
✅ Add error handling and logging
✅ Sanitize all sensitive data
✅ Follow project conventions
✅ Run tests before committing
✅ Break large changes into smaller commits

### DON'T
❌ Commit without running tests
❌ Leave TODO comments without tickets
❌ Hard-code configuration values
❌ Ignore linting warnings
❌ Skip error handling
❌ Commit secrets or credentials
❌ Break existing functionality
❌ Remove tests without replacing them

## Example: Complete Feature Implementation

### Task: Add Entity Statistics to Context Generator

#### 1. Plan
- Modify `ha_ai_context_gen.py`
- Add statistics calculation method
- Update AI_PROMPT.md generation
- Write unit tests
- Update documentation

#### 2. Implementation
```python
# In ha_ai_context_gen.py
def _calculate_entity_statistics(self) -> Dict:
    """Calculate statistics about entities"""
    stats = {
        'total': len(self.context.get('entities', [])),
        'by_domain': {},
        'by_state': {},
    }
    
    for entity in self.context.get('entities', []):
        domain = entity['entity_id'].split('.')[0]
        state = entity.get('state', 'unknown')
        
        stats['by_domain'][domain] = stats['by_domain'].get(domain, 0) + 1
        stats['by_state'][state] = stats['by_state'].get(state, 0) + 1
    
    return stats
```

#### 3. Tests
```python
# In tests/test_context_gen.py
def test_entity_statistics(self, temp_dir, mock_export_data):
    """Test entity statistics calculation"""
    generator = HAContextGenerator(temp_dir)
    # ... setup ...
    stats = generator._calculate_entity_statistics()
    
    assert stats['total'] == 2
    assert 'light' in stats['by_domain']
    assert stats['by_domain']['light'] == 1
```

#### 4. Documentation
```markdown
# In docs/complete_readme.md
## Entity Statistics

The context generator now includes detailed statistics:
- Total entity count
- Entities grouped by domain
- Entities grouped by state
```

#### 5. Validate
```bash
pytest tests/test_context_gen.py -v
black bin/ha_ai_context_gen.py
flake8 bin/ha_ai_context_gen.py
```

## Resources

### Documentation
- [docs/complete_readme.md](../docs/complete_readme.md) - Complete documentation
- [docs/deployment_guide.md](../docs/deployment_guide.md) - Deployment instructions
- [docs/quick_reference.md](../docs/quick_reference.md) - Quick reference

### Testing
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)

### Code Quality
- [PEP 8](https://peps.python.org/pep-0008/) - Python style guide
- [Black](https://black.readthedocs.io/) - Python formatter
- [ShellCheck](https://www.shellcheck.net/) - Shell script analyzer

## Questions?

When in doubt:
1. Check existing code for examples
2. Review test cases for expected behavior
3. Read the documentation
4. Ask for clarification with specific questions

Remember: **Security, Quality, and Testing are not optional!**
