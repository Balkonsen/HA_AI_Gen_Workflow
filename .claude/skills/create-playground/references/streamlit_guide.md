# Streamlit Guide for VRP-Toolkit Playground

Quick reference for building playground features with Streamlit.

## Installation

```bash
uv pip install streamlit
```

## Launch Playground

```bash
# From project root
cd playground
streamlit run app.py

# With custom port
streamlit run app.py --server.port 8502
```

## Core Concepts

### 1. Reactive Programming Model

Streamlit reruns the entire script from top to bottom every time:
- User interacts with a widget
- File changes (in dev mode)
- Data updates

**Implication:** Use `@st.cache_data` for expensive computations.

### 2. Session State

Persist data across reruns:

```python
import streamlit as st

# Initialize
if 'counter' not in st.session_state:
    st.session_state.counter = 0

# Read
st.write(st.session_state.counter)

# Write
st.session_state.counter += 1
```

### 3. Widget Return Values

All widgets return their current value:

```python
name = st.text_input("Name", value="Alice")  # Returns current input
clicked = st.button("Submit")  # Returns True when clicked
```

## Essential Widgets

### Input Widgets

```python
# Text input
name = st.text_input("Enter name", value="default")

# Number input
count = st.number_input("Count", min_value=0, max_value=100, value=10, step=1)

# Slider
temperature = st.slider("Temperature", 0.0, 100.0, 50.0, step=0.1)

# Select box (dropdown)
algorithm = st.selectbox("Algorithm", ["ALNS", "GA", "TabuSearch"])

# Multi-select
operators = st.multiselect("Operators", ["2-opt", "relocate", "exchange"])

# Radio buttons
problem_type = st.radio("Problem", ["VRP", "VRPTW", "PDPTW"])

# Checkbox
show_advanced = st.checkbox("Show advanced options", value=False)

# File uploader
uploaded_file = st.file_uploader("Upload instance", type=["csv", "json"])

# Color picker
route_color = st.color_picker("Route color", "#FF0000")
```

### Display Widgets

```python
# Text display
st.write("Hello world")  # Markdown + magic rendering
st.text("Plain text")
st.markdown("**Bold** and *italic*")
st.code("print('hello')", language="python")

# Data display
st.dataframe(df)  # Interactive table
st.table(df)      # Static table
st.json(data)     # JSON viewer
st.metric("Cost", 1234, delta=-56)  # KPI with change indicator

# Charts (built-in)
st.line_chart(data)
st.bar_chart(data)
st.area_chart(data)

# Charts (Matplotlib/Plotly)
st.pyplot(fig)          # Matplotlib figure
st.plotly_chart(fig)    # Plotly figure

# Media
st.image("path/to/image.png")
st.audio("path/to/audio.mp3")
```

### Layout Widgets

```python
# Columns
col1, col2, col3 = st.columns(3)
with col1:
    st.write("Column 1")
with col2:
    st.write("Column 2")

# Tabs
tab1, tab2 = st.tabs(["Problem", "Solution"])
with tab1:
    st.write("Problem definition")
with tab2:
    st.write("Solution display")

# Expander (collapsible section)
with st.expander("Advanced options"):
    st.slider("Parameter X", 0, 100, 50)

# Sidebar
st.sidebar.title("Configuration")
st.sidebar.slider("Temperature", 0.0, 100.0, 10.0)

# Container
with st.container():
    st.write("This is inside a container")
```

### Control Flow

```python
# Button
if st.button("Run Algorithm"):
    st.write("Running...")
    result = run_algorithm()
    st.success("Done!")

# Form (batch inputs, single submit)
with st.form("config_form"):
    param1 = st.slider("Param 1", 0, 100)
    param2 = st.number_input("Param 2", 0, 1000)
    submitted = st.form_submit_button("Submit")
    if submitted:
        st.write(f"Params: {param1}, {param2}")
```

## Best Practices for VRP Playground

### 1. Cache Expensive Operations

```python
@st.cache_data
def load_instance(file_path):
    """Load instance (cached)."""
    return PDPTWInstance.from_file(file_path)

@st.cache_data
def generate_instance(num_orders, seed):
    """Generate instance (cached by params)."""
    return generate_pdptw_instance(num_orders, seed)
```

