"""
Network Graph component for topology extraction and spatial indexing.

This module provides functionality to build a topological representation
of a street network, including intersection detection, adjacency relationships,
and spatial indexing for efficient proximity queries.
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict
from shapely.strtree import STRtree

from .models import LineSegment, IntersectionPoint, Point


class NetworkGraph:
    """
    Topological representation of a street network.
    
    This class builds and maintains the topological structure of a network
    of line segments, including intersection points, adjacency relationships,
    and spatial indexing for efficient queries.
    
    Attributes:
        segments: List of all line segments in the network
        _intersections: Cached list of intersection points
        _spatial_index: R-tree spatial index for efficient proximity queries
        _endpoint_map: Spatial hash map for finding shared endpoints
        _adjacency_map: Map from segment ID to adjacent segment IDs
    """
    
    def __init__(self, segments: List[LineSegment]):
        """
        Build graph from segments.
        
        Args:
            segments: List of LineSegment objects to build the network from
        """
        self.segments = segments
        self._intersections: List[IntersectionPoint] = []
        self._spatial_index: STRtree = None
        self._endpoint_map: Dict[Tuple[float, float], List[int]] = defaultdict(list)
        self._adjacency_map: Dict[int, Set[int]] = defaultdict(set)
        
        # Build the network topology
        self._build_topology()
        self._build_spatial_index()
    
    def _round_coordinate(self, point: Point, precision: int = 6) -> Tuple[float, float]:
        """
        Round a point's coordinates for use as a hash key.
        
        Args:
            point: The point to round
            precision: Number of decimal places to round to
            
        Returns:
            Tuple of rounded (x, y) coordinates
        """
        factor = 10 ** precision
        return (round(point.x * factor) / factor, round(point.y * factor) / factor)
    
    def _build_topology(self):
        """
        Build spatial hash map for finding shared endpoints and extract intersections.
        
        This method:
        1. Creates a spatial hash map of all segment endpoints
        2. Identifies intersection points where segments share endpoints
        3. Builds adjacency relationships between connected segments
        """
        # Build endpoint map: maps rounded coordinates to segment IDs
        # Use a set to track which (segment_id, endpoint_type) pairs we've seen
        # to avoid counting the same segment twice at the same location
        for segment in self.segments:
            start = self._round_coordinate(segment.start_point())
            end = self._round_coordinate(segment.end_point())
            
            # Only add if start and end are different (avoid self-loops)
            if start != end:
                self._endpoint_map[start].append(segment.id)
                self._endpoint_map[end].append(segment.id)
            else:
                # Degenerate case: segment start and end round to same point
                # Only add once to avoid duplicate counting
                if segment.id not in self._endpoint_map[start]:
                    self._endpoint_map[start].append(segment.id)
        
        # Extract intersections: points where 2+ DIFFERENT segments meet
        intersection_dict: Dict[Tuple[float, float], IntersectionPoint] = {}
        
        for coord, segment_ids in self._endpoint_map.items():
            # Get unique segment IDs (in case a segment appears twice at same location)
            unique_segment_ids = list(set(segment_ids))
            
            if len(unique_segment_ids) >= 2:
                # This is an intersection point (2+ different segments meet)
                point = Point(coord[0], coord[1])
                intersection = IntersectionPoint(
                    location=point,
                    connected_segment_ids=unique_segment_ids
                )
                intersection_dict[coord] = intersection
        
        self._intersections = list(intersection_dict.values())
        
        # Build adjacency map: segments are adjacent if they share an endpoint
        for intersection in self._intersections:
            segment_ids = intersection.connected_segment_ids
            # Each segment at this intersection is adjacent to all others
            for seg_id in segment_ids:
                for other_id in segment_ids:
                    if seg_id != other_id:
                        self._adjacency_map[seg_id].add(other_id)
    
    def _build_spatial_index(self):
        """
        Build R-tree spatial index using Shapely's STRtree.
        
        This creates an efficient spatial index for proximity queries,
        allowing fast identification of segments near a given location.
        """
        if not self.segments:
            self._spatial_index = STRtree([])
            return
        
        # Build STRtree from segment geometries
        geometries = [seg.shapely_geom for seg in self.segments]
        self._spatial_index = STRtree(geometries)
    
    def get_intersections(self) -> List[IntersectionPoint]:
        """
        Return all intersection points where segments meet.
        
        An intersection point is defined as a location where two or more
        segments share an endpoint.
        
        Returns:
            List of IntersectionPoint objects
        """
        return self._intersections.copy()
    
    def get_connected_segments(self, point: IntersectionPoint) -> List[LineSegment]:
        """
        Return segments connected at given intersection.
        
        Args:
            point: The intersection point to query
            
        Returns:
            List of LineSegment objects connected at this intersection
        """
        # Build a map from segment ID to segment for quick lookup
        segment_map = {seg.id: seg for seg in self.segments}
        
        connected = []
        for seg_id in point.connected_segment_ids:
            if seg_id in segment_map:
                connected.append(segment_map[seg_id])
        
        return connected
    
    def get_adjacent_segments(self, segment: LineSegment) -> List[LineSegment]:
        """
        Return segments sharing endpoints with given segment.
        
        Two segments are adjacent if they share at least one endpoint
        (i.e., they are connected at an intersection point).
        
        Args:
            segment: The segment to find adjacent segments for
            
        Returns:
            List of LineSegment objects adjacent to the given segment
        """
        # Get adjacent segment IDs from the adjacency map
        adjacent_ids = self._adjacency_map.get(segment.id, set())
        
        # Build a map from segment ID to segment for quick lookup
        segment_map = {seg.id: seg for seg in self.segments}
        
        adjacent = []
        for seg_id in adjacent_ids:
            if seg_id in segment_map:
                adjacent.append(segment_map[seg_id])
        
        return adjacent
    
    def query_nearby_segments(self, segment: LineSegment, buffer_distance: float = None) -> List[LineSegment]:
        """
        Query segments near the given segment using the spatial index.
        
        This method uses the R-tree spatial index to efficiently find
        segments whose bounding boxes are near the given segment.
        
        Args:
            segment: The segment to query around
            buffer_distance: Optional buffer distance for the query.
                           If None, uses the segment's bounding box.
            
        Returns:
            List of LineSegment objects near the given segment
        """
        if self._spatial_index is None or len(self.segments) == 0:
            return []
        
        # Create query geometry
        if buffer_distance is not None and buffer_distance > 0:
            query_geom = segment.shapely_geom.buffer(buffer_distance)
        else:
            query_geom = segment.shapely_geom
        
        # Query the spatial index - use query method which returns geometries
        nearby_geoms = list(self._spatial_index.query(query_geom))
        
        # Convert geometries back to LineSegments
        # Build a map from shapely geometry id to segment
        geom_to_segment = {id(seg.shapely_geom): seg for seg in self.segments}
        
        nearby_segments = []
        for geom in nearby_geoms:
            geom_id = id(geom)
            if geom_id in geom_to_segment:
                seg = geom_to_segment[geom_id]
                # Exclude the query segment itself
                if seg.id != segment.id:
                    nearby_segments.append(seg)
        
        return nearby_segments
    
    def get_segment_by_id(self, segment_id: int) -> LineSegment:
        """
        Get a segment by its ID.
        
        Args:
            segment_id: The ID of the segment to retrieve
            
        Returns:
            The LineSegment with the given ID
            
        Raises:
            ValueError: If no segment with the given ID exists
        """
        for segment in self.segments:
            if segment.id == segment_id:
                return segment
        raise ValueError(f"No segment found with ID {segment_id}")
