# Integration Patterns: VRP-Toolkit ↔ Playground

How to integrate vrp-toolkit modules into Streamlit playground components.

## Pattern 1: Loading Problem Instances

### From File Upload

```python
import streamlit as st
from vrp_toolkit.problems.pdptw import PDPTWInstance
import pandas as pd

def load_instance_from_upload():
    """Load instance from user-uploaded CSV file."""
    uploaded_file = st.file_uploader(
        "Upload Order Table (CSV)",
        type=['csv'],
        help="CSV file with columns: id, type, x, y, demand, tw_start, tw_end"
    )

    if uploaded_file is not None:
        try:
            # Read CSV into DataFrame
            order_table = pd.read_csv(uploaded_file)

            # Validate required columns
            required_cols = ['id', 'type', 'x', 'y', 'demand', 'tw_start', 'tw_end']
            missing_cols = set(required_cols) - set(order_table.columns)
            if missing_cols:
                st.error(f"Missing columns: {missing_cols}")
                return None

            # Create instance
            instance = PDPTWInstance(order_table=order_table)

            st.success(f"✅ Loaded instance with {instance.n} orders")
            return instance

        except Exception as e:
            st.error(f"❌ Error loading instance: {e}")
            return None

    return None
```

### From Synthetic Generation

```python
from vrp_toolkit.data.generators import OrderGenerator, DemandGenerator
from vrp_toolkit.data.map import RealMap

@st.cache_data
def generate_synthetic_instance(num_orders, seed, map_size=100):
    """Generate synthetic PDPTW instance."""
    # Create synthetic map
    real_map = RealMap(
        num_customers=num_orders,
        num_restaurants=max(3, num_orders // 3),
        area_size=map_size,
        seed=seed
    )

    # Generate demands
    demand_gen = DemandGenerator(
        num_customers=num_orders,
        num_restaurants=real_map.num_restaurants,
        seed=seed
    )
    demand_table = demand_gen.generate()

    # Generate orders
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
    order_table = order_gen.generate()

    # Create instance
    instance = PDPTWInstance(order_table=order_table)

    return instance, real_map
```

### UI Component

```python
def render_instance_loader():
    """Render instance loading UI."""
    st.subheader("📦 Problem Instance")

    # Choose loading method
    load_method = st.radio(
        "Load Method",
        ["Upload CSV", "Generate Synthetic", "Load Example"]
    )

    instance = None

    if load_method == "Upload CSV":
        instance = load_instance_from_upload()

    elif load_method == "Generate Synthetic":
        col1, col2 = st.columns(2)
        with col1:
            num_orders = st.slider("Number of Orders", 2, 50, 10)
        with col2:
            seed = st.number_input("Seed", 0, 99999, 42)

        if st.button("Generate"):
            with st.spinner("Generating instance..."):
                instance, real_map = generate_synthetic_instance(num_orders, seed)
                st.session_state.instance = instance
                st.session_state.real_map = real_map

    elif load_method == "Load Example":
        example_name = st.selectbox("Example", ["Small (5 orders)", "Medium (20 orders)"])
        # Load from examples/ directory
        instance = load_example_instance(example_name)

    return instance
```

## Pattern 2: Configuring Algorithms

### ALNS Configuration

```python
from vrp_toolkit.algorithms.alns import ALNSConfig

def get_alns_config_from_ui():
    """Build ALNSConfig from UI inputs."""
    st.subheader("⚙️ ALNS Configuration")

    # Basic params
    col1, col2 = st.columns(2)
    with col1:
        max_iterations = st.slider("Max Iterations", 100, 10000, 1000)
        start_temp = st.number_input("Start Temperature", 0.1, 100.0, 10.0)

    with col2:
        cooling_rate = st.slider("Cooling Rate", 0.90, 0.99, 0.95, 0.01)
        segment_length = st.number_input("Segment Length", 10, 500, 100)

    # Advanced params (in expander)
    with st.expander("Advanced"):
        num_removal = st.slider("Removal Count", 1, 20, 5)
        p = st.slider("Shaw Relatedness", 1.0, 10.0, 4.0, 0.5)
        r = st.slider("Randomness", 0.0, 1.0, 0.1, 0.05)

    # Create config
    config = ALNSConfig(
        max_iterations=max_iterations,
        start_temp=start_temp,
        cooling_rate=cooling_rate,
        segment_length=segment_length,
        num_removal=num_removal,
        p=p,
        r=r
    )

    return config
```

## Pattern 3: Running Solvers

