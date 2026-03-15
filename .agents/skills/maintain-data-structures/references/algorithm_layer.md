# Algorithm Layer Data Structures

**Purpose:** Data structures for implementing solving algorithms.

**Location:** `vrp_toolkit/algorithms/`

---

## Solver

Base interface for all solving algorithms.

### Interface

```python
class Solver:
    """Base class for solving algorithms"""

    def solve(self, instance: Instance) -> Solution:
        """Solve the problem instance and return solution

        Args:
            instance: Problem instance to solve

        Returns:
            Solution object containing routes and objective value
        """
        raise NotImplementedError
```

### Common Implementations

- `ALNSSolver` - Adaptive Large Neighborhood Search
- `GASolver` - Genetic Algorithm (planned)
- `TabuSearchSolver` - Tabu Search (planned)

---

## ALNSSolver

Adaptive Large Neighborhood Search solver.

### Interface

```python
class ALNSSolver(Solver):
    """ALNS algorithm implementation"""

    def __init__(self, config: ALNSConfig):
        self.config = config
        self.destroy_operators = []
        self.repair_operators = []
        self.local_search_operators = []

    def solve(self, instance: Instance) -> Solution:
        """Run ALNS algorithm"""
        pass
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `config` | `ALNSConfig` | Algorithm configuration parameters |
| `destroy_operators` | `List[DestroyOperator]` | Operators for removing nodes |
| `repair_operators` | `List[RepairOperator]` | Operators for reinserting nodes |
| `local_search_operators` | `List[LocalSearchOperator]` | Improvement operators |
| `operator_weights` | `Dict[str, float]` | Adaptive weights for operator selection |
| `current_solution` | `Solution` | Best solution found so far |
| `temperature` | `float` | Simulated annealing temperature |

---

## ALNSConfig

Configuration for ALNS algorithm.

### Interface

```python
from dataclasses import dataclass

@dataclass
class ALNSConfig:
    """ALNS algorithm configuration"""

    max_iterations: int = 1000
    destroy_rate: float = 0.3  # Fraction of nodes to remove
    temperature_initial: float = 10000.0
    temperature_decay: float = 0.95
    weight_best: float = 33.0  # Weight update for new best
    weight_better: float = 9.0  # Weight update for improvement
    weight_accepted: float = 3.0  # Weight update for accepted
    weight_rejected: float = 0.0  # Weight update for rejected
    time_limit: float = 300.0  # Time limit in seconds
    random_seed: int = 42
```

### Example Usage

```python
# Create custom configuration
config = ALNSConfig(
    max_iterations=5000,
    destroy_rate=0.4,
    temperature_initial=15000.0,
    time_limit=600.0
)

# Use with solver
solver = ALNSSolver(config)
solution = solver.solve(instance)
```

---

## Operator

Base class for ALNS operators.

### DestroyOperator

Removes nodes from a solution.

```python
class DestroyOperator:
    """Base class for destroy operators"""

    def __init__(self, name: str):
        self.name = name
        self.weight = 1.0  # Adaptive weight

    def destroy(
        self,
        solution: Solution,
        destroy_count: int,
        instance: Instance
    ) -> Tuple[Solution, List[int]]:
        """Remove nodes from solution

        Args:
            solution: Current solution
            destroy_count: Number of nodes to remove
            instance: Problem instance

        Returns:
            (partial_solution, removed_nodes)
        """
        raise NotImplementedError
```

#### Common Destroy Operators

| Operator | Description |
|----------|-------------|
| `RandomDestroy` | Remove random nodes |
| `WorstDestroy` | Remove nodes with highest cost |
| `ShawDestroy` | Remove related nodes (similar location/time) |
| `RouteDestroy` | Remove entire routes |
| `SISRDestroy` | Sequential Insertion Sequential Removal (paper-specific) |

### RepairOperator

Reinserts removed nodes into a solution.

```python
class RepairOperator:
    """Base class for repair operators"""

    def __init__(self, name: str):
        self.name = name
        self.weight = 1.0

    def repair(
        self,
        partial_solution: Solution,
        removed_nodes: List[int],
        instance: Instance
    ) -> Solution:
        """Reinsert nodes into solution

        Args:
            partial_solution: Solution with nodes removed
            removed_nodes: Nodes to reinsert
            instance: Problem instance

        Returns:
            Complete solution
        """
        raise NotImplementedError
```

#### Common Repair Operators

| Operator | Description |
|----------|-------------|
| `GreedyRepair` | Insert nodes at lowest-cost positions |
| `RegretRepair` | Use regret heuristic for insertion |
| `RandomRepair` | Insert nodes at random positions |

### LocalSearchOperator

Improves a complete solution.

```python
class LocalSearchOperator:
    """Base class for local search operators"""

    def improve(self, solution: Solution, instance: Instance) -> Solution:
        """Apply local improvement to solution"""
        raise NotImplementedError
