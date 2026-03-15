# Migration Guide - SDR_stochastic to VRP Toolkit

Complete technical guide for migrating code from research codebase to reusable toolkit.

---

## 📍 Source Code Locations

**Original Codebase:**
```
/Users/yuchendu/Desktop/Github/heuristic in VRP/SDR_stochastic/new version/
```

**New Codebase:**
```
/Users/yuchendu/Desktop/Github/heuristic in VRP/vrp-toolkit/
```

---

## 📋 File Mapping

Complete mapping of 9 files from original to new locations:

| # | Original File | New Location | Layer | Refactoring Needed |
|---|--------------|--------------|-------|-------------------|
| 1 | `instance.py` | `vrp_toolkit/problems/pdptw.py` | Problem | Extract generic parts |
| 2 | `solution.py` | `vrp_toolkit/problems/pdptw.py` | Problem | Keep solution class |
| 3 | `solvers.py` | `vrp_toolkit/algorithms/alns/solver.py` | Algorithm | Extract ALNS core |
| 4 | `operators.py` | `vrp_toolkit/algorithms/alns/operators.py` | Algorithm | Modularize operators |
| 5 | `order_info.py` | `vrp_toolkit/data/generators.py` | Data | Rename to OrderGenerator |
| 6 | `real_map.py` | `vrp_toolkit/data/map.py` | Data | Keep as-is initially |
| 7 | `demands.py` | `vrp_toolkit/data/generators.py` | Data | Merge with generators |
| 8 | `test.ipynb` | `tutorials/01_quickstart.ipynb` | Tutorial | Clean up for tutorial |
| 9 | `sensitivity_test.ipynb` | `tutorials/05_sensitivity_analysis.ipynb` | Tutorial | Polish |

**Total:** 9 files to migrate

---

## 🏗️ Architecture Layer Mapping

### Three-Layer Architecture

Files map to one of three layers:

**1. Problem Layer** (`vrp_toolkit/problems/`)
- `instance.py` → `pdptw.py`
- `solution.py` → `pdptw.py`
- Purpose: Define problem instances independent of algorithms

**2. Algorithm Layer** (`vrp_toolkit/algorithms/`)
- `solvers.py` → `alns/solver.py`
- `operators.py` → `alns/operators.py`
- Purpose: Solving algorithms with unified Solver interface

**3. Data Layer** (`vrp_toolkit/data/`)
- `order_info.py` → `generators.py` (as OrderGenerator)
- `demands.py` → `generators.py` (as DemandGenerator)
- `real_map.py` → `map.py`
- Purpose: Data generation, loading, and OSMnx integration

**Tutorials:**
- `test.ipynb` → `tutorials/01_quickstart.ipynb`
- `sensitivity_test.ipynb` → `tutorials/05_sensitivity_analysis.ipynb`

---

## 📅 Migration Phases

### Phase 1: Minimal Migration ✅ COMPLETE

**Objective:** Copy files with minimal changes to make project runnable

**Tasks:**
- [x] Create directory structure
- [x] Create CLAUDE.md and MIGRATION_LOG.md
- [x] Create 10 custom skills for workflow automation
- [x] Copy core files with minimal changes
- [x] Create basic README and quickstart tutorial
- [x] Make it installable (`pip install -e .`)

**Outcome:** All 9 files migrated, package installable

---

### Phase 2: Refactoring 🚧 IN PROGRESS (90%)

**Objective:** Decouple from paper-specific logic, create clean architecture

**Completed:**
- [x] Separate problem definition from algorithm
- [x] Create unified Solver interface (VRPProblem, VRPSolution base classes)
- [x] Adapt ALNS to use new interface (ALNSSolver class)
- [x] Update tutorials to use new architecture
- [x] Add configuration file support
- [x] Improve visualization

**In Progress:**
- [ ] Create comprehensive test suite
- [ ] Test ALNSSolver with other VRPProblem implementations

**Outcome:** Clean separation between Problem/Algorithm/Data layers

---

### Phase 3: Extension ⏳ NOT STARTED

**Objective:** Add new features and expand toolkit capabilities

**Planned:**
- [ ] OSMnx integration for real-world maps
- [ ] Add second algorithm (GA or TabuSearch)
- [ ] Benchmark suite (Solomon, Li & Lim instances)
- [ ] Website project page content

**Outcome:** Production-ready toolkit with multiple algorithms and datasets

---

## 🔧 Refactoring Guidelines

### General Principles

**1. Extract Hardcoded Values**
```python
# Before (hardcoded)
depot_location = (0, 0)
vehicle_capacity = 15

# After (parameterized)
def __init__(self, depot_location, vehicle_capacity):
    self.depot = depot_location
    self.capacity = vehicle_capacity
```