### Basic Execution

```python
from vrp_toolkit.algorithms.alns import ALNS, greedy_insertion_initial_solution

def run_alns(instance, config, num_vehicles, battery_capacity, seed):
    """Run ALNS solver with error handling."""
    try:
        # Generate initial solution
        with st.spinner("Generating initial solution..."):
            from vrp_toolkit.algorithms.base import PDPTWProblemAdapter
            problem = PDPTWProblemAdapter(instance)

            initial_solution = greedy_insertion_initial_solution(
                problem=problem,
                num_vehicles=num_vehicles,
                vehicle_capacity=1000,
                battery_capacity=battery_capacity,
                battery_consume_rate=1.0
            )

            if initial_solution is None:
                st.error("❌ Failed to generate initial solution")
                return None

        # Run ALNS
        with st.spinner("Running ALNS..."):
            dist_matrix = instance.distance_matrix

            alns = ALNS(
                initial_solution=initial_solution._solution,
                config=config,
                dist_matrix=dist_matrix,
                battery_capacity=battery_capacity
            )

            # Run with seed
            import numpy as np
            np.random.seed(seed)

            alns.run()

            st.success("✅ ALNS completed!")

            return alns.best_solution, alns.cost_history

    except ValueError as e:
        st.error(f"❌ Invalid parameters: {e}")
        st.info("💡 Check that all parameters are positive and feasible")
        return None

    except Exception as e:
        st.error(f"❌ Error during solving: {e}")
        st.exception(e)
        return None
```

### With Progress Updates (Advanced)

```python
def run_alns_with_progress(instance, config, num_vehicles, battery_capacity, seed):
    """Run ALNS with live progress updates."""
    # Initialize
    problem = PDPTWProblemAdapter(instance)
    initial_solution = greedy_insertion_initial_solution(
        problem, num_vehicles, 1000, battery_capacity, 1.0
    )

    alns = ALNS(initial_solution._solution, config, instance.distance_matrix, battery_capacity)

    # Progress containers
    progress_bar = st.progress(0)
    status_text = st.empty()
    cost_chart = st.empty()

    # Run with manual iteration control
    cost_history = []

    for iteration in range(config.max_iterations):
        # Run one iteration
        alns.run_one_iteration()  # Hypothetical method

        # Update progress
        progress = (iteration + 1) / config.max_iterations
        progress_bar.progress(progress)

        cost_history.append(alns.current_cost)

        # Update UI every 10 iterations
        if iteration % 10 == 0:
            status_text.text(f"Iteration {iteration}/{config.max_iterations} - Cost: {alns.current_cost:.2f}")
            cost_chart.line_chart(cost_history)

    status_text.text("✅ Complete!")
    return alns.best_solution, cost_history
```

## Pattern 4: Visualizing Solutions

### Route Visualization

```python
from vrp_toolkit.visualization.algorithm import PDPTWVisualizer
import matplotlib.pyplot as plt

def visualize_solution(solution, instance):
    """Visualize solution routes on map."""
    fig, ax = plt.subplots(figsize=(10, 8))

    # Use toolkit visualizer
    visualizer = PDPTWVisualizer(instance)
    visualizer.plot_solution(solution, ax=ax)

    ax.set_title(f"Solution (Cost: {solution.objective_value:.2f})")
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")

    return fig
```

### Convergence Plot

```python
def plot_convergence(cost_history):
    """Plot cost over iterations."""
    fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot(cost_history, linewidth=2, color='#1f77b4')
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Total Cost')
    ax.set_title('Convergence Plot')
    ax.grid(True, alpha=0.3)

    # Highlight best
    best_idx = cost_history.index(min(cost_history))
    best_cost = cost_history[best_idx]
    ax.plot(best_idx, best_cost, 'r*', markersize=15, label='Best Solution')
    ax.legend()

    return fig
```

## Pattern 5: Saving/Loading Experiments

### Save Experiment

