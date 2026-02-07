"""
Conflict Detector component for identifying spatial conflicts.

This module provides functionality to detect segments that violate
minimum distance constraints in a street network.
"""

from typing import List
from shapely.geometry import Point as ShapelyPoint

from .models import Conflict, Point, LineSegment
from .network_graph import NetworkGraph


class ConflictDetector:
    """
    Detector for spatial conflicts between line segments.
    
    This class identifies pairs of non-adjacent segments where the distance
    between them is less than a specified minimum distance threshold.
    
    Attributes:
        network: The NetworkGraph to analyze
        min_distance: Minimum allowed distance between segments
        _conflicts: Cached list of detected conflicts
    """
    
    def __init__(self, network: NetworkGraph, min_distance: float):
        """
        Initialize conflict detector with network and distance threshold.
        
        Args:
            network: The NetworkGraph to analyze for conflicts
            min_distance: Minimum allowed distance between segments
            
        Raises:
            ValueError: If min_distance is not positive
        """
        if min_distance <= 0:
            raise ValueError(f"min_distance must be positive, got {min_distance}")
        
        self.network = network
        self.min_distance = min_distance
        self._conflicts: List[Conflict] = []
    
    def detect_conflicts(self) -> List[Conflict]:
        """
        Return all segment pairs violating minimum distance.
        
        This method checks all segment pairs, computes actual distances and
        excludes adjacent segments.
        
        Returns:
            List of Conflict objects representing spatial conflicts
        """
        conflicts = []
        
        # Get adjacency information to exclude adjacent segments
        adjacent_map = {}
        for segment in self.network.segments:
            adjacent_segments = self.network.get_adjacent_segments(segment)
            adjacent_map[segment.id] = set(s.id for s in adjacent_segments)
        
        # Check all pairs of segments
        checked_pairs = set()
        
        for i, segment in enumerate(self.network.segments):
            for j in range(i + 1, len(self.network.segments)):
                other_segment = self.network.segments[j]
                
                # Skip if segments are adjacent (share an endpoint)
                if other_segment.id in adjacent_map.get(segment.id, set()):
                    continue
                
                # Calculate actual distance between segments
                distance = segment.shapely_geom.distance(other_segment.shapely_geom)
                
                # If distance violates minimum, create conflict
                if distance < self.min_distance:
                    # Find closest points on each segment
                    from shapely.ops import nearest_points
                    
                    point1_shapely, point2_shapely = nearest_points(
                        segment.shapely_geom,
                        other_segment.shapely_geom
                    )
                    
                    point1 = Point(point1_shapely.x, point1_shapely.y)
                    point2 = Point(point2_shapely.x, point2_shapely.y)
                    
                    required_displacement = self.min_distance - distance
                    
                    conflict = Conflict(
                        segment1=segment,
                        segment2=other_segment,
                        min_distance_point1=point1,
                        min_distance_point2=point2,
                        actual_distance=distance,
                        required_displacement=required_displacement
                    )
                    
                    conflicts.append(conflict)
        
        self._conflicts = conflicts
        return conflicts
    
    def get_conflict_zones(self) -> List:
        """
        Return geometric regions containing conflicts.
        
        This method creates buffer polygons around conflict locations
        for visualization purposes.
        
        Returns:
            List of Shapely Polygon objects representing conflict zones
        """
        if not self._conflicts:
            self.detect_conflicts()
        
        zones = []
        for conflict in self._conflicts:
            # Create a buffer around the conflict midpoint
            midpoint_x = (conflict.min_distance_point1.x + conflict.min_distance_point2.x) / 2
            midpoint_y = (conflict.min_distance_point1.y + conflict.min_distance_point2.y) / 2
            
            midpoint = ShapelyPoint(midpoint_x, midpoint_y)
            zone = midpoint.buffer(self.min_distance / 2)
            zones.append(zone)
        
        return zones
    
    def get_conflicts_for_segment(self, segment: LineSegment) -> List[Conflict]:
        """
        Get all conflicts involving a specific segment.
        
        Args:
            segment: The segment to find conflicts for
            
        Returns:
            List of Conflict objects involving the given segment
        """
        if not self._conflicts:
            self.detect_conflicts()
        
        segment_conflicts = []
        for conflict in self._conflicts:
            if conflict.segment1.id == segment.id or conflict.segment2.id == segment.id:
                segment_conflicts.append(conflict)
        
        return segment_conflicts
    
    def get_conflict_count(self) -> int:
        """
        Get the total number of conflicts detected.
        
        Returns:
            Number of conflicts
        """
        if not self._conflicts:
            self.detect_conflicts()
        
        return len(self._conflicts)
    
    def has_conflicts(self) -> bool:
        """
        Check if any conflicts exist in the network.
        
        Returns:
            True if conflicts exist, False otherwise
        """
        return self.get_conflict_count() > 0