```

#### Common Local Search Operators

| Operator | Description |
|----------|-------------|
| `TwoOpt` | Swap two edges in a route |
| `Relocate` | Move a node to different position |
| `Exchange` | Swap two nodes |
| `OrOpt` | Move sequence of nodes |

---

## SearchState

Tracks the state during search.

### Interface

```python
class SearchState:
    """State tracker for iterative search algorithms"""

    def __init__(self, initial_solution: Solution):
        self.current_solution = initial_solution
        self.best_solution = initial_solution.copy()
        self.iteration = 0
        self.temperature = None  # For simulated annealing
        self.operator_statistics = {}
        self.objective_history = []
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `current_solution` | `Solution` | Current working solution |
| `best_solution` | `Solution` | Best solution found so far |
| `iteration` | `int` | Current iteration number |
| `temperature` | `float` | Simulated annealing temperature |
| `operator_statistics` | `Dict[str, OperatorStats]` | Usage statistics per operator |
| `objective_history` | `List[float]` | Objective value over iterations |
| `time_elapsed` | `float` | Time spent so far |

### Methods

```python
def update_best(self, solution: Solution):
    """Update best solution if improved"""
    if solution.objective_value() < self.best_solution.objective_value():
        self.best_solution = solution.copy()

def accept_solution(self, solution: Solution, criterion: str = 'simulated_annealing'):
    """Decide whether to accept new solution"""
    if criterion == 'simulated_annealing':
        # Use SA acceptance criterion
        pass
```

---

## OperatorStats

Statistics for an operator.

### Interface

```python
@dataclass
class OperatorStats:
    """Statistics tracking for an operator"""

    name: str
    times_used: int = 0
    times_best: int = 0      # Found new best solution
    times_better: int = 0    # Improved current solution
    times_accepted: int = 0  # Accepted by criterion
    times_rejected: int = 0  # Rejected
    average_time: float = 0.0  # Average execution time
```

---

## Route Representation

In the algorithm layer, routes are typically represented as lists of node IDs:

```python
Route = List[int]  # e.g., [0, 5, 3, 7, 0]
```

- First and last element is always 0 (depot)
- Middle elements are customer node IDs
- Order matters (sequence of visits)

### Example Route Operations

```python
# Create route
route = [0, 5, 3, 7, 0]

# Insert node 6 between 3 and 7
route = [0, 5, 3, 6, 7, 0]

# Remove node 3
route = [0, 5, 6, 7, 0]

# Calculate route cost
def route_cost(route: List[int], distance_matrix: np.ndarray) -> float:
    cost = 0.0
    for i in range(len(route) - 1):
        cost += distance_matrix[route[i], route[i+1]]
    return cost
```

---

## Insertion Position

Represents where a node can be inserted in a route.

```python
@dataclass
class InsertionPosition:
    """A possible insertion position for a node"""

    route_idx: int  # Which route (index in solution.routes)
    position: int   # Position in route (0 = after depot)
    node_id: int    # Node to insert
    cost_increase: float  # How much objective increases
    feasible: bool  # Whether insertion maintains feasibility
```

### Example Usage

```python
# Find best insertion for node 5
best_insertion = None
min_cost = float('inf')

for route_idx, route in enumerate(solution.routes):
    for pos in range(1, len(route)):  # Don't insert at depot
        insertion = InsertionPosition(
            route_idx=route_idx,
            position=pos,
            node_id=5,
            cost_increase=calculate_cost_increase(...),
            feasible=check_feasibility(...)
        )

        if insertion.feasible and insertion.cost_increase < min_cost:
            best_insertion = insertion
            min_cost = insertion.cost_increase
```

---

## Common Algorithm Patterns

### ALNS Main Loop

```python
def alns_main_loop(instance: Instance, config: ALNSConfig) -> Solution:
    # Initialize
    current = construct_initial_solution(instance)
    best = current.copy()
    state = SearchState(current)

    for iteration in range(config.max_iterations):
        # Select operators
        destroy_op = select_operator(destroy_operators, weights)
        repair_op = select_operator(repair_operators, weights)

        # Apply operators
        partial, removed = destroy_op.destroy(current, destroy_count, instance)
        new_solution = repair_op.repair(partial, removed, instance)

        # Local search
        new_solution = local_search(new_solution, instance)

        # Acceptance criterion
        if accept(new_solution, current, state.temperature):
            current = new_solution

            # Update best
            if new_solution.objective_value() < best.objective_value():
                best = new_solution.copy()

        # Update weights and temperature
        update_weights(destroy_op, repair_op, result)
        state.temperature *= config.temperature_decay

    return best
```

---

## Type Aliases

```python
OperatorWeight = float
OperatorName = str
IterationCount = int
ObjectiveValue = float
Temperature = float
```
