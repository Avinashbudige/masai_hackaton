"""
Core data models for the cartographic displacement system.

This module defines the fundamental geometric and configuration types used
throughout the system.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from shapely.geometry import LineString
import math


@dataclass
class Point:
    """
    A 2D point in Cartesian coordinates.
    
    Attributes:
        x: X-coordinate
        y: Y-coordinate
    """
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        """
        Calculate Euclidean distance to another point.
        
        Args:
            other: The other point
            
        Returns:
            The Euclidean distance between the two points
        """
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def __hash__(self):
        """Make Point hashable for use in sets and dicts."""
        return hash((round(self.x, 6), round(self.y, 6)))
    
    def __eq__(self, other):
        """Check equality with tolerance for floating point comparison."""
        if not isinstance(other, Point):
            return False
        tolerance = 1e-6
        return (abs(self.x - other.x) < tolerance and 
                abs(self.y - other.y) < tolerance)


@dataclass
class Vector2D:
    """
    A 2D vector representing direction and magnitude.
    
    Attributes:
        dx: X-component of the vector
        dy: Y-component of the vector
    """
    dx: float
    dy: float
    
    def magnitude(self) -> float:
        """
        Calculate the length (magnitude) of the vector.
        
        Returns:
            The Euclidean length of the vector
        """
        return math.sqrt(self.dx ** 2 + self.dy ** 2)
    
    def normalize(self) -> 'Vector2D':
        """
        Return a unit vector in the same direction.
        
        Returns:
            A normalized vector with magnitude 1.0
            
        Raises:
            ValueError: If the vector has zero magnitude
        """
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize zero-length vector")
        return Vector2D(self.dx / mag, self.dy / mag)
    
    def scale(self, factor: float) -> 'Vector2D':
        """
        Scale the vector by a factor.
        
        Args:
            factor: The scaling factor
            
        Returns:
            A new vector scaled by the factor
        """
        return Vector2D(self.dx * factor, self.dy * factor)
    
    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        """Add two vectors."""
        return Vector2D(self.dx + other.dx, self.dy + other.dy)
    
    def __sub__(self, other: 'Vector2D') -> 'Vector2D':
        """Subtract two vectors."""
        return Vector2D(self.dx - other.dx, self.dy - other.dy)


@dataclass
class LineSegment:
    """
    A line segment represented as an ordered sequence of points.
    
    Attributes:
        id: Unique identifier for the segment
        coordinates: Ordered list of points defining the segment
        shapely_geom: Shapely LineString representation for geometric operations
    """
    id: int
    coordinates: List[Point]
    shapely_geom: Optional[LineString] = None
    
    def __post_init__(self):
        """Initialize Shapely geometry from coordinates if not provided."""
        if self.shapely_geom is None:
            if len(self.coordinates) < 2:
                raise ValueError(f"LineSegment must have at least 2 points, got {len(self.coordinates)}")
            coords = [(p.x, p.y) for p in self.coordinates]
            self.shapely_geom = LineString(coords)
    
    def length(self) -> float:
        """
        Calculate the total length of the segment.
        
        Returns:
            The total length of the line segment
        """
        return self.shapely_geom.length
    
    def get_perpendicular_vector(self, at_point: Point) -> Vector2D:
        """
        Get a perpendicular vector at a given point on the segment.
        
        This method finds the perpendicular direction (normal) to the segment
        at the specified point. The perpendicular is calculated based on the
        nearest segment between consecutive vertices.
        
        Args:
            at_point: The point at which to calculate the perpendicular
            
        Returns:
            A unit vector perpendicular to the segment at the given point
            
        Raises:
            ValueError: If the point is not on or near the segment
        """
        # Find the nearest segment between consecutive vertices
        min_dist = float('inf')
        best_idx = 0
        
        for i in range(len(self.coordinates) - 1):
            p1 = self.coordinates[i]
            p2 = self.coordinates[i + 1]
            
            # Calculate distance from at_point to this segment
            # Using point-to-line distance formula
            line_vec = Vector2D(p2.x - p1.x, p2.y - p1.y)
            point_vec = Vector2D(at_point.x - p1.x, at_point.y - p1.y)
            
            line_len = line_vec.magnitude()
            if line_len == 0:
                continue
                
            # Project point onto line
            t = max(0, min(1, (point_vec.dx * line_vec.dx + point_vec.dy * line_vec.dy) / (line_len ** 2)))
            closest = Point(p1.x + t * line_vec.dx, p1.y + t * line_vec.dy)
            dist = at_point.distance_to(closest)
            
            if dist < min_dist:
                min_dist = dist
                best_idx = i
        
        # Get the direction vector of the best segment
        p1 = self.coordinates[best_idx]
        p2 = self.coordinates[best_idx + 1]
        direction = Vector2D(p2.x - p1.x, p2.y - p1.y)
        
        # Perpendicular is (-dy, dx) normalized
        perpendicular = Vector2D(-direction.dy, direction.dx)
        return perpendicular.normalize()
    
    def start_point(self) -> Point:
        """Get the first point of the segment."""
        return self.coordinates[0]
    
    def end_point(self) -> Point:
        """Get the last point of the segment."""
        return self.coordinates[-1]


@dataclass
class IntersectionPoint:
    """
    A point where multiple line segments meet.
    
    Attributes:
        location: The geometric location of the intersection
        connected_segment_ids: List of segment IDs that meet at this point
    """
    location: Point
    connected_segment_ids: List[int] = field(default_factory=list)
    
    def degree(self) -> int:
        """
        Get the degree of the intersection (number of connected segments).
        
        Returns:
            The number of segments connected at this intersection
        """
        return len(self.connected_segment_ids)


@dataclass
class Conflict:
    """
    A spatial conflict between two line segments.
    
    Represents a situation where two non-adjacent segments are closer
    than the minimum allowed distance.
    
    Attributes:
        segment1: First segment in conflict
        segment2: Second segment in conflict
        min_distance_point1: Closest point on segment1 to segment2
        min_distance_point2: Closest point on segment2 to segment1
        actual_distance: The measured distance between the segments
        required_displacement: How much displacement is needed to resolve the conflict
    """
    segment1: LineSegment
    segment2: LineSegment
    min_distance_point1: Point
    min_distance_point2: Point
    actual_distance: float
    required_displacement: float
    
    def __post_init__(self):
        """Validate conflict data."""
        if self.actual_distance < 0:
            raise ValueError(f"Actual distance cannot be negative: {self.actual_distance}")
        if self.required_displacement < 0:
            raise ValueError(f"Required displacement cannot be negative: {self.required_displacement}")


@dataclass
class DisplacementConfig:
    """
    Configuration parameters for the displacement system.
    
    Attributes:
        min_distance: Minimum allowed distance between segments (conflict threshold)
        max_displacement: Maximum displacement magnitude allowed for any segment
        strategy: Displacement strategy ("perpendicular", "angular", or "hybrid")
        energy_alpha: Weight for internal energy (shape preservation)
        energy_beta: Weight for external energy (conflict resolution)
        max_iterations: Maximum number of optimization iterations
        convergence_threshold: Energy change threshold for convergence
        coordinate_precision: Number of decimal places for output coordinates
    """
    min_distance: float = 10.0
    max_displacement: float = 50.0
    strategy: str = "perpendicular"
    energy_alpha: float = 0.3
    energy_beta: float = 0.7
    max_iterations: int = 100
    convergence_threshold: float = 0.01
    coordinate_precision: int = 6
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.min_distance <= 0:
            raise ValueError(f"min_distance must be positive, got {self.min_distance}")
        
        if self.max_displacement <= 0:
            raise ValueError(f"max_displacement must be positive, got {self.max_displacement}")
        
        if self.strategy not in ["perpendicular", "angular", "hybrid"]:
            raise ValueError(
                f"strategy must be 'perpendicular', 'angular', or 'hybrid', got '{self.strategy}'"
            )
        
        if not (0 <= self.energy_alpha <= 1):
            raise ValueError(f"energy_alpha must be between 0 and 1, got {self.energy_alpha}")
        
        if not (0 <= self.energy_beta <= 1):
            raise ValueError(f"energy_beta must be between 0 and 1, got {self.energy_beta}")
        
        if self.max_iterations <= 0:
            raise ValueError(f"max_iterations must be positive, got {self.max_iterations}")
        
        if self.convergence_threshold <= 0:
            raise ValueError(f"convergence_threshold must be positive, got {self.convergence_threshold}")
        
        if self.coordinate_precision < 0:
            raise ValueError(f"coordinate_precision cannot be negative, got {self.coordinate_precision}")
