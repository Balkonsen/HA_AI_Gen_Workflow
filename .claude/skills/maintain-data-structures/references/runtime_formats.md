# Runtime Data Formats

**Purpose:** Documents how data is actually represented in running code - the practical formats used in lists, tuples, arrays, and dictionaries.

---

## Route Representation

### Format

Routes are represented as **lists of integers**, where each integer is a node ID.

```python
Route = List[int]
```

### Structure

- **First element**: Always `0` (depot)
- **Last element**: Always `0` (depot)
- **Middle elements**: Customer/pickup/delivery node IDs in visit order

### Examples

```python
# Single route visiting 3 customers
route1 = [0, 5, 3, 7, 0]
# Interpretation: Start at depot → visit node 5 → node 3 → node 7 → return to depot

# Empty route (vehicle not used)
route2 = [0, 0]

# Route with one customer
route3 = [0, 12, 0]

# Multiple routes in a solution
solution_routes = [
    [0, 5, 3, 7, 0],      # Vehicle 1
    [0, 2, 6, 9, 11, 0],  # Vehicle 2
    [0, 1, 4, 0]          # Vehicle 3
]
```

### Common Operations

```python
# Get number of customers in route
n_customers = len(route) - 2  # Exclude two depot visits

# Insert node 8 after node 3
route = [0, 5, 3, 7, 0]
idx = route.index(3)
route.insert(idx + 1, 8)
# Result: [0, 5, 3, 8, 7, 0]

# Remove node 3
route = [0, 5, 3, 7, 0]
route.remove(3)
# Result: [0, 5, 7, 0]

# Check if route is empty
is_empty = len(route) == 2  # Only depot-depot

# Iterate over customers (skip depot)
for node_id in route[1:-1]:
    print(f"Visit node {node_id}")
```

---

## Time Window Representation

### Format

Time windows are represented as **tuples of two floats**.

```python
TimeWindow = Tuple[float, float]
```

### Structure

- **First element**: Earliest allowed service time
- **Second element**: Latest allowed service time

### Examples

```python
# 8 AM to 5 PM (in hours since midnight)
time_window = (8.0, 17.0)

# 9:30 AM to 11:00 AM (in hours)
time_window = (9.5, 11.0)

# No time window constraint (always accessible)
time_window = (0.0, float('inf'))

# Tight time window (10 minutes)
time_window = (120.0, 130.0)  # Minutes since start of day
```

### Common Operations

```python
# Check if arrival time is feasible
earliest, latest = time_window
arrival_time = 10.5

if earliest <= arrival_time <= latest:
    print("Arrival time is feasible")

# Calculate wait time if arriving early
wait_time = max(0, earliest - arrival_time)

# Check if time window is violated
is_violated = arrival_time > latest
```

---

## Coordinate Representation

### Format

Coordinates are represented as **tuples of two floats**.

```python
Coordinate = Tuple[float, float]
```

### Structure

- **First element**: X coordinate (or longitude)
- **Second element**: Y coordinate (or latitude)

### Examples

```python
# Euclidean coordinates
coord = (10.5, 20.3)
x, y = coord

# Geographic coordinates (longitude, latitude)
# Note: OSMnx uses (lat, lon), but we store as (lon, lat) for consistency with (x, y)
coord = (-86.9212, 40.4237)
lon, lat = coord

# List of coordinates for a route
route_coords = [
    (0.0, 0.0),      # Depot
    (10.5, 20.3),    # Customer 1
    (15.2, 18.7),    # Customer 2
    (0.0, 0.0)       # Back to depot
]
```

---

## Distance/Time Matrix Representation

### Format

Matrices are represented as **NumPy 2D arrays**.

```python
import numpy as np

DistanceMatrix = np.ndarray  # Shape: (n_nodes, n_nodes)
TimeMatrix = np.ndarray      # Shape: (n_nodes, n_nodes)
```

### Structure

- **Shape**: `(n_nodes, n_nodes)` where `n_nodes` includes depot
- **Type**: `np.float64`
- **Indexing**: `matrix[i, j]` = distance/time from node `i` to node `j`
- **Diagonal**: `matrix[i, i] = 0` (distance from node to itself)
- **Symmetry**: `matrix[i, j] == matrix[j, i]` for undirected problems

