# Migration from pip to UV

Guide for migrating existing pip-based projects to UV.

## Convert requirements.txt to pyproject.toml

### Option 1: Add packages individually
```bash
# 1. Read existing requirements
cat requirements.txt

# 2. Add packages one by one
uv add package1 package2 package3
```

### Option 2: Install then convert
```bash
# Install from requirements.txt
uv pip install -r requirements.txt

# Review installed packages
uv pip freeze

# Manually create pyproject.toml with packages
```

---

## Migrate Existing Project

Step-by-step migration of a project using pip to UV.

```bash
# 1. In existing project directory
cd existing-project

# 2. Create uv environment
uv venv

# 3. Install from requirements.txt
uv pip install -r requirements.txt

# 4. Generate pyproject.toml (manual)
uv init --no-workspace

# 5. Add dependencies to pyproject.toml
uv add $(cat requirements.txt | grep -v '#' | cut -d'=' -f1)
```

---

## Comparison: pip vs UV

| Task | Traditional (pip) | UV |
|------|------------------|-----|
| Create venv | `python -m venv .venv` | `uv venv` |
| Activate | `source .venv/bin/activate` | Same |
| Install package | `pip install package` | `uv add package` |
| Install requirements | `pip install -r requirements.txt` | `uv pip install -r requirements.txt` |
| Freeze deps | `pip freeze > requirements.txt` | `uv pip freeze > requirements.txt` |
| Run tool | `python -m pytest` | `uv run pytest` |

**Key Advantages of UV:**
- ⚡ 10-100x faster than pip
- 🔒 Built-in dependency locking
- 🐍 Python version management
- 📦 Cleaner dependency specification in pyproject.toml

---

## Migration Checklist

- [ ] Install UV
- [ ] Create new venv with `uv venv`
- [ ] Install dependencies from requirements.txt
- [ ] Create/update pyproject.toml
- [ ] Test all functionality works
- [ ] Update CI/CD to use UV
- [ ] Update documentation
- [ ] Remove old requirements.txt (optional)
