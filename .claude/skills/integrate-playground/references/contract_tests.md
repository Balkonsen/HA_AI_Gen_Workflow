# Contract Testing Guide

**Purpose:** How to write, organize, and maintain contract tests that verify playground ↔ vrp-toolkit interfaces.

---

## What are Contract Tests?

Contract tests verify that:
1. **API signatures match** what `interface_mapping.md` documents
2. **Reproducibility** - same inputs produce same outputs
3. **Feasibility** - outputs meet problem constraints
4. **Consistency** - objective values and results are correct

---

## Test Organization

```
contracts/
├── README.md                    # Overview and running instructions
├── test_realmap_api.py         # RealMap interface tests
├── test_demand_generation.py   # DemandGenerator interface tests
├── test_order_generation.py    # OrderGenerator interface tests
├── test_instance_creation.py   # PDPTWInstance interface tests
├── test_alns_config.py         # ALNSConfig interface tests
├── test_alns_solve.py          # ALNS solver interface tests
└── test_solution_api.py        # Solution object interface tests
```

---

## Test Template

### Basic API Contract Test

```python
# contracts/test_<feature>_api.py
import pytest
import numpy as np
from vrp_toolkit.data.map import RealMap

def test_realmap_signature():
    """Verifies RealMap API matches interface_mapping.md specification."""
    # Test exact parameters work
    real_map = RealMap(
        n_r=3,
        n_c=10,
        dist_function=np.random.uniform,
        dist_params={'low': 0, 'high': 100}
    )

    # Verify expected attributes exist
    assert hasattr(real_map, 'distance_matrix')
    assert hasattr(real_map, 'restaurants')
    assert hasattr(real_map, 'customers')
    assert hasattr(real_map, 'coordinates')

    # Verify types
    assert isinstance(real_map.distance_matrix, np.ndarray)
    assert isinstance(real_map.restaurants, list)
    assert isinstance(real_map.customers, list)

def test_realmap_wrong_params():
    """Verifies wrong parameters are rejected."""
    with pytest.raises(TypeError):
        # Should fail - wrong parameter names
        RealMap(num_customers=10, num_restaurants=3)
```

### Reproducibility Test

```python
def test_realmap_reproducibility():
    """Same seed produces same result."""
    # First generation
    np.random.seed(42)
    map1 = RealMap(
        n_r=3, n_c=10,
        dist_function=np.random.uniform,
        dist_params={'low': 0, 'high': 100}
    )

    # Second generation with same seed
    np.random.seed(42)
    map2 = RealMap(
        n_r=3, n_c=10,
        dist_function=np.random.uniform,
        dist_params={'low': 0, 'high': 100}
    )

    # Should be identical
    np.testing.assert_array_equal(map1.distance_matrix, map2.distance_matrix)
    assert map1.coordinates == map2.coordinates
```

### Feasibility Test

```python
def test_pdptw_instance_feasibility():
    """Instance meets PDPTW constraints."""
    # Create instance...
    instance = PDPTWInstance(...)

    # Verify pickup-delivery pairing
    assert instance.n * 2 <= len(instance.indices)

    # Verify time windows are valid
    for start, end in instance.time_windows:
        assert start <= end

    # Verify demands sum to zero (pickups + deliveries)
    assert abs(sum(instance.demands)) < 1e-6
```

### End-to-End Integration Test