### 2. Manage State for Multi-Step Workflows

```python
# Initialize state
if 'instance' not in st.session_state:
    st.session_state.instance = None
if 'solution' not in st.session_state:
    st.session_state.solution = None

# Step 1: Define problem
if st.button("Generate Instance"):
    st.session_state.instance = generate_instance()

# Step 2: Solve (only if instance exists)
if st.session_state.instance is not None:
    if st.button("Run Solver"):
        st.session_state.solution = solver.solve(st.session_state.instance)

# Step 3: Visualize (only if solution exists)
if st.session_state.solution is not None:
    visualize_solution(st.session_state.solution)
```

### 3. Progressive Disclosure

Hide complexity until needed:

```python
# Simple interface first
st.subheader("Basic Configuration")
num_vehicles = st.slider("Number of vehicles", 1, 10, 3)

# Advanced options hidden by default
with st.expander("⚙️ Advanced Parameters"):
    battery_capacity = st.number_input("Battery capacity", 1.0, 100.0, 10.0)
    charging_time = st.number_input("Charging time", 0.0, 60.0, 15.0)
```

### 4. User Feedback

```python
# Success/error messages
if successful:
    st.success("✅ Solution found!")
else:
    st.error("❌ No feasible solution")

# Info/warning
st.info("ℹ️ Using default parameters")
st.warning("⚠️ Large instance may take several minutes")

# Progress bar
progress_bar = st.progress(0)
for i in range(100):
    progress_bar.progress(i + 1)
    time.sleep(0.01)
st.success("Done!")
```

### 5. Download Results

```python
import json

# Download button
result_json = json.dumps(solution.to_dict(), indent=2)
st.download_button(
    label="📥 Download Solution",
    data=result_json,
    file_name="solution.json",
    mime="application/json"
)
```

## Multi-Page Apps

Structure for larger playgrounds:

```
playground/
├── app.py                         # Home page
├── pages/
│   ├── 1_Problem_Definition.py   # Page 1
│   ├── 2_Algorithm_Config.py     # Page 2
│   └── 3_Experiments.py          # Page 3
```

Each page is a separate script. Streamlit automatically creates navigation.

**Sharing state across pages:**

```python
# In pages/1_Problem_Definition.py
st.session_state.instance = generate_instance()

# In pages/2_Algorithm_Config.py
instance = st.session_state.get('instance', None)
if instance is None:
    st.error("Please define a problem first")
    st.stop()
```

## Common Pitfalls

### Pitfall 1: Infinite Reruns

**Problem:** Script reruns infinitely
**Cause:** Modifying session state unconditionally

```python
# BAD: Sets counter every rerun → triggers rerun → infinite loop
st.session_state.counter = 0

# GOOD: Only initialize once
if 'counter' not in st.session_state:
    st.session_state.counter = 0
```

### Pitfall 2: Widget State Loss

**Problem:** Widget value resets unexpectedly
**Cause:** Widget key not set, or conditional rendering

```python
# BAD: Widget recreated with new identity every rerun
num = st.slider("Number", 0, 100)

# GOOD: Widget has stable key
num = st.slider("Number", 0, 100, key="number_slider")
```

### Pitfall 3: Heavy Computation on Every Rerun

**Problem:** Slow UI because expensive function runs every rerun
**Solution:** Use `@st.cache_data`

```python
# BAD: Loads file on every rerun (even when just clicking a button)
instance = load_large_file("data.csv")

# GOOD: Cached by file path
@st.cache_data
def load_instance(file_path):
    return load_large_file(file_path)

instance = load_instance("data.csv")  # Only loads once
```

## Deployment

### Local Development

```bash
streamlit run app.py
```

### Streamlit Cloud (Free)

1. Push code to GitHub
2. Go to share.streamlit.io
3. Connect repository
4. Deploy

### Custom Server

```bash
# Install
pip install streamlit

# Run with custom config
streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true
```

## Resources

- Official docs: https://docs.streamlit.io
- Component gallery: https://streamlit.io/components
- Cheat sheet: https://docs.streamlit.io/library/cheatsheet
