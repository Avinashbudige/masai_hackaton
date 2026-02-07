"""
Property-based tests for Network Graph component.

Tests universal properties that should hold for all network configurations.
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import List, Tuple

from src.cartographic_displacement.network_graph import NetworkGraph
from src.cartographic_displacement.models import LineSegment, Point, IntersectionPoint


# Custom strategies for generating network segments
@st.composite
def point_strategy(draw, min_value=-1000.0, max_value=1000.0):
    """Generate a random Point."""
    x = draw(st.floats(
        min_value=min_value,
        max_value=max_value,
        allow_nan=False,
        allow_infinity=False
    ))
    y = draw(st.floats(
        min_value=min_value,
        max_value=max_value,
        allow_nan=False,
        allow_infinity=False
    ))
    return Point(x, y)


@st.composite
def line_segment_strategy(draw, segment_id, min_points=2, max_points=5):
    """Generate a random LineSegment."""
    num_points = draw(st.integers(min_value=min_points, max_value=max_points))
    coordinates = [draw(point_strategy()) for _ in range(num_points)]
    
    # Ensure points are not all identical (would create invalid geometry)
    unique_coords = set((p.x, p.y) for p in coordinates)
    assume(len(unique_coords) >= 2)
    
    return LineSegment(id=segment_id, coordinates=coordinates)


@st.composite
def network_with_known_intersections(draw):
    """
    Generate a network with known intersection points.
    
    This strategy creates segments that are guaranteed to share endpoints,
    allowing us to verify that all intersections are detected.
    
    Returns:
        Tuple of (segments, expected_intersection_points)
    """
    # Generate a set of shared intersection points
    num_intersections = draw(st.integers(min_value=1, max_value=5))
    intersection_points = [draw(point_strategy()) for _ in range(num_intersections)]
    
    # Generate segments that connect these intersection points
    segments = []
    segment_id = 0
    expected_intersections = {}  # Map from point to list of segment IDs
    
    # Create at least 2 segments per intersection point
    for intersection_point in intersection_points:
        num_segments_at_intersection = draw(st.integers(min_value=2, max_value=4))
        
        for _ in range(num_segments_at_intersection):
            # Create a segment that starts or ends at this intersection
            use_as_start = draw(st.booleans())
            
            # Generate additional points for the segment
            num_additional_points = draw(st.integers(min_value=1, max_value=3))
            additional_points = [draw(point_strategy()) for _ in range(num_additional_points)]
            
            # Ensure additional points are different from intersection point
            additional_points = [p for p in additional_points 
                               if abs(p.x - intersection_point.x) > 0.01 or 
                                  abs(p.y - intersection_point.y) > 0.01]
            
            if not additional_points:
                # If all points were filtered out, create a distinct point
                additional_points = [Point(
                    intersection_point.x + draw(st.floats(min_value=10, max_value=100)),
                    intersection_point.y + draw(st.floats(min_value=10, max_value=100))
                )]
            
            # Build segment coordinates
            if use_as_start:
                coordinates = [intersection_point] + additional_points
            else:
                coordinates = additional_points + [intersection_point]
            
            segment = LineSegment(id=segment_id, coordinates=coordinates)
            segments.append(segment)
            
            # Track which segments connect at this intersection
            # We need to track BOTH endpoints of each segment
            start_key = (round(coordinates[0].x, 6), round(coordinates[0].y, 6))
            end_key = (round(coordinates[-1].x, 6), round(coordinates[-1].y, 6))
            
            # Add segment to start point's intersection
            if start_key not in expected_intersections:
                expected_intersections[start_key] = []
            if segment_id not in expected_intersections[start_key]:
                expected_intersections[start_key].append(segment_id)
            
            # Add segment to end point's intersection (if different from start)
            if start_key != end_key:
                if end_key not in expected_intersections:
                    expected_intersections[end_key] = []
                if segment_id not in expected_intersections[end_key]:
                    expected_intersections[end_key].append(segment_id)
            
            segment_id += 1
    
    # Filter out intersections with only 1 segment (not real intersections)
    expected_intersections = {k: v for k, v in expected_intersections.items() if len(v) >= 2}
    
    return segments, expected_intersections


@st.composite
def simple_network_strategy(draw, min_segments=2, max_segments=10):
    """Generate a simple network with random segments."""
    num_segments = draw(st.integers(min_value=min_segments, max_value=max_segments))
    segments = [draw(line_segment_strategy(segment_id=i)) for i in range(num_segments)]
    return segments


class TestNetworkGraphProperties:
    """Property-based tests for Network Graph."""
    
    @given(network_with_known_intersections())
    def test_intersection_extraction_completeness(self, network_data):
        """
        Feature: cartographic-displacement, Property 3: Intersection extraction completeness
        Validates: Requirements 1.3
        
        Test that all shared endpoints are identified as intersection points.
        For any successfully parsed street network, all points where segments share
        endpoints should be identified as intersection points.
        """
        segments, expected_intersections = network_data
        
        # Skip if no segments were generated
        assume(len(segments) >= 2)
        assume(len(expected_intersections) >= 1)
        
        # Build network graph
        network = NetworkGraph(segments)
        
        # Get detected intersections
        detected_intersections = network.get_intersections()
        
        # Verify that the number of detected intersections matches expected
        assert len(detected_intersections) == len(expected_intersections), \
            f"Expected {len(expected_intersections)} intersections, but detected {len(detected_intersections)}"
        
        # Build a map of detected intersection locations (rounded for comparison)
        detected_locations = {}
        for intersection in detected_intersections:
            key = (round(intersection.location.x, 6), round(intersection.location.y, 6))
            detected_locations[key] = intersection
        
        # Verify each expected intersection was detected
        for expected_coord, expected_segment_ids in expected_intersections.items():
            assert expected_coord in detected_locations, \
                f"Expected intersection at {expected_coord} was not detected"
            
            detected_intersection = detected_locations[expected_coord]
            
            # Verify the correct segments are connected at this intersection
            detected_segment_ids = set(detected_intersection.connected_segment_ids)
            expected_segment_ids_set = set(expected_segment_ids)
            
            assert detected_segment_ids == expected_segment_ids_set, \
                f"At intersection {expected_coord}: expected segments {expected_segment_ids_set}, " \
                f"but got {detected_segment_ids}"
    
    @given(network_with_known_intersections())
    def test_intersection_degree_correctness(self, network_data):
        """
        Feature: cartographic-displacement, Property 3: Intersection extraction completeness
        Validates: Requirements 1.3
        
        Test that intersection degree (number of connected segments) is correct.
        """
        segments, expected_intersections = network_data
        
        assume(len(segments) >= 2)
        assume(len(expected_intersections) >= 1)
        
        network = NetworkGraph(segments)
        detected_intersections = network.get_intersections()
        
        # Verify each intersection has the correct degree
        for intersection in detected_intersections:
            degree = intersection.degree()
            
            # Degree should be at least 2 (otherwise it's not an intersection)
            assert degree >= 2, \
                f"Intersection at ({intersection.location.x}, {intersection.location.y}) " \
                f"has degree {degree}, expected at least 2"
            
            # Verify degree matches the number of connected segment IDs
            assert degree == len(intersection.connected_segment_ids), \
                f"Intersection degree {degree} doesn't match number of connected segments " \
                f"{len(intersection.connected_segment_ids)}"
    
    @given(network_with_known_intersections())
    def test_get_connected_segments_returns_correct_segments(self, network_data):
        """
        Feature: cartographic-displacement, Property 3: Intersection extraction completeness
        Validates: Requirements 1.3
        
        Test that get_connected_segments returns the correct segments for each intersection.
        """
        segments, expected_intersections = network_data
        
        assume(len(segments) >= 2)
        assume(len(expected_intersections) >= 1)
        
        network = NetworkGraph(segments)
        detected_intersections = network.get_intersections()
        
        for intersection in detected_intersections:
            connected_segments = network.get_connected_segments(intersection)
            
            # Verify the number of connected segments matches the degree
            assert len(connected_segments) == intersection.degree(), \
                f"Number of connected segments {len(connected_segments)} doesn't match " \
                f"intersection degree {intersection.degree()}"
            
            # Verify all returned segments have IDs in the intersection's connected_segment_ids
            returned_ids = set(seg.id for seg in connected_segments)
            expected_ids = set(intersection.connected_segment_ids)
            
            assert returned_ids == expected_ids, \
                f"Connected segments IDs {returned_ids} don't match expected {expected_ids}"
    
    @given(simple_network_strategy(min_segments=1, max_segments=5))
    def test_network_graph_handles_disconnected_segments(self, segments):
        """
        Feature: cartographic-displacement, Property 3: Intersection extraction completeness
        Validates: Requirements 1.3
        
        Test that network graph correctly handles disconnected segments (no shared endpoints).
        """
        # Build network graph
        network = NetworkGraph(segments)
        
        # Get intersections
        intersections = network.get_intersections()
        
        # For disconnected segments, there should be no intersections
        # (or only intersections where segments happen to share endpoints by chance)
        # This property just verifies the graph doesn't crash and returns a valid list
        assert isinstance(intersections, list), \
            "get_intersections should return a list"
        
        # All intersections should have degree >= 2
        for intersection in intersections:
            assert intersection.degree() >= 2, \
                f"Intersection should have degree >= 2, got {intersection.degree()}"
    
    @given(line_segment_strategy(segment_id=0))
    def test_single_segment_network_has_no_intersections(self, segment):
        """
        Feature: cartographic-displacement, Property 3: Intersection extraction completeness
        Validates: Requirements 1.3
        
        Test that a network with a single segment has no intersections.
        """
        network = NetworkGraph([segment])
        intersections = network.get_intersections()
        
        # A single segment cannot have intersections (needs at least 2 segments)
        assert len(intersections) == 0, \
            f"Single segment network should have 0 intersections, got {len(intersections)}"
    
    @given(network_with_known_intersections())
    def test_intersection_locations_are_valid_points(self, network_data):
        """
        Feature: cartographic-displacement, Property 3: Intersection extraction completeness
        Validates: Requirements 1.3
        
        Test that all intersection locations are valid Point objects with finite coordinates.
        """
        segments, _ = network_data
        
        assume(len(segments) >= 2)
        
        network = NetworkGraph(segments)
        intersections = network.get_intersections()
        
        for intersection in intersections:
            # Verify location is a Point
            assert isinstance(intersection.location, Point), \
                f"Intersection location should be a Point, got {type(intersection.location)}"
            
            # Verify coordinates are finite
            import math
            assert math.isfinite(intersection.location.x), \
                f"Intersection x-coordinate should be finite, got {intersection.location.x}"
            assert math.isfinite(intersection.location.y), \
                f"Intersection y-coordinate should be finite, got {intersection.location.y}"
    
    @given(network_with_known_intersections())
    def test_no_duplicate_intersections(self, network_data):
        """
        Feature: cartographic-displacement, Property 3: Intersection extraction completeness
        Validates: Requirements 1.3
        
        Test that no duplicate intersection points are returned.
        """
        segments, _ = network_data
        
        assume(len(segments) >= 2)
        
        network = NetworkGraph(segments)
        intersections = network.get_intersections()
        
        # Build set of intersection locations (rounded for comparison)
        locations = set()
        for intersection in intersections:
            key = (round(intersection.location.x, 6), round(intersection.location.y, 6))
            assert key not in locations, \
                f"Duplicate intersection found at {key}"
            locations.add(key)
