"""
Unit tests for ConflictDetector component.
"""

import pytest
from src.cartographic_displacement import (
    ConflictDetector,
    NetworkGraph,
    LineSegment,
    Point,
)


class TestConflictDetector:
    """Test suite for ConflictDetector class."""
    
    def test_no_conflicts_when_segments_far_apart(self):
        """Test that no conflicts are detected when segments are far apart."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(0, 100), Point(10, 100)]
        )
        network = NetworkGraph([seg1, seg2])
        detector = ConflictDetector(network, min_distance=10.0)
        
        conflicts = detector.detect_conflicts()
        assert len(conflicts) == 0
    
    def test_conflict_detected_when_segments_too_close(self):
        """Test that conflicts are detected when segments are too close."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(0, 3), Point(10, 3)]  # 3 units away
        )
        network = NetworkGraph([seg1, seg2])
        detector = ConflictDetector(network, min_distance=5.0)
        
        conflicts = detector.detect_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0].actual_distance < 5.0
        assert conflicts[0].required_displacement > 0
    
    def test_adjacent_segments_not_in_conflict(self):
        """Test that adjacent segments (sharing endpoints) are not flagged as conflicts."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(10, 0), Point(10, 10)]  # Shares endpoint with seg1
        )
        network = NetworkGraph([seg1, seg2])
        detector = ConflictDetector(network, min_distance=100.0)  # Large distance
        
        conflicts = detector.detect_conflicts()
        # Should be 0 because they're adjacent
        assert len(conflicts) == 0
    
    def test_min_distance_validation(self):
        """Test that min_distance must be positive."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        network = NetworkGraph([seg1])
        
        with pytest.raises(ValueError, match="min_distance must be positive"):
            ConflictDetector(network, min_distance=0.0)
        
        with pytest.raises(ValueError, match="min_distance must be positive"):
            ConflictDetector(network, min_distance=-5.0)
    
    def test_conflict_has_correct_segments(self):
        """Test that conflict correctly identifies the two segments involved."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(0, 2), Point(10, 2)]
        )
        network = NetworkGraph([seg1, seg2])
        detector = ConflictDetector(network, min_distance=5.0)
        
        conflicts = detector.detect_conflicts()
        assert len(conflicts) == 1
        
        conflict = conflicts[0]
        segment_ids = {conflict.segment1.id, conflict.segment2.id}
        assert segment_ids == {1, 2}
    
    def test_get_conflicts_for_segment(self):
        """Test retrieving conflicts for a specific segment."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(0, 2), Point(10, 2)]
        )
        seg3 = LineSegment(
            id=3,
            coordinates=[Point(0, 100), Point(10, 100)]
        )
        network = NetworkGraph([seg1, seg2, seg3])
        detector = ConflictDetector(network, min_distance=5.0)
        
        # seg1 and seg2 are in conflict, seg3 is not
        conflicts_seg1 = detector.get_conflicts_for_segment(seg1)
        assert len(conflicts_seg1) == 1
        
        conflicts_seg3 = detector.get_conflicts_for_segment(seg3)
        assert len(conflicts_seg3) == 0
    
    def test_has_conflicts(self):
        """Test has_conflicts method."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(0, 2), Point(10, 2)]
        )
        network = NetworkGraph([seg1, seg2])
        detector = ConflictDetector(network, min_distance=5.0)
        
        assert detector.has_conflicts() is True
    
    def test_no_conflicts_returns_false(self):
        """Test has_conflicts returns False when no conflicts exist."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(0, 100), Point(10, 100)]
        )
        network = NetworkGraph([seg1, seg2])
        detector = ConflictDetector(network, min_distance=5.0)
        
        assert detector.has_conflicts() is False
    
    def test_get_conflict_count(self):
        """Test get_conflict_count method."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(0, 2), Point(10, 2)]
        )
        seg3 = LineSegment(
            id=3,
            coordinates=[Point(0, 4), Point(10, 4)]
        )
        network = NetworkGraph([seg1, seg2, seg3])
        detector = ConflictDetector(network, min_distance=5.0)
        
        # All three segments are within 5 units of each other
        count = detector.get_conflict_count()
        assert count >= 2  # At least seg1-seg2 and seg2-seg3
    
    def test_conflict_zones_created(self):
        """Test that conflict zones can be generated."""
        seg1 = LineSegment(
            id=1,
            coordinates=[Point(0, 0), Point(10, 0)]
        )
        seg2 = LineSegment(
            id=2,
            coordinates=[Point(0, 2), Point(10, 2)]
        )
        network = NetworkGraph([seg1, seg2])
        detector = ConflictDetector(network, min_distance=5.0)
        
        zones = detector.get_conflict_zones()
        assert len(zones) > 0
        # Each zone should be a Shapely polygon
        for zone in zones:
            assert hasattr(zone, 'area')
            assert zone.area > 0
