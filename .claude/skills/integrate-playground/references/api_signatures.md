# Complete API Signatures

**Purpose:** Detailed API reference with import statements, full parameter lists, and return types.

**Note:** For quick lookup, use `interface_mapping.md`. This file provides comprehensive details.

---

## Import Statements

```python
# Data generation
from vrp_toolkit.data.map import RealMap
from vrp_toolkit.data.generators import DemandGenerator, OrderGenerator

# Problem definition
from vrp_toolkit.problems.pdptw import PDPTWInstance

# Algorithm
from vrp_toolkit.algorithms.alns import ALNS, ALNSConfig, greedy_insertion_initial_solution
from vrp_toolkit.algorithms.base import PDPTWProblemAdapter

# Utilities
import numpy as np
import pandas as pd
```

---

## vrp_toolkit.data.map

### RealMap

```python
class RealMap:
    def __init__(
        self,
        n_r: int,                    # Number of restaurants
        n_c: int,                    # Number of customers
        dist_function: Callable,     # Coordinate generation function
        dist_params: Dict            # Parameters for dist_function
    ):
        """Generate synthetic map with random coordinates."""
        pass

    # Attributes (available after __init__)
    N_R: int                         # Number of restaurants
    N_C: int                         # Number of customers
    n: int                           # Total nodes (N_R + N_C)
    DEPOT_INDEX: int                 # Always 0
    DESTINATION_INDEX: int           # n + 1
    CHARGING_STATION_INDEX: int      # n + 2
    all_nodes: List[int]             # All node indices
    restaurants: List[int]           # Restaurant node indices
    customers: List[int]             # Customer node indices
    coordinates: Dict[int, Tuple[float, float]]  # Node coordinates
    distance_matrix: np.ndarray      # Distance between nodes
    node_type_dict: Dict[int, str]   # Node type mapping
```

**Example:**
```python
np.random.seed(42)
real_map = RealMap(
    n_r=5,
    n_c=20,
    dist_function=np.random.uniform,
    dist_params={'low': 0, 'high': 100}
)
print(real_map.restaurants)  # [1, 2, 3, 4, 5]
print(real_map.customers)    # [6, 7, ..., 25]
```

---

## vrp_toolkit.data.generators

### DemandGenerator

```python
class DemandGenerator:
    def __init__(
        self,
        time_range: int,             # Total time in minutes
        time_step: int,              # Interval length in minutes
        restaurants: List[int],      # Restaurant node IDs
        customers: List[int],        # Customer node IDs
        random_params: Dict          # Random generation parameters
    ):
        """Generate demand over time intervals. Generates on __init__."""
        pass

    # Attributes
    demand_table: pd.DataFrame       # Generated demand data
```

**random_params structure:**
```python
{
    'sample_dist': {
        'function': Callable,        # e.g., np.random.poisson
        'params': Dict               # e.g., {'lam': 3}
    },
    'demand_dist': {
        'function': Callable,        # e.g., np.random.randint
        'params': Dict               # e.g., {'low': 1, 'high': 5}
    }
}
```

**Example:**
```python
demand_gen = DemandGenerator(
    time_range=480,  # 8 hours
    time_step=60,    # 1 hour intervals
    restaurants=real_map.restaurants,
    customers=real_map.customers,
    random_params={
        'sample_dist': {
            'function': np.random.poisson,
            'params': {'lam': 5}
        },
        'demand_dist': {
            'function': np.random.randint,
            'params': {'low': 1, 'high': 10}
        }
    }
)
df = demand_gen.demand_table  # Access immediately
```

### OrderGenerator

```python
class OrderGenerator:
    def __init__(
        self,
        real_map: RealMap,              # Map instance
        demand_table: pd.DataFrame,     # From DemandGenerator
        time_params: Dict[str, int],    # Time-related parameters
        robot_speed: float,             # Speed (distance/minute)
        column_mapping: Optional[Dict[str, str]] = None  # Optional column renaming
    ):
        """Generate complete order table. Generates on __init__."""
        pass

    # Attributes
    order_table: pd.DataFrame           # Complete order table
    time_matrix: np.ndarray             # Travel time matrix
    total_number_orders: int            # Total orders generated
```

**time_params structure:**
```python
{
    'time_window_length': int,          # Delivery window (minutes)
    'service_time': int,                # Service time at node (minutes)
    'extra_time': int,                  # Buffer time (minutes)
    'big_time': int                     # Infinity value (e.g., 1000)
}
```

