# UI Components for VRP-Toolkit Playground

Reusable UI patterns for common playground interactions.

## Instance Viewer

Display problem instance details in a clear, structured way.

```python
def render_instance_viewer(instance):
    """Display instance summary and details."""
    st.subheader("Problem Instance")

    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Orders", instance.n)
    with col2:
        st.metric("Vehicles", instance.num_vehicles)
    with col3:
        st.metric("Nodes", len(instance.indices))
    with col4:
        st.metric("Depot", instance.depot_index)

    # Detailed info in expander
    with st.expander("📋 View Full Instance Data"):
        st.dataframe(instance.order_table)

    # Time windows visualization
    if hasattr(instance, 'time_windows'):
        st.subheader("Time Windows")
        # Simple bar chart of time window spans
        tw_data = {
            'Node': list(instance.time_windows.keys()),
            'Start': [tw[0] for tw in instance.time_windows.values()],
            'End': [tw[1] for tw in instance.time_windows.values()]
        }
        st.bar_chart(tw_data)
```

## Algorithm Configuration Panel

Organize algorithm parameters with progressive disclosure.

```python
def render_alns_config():
    """Render ALNS configuration UI with basic/advanced split."""
    from vrp_toolkit.algorithms.alns import ALNSConfig

    st.subheader("⚙️ ALNS Configuration")

    # Basic parameters (always visible)
    st.write("**Basic Parameters**")
    col1, col2 = st.columns(2)
    with col1:
        max_iterations = st.slider(
            "Max Iterations",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
            help="Maximum number of iterations before stopping"
        )
        num_vehicles = st.number_input(
            "Number of Vehicles",
            min_value=1,
            max_value=20,
            value=3,
            help="Fleet size"
        )
    with col2:
        start_temp = st.number_input(
            "Start Temperature",
            min_value=0.1,
            max_value=100.0,
            value=10.0,
            step=0.1,
            help="Initial temperature for simulated annealing"
        )
        seed = st.number_input(
            "Random Seed",
            min_value=0,
            max_value=99999,
            value=42,
            help="Seed for reproducibility"
        )

    # Advanced parameters (collapsed by default)
    with st.expander("🔧 Advanced Parameters"):
        col1, col2 = st.columns(2)
        with col1:
            cooling_rate = st.slider(
                "Cooling Rate",
                min_value=0.90,
                max_value=0.99,
                value=0.95,
                step=0.01
            )
            segment_length = st.number_input(
                "Segment Length",
                min_value=10,
                max_value=500,
                value=100
            )
        with col2:
            num_removal = st.slider(
                "Num Removal",
                min_value=1,
                max_value=20,
                value=5
            )
            p_param = st.slider(
                "Shaw Relatedness (p)",
                min_value=1.0,
                max_value=10.0,
                value=4.0,
                step=0.5
            )

    # Create config object
    config = ALNSConfig(
        max_iterations=max_iterations,
        start_temp=start_temp,
        cooling_rate=cooling_rate,
        segment_length=segment_length,
        num_removal=num_removal,
        p=p_param
    )

    return config, num_vehicles, seed
```

## Solution Visualizer

Display solution results with multiple views.

```python
def render_solution_viewer(solution, instance):
    """Display solution with routes, metrics, and validation."""
    st.subheader("📊 Solution Results")

    # Top-level metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Cost",
            f"{solution.objective_value:.2f}",
            delta=None
        )
    with col2:
        feasible = solution.is_feasible()
        st.metric(
            "Feasibility",
            "✅ Feasible" if feasible else "❌ Infeasible"
        )
    with col3:
        st.metric(
            "Routes",
            len(solution.routes)
        )

    # Route visualization
    st.subheader("🗺️ Routes")
    fig = visualize_routes(solution, instance)
    st.pyplot(fig)

    # Route details table
    with st.expander("📋 View Route Details"):
        route_data = []
        for i, route in enumerate(solution.routes):
            route_data.append({
                'Route': i + 1,
                'Nodes': len(route),
                'Cost': calculate_route_cost(route, instance),
                'Sequence': ' → '.join(map(str, route))
            })
        st.dataframe(route_data)

    # Constraint violations (if infeasible)
    if not feasible:
        st.warning("⚠️ Constraint Violations Detected")
        violations = check_violations(solution, instance)
        st.json(violations)
```

