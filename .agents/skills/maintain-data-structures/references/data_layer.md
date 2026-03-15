# Data Layer Data Structures

**Purpose:** Data structures for data generation, loading, and transformation.

**Location:** `vrp_toolkit/data/`

---

## OSMnx Data Structures

### Graph (NetworkX MultiDiGraph)

OSMnx returns NetworkX graph objects representing street networks.

```python
import osmnx as ox

# Load street network
G = ox.graph_from_place("Purdue University, West Lafayette, IN", network_type='drive')
```

#### Graph Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `nodes` | `dict` | Node ID -> node attributes dict |
| `edges` | `dict` | Edge tuples -> edge attributes dict |
| `graph` | `dict` | Graph-level metadata |

#### Node Attributes

Each node in the graph has these attributes:

```python
# Access node attributes
node_id = 123456789
node_data = G.nodes[node_id]

# Common attributes:
{
    'y': 40.4237,          # Latitude
    'x': -86.9212,         # Longitude
    'osmid': 123456789,    # OpenStreetMap ID
    'street_count': 3      # Number of streets at intersection
}
```

#### Edge Attributes

Each edge in the graph has these attributes:

```python
# Access edge attributes
u, v, k = 123, 456, 0  # From node, to node, key
edge_data = G.edges[u, v, k]

# Common attributes:
{
    'length': 150.5,       # Length in meters
    'osmid': 987654321,    # OpenStreetMap way ID
    'name': 'State Street',
    'highway': 'residential',
    'maxspeed': '25 mph',
    'oneway': False
}
```

### GeoDataFrame (from GeoPandas)

OSMnx can convert graphs to GeoDataFrames for easier manipulation.

```python
# Convert to GeoDataFrames
nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)
```

#### Nodes GeoDataFrame

| Column | Type | Description |
|--------|------|-------------|
| `geometry` | `Point` | Shapely Point object (lon, lat) |
| `y` | `float` | Latitude |
| `x` | `float` | Longitude |
| `osmid` | `int` | OpenStreetMap ID |
| `street_count` | `int` | Degree of node |

**Example:**

```python
# Access nodes
print(nodes_gdf.head())

#              geometry          y          x       osmid  street_count
# osmid
# 123    POINT (-86.92 40.42)  40.4237  -86.9212  123456789      3
# 456    POINT (-86.91 40.43)  40.4280  -86.9145  456789123      2
```

#### Edges GeoDataFrame

| Column | Type | Description |
|--------|------|-------------|
| `geometry` | `LineString` | Shapely LineString of edge |
| `u` | `int` | From node ID |
| `v` | `int` | To node ID |
| `key` | `int` | Edge key (for parallel edges) |
| `length` | `float` | Length in meters |
| `name` | `str` | Street name |
| `highway` | `str` | Road type |

---

## Distance Matrix

Pairwise distances between all nodes.

### Structure

```python
import numpy as np

# Distance matrix
distance_matrix: np.ndarray  # Shape: (n_nodes, n_nodes)

# Access distance from node i to node j
distance = distance_matrix[i, j]
```

### Common Creation Patterns

#### From Euclidean Coordinates

```python
def create_euclidean_distance_matrix(nodes: List[Node]) -> np.ndarray:
    """Create distance matrix from node coordinates"""
    n = len(nodes)
    matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i != j:
                dx = nodes[i].x - nodes[j].x
                dy = nodes[i].y - nodes[j].y
                matrix[i, j] = np.sqrt(dx**2 + dy**2)

    return matrix
```

#### From OSMnx Graph

```python
def create_osmnx_distance_matrix(
    G: nx.MultiDiGraph,
    node_ids: List[int]
) -> np.ndarray:
    """Create distance matrix using OSMnx routing"""
    n = len(node_ids)
    matrix = np.zeros((n, n))

    for i, origin in enumerate(node_ids):
        # Compute shortest paths from origin to all others
        lengths = nx.single_source_dijkstra_path_length(
            G, origin, weight='length'
        )

        for j, destination in enumerate(node_ids):
            if i != j and destination in lengths:
                matrix[i, j] = lengths[destination]

    return matrix
```

### Properties

- **Symmetric** for undirected graphs: `matrix[i,j] == matrix[j,i]`
- **Zero diagonal**: `matrix[i,i] == 0`
- **Units**: Typically meters or kilometers
- **Type**: `np.float64`

---

## Time Matrix

Similar to distance matrix, but for travel times.

```python
time_matrix: np.ndarray  # Shape: (n_nodes, n_nodes)

# Often derived from distance and speed
time_matrix = distance_matrix / average_speed
```

---

## Generator Output Structures

### OrderGenerator

Generates synthetic orders (pickup-delivery pairs).

#### Output Format

```python
@dataclass
class OrderBatch:
    """Batch of generated orders"""

    orders: List[Order]
    total_demand: float
    time_generated: float  # When in the day orders arrived

@dataclass
class Order:
    """Single pickup-delivery order"""

    order_id: int
    pickup_node: Node
    delivery_node: Node
    demand: float
    time_window_pickup: Tuple[float, float]
    time_window_delivery: Tuple[float, float]
    announced_time: float  # When order becomes known
```

**Example:**

