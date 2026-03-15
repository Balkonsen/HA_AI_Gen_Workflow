# ARCHITECTURE_MAP.md Template

Use this template when creating/updating the system architecture documentation.

```markdown
# VRP-Toolkit Architecture Map

**Last Updated:** [YYYY-MM-DD]
**Version:** [X.Y.Z]
**Status:** [Draft/Stable/Evolving]

---

## System Overview

[2-3 paragraph introduction explaining:]
- What is VRP-Toolkit?
- What problems does it solve?
- Who is it for (researchers, students, practitioners)?
- Key design philosophy (e.g., "educational focus", "three-layer architecture")

**Example:**
> VRP-Toolkit is a Python framework for solving Vehicle Routing Problems (VRP) and its variants (VRPTW, PDPTW, CVRP). Originally developed from academic research code, it has been refactored into a reusable, teachable system with clear separation between problem definitions, solving algorithms, and data management.
>
> The toolkit is designed for researchers and students who want to experiment with VRP algorithms without getting lost in implementation details. It emphasizes learning through tutorials and interactive exploration rather than dense code reading.

---

## Three-Layer Architecture

The toolkit follows a strict three-layer design:

### 1. Problem Layer (`vrp_toolkit/problems/`)

**Purpose:** Define VRP problems independent of how they're solved

**Responsibilities:**
- Problem instance creation (`PDPTWInstance`, `VRPInstance`)
- Solution representation (`PDPTWSolution`, `VRPSolution`)
- Constraint validation (time windows, capacity, etc.)
- Instance/solution serialization (to/from files)

**Key abstractions:**
- `VRPProblem` - Abstract interface for all problem types
- `VRPSolution` - Abstract interface for all solution types

**Dependencies:** None (problems don't know about algorithms)

### 2. Algorithm Layer (`vrp_toolkit/algorithms/`)

**Purpose:** Implement solving algorithms that work on VRP problems

**Responsibilities:**
- Algorithm implementations (ALNS, Genetic Algorithm, Tabu Search)
- Operators (removal, repair, local search)
- Configuration management (`ALNSConfig`, etc.)
- Solution improvement

**Key abstractions:**
- `Solver` - Base class with `solve(problem) → solution` interface
- `ConfigurableSolver` - Solver with configuration support

**Dependencies:** Depends on Problem layer (consumes VRPProblem, produces VRPSolution)

### 3. Data Layer (`vrp_toolkit/data/`)

**Purpose:** Generate, load, and manage problem data

**Responsibilities:**
- Synthetic data generation (`OrderGenerator`, `DemandGenerator`)
- Real-world data loading (CSV files, OSMnx integration)
- Benchmark datasets (Solomon, Li & Lim)
- Distance/time matrix computation

**Dependencies:** Depends on Problem layer (creates problem instances)

### 4. Visualization Layer (`vrp_toolkit/visualization/`)

**Purpose:** Visualize problems, solutions, and algorithm behavior

**Responsibilities:**
- Route visualization (2D maps, network graphs)
- Convergence plots (cost vs. iteration)
- Algorithm diagnostics (operator usage, acceptance rate)
- Interactive visualizations (Streamlit playground)

**Dependencies:** Depends on Problem and Algorithm layers

---

## Module Guide

### `vrp_toolkit/problems/`

**Purpose:** VRP problem definitions and solution representations

**Key Files:**
- `pdptw.py` - Pickup-Delivery Problem with Time Windows
- `vrp.py` - Basic Vehicle Routing Problem (planned)
- `base.py` - Abstract interfaces (VRPProblem, VRPSolution)

**Public API:**
- `PDPTWInstance(order_table, ...)` - Create PDPTW problem
- `PDPTWSolution(routes, instance)` - Create/validate solution
- `VRPProblem` - Interface for custom problems
- `VRPSolution` - Interface for custom solutions

**Links:**
- Data structures: See `maintain-data-structures` skill → `problem_layer.md`

### `vrp_toolkit/algorithms/`

**Purpose:** Solving algorithms for VRP problems

**Key Files:**
- `base.py` - Solver interfaces (Solver, ConfigurableSolver)
- `alns/` - Adaptive Large Neighborhood Search
  - `solver.py` - ALNS implementation
  - `operators.py` - Removal/repair operators
- `genetic/` - Genetic algorithm (planned)

**Public API:**
- `ALNSSolver(config)` - ALNS solver
- `ALNSConfig(...)` - ALNS configuration
- `greedy_insertion_initial_solution(...)` - Initial solution generator

**Links:**
- Data structures: See `maintain-data-structures` skill → `algorithm_layer.md`

### `vrp_toolkit/data/`

**Purpose:** Data generation and loading

**Key Files:**
- `generators.py` - Synthetic data generators
- `map.py` - Synthetic maps (RealMap)
- `osmnx_integration.py` - Real-world street network data
- `benchmarks.py` - Standard benchmark datasets (planned)

**Public API:**
- `OrderGenerator.generate()` - Generate order data
- `DemandGenerator.generate()` - Generate demand data
- `RealMap(...)` - Create synthetic map
- `OSMnxNetworkLoader.load(...)` - Load real street network

**Links:**
- Data structures: See `maintain-data-structures` skill → `data_layer.md`

### `vrp_toolkit/visualization/`

**Purpose:** Visualization tools

**Key Files:**
- `problem.py` - Problem visualizers (PDPTWVisualizer)
- `algorithm.py` - Algorithm visualizers (ALNSVisualizer)
- `data.py` - Data visualizers (MapVisualizer)

**Public API:**
- `PDPTWVisualizer.visualize(instance, solution)` - Plot routes
- `plot_convergence(cost_history)` - Plot cost over iterations

### `vrp_toolkit/utils/`

**Purpose:** Common utilities

**Key Files:**
- `config.py` - Configuration system (VRPConfig, ConfigLoader)
- `validation.py` - Input validation helpers

---

## Entry Points

How to use the toolkit - common workflows:

### 1. Create a PDPTW Problem from Data

```python
import pandas as pd
from vrp_toolkit.problems.pdptw import PDPTWInstance