**2. Decouple from Paper Logic**
```python
# Before (SISR-specific)
def validate_solution(self, solution):
    if not self.check_sisr_constraints(solution):
        return False

# After (generic)
def validate_solution(self, solution):
    if not self.check_time_windows(solution):
        return False
    if not self.check_capacity(solution):
        return False
```

**3. Separate Concerns**
```python
# Before (mixed concerns)
class Instance:
    def solve(self):  # Algorithm in Problem class
        return alns(self)

# After (separated)
class Instance(VRPProblem):  # Problem layer
    pass

class ALNSSolver(Solver):  # Algorithm layer
    def solve(self, problem: VRPProblem):
        pass
```

**4. Add Documentation**
```python
# Add type hints
def calculate_distance(self, node1: Node, node2: Node) -> float:
    pass

# Add docstrings (Google style)
def calculate_distance(self, node1: Node, node2: Node) -> float:
    """Calculate Euclidean distance between two nodes.

    Args:
        node1: First node
        node2: Second node

    Returns:
        Euclidean distance between nodes
    """
    pass
```

---

## 📊 Migration Workflow

### For Each File

**1. Read Original File**
- Understand purpose and functionality
- Identify dependencies
- Note hardcoded values

**2. Plan Refactoring**
- Determine target layer (Problem/Algorithm/Data)
- Identify values to parameterize
- List paper-specific logic to generalize

**3. Create New File**
- Copy to new location
- Rename classes/functions appropriately
- Add proper imports

**4. Refactor**
- Extract hardcoded values to parameters
- Generalize paper-specific logic
- Add type hints and docstrings
- Separate concerns if needed

**5. Verify**
- Code compiles without errors
- Imports work correctly
- Run tests if available

**6. Document**
- Log to MIGRATION_LOG.md
- Update TASK_BOARD.md via update-task-board

---

## 🎯 Common Patterns

### Pattern 1: Instance to Problem Layer

**Original:** `instance.py` with hardcoded parameters

**Refactoring:**
1. Extract depot, capacity, time windows as parameters
2. Separate validation from instance definition
3. Implement VRPProblem interface
4. Move to `vrp_toolkit/problems/pdptw.py`

### Pattern 2: Solver to Algorithm Layer

**Original:** `solvers.py` tightly coupled to Instance

**Refactoring:**
1. Accept generic VRPProblem instead of specific Instance
2. Use problem.get_nodes() instead of instance.nodes
3. Implement Solver interface
4. Move to `vrp_toolkit/algorithms/alns/solver.py`

### Pattern 3: Data Generator

**Original:** `order_info.py` with fixed format

**Refactoring:**
1. Rename to OrderGenerator class
2. Add configuration parameters
3. Generalize output format
4. Move to `vrp_toolkit/data/generators.py`

### Pattern 4: Tutorial Cleanup

**Original:** `test.ipynb` with exploratory code

**Refactoring:**
1. Remove debugging code
2. Add explanatory markdown cells
3. Structure as tutorial (intro → example → exercises)
4. Move to `tutorials/01_quickstart.ipynb`

---

## ⚠️ Common Issues

### Issue 1: Circular Imports

**Problem:** Instance imports Solution, Solution imports Instance

**Solution:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .solution import Solution
```

### Issue 2: Hardcoded Paths

**Problem:** `data_path = "/Users/user/Desktop/data"`

**Solution:**
```python
def __init__(self, data_path: str = None):
    self.data_path = data_path or Path.cwd() / "data"
```

### Issue 3: Mixed Responsibilities

**Problem:** Instance class contains solving logic

**Solution:** Separate into Instance (Problem layer) and Solver (Algorithm layer)

---

## 📝 Documentation Requirements

**For each migrated file, document:**
1. Source and destination paths
2. Key changes made
3. Issues encountered and solutions
4. Verification steps taken

**Use update-migration-log skill** to maintain MIGRATION_LOG.md

---

## 🔗 Related Documents

- **Migration history:** `.claude/MIGRATION_LOG.md`
- **Task tracking:** `.claude/TASK_BOARD.md`
- **Architecture details:** `.claude/skills/maintain-data-structures/references/`
- **File mapping:** `.claude/skills/migrate-module/references/migration_map.md`

---

## 📈 Progress Tracking

**Track progress using:**
- TASK_BOARD.md - Overall migration status
- MIGRATION_LOG.md - Detailed migration entries
- update-task-board skill - Sync status based on logs

**Current Status:** Phase 2 - 90% complete (1 file testing in progress)
