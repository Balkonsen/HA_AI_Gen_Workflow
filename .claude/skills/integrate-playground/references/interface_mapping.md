# Playground → VRP-Toolkit Interface Mapping

**Purpose:** Quick reference table mapping playground needs to exact vrp-toolkit APIs.

**Last Updated:** 2026-01-05

---

## Table of Contents

1. [Data Generation Flow](#data-generation-flow)
2. [Solving Flow](#solving-flow)
3. [Data Access Patterns](#data-access-patterns)
4. [Common Mistakes](#common-mistakes)

---

## Data Generation Flow

Complete workflow from map generation to problem instance creation.

| Step | Playground Need | VRP-Toolkit API | Contract Test | Notes |
|------|-----------------|-----------------|---------------|-------|
| **1. Generate Map** | Synthetic coordinates for restaurants & customers | `RealMap(n_r: int, n_c: int, dist_function: Callable, dist_params: Dict)` | `contracts/test_realmap_api.py` | Set seed via `np.random.seed()` before calling |
| **2. Generate Demands** | Order distribution over time | `DemandGenerator(time_range: int, time_step: int, restaurants: List[int], customers: List[int], random_params: Dict)` | `contracts/test_demand_generation.py` | Generates on `__init__`, access `.demand_table` |
| **3. Generate Orders** | Complete order table | `OrderGenerator(real_map, demand_table: pd.DataFrame, time_params: Dict, robot_speed: float)` | `contracts/test_order_generation.py` | Generates on `__init__`, access `.order_table` and `.time_matrix` |
| **4. Create Instance** | Problem instance for solving | `PDPTWInstance(order_table: pd.DataFrame, distance_matrix: np.ndarray, time_matrix: np.ndarray, robot_speed: float)` | `contracts/test_instance_creation.py` | All 4 parameters required |

### Detailed API Signatures

#### 1. RealMap

```python
RealMap(
    n_r: int,              # Number of restaurants
    n_c: int,              # Number of customers
    dist_function: Callable,  # e.g., np.random.uniform
    dist_params: Dict      # e.g., {'low': 0, 'high': 100}
)
```

**Attributes after init:**
- `.distance_matrix` - np.ndarray of distances between all nodes
- `.restaurants` - List[int] of restaurant node indices
- `.customers` - List[int] of customer node indices
- `.coordinates` - Dict[int, Tuple[float, float]] of node coordinates
- `.node_type_dict` - Dict[int, str] mapping node IDs to types

**Common mistakes:**
- ❌ `RealMap(num_customers=10, ...)` - Wrong parameter names
- ❌ `RealMap(..., seed=42)` - No seed parameter, use `np.random.seed(42)` before
- ✅ `np.random.seed(42); RealMap(n_r=3, n_c=10, ...)`

#### 2. DemandGenerator

```python
DemandGenerator(
    time_range: int,       # Total time in minutes (e.g., 240 for 4 hours)
    time_step: int,        # Interval length in minutes (e.g., 30)
    restaurants: List[int],   # From real_map.restaurants
    customers: List[int],     # From real_map.customers
    random_params: Dict    # See structure below
)
```

**random_params structure:**
```python
{
    'sample_dist': {
        'function': np.random.poisson,
        'params': {'lam': 3}  # Average orders per interval
    },
    'demand_dist': {
        'function': np.random.randint,
        'params': {'low': 1, 'high': 5}  # Items per order
    }
}
```

**Attributes after init:**
- `.demand_table` - pd.DataFrame with columns: [time_interval, restaurant, customer, demand]

**Common mistakes:**
- ❌ `demand_gen.generate()` - No generate() method
- ❌ `DemandGenerator(num_customers=10, ...)` - Wrong parameters
- ✅ `demand_gen.demand_table` - Access via attribute

#### 3. OrderGenerator

```python
OrderGenerator(
    real_map,              # RealMap instance
    demand_table: pd.DataFrame,  # From DemandGenerator
    time_params: Dict,     # See structure below
    robot_speed: float     # Speed in distance units per minute
)
```

**time_params structure:**
```python
{
    'time_window_length': 30,   # Minutes for delivery window
    'service_time': 5,           # Minutes at each node
    'extra_time': 10,            # Buffer time
    'big_time': 1000             # Infinity for time windows
}
```

**Attributes after init:**
- `.order_table` - pd.DataFrame complete order table for PDPTWInstance
- `.time_matrix` - np.ndarray travel time between nodes

**Common mistakes:**
- ❌ `order_gen.generate()` - No generate() method
- ❌ `order_gen.distance_matrix` - Use `real_map.distance_matrix` instead
- ✅ `order_gen.order_table` and `order_gen.time_matrix` - Access via attributes

#### 4. PDPTWInstance

```python
PDPTWInstance(
    order_table: pd.DataFrame,     # From OrderGenerator
    distance_matrix: np.ndarray,   # From real_map.distance_matrix
    time_matrix: np.ndarray,       # From order_gen.time_matrix
    robot_speed: float             # Same as used in OrderGenerator
)
```

**Attributes after init:**
- `.n` - int, number of pickup-delivery pairs
- `.indices` - List[int], all node IDs
- `.demands` - List[float], demand at each node
- `.time_windows` - List[Tuple], time windows for each node
- `.distance_matrix`, `.time_matrix` - Matrices passed in

**Common mistakes:**
- ❌ `PDPTWInstance(order_table=order_table)` - Missing 3 required params
- ❌ `PDPTWInstance(..., time_matrix=real_map.time_matrix)` - Use `order_gen.time_matrix`
- ✅ All 4 parameters must be provided

---

## Solving Flow

| Step | Playground Need | VRP-Toolkit API | Contract Test | Notes |
|------|-----------------|-----------------|---------------|-------|
| **1. Configure ALNS** | Algorithm parameters | `ALNSConfig(max_iterations=1000, ...)` | `contracts/test_alns_config.py` | All parameters optional with defaults |
| **2. Wrap Instance** | Adapt to solver interface | `PDPTWProblemAdapter(instance)` | `contracts/test_adapter.py` | Wraps PDPTWInstance to VRPProblem interface |
| **3. Generate Initial** | Starting solution | `greedy_insertion_initial_solution(problem, ...)` | `contracts/test_initial_solution.py` | Returns Solution object |
| **4. Run ALNS** | Execute solver | `ALNS(config).solve(problem)` | `contracts/test_alns_solve.py` | Returns Solution object |
| **5. Extract Results** | Get routes and costs | `solution.routes`, `solution.objective_value` | `contracts/test_solution_api.py` | Access via attributes |

### Detailed API Signatures

#### 1. ALNSConfig

```python
ALNSConfig(
    # ALNS parameters
    num_segments: int = 10,              # Number of segments (iterations = num_segments * segment_length)
    segment_length: int = 100,           # Segment length

    # Simulated annealing
    start_temp: float = 10000.0,        # Start temperature
    cooling_rate: float = 0.99,         # Cooling rate

    # Reproducibility (IMPORTANT!)
    seed: Optional[int] = None,         # Random seed for reproducibility

    # Operator parameters
    num_removal: int = 5,
    p: float = 4.0,                     # Shaw removal parameter

    # Other parameters (use defaults)
    # ...
)
```

**CRITICAL**:
- ✅ **Use `seed` parameter for reproducibility!**
- ❌ No `max_iterations` - use `num_segments` instead
- Total iterations = `num_segments * segment_length`

#### 2. PDPTWProblemAdapter

```python
adapter = PDPTWProblemAdapter(instance: PDPTWInstance)
```

**Attributes:**
- `.indices`, `.demands`, `.time_windows`, etc. - Forwards from instance

#### 3. ALNS

```python
solver = ALNS(config: ALNSConfig)
solution = solver.solve(problem: VRPProblem)
```

**Returns:** Solution object with `.routes` and `.objective_value`

---

## Data Access Patterns

Critical distinction between attributes and methods.

| Class | What | How to Access | ⚠️ Common Mistake | Contract Test |
|-------|------|---------------|-------------------|---------------|
| **DemandGenerator** | Demand table | `.demand_table` | ❌ `.generate()` | `test_demand_attributes.py` |
| **OrderGenerator** | Order table | `.order_table` | ❌ `.generate()` | `test_order_attributes.py` |
| **OrderGenerator** | Time matrix | `.time_matrix` | ❌ `real_map.time_matrix` | `test_matrix_sources.py` |
| **RealMap** | Distance matrix | `.distance_matrix` | ✅ Correct | `test_map_attributes.py` |
| **RealMap** | Coordinates | `.coordinates` | ✅ Correct | `test_map_attributes.py` |

### Key Pattern: Generators Create on __init__

**Most data generators in vrp-toolkit create their output during `__init__`, not via a separate method:**

```python
# ✅ Correct pattern
demand_gen = DemandGenerator(...)  # Generates immediately
demand_table = demand_gen.demand_table  # Access via attribute

order_gen = OrderGenerator(...)  # Generates immediately
order_table = order_gen.order_table  # Access via attribute

# ❌ Wrong pattern
demand_gen = DemandGenerator(...)
demand_table = demand_gen.generate()  # ❌ No such method!
```

---

## Common Mistakes

### 1. Parameter Name Mismatches

| ❌ Assumed Parameter | ✅ Actual Parameter | API |
|---------------------|---------------------|-----|
| `num_customers` | `n_c` | RealMap |
| `num_restaurants` | `n_r` | RealMap |
| `area_size` | `dist_params={'low': 0, 'high': 100}` | RealMap |
| `seed` | Use `np.random.seed()` before | RealMap |

### 2. Calling Non-Existent Methods

```python
# ❌ Wrong
demand_table = demand_gen.generate()
order_table = order_gen.generate()

# ✅ Correct
demand_table = demand_gen.demand_table
order_table = order_gen.order_table
```

### 3. Missing Required Parameters

```python
# ❌ Wrong - Missing 3 parameters
instance = PDPTWInstance(order_table=order_table)

# ✅ Correct - All 4 required
instance = PDPTWInstance(
    order_table=order_table,
    distance_matrix=real_map.distance_matrix,
    time_matrix=order_gen.time_matrix,
    robot_speed=1.0
)
```

### 4. Wrong Matrix Source

```python
# ❌ Wrong - time_matrix comes from OrderGenerator
instance = PDPTWInstance(
    ...
    time_matrix=real_map.time_matrix  # ❌ RealMap doesn't have this
)

# ✅ Correct
instance = PDPTWInstance(
    ...
    time_matrix=order_gen.time_matrix  # ✅ From OrderGenerator
)
```

### 5. Module-Level vs Instance Attributes

```python
# In generators.py

# ❌ Wrong - DEFAULT_COLUMNS is module-level
df = pd.DataFrame(data, columns=self.DEFAULT_COLUMNS)

# ✅ Correct
df = pd.DataFrame(data, columns=DEFAULT_COLUMNS)
```

---

## Complete Example

**Full playground → vrp-toolkit integration:**

```python
import numpy as np
import streamlit as st
from vrp_toolkit.data.map import RealMap
from vrp_toolkit.data.generators import DemandGenerator, OrderGenerator
from vrp_toolkit.problems.pdptw import PDPTWInstance
from vrp_toolkit.algorithms.alns import ALNS, ALNSConfig
from vrp_toolkit.algorithms.base import PDPTWProblemAdapter

# Step 1: Generate map
np.random.seed(42)  # For reproducibility
real_map = RealMap(
    n_r=3,  # 3 restaurants
    n_c=10,  # 10 customers
    dist_function=np.random.uniform,
    dist_params={'low': 0, 'high': 100}
)

# Step 2: Generate demands
demand_gen = DemandGenerator(
    time_range=240,
    time_step=30,
    restaurants=real_map.restaurants,
    customers=real_map.customers,
    random_params={
        'sample_dist': {'function': np.random.poisson, 'params': {'lam': 3}},
        'demand_dist': {'function': np.random.randint, 'params': {'low': 1, 'high': 5}}
    }
)
demand_table = demand_gen.demand_table

# Step 3: Generate orders
order_gen = OrderGenerator(
    real_map=real_map,
    demand_table=demand_table,
    time_params={
        'time_window_length': 30,
        'service_time': 5,
        'extra_time': 10,
        'big_time': 1000
    },
    robot_speed=1.0
)
order_table = order_gen.order_table

# Step 4: Create instance
instance = PDPTWInstance(
    order_table=order_table,
    distance_matrix=real_map.distance_matrix,
    time_matrix=order_gen.time_matrix,
    robot_speed=1.0
)

# Step 5: Configure and solve
config = ALNSConfig(max_iterations=1000)
problem = PDPTWProblemAdapter(instance)
solver = ALNS(config)
solution = solver.solve(problem)

# Step 6: Display results
st.write(f"Routes: {solution.routes}")
st.write(f"Cost: {solution.objective_value}")
```

---

## Maintenance Notes

**When to update this file:**
1. VRP-toolkit API changes (parameter names, signatures)
2. New playground features added
3. New common mistakes discovered
4. Contract tests added or modified

**How to verify mappings:**
1. Run contract tests: `pytest contracts/ -v`
2. Check actual source code if uncertain
3. Test in playground to confirm behavior
