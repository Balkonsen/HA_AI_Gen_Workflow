# Scanning Scripts for Architecture Documentation

Helper scripts and patterns for automatically extracting architecture information from code.

## Script 1: Scan Module Structure

Extract public API from each module by parsing `__init__.py` files.

```python
# scripts/scan_modules.py
from pathlib import Path
import ast
import re

def extract_docstring(file_path):
    """Extract module docstring from Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
            docstring = ast.get_docstring(tree)
            return docstring or "No description"
    except:
        return "No description"

def extract_all_exports(file_path):
    """Extract __all__ list from __init__.py."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == '__all__':
                            if isinstance(node.value, ast.List):
                                exports = [elt.s for elt in node.value.elts
                                          if isinstance(elt, ast.Constant)]
                                return exports
        return []
    except:
        return []

def scan_module(module_path):
    """Scan a module directory and extract info."""
    init_file = module_path / "__init__.py"

    if not init_file.exists():
        return None

    # Extract info
    docstring = extract_docstring(init_file)
    exports = extract_all_exports(init_file)

    # Find Python files in module
    py_files = [f.stem for f in module_path.glob("*.py")
                if f.stem != "__init__" and not f.stem.startswith("_")]

    return {
        'name': module_path.name,
        'path': str(module_path.relative_to(Path.cwd())),
        'docstring': docstring,
        'exports': exports,
        'files': py_files
    }

def scan_all_modules(root_path="vrp-toolkit/vrp_toolkit"):
    """Scan all modules in vrp_toolkit."""
    root = Path(root_path)
    modules = []

    # Top-level modules
    for module_dir in sorted(root.iterdir()):
        if module_dir.is_dir() and not module_dir.name.startswith('_'):
            info = scan_module(module_dir)
            if info:
                modules.append(info)

                # Scan submodules (e.g., algorithms/alns/)
                for submodule_dir in module_dir.iterdir():
                    if submodule_dir.is_dir() and not submodule_dir.name.startswith('_'):
                        subinfo = scan_module(submodule_dir)
                        if subinfo:
                            subinfo['parent'] = module_dir.name
                            modules.append(subinfo)

    return modules

def print_module_summary(modules):
    """Print module summary for documentation."""
    for module in modules:
        print(f"\n### {module['path']}")
        print(f"**Purpose:** {module['docstring'].split('.')[0]}")

        if module['exports']:
            print(f"**Public API:**")
            for export in module['exports']:
                print(f"- `{export}`")
        else:
            print(f"**Files:** {', '.join(module['files'])}")

if __name__ == "__main__":
    modules = scan_all_modules()
    print("# Module Scan Results")
    print_module_summary(modules)
```

**Usage:**
```bash
python scripts/scan_modules.py > module_summary.txt
```

## Script 2: Extract Entry Points

Find public functions and classes that users interact with.

