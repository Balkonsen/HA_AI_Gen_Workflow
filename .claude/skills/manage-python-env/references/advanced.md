# UV Advanced Usage

Advanced features and patterns for power users.

## Multiple Environments

Create and manage multiple virtual environments for different purposes.

```bash
# Create environment with different name
uv venv .venv-dev

# Activate specific environment
source .venv-dev/bin/activate

# Install different dependencies
uv add specific-package
```

**Use cases:**
- Separate environments for development vs production
- Testing with different dependency versions
- Isolated environments for different projects

---

## Dependency Groups

Organize dependencies into logical groups.

```bash
# Install specific group
uv sync --group dev

# Install multiple groups
uv sync --group dev --group osmnx

# Install all groups
uv sync --all-groups
```

**Example pyproject.toml:**
```toml
[project.optional-dependencies]
dev = ["pytest", "black", "ruff"]
osmnx = ["osmnx", "geopandas", "folium"]
docs = ["sphinx", "sphinx-rtd-theme"]
```

---

## Build and Publish

Package and distribute your project.

```bash
# Build package
uv build

# Publish to PyPI (requires twine)
uv run twine upload dist/*
```

**Publishing workflow:**
1. Update version in `pyproject.toml`
2. Run tests: `uv run pytest`
3. Build: `uv build`
4. Publish: `uv run twine upload dist/*`

---

## Integration with Other Skills

**Works with:**
- **build-session-context**: Check Python environment status
- **migrate-module**: Ensure dependencies are installed
- **osmnx-integration**: Install OSMnx and geo packages

**Example project setup:**
```bash
# 1. Initialize project
uv init vrp-toolkit
cd vrp-toolkit

# 2. Setup environment
uv venv
source .venv/bin/activate

# 3. Install dependencies
uv add numpy pandas matplotlib networkx
uv add --dev pytest black ruff jupyter
uv add osmnx geopandas  # For OSMnx integration

# 4. Install in editable mode
uv pip install -e .

# 5. Verify installation
uv run python -c "from vrp_toolkit import *; print('OK')"

# 6. Start development
uv run jupyter lab
```
