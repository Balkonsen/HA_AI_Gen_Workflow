# OSMnx Troubleshooting Guide

Common issues and solutions when working with OSMnx.

---

## Installation Issues

### Issue: Cannot install OSMnx

**Error:**
```
ERROR: Could not find a version that satisfies the requirement osmnx
```

**Solutions:**

1. **Update pip first:**
   ```bash
   pip install --upgrade pip
   ```

2. **Install with specific version:**
   ```bash
   pip install osmnx==1.6.0
   ```

3. **Use conda (recommended):**
   ```bash
   conda install -c conda-forge osmnx
   ```

### Issue: GeoPandas dependency errors

**Error:**
```
ModuleNotFoundError: No module named 'geopandas'
```

**Solution:**
```bash
# Install all geo dependencies
pip install geopandas shapely fiona pyproj

# Or use conda
conda install -c conda-forge geopandas
```

---

## Data Loading Issues

### Issue: Place name not found

**Error:**
```
InsufficientResponseError: Found no graph data ...
```

**Causes:**
- Incorrect place name
- Too small area
- Area not in OpenStreetMap

**Solutions:**

1. **Try different name formats:**
   ```python
   # Try these variations
   names = [
       "Purdue University, West Lafayette, IN, USA",
       "Purdue University, Indiana",
       "West Lafayette, Indiana, USA"
   ]

   for name in names:
       try:
           G = ox.graph_from_place(name)
           print(f"Success with: {name}")
           break
       except Exception as e:
           print(f"Failed: {name}")
   ```

2. **Use bounding box instead:**
   ```python
   G = ox.graph_from_bbox(north, south, east, west)
   ```

3. **Check place exists on OpenStreetMap:**
   - Visit https://nominatim.openstreetmap.org/
   - Search for your location
   - Use the exact name returned

### Issue: Empty graph returned

**Error:**
```
EmptyOverpassResponse: Found no graph data
```

**Solutions:**

1. **Expand search area:**
   ```python
   G = ox.graph_from_place(
       place_name,
       network_type='drive',
       buffer_dist=1000  # Add 1km buffer
   )
   ```

2. **Change network type:**
   ```python
   # Try 'all' instead of 'drive'
   G = ox.graph_from_place(place_name, network_type='all')
   ```

---

## Routing Issues

### Issue: No path between nodes

**Error:**
```
NetworkXNoPath: No path between nodes X and Y
```

**Causes:**
- Nodes in disconnected components
- One-way streets blocking path
- Isolated nodes

**Solutions:**

1. **Check graph connectivity:**
   ```python
   import networkx as nx

   # Get largest strongly connected component
   largest_scc = max(nx.strongly_connected_components(G), key=len)

   # Keep only connected nodes
   G = G.subgraph(largest_scc).copy()
   ```

2. **Convert to undirected:**
   ```python
   # If one-way streets are not important
   G_undirected = ox.get_undirected(G)
   ```

3. **Check if nodes exist:**
   ```python
   if origin not in G.nodes or dest not in G.nodes:
       print("One or both nodes not in graph!")
   ```

### Issue: Distance matrix has infinity values

**Problem:** Some nodes can't reach others

**Solution:**
```python
import numpy as np
import networkx as nx

def create_distance_matrix_with_fallback(G, nodes):
    """Create distance matrix with fallback for unreachable nodes"""
    n = len(nodes)
    matrix = np.full((n, n), np.inf)
    np.fill_diagonal(matrix, 0)

    for i, origin in enumerate(nodes):
        try:
            lengths = nx.single_source_dijkstra_path_length(
                G, origin, weight='length'
            )
            for j, dest in enumerate(nodes):
                if dest in lengths:
                    matrix[i, j] = lengths[dest]
                else:
                    # Use Euclidean distance as fallback
                    dx = G.nodes[dest]['x'] - G.nodes[origin]['x']
                    dy = G.nodes[dest]['y'] - G.nodes[origin]['y']
                    matrix[i, j] = np.sqrt(dx**2 + dy**2) * 111000  # deg to meters
        except nx.NetworkXError:
            pass

    return matrix
```

---

## Coordinate Issues

### Issue: (lat, lon) vs (lon, lat) confusion

**Problem:** Functions use different coordinate orders

**Rule:**
- **OSMnx `nearest_nodes`**: `(X, Y)` = `(lon, lat)`
- **Most other functions**: `(lat, lon)`
- **Node attributes**: `'x'` = lon, `'y'` = lat

**Solution:**
```python
# Customer location
lat, lon = 40.4237, -86.9212

# CORRECT
node_id = ox.distance.nearest_nodes(G, lon, lat)  # X=lon, Y=lat

# WRONG
node_id = ox.distance.nearest_nodes(G, lat, lon)  # Will find wrong node!

# Node data always uses 'x' for lon, 'y' for lat
node_data = G.nodes[node_id]
print(f"Lat: {node_data['y']}, Lon: {node_data['x']}")
```

---

## Performance Issues

### Issue: Graph loading is very slow

**Problem:** Downloading from Overpass API every time

**Solution:**
```python
import osmnx as ox
import os

# Cache directory
cache_dir = "data/osmnx_cache"
os.makedirs(cache_dir, exist_ok=True)

# Check if cached
cache_file = f"{cache_dir}/purdue_campus.graphml"

if os.path.exists(cache_file):
    # Load from cache (fast!)
    G = ox.load_graphml(cache_file)
    print("Loaded from cache")
else:
    # Download and cache
    G = ox.graph_from_place("Purdue University, West Lafayette, IN, USA")
    ox.save_graphml(G, cache_file)
    print("Downloaded and cached")
```

