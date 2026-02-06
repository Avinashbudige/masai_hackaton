"""
Unit tests for core data models.

Tests the Point, Vector2D, LineSegment, IntersectionPoint, Conflict,
and DisplacementConfig classes.
"""

import pytest
import math
from shapely.geometry import LineString

from src.cartographic_displacement.models import (
    Point,
    Vector2D,
    LineSegment,
    IntersectionPoint,
    Conflict,
    DisplacementConfig,
)


class TestPoint:
    """Tests for the Point class."""
    
    def test_point_creation(self):
        """Test basic point creation."""
        p = Point(3.0, 4.0)
        assert p.x == 3.0
        assert p.y == 4.0
    
    def test_distance_to(self):
        """Test distance calculation between points."""
        p1 = Point(0.0, 0.0)
        p2 = Point(3.0, 4.0)
        assert p1.distance_to(p2) == 5.0
    
    def test_distance_to_same_point(self):
        """Test distance to the same point is zero."""
        p = Point(1.0, 2.0)
        assert p.distance_to(p) == 0.0
    
    def test_point_equality(self):
        """Test point equality with tolerance."""
        p1 = Point(1.0, 2.0)
        p2 = Point(1.0, 2.0)
        p3 = Point(1.0000001, 2.0000001)  # Within tolerance
        p4 = Point(1.1, 2.0)  # Outside tolerance
        
        assert p1 == p2
        assert p1 == p3
        assert p1 != p4
    
    def test_point_hashable(self):
        """Test that points can be used in sets and dicts."""
        p1 = Point(1.0, 2.0)
        p2 = Point(1.0, 2.0)
        p3 = Point(3.0, 4.0)
        
        point_set = {p1, p2, p3}
        assert len(point_set) == 2  # p1 and p2 should be the same


