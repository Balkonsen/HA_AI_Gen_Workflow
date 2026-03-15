# Troubleshooting Guide

**Purpose:** Quick reference for common errors and solutions when integrating playground with vrp-toolkit.

---

## Common Errors by Category

### 0. Reproducibility Errors (CRITICAL)

#### Results not reproducible with same seed

**Error:**
Playground shows different results when using same seed parameter.

**Cause:** ALNSConfig created without `seed` parameter

**Solution:**
```python
# ❌ Wrong - seed not passed to ALNSConfig
np.random.seed(42)  # Not enough!
config = ALNSConfig(
    num_segments=10,
    segment_length=100,
    start_temp=10.0
)

# ✅ Correct - seed in ALNSConfig
config = ALNSConfig(
    num_segments=10,
    segment_length=100,
    start_temp=10.0,
    seed=42  # CRITICAL for reproducibility!
)
```

**Reference:** [contract_tests.md](contract_tests.md#reproducibility-contracts)

---

### 1. Parameter Mismatch Errors

#### TypeError: got an unexpected keyword argument 'num_customers'

**Error:**
```
TypeError: RealMap.__init__() got an unexpected keyword argument 'num_customers'
```

**Cause:** Using wrong parameter names

**Solution:**
```python
# ❌ Wrong
RealMap(num_customers=10, num_restaurants=3)

# ✅ Correct
RealMap(n_r=3, n_c=10, dist_function=..., dist_params=...)
```

**Reference:** [interface_mapping.md](interface_mapping.md#1-realmap)

---

#### TypeError: missing required positional arguments

**Error:**
```
TypeError: PDPTWInstance.__init__() missing 3 required positional arguments:
'distance_matrix', 'time_matrix', and 'robot_speed'
```

**Cause:** Missing required parameters

**Solution:**
```python
# ❌ Wrong - Only passing order_table
instance = PDPTWInstance(order_table=order_table)

# ✅ Correct - All 4 required parameters
instance = PDPTWInstance(
    order_table=order_table,
    distance_matrix=real_map.distance_matrix,
    time_matrix=order_gen.time_matrix,
    robot_speed=1.0
)
```

**Reference:** [interface_mapping.md](interface_mapping.md#4-pdptwinstance)

---

#### TypeError: greedy_insertion_initial_solution() missing 2 required positional arguments

**Error:**
```
TypeError: greedy_insertion_initial_solution() missing 2 required positional arguments:
'penalty_unvisit' and 'penalty_delay'
```

**Cause:** Missing required penalty parameters

**Solution:**
```python
# ❌ Wrong - Missing penalty parameters
initial_solution = greedy_insertion_initial_solution(
    problem=problem,
    num_vehicles=3,
    vehicle_capacity=1000,
    battery_capacity=100.0,
    battery_consume_rate=1.0
)

# ✅ Correct - All 7 required parameters
initial_solution = greedy_insertion_initial_solution(
    problem=problem,
    num_vehicles=3,
    vehicle_capacity=1000,
    battery_capacity=100.0,
    battery_consume_rate=1.0,
    penalty_unvisit=1000.0,  # Required
    penalty_delay=100.0       # Required
)
```

**Reference:** [api_signatures.md](api_signatures.md#greedy_insertion_initial_solution)

---

### 2. Attribute vs Method Errors

#### AttributeError: object has no attribute 'generate'

**Error:**
```
AttributeError: 'DemandGenerator' object has no attribute 'generate'
AttributeError: 'OrderGenerator' object has no attribute 'generate'
```

**Cause:** Trying to call non-existent method - generators create data in `__init__`

**Solution:**
```python
# ❌ Wrong
demand_gen = DemandGenerator(...)
demand_table = demand_gen.generate()  # No such method!

# ✅ Correct
demand_gen = DemandGenerator(...)
demand_table = demand_gen.demand_table  # Access attribute
```

**Reference:** [interface_mapping.md](interface_mapping.md#data-access-patterns)

---

#### AttributeError: object has no attribute 'DEFAULT_COLUMNS'

**Error:**
```
AttributeError: 'OrderGenerator' object has no attribute 'DEFAULT_COLUMNS'
```

**Cause:** Accessing module-level constant as instance attribute

**Solution:**
```python
# In generators.py source code:

# ❌ Wrong
df = pd.DataFrame(data, columns=self.DEFAULT_COLUMNS)

# ✅ Correct
df = pd.DataFrame(data, columns=DEFAULT_COLUMNS)
```

**Reference:** [DEBUG_LOG.md](../../DEBUG_LOG.md) - Search for "DEFAULT_COLUMNS"

---

### 3. Module Caching Issues

#### Changes not reflected after editing vrp-toolkit source

**Symptom:** Modified vrp-toolkit code but playground still uses old behavior

**Cause:** Python/Streamlit caches imported modules

**Solutions:**

**Option 1: Restart Streamlit**
```bash
# Kill current Streamlit process
# Ctrl+C or kill <pid>

# Restart
cd playground
uv run streamlit run app.py
```

**Option 2: Force module reload (not recommended)**
```python
import importlib
import vrp_toolkit.data.generators
importlib.reload(vrp_toolkit.data.generators)
```

**Best practice:** Always restart Streamlit after changing vrp-toolkit source

---

### 4. Wrong Data Source Errors

#### AttributeError: 'RealMap' object has no attribute 'time_matrix'

**Error:**
```
AttributeError: 'RealMap' object has no attribute 'time_matrix'
```

**Cause:** Trying to get time_matrix from wrong source

**Solution:**
```python
# ❌ Wrong - RealMap only has distance_matrix
instance = PDPTWInstance(
    ...
    time_matrix=real_map.time_matrix  # Doesn't exist!
)

# ✅ Correct - time_matrix comes from OrderGenerator
instance = PDPTWInstance(
    ...
    time_matrix=order_gen.time_matrix  # Correct source
)
```

**Reference:** [interface_mapping.md](interface_mapping.md#common-mistakes)

---

### 5. Seed/Reproducibility Issues

#### Results not reproducible with same seed

**Symptom:** Same seed parameter but different results each run

**Cause:** Seed parameter doesn't exist or isn't used correctly

**Solution:**
```python
# ❌ Wrong - No seed parameter in RealMap
real_map = RealMap(..., seed=42)

# ✅ Correct - Set numpy seed before calling
np.random.seed(42)
real_map = RealMap(
    n_r=3, n_c=10,
    dist_function=np.random.uniform,
    dist_params={'low': 0, 'high': 100}
)
```

**Note:** For ALNS solver, use `ALNSConfig(seed=42)`

---

### 6. Data Type Errors

#### ValueError: could not convert string to float

**Cause:** Wrong data type in DataFrame or parameters

**Common cases:**
1. Column mapping issues in order_table
2. String values where floats expected
3. Missing data (NaN) in critical columns

**Debugging:**
```python
# Check DataFrame types
print(order_table.dtypes)

# Check for NaN
print(order_table.isnull().sum())

# Check column names
print(order_table.columns.tolist())
```

---

## Debugging Workflow

### Step 1: Identify Error Type

**Look at error message traceback:**
- `TypeError` → Wrong parameters or types
- `AttributeError` → Trying to access non-existent attribute/method
- `ValueError` → Invalid value for parameter
- `ImportError` → Module not found or not installed

### Step 2: Check Interface Mapping

1. Open [interface_mapping.md](interface_mapping.md)
2. Find the API you're calling
3. Compare your code with the documented signature
4. Check "Common Mistakes" section

### Step 3: Run Contract Test

```bash
# Test specific API
pytest contracts/test_<feature>_api.py -v

# If test passes, your vrp-toolkit is correct
# If test fails, vrp-toolkit may have changed
```

### Step 4: Verify Environment

```bash
# Check Python version
python --version  # Should be 3.11+

# Check vrp-toolkit installation
pip show vrp-toolkit

# Check if editable install
pip list | grep vrp-toolkit  # Should show path if editable
```

### Step 5: Check Module Cache

**If changes not reflecting:**
1. Restart Streamlit completely
2. Check if virtual environment is correct
3. Verify file was actually saved

---

## Quick Fixes

### Reset Everything

```bash
# Kill Streamlit
# Ctrl+C or kill <pid>

# Reinstall vrp-toolkit (if needed)
cd vrp-toolkit
pip install -e .

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Restart Streamlit
cd ../playground
streamlit run app.py
```

### Verify Installation

```python
# In Python/Streamlit
import vrp_toolkit
print(vrp_toolkit.__file__)  # Should show correct path

from vrp_toolkit.data.map import RealMap
print(RealMap.__init__.__doc__)  # Check signature
```

---

## Prevention Checklist

Before writing integration code:

- [ ] Check interface_mapping.md for exact API
- [ ] Verify parameter names match exactly
- [ ] Confirm it's attribute vs method access
- [ ] Check which object provides which data (RealMap vs OrderGenerator)
- [ ] Set numpy seed if reproducibility needed
- [ ] Add try/except with helpful error messages

Example error handling:
```python
try:
    instance = PDPTWInstance(
        order_table=order_table,
        distance_matrix=real_map.distance_matrix,
        time_matrix=order_gen.time_matrix,
        robot_speed=1.0
    )
except TypeError as e:
    st.error(f"❌ API mismatch: {e}")
    st.info("💡 Check interface_mapping.md for correct parameters")
    st.stop()
```

---

## Getting Help

If error persists:

1. **Check DEBUG_LOG.md** for similar issues
2. **Run contract tests** to isolate the problem
3. **Read actual source code** as last resort (but update mapping table after!)
4. **Document the solution** in DEBUG_LOG.md for future reference

---

## Common Error Quick Reference

| Error Message Snippet | Likely Cause | Fix |
|----------------------|--------------|-----|
| `unexpected keyword argument` | Wrong parameter name | Check interface_mapping.md |
| `missing required positional arguments` | Missing parameters | Add all required params |
| `has no attribute 'generate'` | Trying to call method | Access attribute instead |
| `has no attribute 'DEFAULT_COLUMNS'` | Module vs instance confusion | Remove `self.` prefix |
| `'RealMap' object has no attribute 'time_matrix'` | Wrong data source | Get from OrderGenerator |
| Changes not reflected | Module cache | Restart Streamlit |
| Results not reproducible | Seed not set | Use `np.random.seed()` |
