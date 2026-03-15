# OSMnx Usage Examples

Complete examples for common OSMnx integration tasks in VRP projects.

---

## Example 1: Load Campus Area

Load a university campus for delivery robot routing.

```python
import osmnx as ox

# Load Purdue University campus
place_name = "Purdue University, West Lafayette, IN, USA"
G = ox.graph_from_place(
    place_name,
    network_type='drive',  # Use 'walk' for pedestrian routing
    simplify=True
)

# Save for later use
ox.save_graphml(G, filepath="purdue_campus.graphml")

# Basic statistics
print(f"Nodes: {len(G.nodes)}")
print(f"Edges: {len(G.edges)}")
```

**Output:**
- Graph with street network
- Nodes represent intersections
- Edges represent roads

---

## Example 2: Load by Bounding Box

Load an area by coordinates (useful for specific regions).

```python
import osmnx as ox

# Define bounding box (north, south, east, west)
bbox = {
    'north': 40.4300,
    'south': 40.4200,
    'east': -86.9100,
    'west': -86.9250
}

G = ox.graph_from_bbox(
    bbox['north'],
    bbox['south'],
    bbox['east'],
    bbox['west'],
    network_type='drive'
)

# Visualize
ox.plot_graph(G)
```

---

## Example 3: Extract Potential Customer Locations

Find points of interest (POIs) as potential delivery locations.

```python
import osmnx as ox

# Load POIs in an area
tags = {
    'amenity': ['cafe', 'restaurant', 'library'],
    'building': ['university', 'dormitory']
}

pois = ox.geometries_from_place(
    "Purdue University, West Lafayette, IN, USA",
    tags=tags
)

# Extract coordinates
locations = []
for idx, poi in pois.iterrows():
    if poi.geometry.geom_type == 'Point':
        locations.append((poi.geometry.y, poi.geometry.x))  # (lat, lon)
    elif poi.geometry.geom_type == 'Polygon':
        centroid = poi.geometry.centroid
        locations.append((centroid.y, centroid.x))

print(f"Found {len(locations)} potential locations")
```

---

## Example 4: Find Nearest Network Nodes

Map arbitrary coordinates to nearest nodes in street network.

```python
import osmnx as ox

# Load graph
G = ox.graph_from_place("Purdue University, West Lafayette, IN, USA")

# Customer locations (lat, lon)
customer_locations = [
    (40.4237, -86.9212),
    (40.4280, -86.9145),
    (40.4200, -86.9180)
]

# Find nearest nodes
nearest_nodes = []
for lat, lon in customer_locations:
    node_id = ox.distance.nearest_nodes(G, lon, lat)  # Note: lon, lat order!
    nearest_nodes.append(node_id)

    # Get node attributes
    node_data = G.nodes[node_id]
    print(f"Node {node_id}: ({node_data['y']:.4f}, {node_data['x']:.4f})")

print(f"Nearest nodes: {nearest_nodes}")
```

**Important:** `nearest_nodes` takes `(X, Y)` which is `(lon, lat)`, not `(lat, lon)`!

---

## Example 5: Compute Distance Matrix

Calculate shortest path distances between all nodes.

```python
import osmnx as ox
import networkx as nx
import numpy as np

# Load graph
G = ox.graph_from_place("Purdue University, West Lafayette, IN, USA")

# Select nodes (e.g., depot + customers)
node_ids = [123456, 234567, 345678, 456789]  # Replace with actual IDs

# Compute distance matrix
n = len(node_ids)
distance_matrix = np.zeros((n, n))

for i, origin in enumerate(node_ids):
    # Compute shortest paths from origin
    lengths = nx.single_source_dijkstra_path_length(
        G, origin, weight='length'
    )

    for j, dest in enumerate(node_ids):
        if i != j and dest in lengths:
            distance_matrix[i, j] = lengths[dest]

print("Distance Matrix (meters):")
print(distance_matrix)
```

---

## Example 6: Compute Travel Time Matrix

Convert distances to travel times using average speed.

```python
import numpy as np

# Assume distance_matrix already computed (in meters)
average_speed_kmh = 30  # km/h
average_speed_ms = average_speed_kmh * 1000 / 3600  # m/s

# Time matrix (in seconds)
time_matrix = distance_matrix / average_speed_ms

# Convert to minutes
time_matrix_minutes = time_matrix / 60

print("Time Matrix (minutes):")
print(time_matrix_minutes)
```

---

## Example 7: Create PDPTW Instance from OSMnx

Complete workflow: OSMnx → VRP Instance.

