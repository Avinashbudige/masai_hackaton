# Cartographic Displacement System

A Python system for resolving spatial conflicts in street network data through cartographic displacement while preserving topology.

## Overview

When map features are too close together at a given scale, they must be displaced (moved slightly) while maintaining topological relationships, connectivity, and visual clarity. This system:

- Parses WKT LINESTRING geometries
- Detects spatial conflicts between segments
- Applies displacement transformations using energy minimization
- Preserves network topology and connectivity
- Outputs adjusted geometry in WKT format

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

## Requirements

- Python 3.8+
- shapely >= 2.0
- numpy >= 1.20.0
- matplotlib >= 3.3.0
- scipy >= 1.7.0
- hypothesis >= 6.0.0 (for testing)
- pytest >= 7.0.0 (for testing)

## Project Structure

```
.
├── src/
│   └── cartographic_displacement/
│       ├── __init__.py
│       └── models.py          # Core data models
├── tests/
│   ├── unit/                  # Unit tests
│   ├── property/              # Property-based tests
│   └── integration/           # Integration tests
├── requirements.txt
├── setup.py
└── pytest.ini
```

## Core Data Models

### Point
A 2D point in Cartesian coordinates with distance calculation.

### Vector2D
A 2D vector representing direction and magnitude with normalization and scaling.

### LineSegment
A line segment with ordered coordinates and Shapely geometry representation.

### IntersectionPoint
A point where multiple line segments meet, tracking connected segments.

### Conflict
A spatial conflict between two segments that are too close together.

### DisplacementConfig
Configuration parameters for the displacement system including:
- Minimum distance threshold
- Maximum displacement magnitude
- Displacement strategy (perpendicular, angular, hybrid)
- Energy function weights
- Optimization parameters

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run with coverage report
pytest --cov=src/cartographic_displacement --cov-report=html
```

## Development Status

This is the initial implementation with core data models. Additional components will be added:
- WKT Parser
- Network Graph
- Conflict Detector
- Displacement Engine
- Topology Validator
- Pretty Printer
- Visualizer

## License

TBD
