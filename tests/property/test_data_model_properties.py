"""
Property-based tests for data model invariants.

Tests universal properties that should hold for all valid inputs to the
Point, Vector2D, and LineSegment classes.
"""

import pytest
import math
from hypothesis import given, strategies as st, assume

from src.cartographic_displacement.models import (
    Point,
    Vector2D,
    LineSegment,
)


# Custom strategies for generating test data
@st.composite
def points(draw, min_value=-10000.0, max_value=10000.0):
    """Generate random Point objects."""
    x = draw(st.floats(min_value=min_value, max_value=max_value, 
                       allow_nan=False, allow_infinity=False))
    y = draw(st.floats(min_value=min_value, max_value=max_value,
                       allow_nan=False, allow_infinity=False))
    return Point(x, y)


@st.composite
def vectors(draw, min_value=-10000.0, max_value=10000.0):
    """Generate random Vector2D objects."""
    dx = draw(st.floats(min_value=min_value, max_value=max_value,
                        allow_nan=False, allow_infinity=False))
    dy = draw(st.floats(min_value=min_value, max_value=max_value,
                        allow_nan=False, allow_infinity=False))
    return Vector2D(dx, dy)


@st.composite
def non_zero_vectors(draw, min_value=-10000.0, max_value=10000.0):
    """Generate random non-zero Vector2D objects."""
    vec = draw(vectors(min_value, max_value))
    assume(vec.magnitude() > 1e-10)  # Ensure non-zero
    return vec


@st.composite
def line_segments(draw, min_points=2, max_points=10):
    """Generate random LineSegment objects."""
    num_points = draw(st.integers(min_value=min_points, max_value=max_points))
    coords = draw(st.lists(points(), min_size=num_points, max_size=num_points))
    segment_id = draw(st.integers(min_value=0, max_value=10000))
    return LineSegment(id=segment_id, coordinates=coords)


class TestPointProperties:
    """Property-based tests for Point class invariants."""
    
    @given(points(), points())
    def test_distance_symmetry(self, p1, p2):
        """
        Feature: cartographic-displacement, Property: Data model consistency
        Validates: Requirements 1.1, 1.3
        
        Test that Point distance calculations are symmetric.
        For any two points p1 and p2, distance(p1, p2) == distance(p2, p1).
        """
        dist1 = p1.distance_to(p2)
        dist2 = p2.distance_to(p1)
        assert abs(dist1 - dist2) < 1e-10, \
            f"Distance should be symmetric: {dist1} != {dist2}"
    
    @given(points(), points(), points())
    def test_triangle_inequality(self, p1, p2, p3):
        """
        Feature: cartographic-displacement, Property: Data model consistency
        Validates: Requirements 1.1, 1.3
        
        Test that Point distances satisfy the triangle inequality.
        For any three points p1, p2, p3: distance(p1, p3) <= distance(p1, p2) + distance(p2, p3).
        """
        d12 = p1.distance_to(p2)
        d23 = p2.distance_to(p3)
        d13 = p1.distance_to(p3)
        
        # Triangle inequality with small tolerance for floating point errors
        assert d13 <= d12 + d23 + 1e-10, \
            f"Triangle inequality violated: {d13} > {d12} + {d23}"
    
    @given(points())
    def test_distance_to_self_is_zero(self, p):
        """
        Feature: cartographic-displacement, Property: Data model consistency
        Validates: Requirements 1.1, 1.3
        
        Test that distance from a point to itself is always zero.
        """
        assert p.distance_to(p) == 0.0, \
            f"Distance to self should be zero, got {p.distance_to(p)}"
    
    @given(points(), points())
    def test_distance_non_negative(self, p1, p2):
        """
        Feature: cartographic-displacement, Property: Data model consistency
        Validates: Requirements 1.1, 1.3
        
        Test that distance between any two points is always non-negative.
        """
        dist = p1.distance_to(p2)
        assert dist >= 0.0, \
            f"Distance should be non-negative, got {dist}"