# Load order data
order_table = pd.read_csv("orders.csv")

# Create instance
instance = PDPTWInstance(order_table=order_table)

print(f"Created instance with {instance.n} orders")
```

### 2. Generate Synthetic Problem

```python
from vrp_toolkit.data.generators import OrderGenerator, DemandGenerator
from vrp_toolkit.data.map import RealMap

# Create synthetic map
real_map = RealMap(num_customers=20, num_restaurants=5, seed=42)

# Generate demands
demand_gen = DemandGenerator(num_customers=20, num_restaurants=5, seed=42)
demand_table = demand_gen.generate()

# Generate orders
order_gen = OrderGenerator(
    real_map=real_map,
    demand_table=demand_table,
    time_params={'time_window_length': 30, 'service_time': 5},
    robot_speed=1.0
)
order_table = order_gen.generate()

# Create instance
instance = PDPTWInstance(order_table=order_table)
```

### 3. Solve with ALNS

```python
from vrp_toolkit.algorithms.alns import ALNSSolver, ALNSConfig
from vrp_toolkit.algorithms.base import PDPTWProblemAdapter

# Configure ALNS
config = ALNSConfig(
    max_iterations=1000,
    start_temp=10.0,
    cooling_rate=0.95
)

# Wrap instance in adapter
problem = PDPTWProblemAdapter(instance)

# Solve
solver = ALNSSolver(config)
solution = solver.solve(problem, num_vehicles=3, battery_capacity=10.0)

print(f"Solution cost: {solution.objective_value}")
```

### 4. Visualize Solution

```python
from vrp_toolkit.visualization.problem import PDPTWVisualizer
import matplotlib.pyplot as plt

# Create visualizer
visualizer = PDPTWVisualizer(instance)

# Plot solution
fig, ax = plt.subplots(figsize=(10, 8))
visualizer.visualize(solution, ax=ax)
plt.show()
```

### 5. Save/Load Experiment

```python
import json

# Save configuration and results
experiment = {
    'config': config.__dict__,
    'solution': {
        'routes': [list(route) for route in solution.routes],
        'cost': solution.objective_value
    },
    'metrics': {
        'runtime': 45.2,
        'iterations': 1000,
        'feasible': solution.is_feasible()
    }
}

with open('experiment_001.json', 'w') as f:
    json.dump(experiment, f, indent=2)
```

---

## Data Flows

### Primary Flow: Problem → Solution

```
┌──────────────┐
│  Data Layer  │  Generate/load order data
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Problem Layer │  Create PDPTWInstance
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Algorithm     │  Solve: ALNSSolver.solve(instance)
│  Layer       │    → greedy initial solution
└──────┬───────┘    → ALNS iterations (destroy/repair)
       │            → return best solution
       ▼
┌──────────────┐
│Visualization │  Visualize routes and metrics
│   Layer      │
└──────────────┘
```

### Configuration Flow

```
User Input
   ↓
Streamlit UI / Python dict
   ↓
ALNSConfig(max_iterations=1000, ...)
   ↓
ALNSSolver.__init__(config)
   ↓
ALNS.run() → uses config.start_temp, config.cooling_rate, etc.
```

### Solution Construction Flow

```
PDPTWInstance
   ↓
greedy_insertion_initial_solution()
   ├─ Create empty routes
   ├─ Sort requests by time window
   ├─ Insert each request into best position
   └─ Return initial solution
      ↓
