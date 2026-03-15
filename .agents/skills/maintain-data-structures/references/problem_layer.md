# Problem Layer Data Structures

**Purpose:** Data structures for defining problem instances, independent of solving algorithms.

**Location:** `vrp_toolkit/problems/`

---

## Instance

Base class for problem instances.

### Interface

```python
class Instance:
    """Base class for all problem instances"""

    def __init__(self, nodes, constraints, objectives):
        self.nodes = nodes              # List of Node objects
        self.constraints = constraints  # Dict of constraint name -> constraint object
        self.objectives = objectives    # List of objective functions
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `nodes` | `List[Node]` | All nodes in the problem (depot + customers) |
| `constraints` | `Dict[str, Constraint]` | Constraint objects (time windows, capacity, etc.) |
| `objectives` | `List[Callable]` | Objective functions to minimize/maximize |

### Example Usage

```python
# Creating a basic instance
nodes = [depot, customer1, customer2, customer3]
constraints = {
    'time_window': TimeWindowConstraint(),
    'capacity': CapacityConstraint(max_capacity=100)
}
objectives = [minimize_total_distance]

instance = Instance(nodes, constraints, objectives)
```

---

## PDPTWInstance

Pickup and Delivery Problem with Time Windows instance.

### Interface

```python
class PDPTWInstance(Instance):
    """PDPTW problem instance with battery constraints"""

    def __init__(
        self,
        nodes: List[Node],
        battery_capacity: float,
        max_route_time: float,
        vehicle_capacity: float
    ):
        self.nodes = nodes
        self.battery_capacity = battery_capacity
        self.max_route_time = max_route_time
        self.vehicle_capacity = vehicle_capacity
        # ... additional initialization
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `nodes` | `List[Node]` | Depot + pickup/delivery nodes |
| `battery_capacity` | `float` | Maximum battery capacity (e.g., 100.0) |
| `max_route_time` | `float` | Maximum time per route (e.g., 480.0 minutes) |
| `vehicle_capacity` | `float` | Maximum vehicle load capacity |
| `pickup_delivery_pairs` | `List[Tuple[int, int]]` | Pairs of (pickup_node_id, delivery_node_id) |
| `distance_matrix` | `np.ndarray` | Distance between all node pairs |
| `time_matrix` | `np.ndarray` | Travel time between all node pairs |

### Example

```python
pdptw = PDPTWInstance(
    nodes=all_nodes,
    battery_capacity=100.0,
    max_route_time=480.0,  # 8 hours
    vehicle_capacity=50.0
)
```

---

## Solution

Represents a solution to a problem instance.

### Interface

```python
class Solution:
    """Base class for solutions"""

    def __init__(self, routes: List[Route]):
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

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `routes` | `List[Route]` | List of Route objects representing vehicle routes |
| `objective_value` | `float` | Cached objective value (distance, cost, etc.) |
| `is_feasible_cached` | `bool` | Cached feasibility check result |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `is_feasible()` | `bool` | Checks all constraints (time, capacity, pairing) |
| `objective_value()` | `float` | Calculates total distance/cost |
| `plot()` | `None` | Creates visualization of routes |
| `copy()` | `Solution` | Deep copy of solution |

### Example

```python
# Create solution with two routes
route1 = [0, 5, 3, 7, 0]  # Depot -> nodes 5,3,7 -> Depot
route2 = [0, 2, 6, 0]     # Depot -> nodes 2,6 -> Depot
solution = Solution(routes=[route1, route2])

# Check feasibility and objective
if solution.is_feasible():
    print(f"Total distance: {solution.objective_value()}")
    solution.plot()