```python
import json
from datetime import datetime
from pathlib import Path

def save_experiment(config, solution, instance, metrics):
    """Save experiment to runs/ directory."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = Path(f"runs/{timestamp}")
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save config
    config_dict = {
        'max_iterations': config.max_iterations,
        'start_temp': config.start_temp,
        'cooling_rate': config.cooling_rate,
        # ... other params
    }
    with open(run_dir / "config.json", "w") as f:
        json.dump(config_dict, f, indent=2)

    # Save metrics
    metrics_dict = {
        'cost': solution.objective_value,
        'feasible': solution.is_feasible(),
        'runtime': metrics['runtime'],
        'iterations': metrics['iterations']
    }
    with open(run_dir / "metrics.json", "w") as f:
        json.dump(metrics_dict, f, indent=2)

    # Save solution (routes)
    solution_dict = {
        'routes': [list(route) for route in solution.routes],
        'cost': solution.objective_value
    }
    with open(run_dir / "solution.json", "w") as f:
        json.dump(solution_dict, f, indent=2)

    # Save instance (for reproducibility)
    instance.order_table.to_csv(run_dir / "instance.csv", index=False)

    st.success(f"💾 Saved to {run_dir}")
    return run_dir
```

### Load Experiment

```python
def load_experiment(run_dir):
    """Load experiment from runs/ directory."""
    run_path = Path(run_dir)

    # Load config
    with open(run_path / "config.json") as f:
        config_dict = json.load(f)

    # Load metrics
    with open(run_path / "metrics.json") as f:
        metrics = json.load(f)

    # Load instance
    instance = PDPTWInstance.from_csv(run_path / "instance.csv")

    # Load solution (reconstruct)
    with open(run_path / "solution.json") as f:
        solution_dict = json.load(f)

    # Note: Full solution reconstruction may need more info
    # For now, just return the data
    return {
        'config': config_dict,
        'metrics': metrics,
        'instance': instance,
        'routes': solution_dict['routes']
    }
```

## Pattern 6: Validation & Error Handling

### Solution Validation

```python
def validate_and_display(solution, instance):
    """Validate solution and display results."""
    st.subheader("✅ Validation")

    is_feasible = solution.is_feasible()

    if is_feasible:
        st.success("✅ Solution is feasible!")
    else:
        st.error("❌ Solution has constraint violations")

    # Check specific constraints
    violations = []

    # Capacity check
    for i, route in enumerate(solution.routes):
        total_demand = sum(instance.demands[node] for node in route if node > 0)
        if total_demand > instance.vehicle_capacity:
            violations.append(f"Route {i+1}: Capacity exceeded ({total_demand} > {instance.vehicle_capacity})")

    # Time window check
    # ... (similar validation logic)

    if violations:
        st.warning("Violations detected:")
        for v in violations:
            st.write(f"- {v}")
```

## Pattern 7: State Management

### Multi-Step Workflow

```python
def initialize_session_state():
    """Initialize session state for multi-step workflow."""
    if 'step' not in st.session_state:
        st.session_state.step = 1

    if 'instance' not in st.session_state:
        st.session_state.instance = None

    if 'config' not in st.session_state:
        st.session_state.config = None

    if 'solution' not in st.session_state:
        st.session_state.solution = None

def render_workflow():
    """Render multi-step workflow with state management."""
    initialize_session_state()

    # Step 1: Define problem
    st.header("Step 1: Define Problem")
    if st.session_state.instance is None:
        instance = render_instance_loader()
        if instance is not None:
            st.session_state.instance = instance
            st.session_state.step = 2
            st.experimental_rerun()
    else:
        st.success(f"✅ Instance loaded ({st.session_state.instance.n} orders)")
        if st.button("Change Instance"):
            st.session_state.instance = None
            st.session_state.step = 1
            st.experimental_rerun()

    # Step 2: Configure algorithm (only if instance exists)
    if st.session_state.step >= 2:
        st.header("Step 2: Configure Algorithm")
        config = get_alns_config_from_ui()

        if st.button("Run Solver"):
            st.session_state.config = config
            # Run solver...
            st.session_state.solution = run_alns(...)
            st.session_state.step = 3

    # Step 3: View results (only if solution exists)
    if st.session_state.step >= 3:
        st.header("Step 3: Results")
        visualize_solution(st.session_state.solution, st.session_state.instance)
```

## Pattern 8: Contract Testing

### Reproducibility Test

```python
# In contracts/test_reproducibility.py
import pytest
from playground.utils.solver_runner import run_alns_from_config

def test_same_seed_same_result():
    """Test that same seed produces same result."""
    config = {
        'max_iterations': 100,
        'start_temp': 10.0,
        'seed': 42
    }
    instance = load_test_instance()

    # Run twice
    solution1 = run_alns_from_config(instance, config)
    solution2 = run_alns_from_config(instance, config)

    # Should be identical
    assert solution1.objective_value == solution2.objective_value
    assert solution1.routes == solution2.routes
```

---

**Usage:** Follow these patterns when integrating new features into the playground to ensure consistent error handling, state management, and user experience.