### Issue: Distance matrix computation is slow

**Problem:** Computing all-pairs shortest paths is O(n²)

**Solutions:**

1. **Use multiprocessing:**
   ```python
   from multiprocessing import Pool
   import networkx as nx

   def compute_row(args):
       G, origin, destinations = args
       lengths = nx.single_source_dijkstra_path_length(G, origin, weight='length')
       return [lengths.get(dest, np.inf) for dest in destinations]

   # Parallel computation
   with Pool() as pool:
       args = [(G, node, all_nodes) for node in all_nodes]
       rows = pool.map(compute_row, args)
       distance_matrix = np.array(rows)
   ```

2. **Cache computed matrices:**
   ```python
   import pickle

   # Save
   with open('distance_matrix.pkl', 'wb') as f:
       pickle.dump(distance_matrix, f)

   # Load
   with open('distance_matrix.pkl', 'rb') as f:
       distance_matrix = pickle.load(f)
   ```

---

## Data Quality Issues

### Issue: Missing speed limit data

**Problem:** `maxspeed` attribute not available for all edges

**Solution:**
```python
def get_speed_or_default(edge_data, default_speed=30):
    """Get speed with fallback to road type defaults"""

    # Try maxspeed attribute
    if 'maxspeed' in edge_data:
        maxspeed = edge_data['maxspeed']
        if isinstance(maxspeed, list):
            maxspeed = maxspeed[0]
        try:
            return float(maxspeed.split()[0])
        except:
            pass

    # Fallback based on highway type
    highway = edge_data.get('highway', 'residential')
    if isinstance(highway, list):
        highway = highway[0]

    speed_defaults = {
        'motorway': 100,
        'trunk': 80,
        'primary': 60,
        'secondary': 50,
        'tertiary': 40,
        'residential': 30,
        'service': 20
    }

    return speed_defaults.get(highway, default_speed)
```

### Issue: Simplified graph loses important nodes

**Problem:** `simplify=True` removes intermediate nodes

**Solution:**
```python
# Load without simplification
G = ox.graph_from_place(
    place_name,
    network_type='drive',
    simplify=False  # Keep all nodes
)

# Or re-add important nodes before simplifying
important_nodes = [...]  # Your important locations

G = ox.graph_from_place(place_name, simplify=True)

# Find nearest nodes to important locations
for loc in important_nodes:
    nearest = ox.distance.nearest_nodes(G, loc[1], loc[0])
    # Nearest node will still exist after simplification
```

---

## Memory Issues

### Issue: Out of memory with large graphs

**Problem:** Loading very large city networks

**Solutions:**

1. **Use smaller bounding box:**
   ```python
   # Instead of entire city, use smaller area
   G = ox.graph_from_bbox(north, south, east, west, truncate_by_edge=True)
   ```

2. **Filter network type:**
   ```python
   # Only major roads
   custom_filter = '["highway"~"motorway|trunk|primary"]'
   G = ox.graph_from_place(place_name, custom_filter=custom_filter)
   ```

3. **Process in chunks:**
   ```python
   # Divide area into grid and process separately
   # Then connect the grids
   ```

---

## Version Compatibility Issues

### Issue: API changed between versions

**Problem:** Code works with old OSMnx but not new version (or vice versa)

**Solution:**
```python
import osmnx as ox

print(f"OSMnx version: {ox.__version__}")

# For older versions (<1.0)
if int(ox.__version__.split('.')[0]) < 1:
    # Use old API
    G = ox.graph_from_place(place_name, network_type='drive')
else:
    # Use new API (1.0+)
    G = ox.graph_from_place(place_name, network_type='drive')
```

**Recommendation:** Pin version in requirements:
```
# requirements.txt
osmnx==1.6.0
```

---

## Common Warnings

### Warning: CRS mismatch

**Warning:**
```
UserWarning: CRS mismatch between the CRS of left geometries and the CRS of right geometries.
```

**Solution:**
```python
import geopandas as gpd

# Ensure consistent CRS
nodes_gdf = nodes_gdf.to_crs("EPSG:4326")  # WGS84
edges_gdf = edges_gdf.to_crs("EPSG:4326")
```

### Warning: Deprecated function

**Warning:**
```
DeprecationWarning: graph_from_place is deprecated, use graph_from_polygon
```

**Solution:**
Update OSMnx or use new function:
```bash
pip install --upgrade osmnx
```

---

## Debugging Tips

### Enable detailed logging

```python
import logging

# Set OSMnx to debug mode
ox.settings.log_console = True
ox.settings.log_file = True
ox.settings.log_filename = 'osmnx_debug.log'
```

### Inspect graph properties

```python
# Graph info
print(f"Nodes: {len(G.nodes)}")
print(f"Edges: {len(G.edges)}")
print(f"Is directed: {G.is_directed()}")
print(f"Is multigraph: {G.is_multigraph()}")

# Check connectivity
print(f"Is connected: {nx.is_weakly_connected(G)}")
print(f"Number of components: {nx.number_weakly_connected_components(G)}")

# Node attribute keys
sample_node = list(G.nodes(data=True))[0]
print(f"Node attributes: {sample_node[1].keys()}")

# Edge attribute keys
sample_edge = list(G.edges(data=True))[0]
print(f"Edge attributes: {sample_edge[2].keys()}")
```

---

## Getting Help

If issues persist:

1. **Check OSMnx documentation:** https://osmnx.readthedocs.io/
2. **Search GitHub issues:** https://github.com/gboeing/osmnx/issues
3. **Verify OpenStreetMap data:** https://www.openstreetmap.org/
4. **Test with simple example first:** Use a well-known location like "Manhattan, New York, USA"
