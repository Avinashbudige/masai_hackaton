"""
Property-based tests for Conflict Detector component.

Tests universal properties that should hold for conflict detection operations.
"""

import pytest
from hypothesis import given, strategies as st

from src.cartographic_displacement.conflict_detector import ConflictDetector
from src.cartographic_displacement.network_graph import NetworkGraph
from src.cartographic_displacement.models import LineSegment, Point
from shapely.geometry import LineString


# Custom strategies for generating test data
@st.composite
def simple_network(draw, num_segments=2):
    """
    Generate a simple network with a few segments.
    
    Args:
        draw: Hypothesis draw function
        num_segments: Number of segments to generate
        
    Returns:
        NetworkGraph instance
    """
    segments = []
    for i in range(num_segments):
        # Generate two points for a simple line segment
        x1 = draw(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False))
        y1 = draw(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False))
        x2 = draw(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False))
        y2 = draw(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False))
        
        # Ensure the two points are different
        if abs(x1 - x2) < 0.1 and abs(y1 - y2) < 0.1:
            x2 = x1 + 10.0
            y2 = y1 + 10.0
        
        coords = [Point(x1, y1), Point(x2, y2)]
        shapely_geom = LineString([(x1, y1), (x2, y2)])
        segment = LineSegment(id=i, coordinates=coords, shapely_geom=shapely_geom)
        segments.append(segment)
    
    return NetworkGraph(segments)


class TestConflictDetectorProperties:
    """Property-based tests for Conflict Detector."""
    
    @given(
        st.floats(min_value=0.001, max_value=10000.0, allow_nan=False, allow_infinity=False),
        simple_network()
    )
    def test_positive_min_distance_accepted(self, min_distance, network):
        """
        Feature: cartographic-displacement, Property 5: Minimum distance validation
        Validates: Requirements 2.1
        
        Test that positive minimum distance values are accepted without errors.
        """
        # Should not raise an exception
        detector = ConflictDetector(network, min_distance)
        
        # Verify the detector was created successfully
        assert detector is not None, "ConflictDetector should be created"
        assert detector.min_distance == min_distance, \
            f"min_distance should be {min_distance}, got {detector.min_distance}"
        assert detector.network is network, "Network should be stored correctly"
    
    @given(
        st.floats(min_value=-10000.0, max_value=0.0, allow_nan=False, allow_infinity=False),
        simple_network()
    )
    def test_non_positive_min_distance_rejected(self, min_distance, network):
        """
        Feature: cartographic-displacement, Property 5: Minimum distance validation
        Validates: Requirements 2.1
        
        Test that non-positive minimum distance values are rejected with clear error messages.
        """
        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            ConflictDetector(network, min_distance)
        
        error_message = str(exc_info.value)
        
        # Verify error message is descriptive
        assert error_message is not None, "Error should have a message"
        assert len(error_message) > 0, "Error message should not be empty"
        
        # Error message should mention that min_distance must be positive
        assert "positive" in error_message.lower() or "must be" in error_message.lower(), \
            f"Error message should mention 'positive': {error_message}"
        
        # Error message should include the invalid value
        assert str(min_distance) in error_message or "min_distance" in error_message.lower(), \
            f"Error message should mention the parameter or value: {error_message}"
    
    @given(simple_network())
    def test_zero_min_distance_rejected(self, network):
        """
        Feature: cartographic-displacement, Property 5: Minimum distance validation
        Validates: Requirements 2.1
        
        Test that zero minimum distance is rejected with a clear error message.
        """
        # Should raise ValueError for zero
        with pytest.raises(ValueError) as exc_info:
            ConflictDetector(network, 0.0)
        
        error_message = str(exc_info.value)
        
        # Verify error message is descriptive
        assert error_message is not None, "Error should have a message"
        assert len(error_message) > 0, "Error message should not be empty"
        assert "positive" in error_message.lower(), \
            f"Error message should mention 'positive': {error_message}"
    
    @given(simple_network())
    def test_negative_min_distance_rejected(self, network):
        """
        Feature: cartographic-displacement, Property 5: Minimum distance validation
        Validates: Requirements 2.1
        
        Test that negative minimum distance is rejected with a clear error message.
        """
        # Test with a specific negative value
        with pytest.raises(ValueError) as exc_info:
            ConflictDetector(network, -10.0)
        
        error_message = str(exc_info.value)
        
        # Verify error message is descriptive
        assert error_message is not None, "Error should have a message"
        assert len(error_message) > 0, "Error message should not be empty"
        assert "positive" in error_message.lower(), \
            f"Error message should mention 'positive': {error_message}"
        assert "-10" in error_message or "negative" in error_message.lower(), \
            f"Error message should mention the negative value: {error_message}"
    
    @given(
        st.floats(min_value=0.001, max_value=10000.0, allow_nan=False, allow_infinity=False),
        simple_network()
    )
    def test_detector_stores_min_distance_correctly(self, min_distance, network):
        """
        Feature: cartographic-displacement, Property 5: Minimum distance validation
        Validates: Requirements 2.1
        
        Test that the detector correctly stores the minimum distance parameter.
        """
        detector = ConflictDetector(network, min_distance)
        
        # Verify the min_distance is stored correctly
        assert detector.min_distance == min_distance, \
            f"Stored min_distance {detector.min_distance} should match input {min_distance}"
        
        # Verify it's accessible as an attribute
        assert hasattr(detector, 'min_distance'), \
            "ConflictDetector should have min_distance attribute"
    
    @given(
        st.floats(min_value=0.001, max_value=10000.0, allow_nan=False, allow_infinity=False),
        simple_network()
    )
    def test_detector_stores_network_correctly(self, min_distance, network):
        """
        Feature: cartographic-displacement, Property 5: Minimum distance validation
        Validates: Requirements 2.1
        
        Test that the detector correctly stores the network parameter.
        """
        detector = ConflictDetector(network, min_distance)
        
        # Verify the network is stored correctly
        assert detector.network is network, \
            "Stored network should be the same object as input"
        
        # Verify it's accessible as an attribute
        assert hasattr(detector, 'network'), \
            "ConflictDetector should have network attribute"