class TestVector2DProperties:
    """Property-based tests for Vector2D class invariants."""
    
    @given(non_zero_vectors())
    def test_normalization_produces_unit_vector(self, v):
        """
        Feature: cartographic-displacement, Property: Data model consistency
        Validates: Requirements 1.1, 1.3
        
        Test that Vector2D normalization produces unit vectors.
        For any non-zero vector v, normalize(v).magnitude() == 1.0.
        """
        normalized = v.normalize()
        magnitude = normalized.magnitude()
        assert abs(magnitude - 1.0) < 1e-10, \
            f"Normalized vector should have magnitude 1.0, got {magnitude}"
    
    @given(non_zero_vectors())
    def test_normalization_preserves_direction(self, v):
        """
        Feature: cartographic-displacement, Property: Data model consistency
        Validates: Requirements 1.1, 1.3
        
        Test that normalization preserves the direction of the vector.
        The normalized vector should be parallel to the original (same ratio dx/dy).
        """
        normalized = v.normalize()
        original_mag = v.magnitude()
        
        # Check that normalized vector is parallel to original
        # by verifying that normalized * original_magnitude == original
        scaled_back = normalized.scale(original_mag)
        
        assert abs(scaled_back.dx - v.dx) < 1e-6, \
            f"Normalization should preserve direction: dx {scaled_back.dx} != {v.dx}"
        assert abs(scaled_back.dy - v.dy) < 1e-6, \
            f"Normalization should preserve direction: dy {scaled_back.dy} != {v.dy}"
    
    @given(vectors())
    def test_magnitude_non_negative(self, v):
        """
        Feature: cartographic-displacement, Property: Data model consistency
        Validates: Requirements 1.1, 1.3
        
        Test that vector magnitude is always non-negative.
        """
        mag = v.magnitude()
        assert mag >= 0.0, \
            f"Magnitude should be non-negative, got {mag}"
    
    @given(vectors(), st.floats(min_value=-100.0, max_value=100.0, 
                                 allow_nan=False, allow_infinity=False))
    def test_scale_magnitude_relationship(self, v, factor):
        """
        Feature: cartographic-displacement, Property: Data model consistency
        Validates: Requirements 1.1, 1.3
        
        Test that scaling a vector by a factor scales its magnitude by abs(factor).
        """
        original_mag = v.magnitude()
        scaled = v.scale(factor)
        scaled_mag = scaled.magnitude()
        
        expected_mag = original_mag * abs(factor)
        assert abs(scaled_mag - expected_mag) < 1e-6, \
            f"Scaled magnitude should be {expected_mag}, got {scaled_mag}"


class TestLineSegmentProperties:
    """Property-based tests for LineSegment class invariants."""
    
    @given(line_segments())
    def test_length_non_negative(self, segment):
        """
        Feature: cartographic-displacement, Property: Data model consistency
        Validates: Requirements 1.1, 1.3
        
        Test that LineSegment length is always non-negative.
        """
        length = segment.length()
        assert length >= 0.0, \
            f"Segment length should be non-negative, got {length}"
    
    @given(line_segments())
    def test_length_zero_only_for_degenerate_segments(self, segment):
        """
        Feature: cartographic-displacement, Property: Data model consistency
        Validates: Requirements 1.1, 1.3
        
        Test that only degenerate segments (all points at same location) have zero length.
        """
        length = segment.length()
        
        # Check if all points are at the same location
        all_same = all(
            p.distance_to(segment.coordinates[0]) < 1e-10 
            for p in segment.coordinates
        )
        
        if all_same:
            assert length < 1e-10, \
                f"Degenerate segment should have near-zero length, got {length}"
        else:
            assert length > 0.0, \
                f"Non-degenerate segment should have positive length, got {length}"
    
    @given(line_segments())
    def test_perpendicular_vector_is_unit_vector(self, segment):
        """
        Feature: cartographic-displacement, Property: Data model consistency
        Validates: Requirements 1.1, 1.3
        
        Test that perpendicular vectors are always unit vectors.
        """
        # Skip degenerate segments
        assume(segment.length() > 1e-6)
        
        # Get a point on the segment (use midpoint of first segment)
        p1 = segment.coordinates[0]
        p2 = segment.coordinates[1]
        mid_point = Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
        
        perp = segment.get_perpendicular_vector(mid_point)
        mag = perp.magnitude()
        
        assert abs(mag - 1.0) < 1e-10, \
            f"Perpendicular vector should be unit vector, got magnitude {mag}"
    
    @given(line_segments())
    def test_perpendicular_vector_is_perpendicular(self, segment):
        """
        Feature: cartographic-displacement, Property: Data model consistency
        Validates: Requirements 1.1, 1.3
        
        Test that perpendicular vectors are actually perpendicular to the segment direction.
        """
        # Skip degenerate segments
        assume(segment.length() > 1e-6)
        
        # Get the direction of the first segment
        p1 = segment.coordinates[0]
        p2 = segment.coordinates[1]
        direction = Vector2D(p2.x - p1.x, p2.y - p1.y)
        
        # Skip if direction is too small
        assume(direction.magnitude() > 1e-6)
        
        mid_point = Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
        perp = segment.get_perpendicular_vector(mid_point)
        
        # Dot product of perpendicular vectors should be zero
        dot_product = direction.dx * perp.dx + direction.dy * perp.dy
        
        assert abs(dot_product) < 1e-6, \
            f"Perpendicular vector should be orthogonal, dot product = {dot_product}"
