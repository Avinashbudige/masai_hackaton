"""
Unit tests for NetworkGraph component.
"""

import pytest
from src.cartographic_displacement import (
    NetworkGraph,
    LineSegment,
    Point,
    IntersectionPoint,
)


class TestNetworkGraph:
    """Test suite for NetworkGraph class."""
    
    def test_empty_network(self):
        """Test creating a network with no segments."""
        network = NetworkGraph([])
        assert len(network.segments) == 0
        assert len(network.get_intersections()) == 0
    
    def test_single_segment(self):
        """Test network with a single segment."""
        segment = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 10)]
        )
        network = NetworkGraph([segment])
        
        assert len(network.segments) == 1
        assert len(network.get_intersections()) == 0  # No intersections with single segment
    
    def test_two_disconnected_segments(self):
        """Test network with two disconnected segments."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(0, 10), Point(10, 10)]
        )
        network = NetworkGraph([seg1, seg2])
        
        assert len(network.segments) == 2
        assert len(network.get_intersections()) == 0
    
    def test_two_connected_segments(self):
        """Test network with two segments sharing an endpoint."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(10, 0), Point(10, 10)]
        )
        network = NetworkGraph([seg1, seg2])
        
        intersections = network.get_intersections()
        assert len(intersections) == 1
        assert intersections[0].location == Point(10, 0)
        assert set(intersections[0].connected_segment_ids) == {1, 2}
    
    def test_three_way_intersection(self):
        """Test network with three segments meeting at a point."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 10)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(10, 10), Point(20, 10)]
        )
        seg3 = LineSegment(
            id=3,
            coordinates=[Point(10, 10), Point(10, 20)]
        )
        network = NetworkGraph([seg1, seg2, seg3])
        
        intersections = network.get_intersections()
        assert len(intersections) == 1
        assert intersections[0].degree() == 3
        assert set(intersections[0].connected_segment_ids) == {1, 2, 3}
    
    def test_get_connected_segments(self):
        """Test retrieving segments connected at an intersection."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(10, 0), Point(10, 10)]
        )
        network = NetworkGraph([seg1, seg2])
        
        intersections = network.get_intersections()
        connected = network.get_connected_segments(intersections[0])
        
        assert len(connected) == 2
        assert set(seg.id for seg in connected) == {1, 2}
    
    def test_get_adjacent_segments(self):
        """Test retrieving adjacent segments."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(10, 0), Point(10, 10)]
        )
        seg3 = LineSegment(
            id=3,
            coordinates=[Point(0, 10), Point(10, 10)]
        )
        network = NetworkGraph([seg1, seg2, seg3])
        
        # seg1 and seg2 are adjacent (share endpoint at 10,0)
        adjacent_to_seg1 = network.get_adjacent_segments(seg1)
        assert len(adjacent_to_seg1) == 1
        assert adjacent_to_seg1[0].id == 2
        
        # seg2 and seg3 are adjacent (share endpoint at 10,10)
        adjacent_to_seg2 = network.get_adjacent_segments(seg2)
        assert len(adjacent_to_seg2) == 2
        assert set(seg.id for seg in adjacent_to_seg2) == {1, 3}
    
    def test_query_nearby_segments(self):
        """Test spatial index query for nearby segments."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(0, 5), Point(10, 5)]
        )
        seg3 = LineSegment(
            id=3,
            coordinates=[Point(0, 100), Point(10, 100)]
        )
        network = NetworkGraph([seg1, seg2, seg3])
        
        # Query segments near seg1 with buffer of 10
        nearby = network.query_nearby_segments(seg1, buffer_distance=10)
        
        # Should find seg2 (5 units away) but not seg3 (100 units away)
        assert len(nearby) >= 1
        assert any(seg.id == 2 for seg in nearby)
        assert not any(seg.id == 3 for seg in nearby)
    
    def test_get_segment_by_id(self):
        """Test retrieving a segment by its ID."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(10, 0), Point(10, 10)]
        )
        network = NetworkGraph([seg1, seg2])
        
        retrieved = network.get_segment_by_id(1)
        assert retrieved.id == 1
        assert retrieved == seg1
        
        with pytest.raises(ValueError, match="No segment found with ID 999"):
            network.get_segment_by_id(999)
    
    def test_intersection_caching(self):
        """Test that intersections are cached after first call."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(10, 0), Point(10, 10)]
        )
        network = NetworkGraph([seg1, seg2])
        
        # First call computes intersections
        intersections1 = network.get_intersections()
        
        # Second call should return cached result
        intersections2 = network.get_intersections()
        
        assert intersections1 is intersections2  # Same object reference