## Convergence Plot

Show algorithm search progress over iterations.

```python
def render_convergence_plot(cost_history):
    """Plot cost convergence over iterations."""
    import matplotlib.pyplot as plt

    st.subheader("📈 Convergence")

    if len(cost_history) == 0:
        st.info("No convergence data yet. Run the algorithm first.")
        return

    # Plot using Matplotlib
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(cost_history, linewidth=2, color='#1f77b4')
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Total Cost')
    ax.set_title('Cost Convergence')
    ax.grid(True, alpha=0.3)

    # Annotate best solution
    best_idx = cost_history.index(min(cost_history))
    best_cost = cost_history[best_idx]
    ax.plot(best_idx, best_cost, 'r*', markersize=15, label='Best')
    ax.legend()

    st.pyplot(fig)

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Initial Cost", f"{cost_history[0]:.2f}")
    with col2:
        st.metric("Final Cost", f"{cost_history[-1]:.2f}")
    with col3:
        improvement = ((cost_history[0] - cost_history[-1]) / cost_history[0] * 100)
        st.metric("Improvement", f"{improvement:.1f}%")
```

## Experiment Comparison

Compare multiple algorithm runs side-by-side.

```python
def render_experiment_comparison(experiments):
    """Compare multiple experiments in table and charts."""
    st.subheader("🔬 Experiment Comparison")

    if len(experiments) == 0:
        st.info("No experiments saved yet.")
        return

    # Comparison table
    comparison_data = []
    for exp in experiments:
        comparison_data.append({
            'Name': exp['name'],
            'Cost': exp['cost'],
            'Feasible': '✅' if exp['feasible'] else '❌',
            'Runtime (s)': exp['runtime'],
            'Iterations': exp['iterations'],
            'Seed': exp['seed']
        })

    st.dataframe(comparison_data)

    # Side-by-side convergence plots
    st.subheader("Convergence Comparison")
    fig, ax = plt.subplots(figsize=(10, 5))

    for exp in experiments:
        ax.plot(exp['cost_history'], label=exp['name'], linewidth=2)

    ax.set_xlabel('Iteration')
    ax.set_ylabel('Cost')
    ax.set_title('Convergence Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)

    st.pyplot(fig)

    # Best configuration
    best_exp = min(experiments, key=lambda x: x['cost'])
    st.success(f"🏆 Best: {best_exp['name']} (Cost: {best_exp['cost']:.2f})")

    with st.expander("📋 View Best Configuration"):
        st.json(best_exp['config'])
```

## Run History Manager

Save and load experiment runs.

```python
def render_run_history():
    """Display and manage saved runs."""
    st.subheader("📁 Saved Experiments")

    # Load saved runs
    runs = load_saved_runs()  # From utils/export_utils.py

    if len(runs) == 0:
        st.info("No saved runs yet.")
        return

    # Run selector
    selected_run = st.selectbox(
        "Select Run",
        options=runs,
        format_func=lambda x: f"{x['timestamp']} - Cost: {x['metrics']['cost']:.2f}"
    )

    # Display selected run
    if selected_run:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.write("**Configuration:**")
            st.json(selected_run['config'])

        with col2:
            st.write("**Metrics:**")
            for key, value in selected_run['metrics'].items():
                st.metric(key, value)

        # Load and visualize solution
        if st.button("📊 Load and Visualize"):
            solution = load_solution_from_run(selected_run)
            instance = load_instance_from_run(selected_run)
            render_solution_viewer(solution, instance)

        # Download button
        run_json = json.dumps(selected_run, indent=2)
        st.download_button(
            "📥 Download Run Data",
            data=run_json,
            file_name=f"run_{selected_run['timestamp']}.json",
            mime="application/json"
        )
```

## Operator Impact Visualizer

