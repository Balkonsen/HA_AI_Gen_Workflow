# Migration Map: SDR_stochastic → vrp-toolkit

## Source and Destination Paths

- **Source:** `/Users/yuchendu/Desktop/Github/heuristic in VRP/SDR_stochastic/new version/`
- **Destination:** `/Users/yuchendu/Desktop/Github/heuristic in VRP/vrp-toolkit/`

## File Mapping Table

| Original File | New Location | Refactoring Requirements |
|--------------|--------------|-------------------------|
| `instance.py` | `vrp_toolkit/problems/pdptw.py` | Extract generic parts from paper-specific code |
| `solution.py` | `vrp_toolkit/problems/pdptw.py` | Keep solution class, ensure it's decoupled from algorithm |
| `solvers.py` | `vrp_toolkit/algorithms/alns/solver.py` | Extract ALNS core algorithm |
| `operators.py` | `vrp_toolkit/algorithms/alns/operators.py` | Modularize operators, make them pluggable |
| `order_info.py` | `vrp_toolkit/data/generators.py` | Rename to OrderGenerator, generalize |
| `real_map.py` | `vrp_toolkit/data/map.py` | Keep as-is initially, refactor later |
| `demands.py` | `vrp_toolkit/data/generators.py` | Merge with generators module |
| `test.ipynb` | `tutorials/01_quickstart.ipynb` | Clean up for tutorial, add explanations |
| `sensitivity_test.ipynb` | `tutorials/05_sensitivity_analysis.ipynb` | Polish for educational clarity |

## Common Refactoring Patterns

### 1. Hardcoded Values to Extract
- Paper-specific parameters (e.g., specific campus locations, fixed battery levels)
- Magic numbers in algorithms
- File paths and dataset names
- Experiment-specific configurations

### 2. Code to Generalize
- Problem-specific constraints → Generic constraint framework
- Single instance types → Multiple problem variants (VRP, CVRP, PDPTW)
- Hardcoded operators → Pluggable operator interface
- Specific data formats → Generic data loaders

### 3. Configuration Extraction
Convert hardcoded values to function parameters or configuration dictionaries:

```python
# Before (hardcoded)
def solve_pdptw():
    battery_capacity = 100
    max_time = 480
    campus = "purdue"
    # ...

# After (parameterized)
def solve_pdptw(battery_capacity: float, max_time: float, location: str):
    # ...
```