class TestAdjacencyRelationships:
    """Test suite for adjacency relationship detection."""
    
    def test_adjacent_segments_correctly_identified(self):
        """Test that adjacent segments (sharing endpoints) are correctly identified."""
        # Create a simple T-junction: seg1 and seg2 share endpoint, seg2 and seg3 share endpoint
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(10, 0), Point(20, 0)]
        )
        seg3 = LineSegment(
            id=3,
            coordinates=[Point(20, 0), Point(20, 10)]
        )
        network = NetworkGraph([seg1, seg2, seg3])
        
        # seg1 should be adjacent to seg2
        adjacent_to_seg1 = network.get_adjacent_segments(seg1)
        assert len(adjacent_to_seg1) == 1
        assert adjacent_to_seg1[0].id == 2
        
        # seg2 should be adjacent to both seg1 and seg3
        adjacent_to_seg2 = network.get_adjacent_segments(seg2)
        assert len(adjacent_to_seg2) == 2
        assert set(seg.id for seg in adjacent_to_seg2) == {1, 3}
        
        # seg3 should be adjacent to seg2
        adjacent_to_seg3 = network.get_adjacent_segments(seg3)
        assert len(adjacent_to_seg3) == 1
        assert adjacent_to_seg3[0].id == 2
    
    def test_non_adjacent_segments_not_identified(self):
        """Test that non-adjacent segments are not identified as adjacent."""
        # Create two disconnected segments
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(20, 20), Point(30, 30)]
        )
        network = NetworkGraph([seg1, seg2])
        
        # Neither segment should have adjacent segments
        adjacent_to_seg1 = network.get_adjacent_segments(seg1)
        assert len(adjacent_to_seg1) == 0
        
        adjacent_to_seg2 = network.get_adjacent_segments(seg2)
        assert len(adjacent_to_seg2) == 0
    
    def test_single_segment_has_no_adjacent_segments(self):
        """Test that a single segment has no adjacent segments."""
        segment = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 10)]
        )
        network = NetworkGraph([segment])
        
        adjacent = network.get_adjacent_segments(segment)
        assert len(adjacent) == 0
    
    def test_disconnected_segments_have_no_adjacency(self):
        """Test that completely disconnected segments have no adjacency relationships."""
        # Create three disconnected segments
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(20, 20), Point(30, 20)]
        )
        seg3 = LineSegment(
            id=3,
            coordinates=[Point(40, 40), Point(50, 40)]
        )
        network = NetworkGraph([seg1, seg2, seg3])
        
        # No segment should have adjacent segments
        assert len(network.get_adjacent_segments(seg1)) == 0
        assert len(network.get_adjacent_segments(seg2)) == 0
        assert len(network.get_adjacent_segments(seg3)) == 0
    
    def test_four_way_intersection_adjacency(self):
        """Test adjacency at a four-way intersection."""
        # Create four segments meeting at a central point
        center = Point(10, 10)
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 10), center]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[center, Point(20, 10)]
        )
        seg3 = LineSegment(
            id=3,
            coordinates=[Point(10, 0), center]
        )
        seg4 = LineSegment(
            id=4,
            coordinates=[center, Point(10, 20)]
        )
        network = NetworkGraph([seg1, seg2, seg3, seg4])
        
        # Each segment should be adjacent to all other three
        for segment in [seg1, seg2, seg3, seg4]:
            adjacent = network.get_adjacent_segments(segment)
            assert len(adjacent) == 3
            adjacent_ids = set(seg.id for seg in adjacent)
            expected_ids = {1, 2, 3, 4} - {segment.id}
            assert adjacent_ids == expected_ids
    
    def test_multiple_intersections_adjacency(self):
        """Test adjacency with multiple intersection points."""
        # Create a chain: seg1 -- seg2 -- seg3
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(10, 0), Point(20, 0)]
        )
        seg3 = LineSegment(
            id=3,
            coordinates=[Point(20, 0), Point(30, 0)]
        )
        network = NetworkGraph([seg1, seg2, seg3])
        
        # seg1 adjacent to seg2 only
        adjacent_to_seg1 = network.get_adjacent_segments(seg1)
        assert len(adjacent_to_seg1) == 1
        assert adjacent_to_seg1[0].id == 2
        
        # seg2 adjacent to both seg1 and seg3
        adjacent_to_seg2 = network.get_adjacent_segments(seg2)
        assert len(adjacent_to_seg2) == 2
        assert set(seg.id for seg in adjacent_to_seg2) == {1, 3}
        
        # seg3 adjacent to seg2 only
        adjacent_to_seg3 = network.get_adjacent_segments(seg3)
        assert len(adjacent_to_seg3) == 1
        assert adjacent_to_seg3[0].id == 2
    
    def test_segment_with_multiple_points_adjacency(self):
        """Test adjacency for segments with multiple intermediate points."""
        # Create segments with multiple points
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(5, 5), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(10, 0), Point(15, 5), Point(20, 0)]
        )
        network = NetworkGraph([seg1, seg2])
        
        # Segments share endpoint at (10, 0), so they should be adjacent
        adjacent_to_seg1 = network.get_adjacent_segments(seg1)
        assert len(adjacent_to_seg1) == 1
        assert adjacent_to_seg1[0].id == 2
        
        adjacent_to_seg2 = network.get_adjacent_segments(seg2)
        assert len(adjacent_to_seg2) == 1
        assert adjacent_to_seg2[0].id == 1
    
    def test_adjacency_with_floating_point_coordinates(self):
        """Test adjacency detection with floating point coordinates."""
        # Create segments with floating point coordinates that should match
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0.0, 0.0), Point(10.123456, 5.654321)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(10.123456, 5.654321), Point(20.0, 10.0)]
        )
        network = NetworkGraph([seg1, seg2])
        
        # Should detect adjacency despite floating point coordinates
        adjacent_to_seg1 = network.get_adjacent_segments(seg1)
        assert len(adjacent_to_seg1) == 1
        assert adjacent_to_seg1[0].id == 2
    
    def test_adjacency_with_near_but_not_equal_endpoints(self):
        """Test that segments with very close but not equal endpoints are not adjacent."""
        # Create segments with endpoints that are close but not equal (beyond tolerance)
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10.0, 0.0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(10.001, 0.001), Point(20, 0)]  # Slightly off
        )
        network = NetworkGraph([seg1, seg2])
        
        # Should NOT detect adjacency (beyond tolerance threshold)
        adjacent_to_seg1 = network.get_adjacent_segments(seg1)
        # This might be 0 or 1 depending on rounding precision (6 decimal places)
        # At 6 decimal places, 10.001 rounds to 10.001, so they won't match
        assert len(adjacent_to_seg1) == 0
    
    def test_self_loop_segment_not_adjacent_to_itself(self):
        """Test that a segment with start and end at same location doesn't create self-adjacency."""
        # Create a segment that loops back to its start (degenerate case)
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 10), Point(0, 0)]
        )
        network = NetworkGraph([seg1])
        
        # Should not be adjacent to itself
        adjacent = network.get_adjacent_segments(seg1)
        assert len(adjacent) == 0
