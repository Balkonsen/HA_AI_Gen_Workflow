# UV Troubleshooting Guide

Common issues and solutions when using UV.

## UV Not Found After Install

**Problem:** UV command not recognized after installation.

**Solution:**
```bash
# Add to PATH (add to ~/.zshrc or ~/.bashrc)
export PATH="$HOME/.cargo/bin:$PATH"

# Reload shell
source ~/.zshrc
```

---

## Wrong Python Version

**Problem:** Project using incorrect Python version.

**Solution:**
```bash
# Check current Python
uv run python --version

# List available versions
uv python list

# Install correct version
uv python install 3.11

# Pin to project
uv python pin 3.11

# Recreate venv
rm -rf .venv
uv venv
```

---

## Dependency Conflicts

**Problem:** Packages have conflicting requirements.

**Solution:**
```bash
# See resolution
uv tree

# Try updating
uv sync --upgrade

# Force reinstall
rm -rf .venv uv.lock
uv venv
uv sync
```

---

## Package Not Found

**Problem:** Cannot find package on PyPI.

**Solution:**
```bash
# Make sure package name is correct
uv add numpy  # Correct
uv add NumPy  # Wrong (case sensitive)

# Check if package exists
pip search package-name

# Or search on PyPI: https://pypi.org/
```
