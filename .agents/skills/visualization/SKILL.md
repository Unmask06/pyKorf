---
name: visualization
description: Interactive PyVis network visualization, HTML/JSON export, and node styling
---

# KORF Model Visualization

## Overview
The `pykorf.visualization` package provides interactive network visualizations of KDF models using PyVis. It respects the original XY layout and styles nodes by element type.

## Visualizer API

```python
from pykorf import Model
from pykorf.visualization import Visualizer

model = Model("model.kdf")
viz = Visualizer(model)

# Export options
viz.to_json("network_data.json")  # Raw JSON for web consumption
viz.to_html("network.html")      # Interactive PyVis HTML (requires pyvis)
```

## Features
- **XY Fidelity:** Nodes are placed at their exact scaled KDF coordinates.
- **Directional Edges:** Flow direction is inferred from connection roles (NOZI/NOZO/CON).
- **Element Styling:** Distinct colors and shapes for each element type (Feed, Prod, Pump, etc.).
- **Legend:** Interactive HTML legend included in exported visualizations.

## Implementation Details
- Uses `NetworkData`, `NodeData`, and `EdgeData` models for structured visualization data.
- Scales model coordinates to a standard 1200x700 PyVis canvas.
- Disables physics engine by default for static layout preservation.

## Key Files
- `pykorf/visualization/visualizer.py`: Core `Visualizer` class.
- `pykorf/visualization/models.py`: Pydantic models for visualization data.
- `tests/test_visualization.py`: Visualization tests.