class TestVector2D:
    """Tests for the Vector2D class."""
    
    def test_vector_creation(self):
        """Test basic vector creation."""
        v = Vector2D(3.0, 4.0)
        assert v.dx == 3.0
        assert v.dy == 4.0
    
    def test_magnitude(self):
        """Test vector magnitude calculation."""
        v = Vector2D(3.0, 4.0)
        assert v.magnitude() == 5.0
    
    def test_magnitude_zero_vector(self):
        """Test magnitude of zero vector."""
        v = Vector2D(0.0, 0.0)
        assert v.magnitude() == 0.0
    
    def test_normalize(self):
        """Test vector normalization."""
        v = Vector2D(3.0, 4.0)
        normalized = v.normalize()
        assert abs(normalized.magnitude() - 1.0) < 1e-10
        assert abs(normalized.dx - 0.6) < 1e-10
        assert abs(normalized.dy - 0.8) < 1e-10
    
    def test_normalize_zero_vector_raises_error(self):
        """Test that normalizing zero vector raises ValueError."""
        v = Vector2D(0.0, 0.0)
        with pytest.raises(ValueError, match="Cannot normalize zero-length vector"):
            v.normalize()
    
    def test_scale(self):
        """Test vector scaling."""
        v = Vector2D(2.0, 3.0)
        scaled = v.scale(2.5)
        assert scaled.dx == 5.0
        assert scaled.dy == 7.5
    
    def test_vector_addition(self):
        """Test vector addition."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, 4.0)
        result = v1 + v2
        assert result.dx == 4.0
        assert result.dy == 6.0
    
    def test_vector_subtraction(self):
        """Test vector subtraction."""
        v1 = Vector2D(5.0, 7.0)
        v2 = Vector2D(2.0, 3.0)
        result = v1 - v2
        assert result.dx == 3.0
        assert result.dy == 4.0


class TestLineSegment:
    """Tests for the LineSegment class."""
    
    def test_line_segment_creation(self):
        """Test basic line segment creation."""
        points = [Point(0.0, 0.0), Point(1.0, 1.0)]
        segment = LineSegment(id=1, coordinates=points)
        assert segment.id == 1
        assert len(segment.coordinates) == 2
        assert segment.shapely_geom is not None
    
    def test_line_segment_with_shapely_geom(self):
        """Test line segment creation with provided Shapely geometry."""
        points = [Point(0.0, 0.0), Point(1.0, 1.0)]
        shapely_line = LineString([(0.0, 0.0), (1.0, 1.0)])
        segment = LineSegment(id=1, coordinates=points, shapely_geom=shapely_line)
        assert segment.shapely_geom == shapely_line
    
    def test_line_segment_too_few_points_raises_error(self):
        """Test that creating segment with < 2 points raises ValueError."""
        points = [Point(0.0, 0.0)]
        with pytest.raises(ValueError, match="must have at least 2 points"):
            LineSegment(id=1, coordinates=points)
    
    def test_line_segment_length(self):
        """Test line segment length calculation."""
        points = [Point(0.0, 0.0), Point(3.0, 4.0)]
        segment = LineSegment(id=1, coordinates=points)
        assert segment.length() == 5.0
    
    def test_line_segment_length_multi_point(self):
        """Test length calculation for multi-point segment."""
        points = [Point(0.0, 0.0), Point(3.0, 0.0), Point(3.0, 4.0)]
        segment = LineSegment(id=1, coordinates=points)
        assert segment.length() == 7.0  # 3 + 4
    
    def test_start_point(self):
        """Test getting the start point of a segment."""
        points = [Point(1.0, 2.0), Point(3.0, 4.0)]
        segment = LineSegment(id=1, coordinates=points)
        start = segment.start_point()
        assert start == Point(1.0, 2.0)
    
    def test_end_point(self):
        """Test getting the end point of a segment."""
        points = [Point(1.0, 2.0), Point(3.0, 4.0)]
        segment = LineSegment(id=1, coordinates=points)
        end = segment.end_point()
        assert end == Point(3.0, 4.0)
    
    def test_get_perpendicular_vector_horizontal_line(self):
        """Test perpendicular vector for horizontal line."""
        points = [Point(0.0, 0.0), Point(10.0, 0.0)]
        segment = LineSegment(id=1, coordinates=points)
        perp = segment.get_perpendicular_vector(Point(5.0, 0.0))
        
        # Perpendicular to horizontal should be vertical
        assert abs(perp.dx) < 1e-10
        assert abs(abs(perp.dy) - 1.0) < 1e-10
    
    def test_get_perpendicular_vector_vertical_line(self):
        """Test perpendicular vector for vertical line."""
        points = [Point(0.0, 0.0), Point(0.0, 10.0)]
        segment = LineSegment(id=1, coordinates=points)
        perp = segment.get_perpendicular_vector(Point(0.0, 5.0))
        
        # Perpendicular to vertical should be horizontal
        assert abs(abs(perp.dx) - 1.0) < 1e-10
        assert abs(perp.dy) < 1e-10
    
    def test_get_perpendicular_vector_diagonal_line(self):
        """Test perpendicular vector for diagonal line."""
        points = [Point(0.0, 0.0), Point(3.0, 4.0)]
        segment = LineSegment(id=1, coordinates=points)
        perp = segment.get_perpendicular_vector(Point(1.5, 2.0))
        
        # Perpendicular should be unit vector
        assert abs(perp.magnitude() - 1.0) < 1e-10
        
        # Perpendicular to (3,4) direction should be (-4,3) normalized
        expected_perp = Vector2D(-4.0, 3.0).normalize()
        assert abs(perp.dx - expected_perp.dx) < 1e-10
        assert abs(perp.dy - expected_perp.dy) < 1e-10


class TestIntersectionPoint:
    """Tests for the IntersectionPoint class."""
    
    def test_intersection_point_creation(self):
        """Test basic intersection point creation."""
        location = Point(5.0, 5.0)
        intersection = IntersectionPoint(location=location, connected_segment_ids=[1, 2, 3])
        assert intersection.location == location
        assert len(intersection.connected_segment_ids) == 3
    
    def test_intersection_point_default_segments(self):
        """Test intersection point with default empty segment list."""
        location = Point(5.0, 5.0)
        intersection = IntersectionPoint(location=location)
        assert len(intersection.connected_segment_ids) == 0
    
    def test_degree(self):
        """Test degree calculation (number of connected segments)."""
        location = Point(5.0, 5.0)
        intersection = IntersectionPoint(location=location, connected_segment_ids=[1, 2, 3, 4])
        assert intersection.degree() == 4
    
    def test_degree_empty(self):
        """Test degree for intersection with no connected segments."""
        location = Point(5.0, 5.0)
        intersection = IntersectionPoint(location=location)
        assert intersection.degree() == 0


class TestConflict:
    """Tests for the Conflict class."""
    
    def test_conflict_creation(self):
        """Test basic conflict creation."""
        seg1 = LineSegment(id=1, coordinates=[Point(0.0, 0.0), Point(10.0, 0.0)])
        seg2 = LineSegment(id=2, coordinates=[Point(0.0, 5.0), Point(10.0, 5.0)])
        
        conflict = Conflict(
            segment1=seg1,
            segment2=seg2,
            min_distance_point1=Point(5.0, 0.0),
            min_distance_point2=Point(5.0, 5.0),
            actual_distance=5.0,
            required_displacement=5.0
        )
        
        assert conflict.segment1 == seg1
        assert conflict.segment2 == seg2
        assert conflict.actual_distance == 5.0
        assert conflict.required_displacement == 5.0
    
    def test_conflict_negative_distance_raises_error(self):
        """Test that negative actual distance raises ValueError."""
        seg1 = LineSegment(id=1, coordinates=[Point(0.0, 0.0), Point(10.0, 0.0)])
        seg2 = LineSegment(id=2, coordinates=[Point(0.0, 5.0), Point(10.0, 5.0)])
        
        with pytest.raises(ValueError, match="Actual distance cannot be negative"):
            Conflict(
                segment1=seg1,
                segment2=seg2,
                min_distance_point1=Point(5.0, 0.0),
                min_distance_point2=Point(5.0, 5.0),
                actual_distance=-1.0,
                required_displacement=5.0
            )
    
    def test_conflict_negative_required_displacement_raises_error(self):
        """Test that negative required displacement raises ValueError."""
        seg1 = LineSegment(id=1, coordinates=[Point(0.0, 0.0), Point(10.0, 0.0)])
        seg2 = LineSegment(id=2, coordinates=[Point(0.0, 5.0), Point(10.0, 5.0)])
        
        with pytest.raises(ValueError, match="Required displacement cannot be negative"):
            Conflict(
                segment1=seg1,
                segment2=seg2,
                min_distance_point1=Point(5.0, 0.0),
                min_distance_point2=Point(5.0, 5.0),
                actual_distance=5.0,
                required_displacement=-1.0
            )


class TestDisplacementConfig:
    """Tests for the DisplacementConfig class."""
    
    def test_config_default_values(self):
        """Test configuration with default values."""
        config = DisplacementConfig()
        assert config.min_distance == 10.0
        assert config.max_displacement == 50.0
        assert config.strategy == "perpendicular"
        assert config.energy_alpha == 0.3
        assert config.energy_beta == 0.7
        assert config.max_iterations == 100
        assert config.convergence_threshold == 0.01
        assert config.coordinate_precision == 6
    
    def test_config_custom_values(self):
        """Test configuration with custom values."""
        config = DisplacementConfig(
            min_distance=20.0,
            max_displacement=100.0,
            strategy="angular",
            energy_alpha=0.5,
            energy_beta=0.5
        )
        assert config.min_distance == 20.0
        assert config.max_displacement == 100.0
        assert config.strategy == "angular"
        assert config.energy_alpha == 0.5
        assert config.energy_beta == 0.5
    
    def test_config_negative_min_distance_raises_error(self):
        """Test that negative min_distance raises ValueError."""
        with pytest.raises(ValueError, match="min_distance must be positive"):
            DisplacementConfig(min_distance=-10.0)
    
    def test_config_zero_min_distance_raises_error(self):
        """Test that zero min_distance raises ValueError."""
        with pytest.raises(ValueError, match="min_distance must be positive"):
            DisplacementConfig(min_distance=0.0)
    
    def test_config_negative_max_displacement_raises_error(self):
        """Test that negative max_displacement raises ValueError."""
        with pytest.raises(ValueError, match="max_displacement must be positive"):
            DisplacementConfig(max_displacement=-50.0)
    
    def test_config_invalid_strategy_raises_error(self):
        """Test that invalid strategy raises ValueError."""
        with pytest.raises(ValueError, match="strategy must be"):
            DisplacementConfig(strategy="invalid")
    
    def test_config_energy_alpha_out_of_range_raises_error(self):
        """Test that energy_alpha outside [0,1] raises ValueError."""
        with pytest.raises(ValueError, match="energy_alpha must be between 0 and 1"):
            DisplacementConfig(energy_alpha=1.5)
        
        with pytest.raises(ValueError, match="energy_alpha must be between 0 and 1"):
            DisplacementConfig(energy_alpha=-0.1)
    
    def test_config_energy_beta_out_of_range_raises_error(self):
        """Test that energy_beta outside [0,1] raises ValueError."""
        with pytest.raises(ValueError, match="energy_beta must be between 0 and 1"):
            DisplacementConfig(energy_beta=1.5)
        
        with pytest.raises(ValueError, match="energy_beta must be between 0 and 1"):
            DisplacementConfig(energy_beta=-0.1)
    
    def test_config_negative_max_iterations_raises_error(self):
        """Test that negative max_iterations raises ValueError."""
        with pytest.raises(ValueError, match="max_iterations must be positive"):
            DisplacementConfig(max_iterations=-10)
    
    def test_config_negative_convergence_threshold_raises_error(self):
        """Test that negative convergence_threshold raises ValueError."""
        with pytest.raises(ValueError, match="convergence_threshold must be positive"):
            DisplacementConfig(convergence_threshold=-0.01)
    
    def test_config_negative_coordinate_precision_raises_error(self):
        """Test that negative coordinate_precision raises ValueError."""
        with pytest.raises(ValueError, match="coordinate_precision cannot be negative"):
            DisplacementConfig(coordinate_precision=-1)
    
    def test_config_all_strategies_valid(self):
        """Test that all documented strategies are valid."""
        strategies = ["perpendicular", "angular", "hybrid"]
        for strategy in strategies:
            config = DisplacementConfig(strategy=strategy)
            assert config.strategy == strategy