```python
from vrp_toolkit.data.generators import OrderGenerator

gen = OrderGenerator(seed=42)
orders = gen.generate_orders(
    n_orders=50,
    area_bounds=(0, 100, 0, 100),
    demand_range=(5, 25)
)

for order in orders:
    print(f"Order {order.order_id}: "
          f"Pickup at ({order.pickup_node.x}, {order.pickup_node.y}), "
          f"Deliver at ({order.delivery_node.x}, {order.delivery_node.y})")
```

---

## Benchmark Dataset Structures

### Solomon Format

Standard VRP benchmark format.

#### File Structure

```
NAME: C101
VEHICLE:
  NUMBER: 25
  CAPACITY: 200

CUSTOMER
  CUST_NO  XCOORD  YCOORD  DEMAND  READY_TIME  DUE_DATE  SERVICE_TIME
       0      40      50       0          0       1236             0
       1      45      68      10        912        967            90
       2      45      70      30        825        870            90
```

#### Parsed Structure

```python
@dataclass
class SolomonInstance:
    """Parsed Solomon benchmark instance"""

    name: str
    vehicle_number: int
    vehicle_capacity: float
    customers: List[SolomonCustomer]

@dataclass
class SolomonCustomer:
    """Customer in Solomon format"""

    cust_no: int
    x: float
    y: float
    demand: float
    ready_time: float
    due_date: float
    service_time: float
```

---

## Data Loading Functions

### Common Signatures

```python
# Load from file
def load_instance(filepath: str) -> Instance:
    """Load problem instance from file"""
    pass

# Load benchmark
def load_solomon_instance(filepath: str) -> PDPTWInstance:
    """Load Solomon benchmark instance"""
    pass

# Load OSMnx area
def load_area_from_osmnx(place_name: str) -> Tuple[nx.MultiDiGraph, gpd.GeoDataFrame]:
    """Load area from OpenStreetMap"""
    pass

# Create distance matrix
def compute_distance_matrix(
    G: nx.MultiDiGraph,
    node_ids: List[int],
    method: str = 'shortest_path'
) -> np.ndarray:
    """Compute distance matrix from graph"""
    pass
```

---

## Visualization Data Structures

### Plot Configuration

```python
@dataclass
class PlotConfig:
    """Configuration for visualizations"""

    figsize: Tuple[int, int] = (12, 8)
    node_size: int = 100
    route_colors: List[str] = None  # Auto-generate if None
    show_node_labels: bool = True
    show_time_windows: bool = False
    title: str = ""
    save_path: str = None
```

### Route Visualization Data

```python
@dataclass
class RouteVisualization:
    """Data for visualizing a route"""

    route: List[int]  # Node IDs
    coordinates: List[Tuple[float, float]]  # (x, y) for each node
    color: str
    label: str  # e.g., "Route 1"
    metrics: Dict[str, float]  # e.g., {"distance": 150.5, "load": 45.0}
```

---

## Cache Structures

For efficient repeated operations.

```python
@dataclass
class DistanceCache:
    """Cache for distance calculations"""

    matrix: np.ndarray
    node_id_to_index: Dict[int, int]  # Map node ID to matrix index
    index_to_node_id: Dict[int, int]  # Map matrix index to node ID

    def get_distance(self, node_i: int, node_j: int) -> float:
        """Get distance between two nodes by ID"""
        i = self.node_id_to_index[node_i]
        j = self.node_id_to_index[node_j]
        return self.matrix[i, j]
```

---

## Common Data Transformations

### OSMnx Graph → VRP Instance

```python
def osmnx_to_vrp_instance(
    G: nx.MultiDiGraph,
    pickup_locations: List[Tuple[float, float]],  # (lat, lon)
    delivery_locations: List[Tuple[float, float]],
    **kwargs
) -> PDPTWInstance:
    """Convert OSMnx graph to PDPTW instance"""

    # Find nearest nodes in graph
    pickup_nodes = [ox.distance.nearest_nodes(G, lon, lat)
                    for lat, lon in pickup_locations]

    delivery_nodes = [ox.distance.nearest_nodes(G, lon, lat)
                      for lat, lon in delivery_locations]

    # Compute distance matrix
    all_nodes = [depot_node] + pickup_nodes + delivery_nodes
    distance_matrix = compute_distance_matrix(G, all_nodes)

    # Create Node objects
    nodes = create_nodes_from_osmnx(G, all_nodes)

    # Build instance
    instance = PDPTWInstance(
        nodes=nodes,
        distance_matrix=distance_matrix,
        **kwargs
    )

    return instance
```

### Solomon → VRP Instance

```python
def solomon_to_vrp_instance(filepath: str) -> PDPTWInstance:
    """Load Solomon benchmark as PDPTW instance"""

    solomon = parse_solomon_file(filepath)

    nodes = [
        Node(
            node_id=c.cust_no,
            x=c.x,
            y=c.y,
            demand=c.demand,
            time_window=(c.ready_time, c.due_date),
            service_time=c.service_time
        )
        for c in solomon.customers
    ]

    instance = PDPTWInstance(
        nodes=nodes,
        vehicle_capacity=solomon.vehicle_capacity,
        # ... other parameters
    )

    return instance
```

---

## Type Aliases

```python
OSMNodeID = int
Coordinate = Tuple[float, float]  # (x, y) or (lon, lat)
BoundingBox = Tuple[float, float, float, float]  # (min_x, max_x, min_y, max_y)
NetworkGraph = nx.MultiDiGraph
NodesGDF = gpd.GeoDataFrame
EdgesGDF = gpd.GeoDataFrame
```
