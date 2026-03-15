# VRP Toolkit Architecture Guide

## Three-Layer Architecture

The toolkit follows a clean separation of concerns across three layers:

### 1. Problem Layer (`vrp_toolkit/problems/`)
- **Purpose:** Define problem instances independent of solving algorithms
- **Components:** Nodes, constraints, objectives
- **Examples:** `PDPTWInstance`, `VRPTWInstance`, `CVRPInstance`

**Key principle:** Problem definitions should not know about solution algorithms.

### 2. Algorithm Layer (`vrp_toolkit/algorithms/`)
- **Purpose:** Implement solving algorithms with pluggable components
- **Interface:** `Solver.solve(instance) -> Solution`
- **Components:** Removal operators, repair operators, local search methods

**Key principle:** Algorithms work with abstract problem instances through common interfaces.

### 3. Data Layer (`vrp_toolkit/data/`)
- **Purpose:** Data generation, loading, and transformation
- **Components:**
  - Synthetic data generators
  - Benchmark dataset loaders
  - OSMnx real-world map integration

**Key principle:** Separate data concerns from problem modeling and solving.

## Core Abstractions

### Instance Interface
```python
class Instance:
    """Base class for problem instances"""
    def __init__(self, nodes, constraints, objectives):
        self.nodes = nodes
        self.constraints = constraints
        self.objectives = objectives
```

### Solution Interface
```python
class Solution:
    """Base class for solutions"""
    def __init__(self, routes):
        self.routes = routes

    def is_feasible(self) -> bool:
        """Check if solution satisfies all constraints"""
        pass

    def objective_value(self) -> float:
        """Calculate objective function value"""
        pass

    def plot(self):
        """Visualize the solution"""
        pass
```

### Solver Interface
```python
class Solver:
    """Base class for solving algorithms"""
    def solve(self, instance: Instance) -> Solution:
        """Solve the problem instance and return solution"""
        pass
```

## Code Style Guidelines

### Type Hints
- Use where helpful for clarity
- Not required everywhere
- Focus on public APIs

### Docstrings
- Required for public APIs only
- Use Google or NumPy style
- Include parameters, return values, and examples

### Comments
- Only for non-obvious logic
- Prefer self-documenting code
- Avoid redundant comments

### Naming Conventions
- Classes: `PascalCase` (e.g., `PDPTWInstance`)
- Functions/methods: `snake_case` (e.g., `solve_instance`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_ITERATIONS`)
- Private members: `_leading_underscore`

## Configuration Management

Prefer simple, explicit configurations:

**Good:**
```python
from dataclasses import dataclass

@dataclass
class ALNSConfig:
    max_iterations: int = 1000
    destroy_rate: float = 0.3
    temperature: float = 10000
```

**Avoid:**
- Config classes with 50+ parameters
- Deep nested configurations
- Magic string-based configuration