**Example:**
```python
order_gen = OrderGenerator(
    real_map=real_map,
    demand_table=demand_gen.demand_table,
    time_params={
        'time_window_length': 30,
        'service_time': 5,
        'extra_time': 10,
        'big_time': 1000
    },
    robot_speed=1.0
)
order_table = order_gen.order_table
time_matrix = order_gen.time_matrix
```

---

## vrp_toolkit.problems.pdptw

### PDPTWInstance

```python
class PDPTWInstance(VRPProblem):
    def __init__(
        self,
        order_table: pd.DataFrame,      # From OrderGenerator
        distance_matrix: np.ndarray,    # From RealMap
        time_matrix: np.ndarray,        # From OrderGenerator
        robot_speed: float,             # Speed value
        column_mapping: Optional[Dict[str, str]] = None
    ):
        """Create PDPTW problem instance."""
        pass

    # Attributes
    n: int                              # Number of pickup-delivery pairs
    indices: List[int]                  # All node IDs
    demands: List[float]                # Demand at each node
    time_windows: List[Tuple[float, float]]  # Time windows
    service_times: List[float]          # Service time at each node
    distance_matrix: np.ndarray         # Distance matrix
    time_matrix: np.ndarray             # Time matrix
    depot: Tuple[float, float]          # Depot coordinates
    pickup_points: List[Tuple]          # Pickup coordinates
    delivery_points: List[Tuple]        # Delivery coordinates
```

**Example:**
```python
instance = PDPTWInstance(
    order_table=order_gen.order_table,
    distance_matrix=real_map.distance_matrix,
    time_matrix=order_gen.time_matrix,
    robot_speed=1.0
)
print(f"Problem has {instance.n} orders")
```

---

## vrp_toolkit.algorithms.alns

### ALNSConfig

```python
@dataclass
class ALNSConfig:
    # ALNS parameters
    num_segments: int = 10                    # Number of segments
    segment_length: int = 100                 # Segment length (iterations = num_segments * segment_length)
    max_no_improve: int = 100

    # Simulated annealing
    start_temp: float = 10000.0              # Start temperature
    cooling_rate: float = 0.99               # Cooling rate

    # Operator parameters
    num_removal: int = 5
    p: float = 4.0                            # Shaw removal parameter
    k: int = 3                                # Regret insertion parameter

    # Reproducibility (CRITICAL!)
    seed: Optional[int] = None                # Random seed for reproducible results

    # Other parameters with defaults...
```

**CRITICAL CHANGES:**
- ❌ No `max_iterations` parameter!
- ✅ Use `num_segments` instead (total iterations = num_segments * segment_length)
- ✅ **Always set `seed` for reproducibility**

### ALNS

```python
class ALNS(ConfigurableSolver):
    def __init__(self, config: ALNSConfig):
        """Initialize ALNS solver with configuration."""
        pass

    def solve(
        self,
        problem: VRPProblem,
        initial_solution: Optional[VRPSolution] = None,
        **kwargs
    ) -> VRPSolution:
        """Solve VRP problem using ALNS."""
        pass
```

### greedy_insertion_initial_solution

```python
def greedy_insertion_initial_solution(
    problem: VRPProblem,
    num_vehicles: int,
    vehicle_capacity: float,
    battery_capacity: float,
    battery_consume_rate: float,
    penalty_unvisit: float,        # NEW: Penalty for unvisited nodes (default: 1000.0)
    penalty_delay: float            # NEW: Penalty for delayed orders (default: 100.0)
) -> VRPSolution:
    """Generate initial solution using greedy insertion."""
    pass
```

**Example:**
```python
problem = PDPTWProblemAdapter(instance)
initial_solution = greedy_insertion_initial_solution(
    problem=problem,
    num_vehicles=3,
    vehicle_capacity=1000,
    battery_capacity=100.0,
    battery_consume_rate=1.0,
    penalty_unvisit=1000.0,         # Required parameter
    penalty_delay=100.0             # Required parameter
)
```

---

## vrp_toolkit.algorithms.base

### PDPTWProblemAdapter

```python
class PDPTWProblemAdapter(VRPProblem):
    def __init__(self, instance: PDPTWInstance):
        """Adapt PDPTWInstance to VRPProblem interface."""
        pass

    # Forwards attributes from instance
    indices: List[int]
    demands: List[float]
    time_windows: List[Tuple]
    # ... etc
```

---

## Return Types

### Solution Object

```python
class VRPSolution:
    routes: List[List[int]]             # List of routes (list of node IDs)
    objective_value: float              # Total cost
    # ... other attributes
```

**Access pattern:**
```python
solution = solver.solve(problem)
routes = solution.routes                # [[0, 1, 3, 0], [0, 2, 4, 0]]
cost = solution.objective_value         # 245.6
```
