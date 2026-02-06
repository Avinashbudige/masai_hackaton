"""
Cartographic Displacement System

A system for resolving spatial conflicts in street network data through
cartographic displacement while preserving topology.
"""

from .models import (
    Point,
    Vector2D,
    LineSegment,
    IntersectionPoint,
    Conflict,
    DisplacementConfig,
)
from .parser import WKTParser, WKTParseError

__version__ = "0.1.0"

__all__ = [
    "Point",
    "Vector2D",
    "LineSegment",
    "IntersectionPoint",
    "Conflict",
    "DisplacementConfig",
    "WKTParser",
    "WKTParseError",
]