```

---

## Node

Represents a location in the problem (depot, customer, pickup, delivery).

### Interface

```python
class Node:
    """A node in the problem"""

    def __init__(
        self,
        node_id: int,
        x: float,
        y: float,
        demand: float = 0.0,
        time_window: Tuple[float, float] = (0, float('inf')),
        service_time: float = 0.0,
        node_type: str = 'customer'
    ):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.demand = demand
        self.time_window = time_window
        self.service_time = service_time
        self.node_type = node_type
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `node_id` | `int` | Unique identifier (0 is typically depot) |
| `x` | `float` | X coordinate (or longitude) |
| `y` | `float` | Y coordinate (or latitude) |
| `demand` | `float` | Demand/load (positive = pickup, negative = delivery) |
| `time_window` | `Tuple[float, float]` | (earliest, latest) service time |
| `service_time` | `float` | Time required to service this node |
| `node_type` | `str` | 'depot', 'pickup', 'delivery', 'customer' |
| `pair_node_id` | `int` (optional) | For PDPTW: paired pickup/delivery node |

### Example

```python
# Depot
depot = Node(node_id=0, x=0.0, y=0.0, node_type='depot')

# Customer with time window
customer = Node(
    node_id=5,
    x=10.5,
    y=20.3,
    demand=15.0,
    time_window=(8.0, 17.0),  # 8am - 5pm
    service_time=0.5,  # 30 minutes
    node_type='customer'
)

# Pickup-delivery pair
pickup = Node(
    node_id=1,
    x=5.0,
    y=10.0,
    demand=10.0,  # Positive = pickup
    node_type='pickup',
    pair_node_id=2  # Paired with delivery node 2
)

delivery = Node(
    node_id=2,
    x=15.0,
    y=12.0,
    demand=-10.0,  # Negative = delivery
    node_type='delivery',
    pair_node_id=1  # Paired with pickup node 1
)
```

---

## Constraint

Base class for problem constraints.

### Common Constraints

#### TimeWindowConstraint
```python
class TimeWindowConstraint:
    """Ensures nodes are visited within their time windows"""

    def is_satisfied(self, route: List[int], instance: Instance) -> bool:
        # Check if route respects all time windows
        pass
```

#### CapacityConstraint
```python
class CapacityConstraint:
    """Ensures vehicle capacity is not exceeded"""

    def __init__(self, max_capacity: float):
        self.max_capacity = max_capacity

    def is_satisfied(self, route: List[int], instance: Instance) -> bool:
        # Check if total demand <= max_capacity
        pass
```

#### PairingConstraint
```python
class PairingConstraint:
    """Ensures pickups occur before deliveries in PDPTW"""

    def is_satisfied(self, route: List[int], instance: Instance) -> bool:
        # Check if pickup comes before its paired delivery
        pass
```

---

## Type Aliases

Common type aliases used in the problem layer:

```python
NodeID = int
Coordinate = Tuple[float, float]
TimeWindow = Tuple[float, float]  # (earliest, latest)
Route = List[NodeID]
DistanceMatrix = np.ndarray  # Shape: (n_nodes, n_nodes)
TimeMatrix = np.ndarray      # Shape: (n_nodes, n_nodes)
```

---

## Key Design Principles

1. **Independence**: Problem definitions should not import or depend on algorithm implementations
2. **Generalization**: Structures should support multiple problem variants (VRP, CVRP, PDPTW, VRPTW)
3. **Validation**: Each structure should validate its own data integrity
4. **Serialization**: Support saving/loading instances from files

---

## Common Patterns

### Creating an Instance from Data

```python
def create_instance_from_file(filepath: str) -> PDPTWInstance:
    """Load instance from data file"""
    data = load_data(filepath)

    nodes = [Node(**node_data) for node_data in data['nodes']]
    instance = PDPTWInstance(
        nodes=nodes,
        battery_capacity=data['battery_capacity'],
        max_route_time=data['max_route_time'],
        vehicle_capacity=data['vehicle_capacity']
    )
    return instance
```

### Validating a Solution

```python
def validate_solution(solution: Solution, instance: Instance) -> bool:
    """Check if solution is valid for instance"""

    # Check each constraint
    for constraint_name, constraint in instance.constraints.items():
        for route in solution.routes:
            if not constraint.is_satisfied(route, instance):
                print(f"Constraint {constraint_name} violated in route {route}")
                return False

    return True
```