Show before/after comparison for a single operator move.

```python
def render_operator_impact(before_solution, after_solution, operator_name):
    """Visualize the impact of a single operator move."""
    st.subheader(f"🔄 {operator_name} Impact")

    # Side-by-side comparison
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Before**")
        st.metric("Cost", f"{before_solution.objective_value:.2f}")
        fig_before = visualize_routes(before_solution)
        st.pyplot(fig_before)

    with col2:
        st.write("**After**")
        cost_after = after_solution.objective_value
        cost_change = cost_after - before_solution.objective_value
        st.metric(
            "Cost",
            f"{cost_after:.2f}",
            delta=f"{cost_change:+.2f}"
        )
        fig_after = visualize_routes(after_solution)
        st.pyplot(fig_after)

    # Detailed change summary
    with st.expander("📋 View Detailed Changes"):
        st.write("**Routes Modified:**")
        # Highlight routes that changed
        for i, (before, after) in enumerate(zip(before_solution.routes, after_solution.routes)):
            if before != after:
                st.write(f"Route {i+1}:")
                st.write(f"  Before: {' → '.join(map(str, before))}")
                st.write(f"  After:  {' → '.join(map(str, after))}")
```

## Validation Feedback

Display constraint validation results clearly.

```python
def render_validation_feedback(solution, instance):
    """Show constraint validation with clear feedback."""
    st.subheader("✅ Solution Validation")

    # Run validation
    validation_results = validate_solution(solution, instance)

    # Overall status
    if validation_results['is_feasible']:
        st.success("✅ All constraints satisfied!")
    else:
        st.error("❌ Constraint violations detected")

    # Detailed results
    for constraint, result in validation_results['constraints'].items():
        with st.expander(f"{'✅' if result['satisfied'] else '❌'} {constraint}"):
            st.write(f"**Status:** {'Satisfied' if result['satisfied'] else 'Violated'}")
            if 'details' in result:
                st.write(f"**Details:** {result['details']}")
            if 'violations' in result:
                st.dataframe(result['violations'])
```

## Parameter Impact Hint

Provide contextual hints about parameter effects.

```python
def render_parameter_hints(param_name, param_value):
    """Show hints about parameter impact."""
    hints = {
        'start_temp': {
            'low': 'Low temperature → More greedy, faster convergence, may miss global optimum',
            'medium': 'Medium temperature → Balanced exploration/exploitation',
            'high': 'High temperature → More exploration, slower convergence, better global search'
        },
        'cooling_rate': {
            'low': 'Low cooling rate → Fast cooling, quick convergence',
            'medium': 'Medium cooling rate → Standard annealing schedule',
            'high': 'High cooling rate → Slow cooling, more iterations'
        }
    }

    if param_name in hints:
        if param_value < 5:
            level = 'low'
        elif param_value < 50:
            level = 'medium'
        else:
            level = 'high'

        st.info(f"💡 **Hint:** {hints[param_name][level]}")
```

## Loading State

Show progress during long-running operations.

```python
def run_with_progress(solver, instance, config):
    """Run solver with progress updates."""
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Run in background with callbacks
    for iteration, cost in solver.solve_with_callback(instance, config):
        progress = iteration / config.max_iterations
        progress_bar.progress(progress)
        status_text.text(f"Iteration {iteration}/{config.max_iterations} - Cost: {cost:.2f}")

    progress_bar.progress(1.0)
    status_text.text("✅ Complete!")

    return solver.best_solution
```

## Quick Actions Toolbar

Provide common actions in a horizontal toolbar.

```python
def render_quick_actions(solution, instance):
    """Render quick action buttons."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("💾 Save"):
            save_experiment(solution, instance)

    with col2:
        if st.button("📥 Export CSV"):
            export_to_csv(solution)

    with col3:
        if st.button("📊 Full Report"):
            generate_report(solution, instance)

    with col4:
        if st.button("🔄 Reset"):
            st.session_state.clear()
            st.experimental_rerun()
```

---

**Usage:** Import and use these components in your playground pages to maintain consistent UI/UX across features.