```python
import osmnx as ox
import networkx as nx
import numpy as np
from vrp_toolkit.problems import PDPTWInstance, Node

# 1. Load street network
G = ox.graph_from_place("Purdue University, West Lafayette, IN, USA")

# 2. Define locations (lat, lon)
depot_loc = (40.4237, -86.9212)
pickup_locs = [
    (40.4280, -86.9145),
    (40.4200, -86.9180)
]
delivery_locs = [
    (40.4250, -86.9100),
    (40.4210, -86.9220)
]

# 3. Find nearest nodes
depot_node = ox.distance.nearest_nodes(G, depot_loc[1], depot_loc[0])
pickup_nodes = [ox.distance.nearest_nodes(G, lon, lat)
                for lat, lon in pickup_locs]
delivery_nodes = [ox.distance.nearest_nodes(G, lon, lat)
                  for lat, lon in delivery_locs]

all_osm_nodes = [depot_node] + pickup_nodes + delivery_nodes

# 4. Compute distance matrix
n = len(all_osm_nodes)
distance_matrix = np.zeros((n, n))

for i, origin in enumerate(all_osm_nodes):
    lengths = nx.single_source_dijkstra_path_length(G, origin, weight='length')
    for j, dest in enumerate(all_osm_nodes):
        if i != j and dest in lengths:
            distance_matrix[i, j] = lengths[dest]

# 5. Create Node objects
nodes = []

# Depot
nodes.append(Node(
    node_id=0,
    x=G.nodes[depot_node]['x'],
    y=G.nodes[depot_node]['y'],
    node_type='depot'
))

# Pickups and deliveries
for idx, (p_node, d_node) in enumerate(zip(pickup_nodes, delivery_nodes), 1):
    pickup_idx = idx * 2 - 1
    delivery_idx = idx * 2

    # Pickup
    nodes.append(Node(
        node_id=pickup_idx,
        x=G.nodes[p_node]['x'],
        y=G.nodes[p_node]['y'],
        demand=10.0,
        time_window=(8.0, 17.0),
        node_type='pickup',
        pair_node_id=delivery_idx
    ))

    # Delivery
    nodes.append(Node(
        node_id=delivery_idx,
        x=G.nodes[d_node]['x'],
        y=G.nodes[d_node]['y'],
        demand=-10.0,
        time_window=(8.0, 17.0),
        node_type='delivery',
        pair_node_id=pickup_idx
    ))

# 6. Create instance
instance = PDPTWInstance(
    nodes=nodes,
    battery_capacity=100.0,
    max_route_time=480.0,
    vehicle_capacity=50.0
)

# Store distance matrix
instance.distance_matrix = distance_matrix

print(f"Created instance with {len(nodes)} nodes")
```

---

## Example 8: Visualize Routes on Map

Plot solution routes on the actual street network.

```python
import osmnx as ox
import matplotlib.pyplot as plt

# Load graph
G = ox.graph_from_place("Purdue University, West Lafayette, IN, USA")

# Solution routes (as OSM node IDs)
routes = [
    [depot_node, pickup_nodes[0], delivery_nodes[0], depot_node],
    [depot_node, pickup_nodes[1], delivery_nodes[1], depot_node]
]

# Plot graph
fig, ax = ox.plot_graph(
    G,
    bgcolor='white',
    node_size=0,
    edge_color='gray',
    show=False,
    close=False
)

# Plot routes
colors = ['blue', 'red', 'green', 'orange']

for route_idx, route in enumerate(routes):
    # Get coordinates for route
    route_coords = [(G.nodes[node]['x'], G.nodes[node]['y'])
                    for node in route]

    xs, ys = zip(*route_coords)

    # Plot route
    ax.plot(xs, ys,
            color=colors[route_idx],
            linewidth=3,
            alpha=0.7,
            label=f'Route {route_idx + 1}')

    # Plot stops
    ax.scatter(xs, ys,
              color=colors[route_idx],
              s=100,
              zorder=5)

ax.legend()
plt.title("VRP Solution on Street Network")
plt.show()
```

---

## Example 9: Save/Load Graphs

Save processed graphs for reuse (much faster than re-downloading).

```python
import osmnx as ox

# Save graph
G = ox.graph_from_place("Purdue University, West Lafayette, IN, USA")
ox.save_graphml(G, filepath="data/purdue_campus.graphml")

# Load graph (instant!)
G_loaded = ox.load_graphml(filepath="data/purdue_campus.graphml")

# Also save as GeoDataFrame for GIS tools
nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)
nodes_gdf.to_file("data/purdue_nodes.geojson", driver="GeoJSON")
edges_gdf.to_file("data/purdue_edges.geojson", driver="GeoJSON")
```

---

## Example 10: Extract Road Attributes

Get speed limits, road types for more accurate routing.

```python
import osmnx as ox

G = ox.graph_from_place("Purdue University, West Lafayette, IN, USA")

# Inspect edge attributes
for u, v, key, data in list(G.edges(keys=True, data=True))[:5]:
    print(f"Edge {u} -> {v}:")
    print(f"  Length: {data.get('length', 'N/A')} m")
    print(f"  Highway type: {data.get('highway', 'N/A')}")
    print(f"  Max speed: {data.get('maxspeed', 'N/A')}")
    print(f"  Name: {data.get('name', 'Unnamed')}")
    print()

# Calculate time weights based on speed limits
for u, v, key, data in G.edges(keys=True, data=True):
    length = data['length']  # meters

    # Get speed limit (or use default)
    maxspeed = data.get('maxspeed', '30 mph')
    if isinstance(maxspeed, list):
        maxspeed = maxspeed[0]

    # Parse speed (simple version)
    try:
        speed_kmh = float(maxspeed.split()[0])
    except:
        speed_kmh = 30.0  # default

    # Calculate travel time (in seconds)
    speed_ms = speed_kmh * 1000 / 3600
    travel_time = length / speed_ms

    # Add as edge attribute
    data['travel_time'] = travel_time

# Now use 'travel_time' as weight in routing
path = nx.shortest_path(G, origin, dest, weight='travel_time')
```

---

## Common Parameters

### network_type Options

- `'drive'` - Roads for cars
- `'walk'` - Pedestrian paths
- `'bike'` - Bicycle routes
- `'all'` - All ways (including private roads)
- `'all_private'` - All ways including private

### simplify Parameter

- `True` - Simplify graph topology (faster, fewer nodes)
- `False` - Keep full detail (more nodes, exact geometry)

### Custom Filters

```python
# Custom filter for specific road types
custom_filter = '["highway"~"residential|service"]'
G = ox.graph_from_place(
    place_name,
    custom_filter=custom_filter
)
```