### Examples

```python
# Create 5-node distance matrix
n_nodes = 5
distance_matrix = np.array([
    [0.0, 10.5, 15.2, 20.1, 12.3],  # From depot to all nodes
    [10.5, 0.0, 8.5, 14.2, 9.1],    # From node 1 to all nodes
    [15.2, 8.5, 0.0, 11.3, 6.8],    # From node 2 to all nodes
    [20.1, 14.2, 11.3, 0.0, 13.5],  # From node 3 to all nodes
    [12.3, 9.1, 6.8, 13.5, 0.0]     # From node 4 to all nodes
])

# Access distance from node 1 to node 3
distance = distance_matrix[1, 3]  # 14.2

# Calculate route length
route = [0, 2, 3, 1, 0]
total_distance = sum(
    distance_matrix[route[i], route[i+1]]
    for i in range(len(route) - 1)
)
```

---

## Pickup-Delivery Pairs Representation

### Format

Pairs are represented as **list of tuples**.

```python
PickupDeliveryPairs = List[Tuple[int, int]]
```

### Structure

- Each tuple: `(pickup_node_id, delivery_node_id)`
- **First element**: Node ID of pickup location
- **Second element**: Node ID of corresponding delivery location

### Examples

```python
# Three pickup-delivery pairs
pairs = [
    (1, 2),   # Pickup at node 1, deliver at node 2
    (3, 4),   # Pickup at node 3, deliver at node 4
    (5, 6)    # Pickup at node 5, deliver at node 6
]

# Check if two nodes are paired
pickup_node = 1
delivery_node = 2

for p, d in pairs:
    if p == pickup_node and d == delivery_node:
        print("These nodes are paired!")

# Find delivery node for a pickup
pickup_node = 3
delivery_node = None

for p, d in pairs:
    if p == pickup_node:
        delivery_node = d
        break

print(f"Delivery node for pickup {pickup_node}: {delivery_node}")
```

---

## Solution Representation

### Format

A solution is represented as a **list of routes**.

```python
Solution = List[Route]
# where Route = List[int]
```

### Structure

- List of routes, each route is a list of node IDs
- Number of routes = number of vehicles used
- Some routes may be empty `[0, 0]` if vehicle not used

### Examples

```python
# Solution with 3 vehicles
solution = [
    [0, 5, 3, 7, 0],       # Vehicle 1 route
    [0, 2, 6, 9, 11, 0],   # Vehicle 2 route
    [0, 1, 4, 0]           # Vehicle 3 route
]

# Count vehicles used
vehicles_used = sum(1 for route in solution if len(route) > 2)

# Count total customers served
total_customers = sum(len(route) - 2 for route in solution)

# Get all visited nodes (excluding depot)
visited_nodes = []
for route in solution:
    visited_nodes.extend(route[1:-1])

# Check if all customers are served
all_customers = set(range(1, n_customers + 1))  # Assuming depot is 0
served = set(visited_nodes)
unserved = all_customers - served
```

---

## Configuration Dictionary Representation

### Format

Configurations are often represented as **dictionaries** or **dataclasses**.

```python
# As dictionary
config = {
    'max_iterations': 1000,
    'destroy_rate': 0.3,
    'temperature': 10000.0,
    'random_seed': 42
}

# As dataclass (preferred)
from dataclasses import dataclass

@dataclass
class Config:
    max_iterations: int = 1000
    destroy_rate: float = 0.3
    temperature: float = 10000.0
    random_seed: int = 42
```

### Common Usage

```python
# Dictionary access
max_iter = config['max_iterations']
config['temperature'] = 15000.0

# Dataclass access
max_iter = config.max_iterations
config.temperature = 15000.0

# Convert between formats
config_dict = {
    'max_iterations': 1000,
    'destroy_rate': 0.3
}
config_obj = Config(**config_dict)  # Dict to dataclass

config_dict = config_obj.__dict__  # Dataclass to dict
```

---

## Operator Weights Representation

### Format