```python
def test_full_workflow():
    """Complete workflow from map to solution."""
    # Generate map
    np.random.seed(42)
    real_map = RealMap(n_r=2, n_c=5,
                       dist_function=np.random.uniform,
                       dist_params={'low': 0, 'high': 50})

    # Generate demands
    demand_gen = DemandGenerator(
        time_range=120, time_step=30,
        restaurants=real_map.restaurants,
        customers=real_map.customers,
        random_params={
            'sample_dist': {'function': np.random.poisson, 'params': {'lam': 2}},
            'demand_dist': {'function': np.random.randint, 'params': {'low': 1, 'high': 3}}
        }
    )

    # Generate orders
    order_gen = OrderGenerator(
        real_map=real_map,
        demand_table=demand_gen.demand_table,
        time_params={'time_window_length': 20, 'service_time': 5, 'extra_time': 5, 'big_time': 500},
        robot_speed=1.0
    )

    # Create instance
    instance = PDPTWInstance(
        order_table=order_gen.order_table,
        distance_matrix=real_map.distance_matrix,
        time_matrix=order_gen.time_matrix,
        robot_speed=1.0
    )

    # Solve
    config = ALNSConfig(max_iterations=100, seed=42)
    problem = PDPTWProblemAdapter(instance)
    solver = ALNS(config)
    solution = solver.solve(problem, num_vehicles=2)

    # Verify solution
    assert solution is not None
    assert hasattr(solution, 'routes')
    assert hasattr(solution, 'objective_value')
    assert len(solution.routes) > 0
    assert solution.objective_value > 0
```

---

## Running Tests

### Run all contract tests
```bash
pytest contracts/ -v
```

### Run specific test file
```bash
pytest contracts/test_realmap_api.py -v
```

### Run specific test function
```bash
pytest contracts/test_realmap_api.py::test_realmap_signature -v
```

### Show print output
```bash
pytest contracts/ -v -s
```

---

## Maintenance Workflow

### When API Changes

1. **Update interface_mapping.md** first with new signature
2. **Update or create contract test**:
   ```python
   def test_new_api():
       """Verifies new API matches updated spec."""
       # Test new signature...
   ```
3. **Run tests** to verify: `pytest contracts/test_<feature>.py`
4. **Update playground code** to use new API
5. **Add reference** in interface_mapping.md to the test

### When Adding New Playground Feature

1. **Add API to interface_mapping.md**
2. **Create contract test** in `contracts/test_<feature>.py`
3. **Link from mapping table**: Add "Contract Test" column entry
4. **Verify test passes**: `pytest contracts/test_<feature>.py -v`

### Test Maintenance Checklist

- [ ] Test names clearly describe what they verify
- [ ] Tests are independent (can run in any order)
- [ ] Tests use fixtures for common setup (if needed)
- [ ] Tests document expected behavior in docstrings
- [ ] Tests linked from interface_mapping.md
- [ ] Tests run quickly (< 5 seconds each)

---

## Common Test Patterns

### Parameterized Tests

```python
@pytest.mark.parametrize("n_r,n_c", [(2, 5), (3, 10), (5, 20)])
def test_realmap_sizes(n_r, n_c):
    """Test RealMap with various sizes."""
    np.random.seed(42)
    real_map = RealMap(n_r=n_r, n_c=n_c,
                       dist_function=np.random.uniform,
                       dist_params={'low': 0, 'high': 100})

    assert len(real_map.restaurants) == n_r
    assert len(real_map.customers) == n_c
```

### Fixtures for Common Setup

```python
@pytest.fixture
def simple_real_map():
    """Create simple real map for testing."""
    np.random.seed(42)
    return RealMap(n_r=2, n_c=5,
                   dist_function=np.random.uniform,
                   dist_params={'low': 0, 'high': 50})

def test_with_fixture(simple_real_map):
    """Use fixture in test."""
    assert len(simple_real_map.restaurants) == 2
```

---

## Test Coverage Goals

**Minimum coverage for each API:**
1. ✅ Signature test (correct parameters work)
2. ✅ Attribute test (expected attributes exist)
3. ✅ Type test (attributes have correct types)
4. ✅ Reproducibility test (same seed → same result)
5. ✅ Error test (wrong parameters fail appropriately)

**Optional but recommended:**
- Edge case tests (empty inputs, large inputs)
- Integration tests (multi-step workflows)
- Performance tests (time/memory constraints)