```python
# scripts/extract_entry_points.py
import ast
from pathlib import Path

def is_public_function(node):
    """Check if function is public (not starting with _)."""
    return isinstance(node, ast.FunctionDef) and not node.name.startswith('_')

def is_public_class(node):
    """Check if class is public."""
    return isinstance(node, ast.ClassDef) and not node.name.startswith('_')

def extract_function_signature(node):
    """Extract function signature from AST node."""
    args = []
    for arg in node.args.args:
        args.append(arg.arg)

    # Get return type if annotated
    return_type = ""
    if node.returns:
        if isinstance(node.returns, ast.Name):
            return_type = f" -> {node.returns.id}"

    return f"{node.name}({', '.join(args)}){return_type}"

def find_entry_points(file_path):
    """Find public functions and classes in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())

        functions = []
        classes = []

        for node in tree.body:
            if is_public_function(node):
                sig = extract_function_signature(node)
                doc = ast.get_docstring(node) or "No description"
                functions.append({
                    'name': node.name,
                    'signature': sig,
                    'doc': doc.split('\n')[0]  # First line only
                })
            elif is_public_class(node):
                doc = ast.get_docstring(node) or "No description"
                classes.append({
                    'name': node.name,
                    'doc': doc.split('\n')[0]
                })

        return functions, classes
    except:
        return [], []

def scan_entry_points(root_path="vrp-toolkit/vrp_toolkit"):
    """Scan all entry points in codebase."""
    root = Path(root_path)
    entry_points = {
        'functions': [],
        'classes': []
    }

    for py_file in root.rglob("*.py"):
        if py_file.stem.startswith('_'):
            continue

        module_path = py_file.relative_to(root).with_suffix('')
        module_name = str(module_path).replace('/', '.')

        funcs, classes = find_entry_points(py_file)

        for func in funcs:
            func['module'] = module_name
            entry_points['functions'].append(func)

        for cls in classes:
            cls['module'] = module_name
            entry_points['classes'].append(cls)

    return entry_points

def print_entry_points(entry_points):
    """Print entry points for documentation."""
    print("## Public Classes\n")
    for cls in sorted(entry_points['classes'], key=lambda x: x['module']):
        print(f"- `{cls['module']}.{cls['name']}` - {cls['doc']}")

    print("\n## Public Functions\n")
    for func in sorted(entry_points['functions'], key=lambda x: x['module']):
        print(f"- `{func['module']}.{func['name']}()` - {func['doc']}")

if __name__ == "__main__":
    entry_points = scan_entry_points()
    print_entry_points(entry_points)
```

## Script 3: Generate Dependency Graph

Analyze import statements to create dependency graph.

```python
# scripts/generate_dependency_graph.py
import ast
from pathlib import Path
from collections import defaultdict

def extract_imports(file_path, root_path):
    """Extract imports from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())

        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        # Filter to only vrp_toolkit imports
        toolkit_imports = [imp for imp in imports
                          if imp.startswith('vrp_toolkit')]

        return toolkit_imports
    except:
        return []

def build_dependency_graph(root_path="vrp-toolkit/vrp_toolkit"):
    """Build module dependency graph."""
    root = Path(root_path)
    dependencies = defaultdict(set)

    for py_file in root.rglob("*.py"):
        if py_file.stem.startswith('_') and py_file.stem != '__init__':
            continue

        module_path = py_file.relative_to(root).with_suffix('')
        module_name = str(module_path).replace('/', '.')
        module_name = 'vrp_toolkit.' + module_name

        imports = extract_imports(py_file, root)

        for imp in imports:
            # Get top-level module (e.g., vrp_toolkit.problems)
            parts = imp.split('.')
            if len(parts) >= 2:
                top_level = '.'.join(parts[:2])
                current_top = '.'.join(module_name.split('.')[:2])

                if top_level != current_top:  # Don't include self-dependencies
                    dependencies[current_top].add(top_level)

    return dependencies

def print_dependency_graph(dependencies):
    """Print dependency graph."""
    print("# Module Dependencies\n")

    # Group by layer
    layers = {
        'problems': 'vrp_toolkit.problems',
        'algorithms': 'vrp_toolkit.algorithms',
        'data': 'vrp_toolkit.data',
        'visualization': 'vrp_toolkit.visualization',
        'utils': 'vrp_toolkit.utils'
    }

    for layer_name, layer_module in layers.items():
        if layer_module in dependencies:
            deps = sorted(dependencies[layer_module])
            print(f"\n## {layer_name}/")
            print(f"**Depends on:**")
            for dep in deps:
                dep_name = dep.split('.')[-1]
                print(f"- {dep_name}/")
        else:
            print(f"\n## {layer_name}/")
            print("**Depends on:** None (leaf module)")

    # Check for violations
    print("\n## Architecture Violations\n")
    violations = []

    # Rule: Problems should not depend on Algorithms
    if 'vrp_toolkit.problems' in dependencies:
        if 'vrp_toolkit.algorithms' in dependencies['vrp_toolkit.problems']:
            violations.append("❌ problems/ depends on algorithms/ (violation!)")

    if not violations:
        print("✅ No violations detected")
    else:
        for v in violations:
            print(v)

if __name__ == "__main__":
    deps = build_dependency_graph()
    print_dependency_graph(deps)
```

## Script 4: Generate ASCII Diagrams