ALNS.run()
   ├─ Destroy: Remove requests (Shaw/Random/Worst/SISR)
   ├─ Repair: Reinsert requests (Greedy/Regret)
   ├─ Accept: Simulated annealing criterion
   └─ Repeat until max_iterations
      ↓
Best solution found
```

**Detailed flows:** See `.claude/docs/data_flows.md`

---

## Key Abstractions

### VRPProblem Interface

Abstract interface that all problem types must implement:

```python
class VRPProblem(ABC):
    @abstractmethod
    def get_num_nodes(self) -> int: ...

    @abstractmethod
    def get_distance(self, i: int, j: int) -> float: ...

    @abstractmethod
    def get_time(self, i: int, j: int) -> float: ...

    # ... other methods
```

**Purpose:** Allows algorithms to work with any problem type (PDPTW, VRP, CVRP) without knowing implementation details.

### VRPSolution Interface

Abstract interface for solutions:

```python
class VRPSolution(ABC):
    @abstractmethod
    def get_routes(self) -> List[List[int]]: ...

    @abstractmethod
    def objective_value(self) -> float: ...

    @abstractmethod
    def is_feasible(self) -> bool: ...
```

**Purpose:** Provides standard way to query solution quality and feasibility.

### Solver Interface

All algorithms implement this interface:

```python
class Solver(ABC):
    @abstractmethod
    def solve(self, problem: VRPProblem, **kwargs) -> VRPSolution: ...
```

**Purpose:** Unified API for all solving algorithms.

### Adapter Pattern

Used to bridge old specific interfaces with new generic interfaces:

- `PDPTWProblemAdapter`: Wraps `PDPTWInstance` to implement `VRPProblem`
- `PDPTWSolutionAdapter`: Wraps `PDPTWSolution` to implement `VRPSolution`

**Purpose:** Backward compatibility while migrating to new architecture.

---

## Module Dependencies

```
        Data
         ↓
      Problem ←─────────┐
         ↓              │
     Algorithm          │
         ↓              │
    Visualization ──────┘

Utils (used by all)
```

**Dependency rules:**
- ✅ Higher layers can depend on lower layers
- ❌ Lower layers cannot depend on higher layers
- ✅ All layers can use Utils

**No circular dependencies** - verified by import analysis

**Detailed dependency graph:** See `.claude/docs/module_dependencies.md`

---

## Extension Guide

### Adding a New Problem Type

1. Create `vrp_toolkit/problems/cvrp.py`
2. Define `CVRPInstance` class inheriting from `VRPProblem`
3. Implement required methods (get_num_nodes, get_distance, etc.)
4. Add exports to `vrp_toolkit/problems/__init__.py`
5. Create tutorial `tutorials/XX_cvrp_problems.ipynb`
6. Update this document (ARCHITECTURE_MAP.md)

### Adding a New Algorithm

1. Create `vrp_toolkit/algorithms/genetic/solver.py`
2. Define `GeneticSolver` class inheriting from `ConfigurableSolver`
3. Implement `solve(problem) → solution` method
4. Create `GeneticConfig` dataclass for parameters
5. Add exports to `vrp_toolkit/algorithms/__init__.py`
6. Create tutorial `tutorials/XX_genetic_algorithm.ipynb`
7. Update this document

### Adding a New Operator

1. Add method to `vrp_toolkit/algorithms/alns/operators.py`
2. Update `RemovalOperators` or `RepairOperators` class
3. Add operator to ALNS operator selection logic
4. Create unit test in `tests/unit/algorithms/alns/test_operators.py`
5. Document in algorithm layer data structures

---

## Quick Reference

| Task | Code |
|------|------|
| Load instance from CSV | `instance = PDPTWInstance(order_table=pd.read_csv("data.csv"))` |
| Generate synthetic instance | `instance = generate_pdptw_instance(num_orders=20, seed=42)` |
| Configure ALNS | `config = ALNSConfig(max_iterations=1000, start_temp=10.0)` |
| Solve problem | `solution = solver.solve(problem)` |
| Get solution cost | `cost = solution.objective_value` |
| Check feasibility | `is_feasible = solution.is_feasible()` |
| Visualize routes | `PDPTWVisualizer(instance).visualize(solution)` |
| Plot convergence | `plt.plot(alns.cost_history)` |
| Save experiment | `json.dump({'config': ..., 'solution': ...}, file)` |

---

## Related Documentation

- **Data Structures:** See `maintain-data-structures` skill for detailed class documentation
- **Tutorials:** See `tutorials/` directory for step-by-step guides
- **Playground:** See `playground/VISION.md` for interactive learning philosophy
- **Migration Guide:** See `migrate-module` skill for migration history

**Last Updated:** [YYYY-MM-DD]
```