Operator weights are represented as **dictionaries** mapping operator names to weights.

```python
OperatorWeights = Dict[str, float]
```

### Examples

```python
# Initial weights (all equal)
weights = {
    'random_destroy': 1.0,
    'worst_destroy': 1.0,
    'shaw_destroy': 1.0,
    'greedy_repair': 1.0,
    'regret_repair': 1.0
}

# After adaptation (some operators performing better)
weights = {
    'random_destroy': 0.8,
    'worst_destroy': 1.5,   # Performing well
    'shaw_destroy': 1.2,
    'greedy_repair': 1.3,
    'regret_repair': 0.9
}

# Select operator based on weights
import random

def select_operator(weights: Dict[str, float]) -> str:
    """Roulette wheel selection"""
    total = sum(weights.values())
    probs = {op: w/total for op, w in weights.items()}

    rand = random.random()
    cumulative = 0.0
    for op, prob in probs.items():
        cumulative += prob
        if rand <= cumulative:
            return op
```

---

## Statistics Representation

### Format

Statistics are represented as **dictionaries** or **dataclasses**.

```python
# Simple statistics as dict
stats = {
    'iterations': 1000,
    'best_objective': 452.3,
    'time_elapsed': 120.5,
    'improvement_rate': 0.15
}

# Detailed statistics as dataclass
@dataclass
class RunStatistics:
    iterations: int
    best_objective: float
    average_objective: float
    time_elapsed: float
    operators_used: Dict[str, int]
    objective_history: List[float]
```

---

## Node Attributes Dictionary

When working with raw data, node attributes are often in dictionaries:

```python
# Node attributes as dictionary
node_attrs = {
    'node_id': 5,
    'x': 10.5,
    'y': 20.3,
    'demand': 15.0,
    'time_window': (8.0, 17.0),
    'service_time': 0.5,
    'node_type': 'customer'
}

# Create Node object from dictionary
from vrp_toolkit.problems import Node

node = Node(**node_attrs)

# Convert Node object to dictionary
node_dict = {
    'node_id': node.node_id,
    'x': node.x,
    'y': node.y,
    'demand': node.demand,
    'time_window': node.time_window,
    'service_time': node.service_time
}
```

---

## Common Type Conversions

### List to NumPy Array

```python
# List of coordinates to array
coords_list = [(0.0, 0.0), (10.5, 20.3), (15.2, 18.7)]
coords_array = np.array(coords_list)  # Shape: (3, 2)

# Access
x_coords = coords_array[:, 0]  # All x coordinates
y_coords = coords_array[:, 1]  # All y coordinates
```

### Route to Coordinate List

```python
# Convert route (node IDs) to coordinates
route = [0, 5, 3, 7, 0]
nodes = [...]  # List of Node objects

route_coords = [
    (nodes[node_id].x, nodes[node_id].y)
    for node_id in route
]
```

### Dictionary to Dataclass

```python
from dataclasses import dataclass

@dataclass
class NodeData:
    node_id: int
    x: float
    y: float

# From dict
node_dict = {'node_id': 5, 'x': 10.5, 'y': 20.3}
node_obj = NodeData(**node_dict)

# To dict
node_dict = node_obj.__dict__
```

---

## Memory Efficiency Notes

### When to Use Each Format

| Data | Format | Reason |
|------|--------|--------|
| Routes | `List[int]` | Flexible, easy to modify |
| Distance matrix | `np.ndarray` | Fast numerical operations |
| Coordinates | `Tuple[float, float]` | Immutable, hashable |
| Configuration | `dataclass` | Type checking, defaults |
| Statistics | `Dict` or `dataclass` | Flexible structure |
| Node attributes | Object with `__slots__` | Memory efficient for many nodes |

### Memory-Efficient Node Class

```python
class Node:
    __slots__ = ['node_id', 'x', 'y', 'demand', 'time_window', 'service_time']

    def __init__(self, node_id, x, y, demand=0, time_window=(0, float('inf')), service_time=0):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.demand = demand
        self.time_window = time_window
        self.service_time = service_time
```

Using `__slots__` reduces memory usage when creating thousands of Node objects.