Create ASCII art diagrams for data flows.

```python
# scripts/generate_diagrams.py

def generate_layer_diagram():
    """Generate three-layer architecture diagram."""
    diagram = """
┌─────────────────────────────────────┐
│         Data Layer                  │
│  (generators, loaders, maps)        │
└──────────────┬──────────────────────┘
               │ creates instances
               ↓
┌─────────────────────────────────────┐
│       Problem Layer                 │
│  (PDPTWInstance, VRPProblem)        │
└──────────────┬──────────────────────┘
               │ consumed by
               ↓
┌─────────────────────────────────────┐
│      Algorithm Layer                │
│  (ALNSSolver, operators)            │
└──────────────┬──────────────────────┘
               │ produces
               ↓
┌─────────────────────────────────────┐
│    Visualization Layer              │
│  (PDPTWVisualizer, plots)           │
└─────────────────────────────────────┘
"""
    return diagram

def generate_data_flow_diagram():
    """Generate primary data flow diagram."""
    diagram = """
┌──────────────┐
│  Load/Generate│
│  Order Data   │
└───────┬───────┘
        │
        ▼
┌──────────────┐
│ PDPTWInstance│
│ (order_table)│
└───────┬───────┘
        │
        ▼
┌──────────────┐
│ ALNSSolver   │
│  .solve()    │
└───────┬───────┘
        │
        ├─→ Initial Solution (greedy)
        │
        ├─→ ALNS Loop:
        │   ├─ Destroy (remove requests)
        │   ├─ Repair (reinsert)
        │   └─ Accept (simulated annealing)
        │
        ▼
┌──────────────┐
│ VRPSolution  │
│ (best routes)│
└───────┬───────┘
        │
        ▼
┌──────────────┐
│ Visualize    │
│ (plot routes)│
└──────────────┘
"""
    return diagram

if __name__ == "__main__":
    print("# Architecture Diagrams\n")
    print("## Three-Layer Architecture\n")
    print(generate_layer_diagram())
    print("\n## Primary Data Flow\n")
    print(generate_data_flow_diagram())
```

## Script 5: Update ARCHITECTURE_MAP.md

Automatically insert scanned information into ARCHITECTURE_MAP.md.

```python
# scripts/update_architecture_map.py
import re
from pathlib import Path

def update_module_guide(architecture_file, modules):
    """Update Module Guide section with scanned modules."""
    content = architecture_file.read_text()

    # Find Module Guide section
    pattern = r'(## Module Guide.*?)(##|\Z)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        # Generate new module guide
        guide = "## Module Guide\n\n"

        for module in modules:
            guide += f"### `{module['path']}`\n\n"
            guide += f"**Purpose:** {module['docstring'].split('.')[0]}\n\n"

            if module['exports']:
                guide += "**Public API:**\n"
                for export in module['exports']:
                    guide += f"- `{export}`\n"
                guide += "\n"

        # Replace
        new_content = content[:match.start(1)] + guide + match.group(2) + content[match.end():]
        architecture_file.write_text(new_content)
        print("✅ Updated Module Guide section")
    else:
        print("❌ Could not find Module Guide section")

# Usage:
# from scan_modules import scan_all_modules
# modules = scan_all_modules()
# update_module_guide(Path(".claude/ARCHITECTURE_MAP.md"), modules)
```

## Manual Workflow

If automation is too complex, use this manual checklist:

### Step 1: List all modules
```bash
cd vrp-toolkit/vrp_toolkit
find . -name "__init__.py" | sort
```

### Step 2: For each module, extract:
- [ ] Docstring (from `__init__.py`)
- [ ] Public classes (from `__all__` or file inspection)
- [ ] Public functions (from `__all__` or file inspection)

### Step 3: Document dependencies
```bash
# Find all imports in a module
grep -r "from vrp_toolkit" vrp_toolkit/problems/
```

### Step 4: Manually update ARCHITECTURE_MAP.md
- Copy template from `architecture_template.md`
- Fill in each section with extracted info
- Add examples from tutorials/

---

**Recommended approach:** Start with manual workflow, then gradually automate repetitive parts as needed.
