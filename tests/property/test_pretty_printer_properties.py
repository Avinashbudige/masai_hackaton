"""
Property-based tests for WKT Pretty Printer component.

Tests universal properties that should hold for all valid geometry formatting operations.
"""

import pytest
import re
from hypothesis import given, strategies as st, assume

from src.cartographic_displacement.parser import WKTParser
from src.cartographic_displacement.pretty_printer import WKTPrettyPrinter
from src.cartographic_displacement.models import LineSegment, Point


# Custom strategies for generating valid coordinates
@st.composite
def valid_coordinates(draw, min_value=-10000.0, max_value=10000.0):
    """Generate a valid coordinate pair (x, y)."""
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
    return (x, y)


@st.composite
def valid_wkt_linestring(draw, min_points=2, max_points=20):
    """
    Generate a valid WKT LINESTRING string.
    
    Args:
        draw: Hypothesis draw function
        min_points: Minimum number of points (must be >= 2)
        max_points: Maximum number of points
        
    Returns:
        Valid WKT LINESTRING string
    """
    # Generate random number of points
    num_points = draw(st.integers(min_value=min_points, max_value=max_points))
    
    # Generate coordinate pairs
    coords = [draw(valid_coordinates()) for _ in range(num_points)]
    
    # Format as WKT string
    coord_strings = [f"{x} {y}" for x, y in coords]
    coord_list = ", ".join(coord_strings)
    
    wkt = f"LINESTRING ({coord_list})"
    
    return wkt


class TestRoundTripConsistency:
    """Property-based tests for round-trip consistency."""
    
    @given(valid_wkt_linestring())
    def test_round_trip_consistency(self, wkt_string):
        """
        Feature: cartographic-displacement, Property 4: Round-trip consistency
        Validates: Requirements 1.5
        
        Test that parse → print → parse produces equivalent geometry.
        This property verifies that formatting and parsing are inverse operations.
        """
        parser = WKTParser()
        printer = WKTPrettyPrinter(precision=6)
        
        # Parse original WKT
        segment1 = parser.parse_linestring(wkt_string)
        
        # Format to WKT
        formatted_wkt = printer.format_segment(segment1)
        
        # Parse formatted WKT
        parser.reset_id_counter()
        segment2 = parser.parse_linestring(formatted_wkt)
        
        # Verify coordinates match within precision tolerance
        assert len(segment1.coordinates) == len(segment2.coordinates), \
            f"Coordinate count mismatch: {len(segment1.coordinates)} != {len(segment2.coordinates)}"
        
        # Check each coordinate pair
        for i, (p1, p2) in enumerate(zip(segment1.coordinates, segment2.coordinates)):
            # Use tolerance based on precision (6 decimal places = 1e-6 tolerance)
            tolerance = 1e-5  # Slightly larger to account for rounding
            assert abs(p1.x - p2.x) < tolerance, \
                f"Point {i} x-coordinate mismatch: {p1.x} != {p2.x} (diff: {abs(p1.x - p2.x)})"
            assert abs(p1.y - p2.y) < tolerance, \
                f"Point {i} y-coordinate mismatch: {p1.y} != {p2.y} (diff: {abs(p1.y - p2.y)})"
    
    @given(valid_wkt_linestring(), st.integers(min_value=0, max_value=10))
    def test_round_trip_with_various_precisions(self, wkt_string, precision):
        """
        Feature: cartographic-displacement, Property 4: Round-trip consistency
        Validates: Requirements 1.5
        
        Test that round-trip consistency holds for various precision settings.
        """
        parser = WKTParser()
        printer = WKTPrettyPrinter(precision=precision)
        
        # Parse original WKT
        segment1 = parser.parse_linestring(wkt_string)
        
        # Format to WKT
        formatted_wkt = printer.format_segment(segment1)
        
        # Parse formatted WKT
        parser.reset_id_counter()
        segment2 = parser.parse_linestring(formatted_wkt)
        
        # Verify coordinates match within precision tolerance
        tolerance = 10 ** (-precision) * 10  # Tolerance based on precision
        
        for i, (p1, p2) in enumerate(zip(segment1.coordinates, segment2.coordinates)):
            assert abs(p1.x - p2.x) < tolerance, \
                f"Point {i} x-coordinate mismatch at precision {precision}: {p1.x} != {p2.x}"
            assert abs(p1.y - p2.y) < tolerance, \
                f"Point {i} y-coordinate mismatch at precision {precision}: {p1.y} != {p2.y}"
    
    @given(st.lists(valid_wkt_linestring(), min_size=1, max_size=10))
    def test_round_trip_network_consistency(self, wkt_strings):
        """
        Feature: cartographic-displacement, Property 4: Round-trip consistency
        Validates: Requirements 1.5
        
        Test that round-trip consistency holds for entire networks.
        """
        parser = WKTParser()
        printer = WKTPrettyPrinter(precision=6)
        
        # Parse all segments
        segments1 = [parser.parse_linestring(wkt) for wkt in wkt_strings]
        
        # Format network
        formatted_wkt = printer.format_network(segments1)
        
        # Parse formatted network
        parser.reset_id_counter()
        formatted_lines = formatted_wkt.strip().split('\n')
        segments2 = [parser.parse_linestring(line) for line in formatted_lines]
        
        # Verify segment count matches
        assert len(segments1) == len(segments2), \
            f"Segment count mismatch: {len(segments1)} != {len(segments2)}"
        
        # Verify each segment matches
        tolerance = 1e-5
        for seg_idx, (seg1, seg2) in enumerate(zip(segments1, segments2)):
            assert len(seg1.coordinates) == len(seg2.coordinates), \
                f"Segment {seg_idx} coordinate count mismatch"
            
            for pt_idx, (p1, p2) in enumerate(zip(seg1.coordinates, seg2.coordinates)):
                assert abs(p1.x - p2.x) < tolerance, \
                    f"Segment {seg_idx}, point {pt_idx} x-coordinate mismatch"
                assert abs(p1.y - p2.y) < tolerance, \
                    f"Segment {seg_idx}, point {pt_idx} y-coordinate mismatch"
    
    @given(valid_wkt_linestring())
    def test_round_trip_preserves_geometry_type(self, wkt_string):
        """
        Feature: cartographic-displacement, Property 4: Round-trip consistency
        Validates: Requirements 1.5
        
        Test that round-trip preserves geometry type (LINESTRING).
        """
        parser = WKTParser()
        printer = WKTPrettyPrinter(precision=6)
        
        # Parse original WKT
        segment1 = parser.parse_linestring(wkt_string)
        
        # Format to WKT
        formatted_wkt = printer.format_segment(segment1)
        
        # Verify formatted WKT starts with LINESTRING
        assert formatted_wkt.upper().startswith("LINESTRING"), \
            f"Formatted WKT should start with LINESTRING: {formatted_wkt}"
        
        # Parse formatted WKT
        parser.reset_id_counter()
        segment2 = parser.parse_linestring(formatted_wkt)
        
        # Verify both have same geometry type
        assert segment1.shapely_geom.geom_type == segment2.shapely_geom.geom_type, \
            "Geometry type should be preserved"
        assert segment1.shapely_geom.geom_type == "LineString", \
            "Geometry type should be LineString"


class TestCoordinatePrecisionConsistency:
    """Property-based tests for coordinate precision consistency."""
    
    @given(valid_wkt_linestring(), st.integers(min_value=1, max_value=10))
    def test_coordinate_precision_consistency(self, wkt_string, precision):
        """
        Feature: cartographic-displacement, Property 18: Coordinate precision consistency
        Validates: Requirements 6.3
        
        Test that all coordinates in formatted output have consistent decimal places.
        """
        parser = WKTParser()
        printer = WKTPrettyPrinter(precision=precision)
        
        # Parse and format
        segment = parser.parse_linestring(wkt_string)
        formatted_wkt = printer.format_segment(segment)
        
        # Extract all coordinate values from formatted WKT
        # Pattern matches numbers like: 123.456 or -123.456
        coord_pattern = r'-?\d+\.\d+'
        coordinates = re.findall(coord_pattern, formatted_wkt)
        
        # Verify all coordinates have the same number of decimal places
        for coord_str in coordinates:
            decimal_part = coord_str.split('.')[1]
            assert len(decimal_part) == precision, \
                f"Coordinate {coord_str} should have {precision} decimal places, got {len(decimal_part)}"
    
    @given(st.lists(valid_wkt_linestring(), min_size=1, max_size=10), 
           st.integers(min_value=1, max_value=10))
    def test_network_precision_consistency(self, wkt_strings, precision):
        """
        Feature: cartographic-displacement, Property 18: Coordinate precision consistency
        Validates: Requirements 6.3
        
        Test that all coordinates in a network have consistent precision.
        """
        parser = WKTParser()
        printer = WKTPrettyPrinter(precision=precision)
        
        # Parse all segments
        segments = [parser.parse_linestring(wkt) for wkt in wkt_strings]
        
        # Format network
        formatted_wkt = printer.format_network(segments)
        
        # Extract all coordinate values
        coord_pattern = r'-?\d+\.\d+'
        coordinates = re.findall(coord_pattern, formatted_wkt)
        
        # Verify all coordinates have consistent precision
        for coord_str in coordinates:
            decimal_part = coord_str.split('.')[1]
            assert len(decimal_part) == precision, \
                f"All coordinates should have {precision} decimal places, but {coord_str} has {len(decimal_part)}"
    
    @given(valid_wkt_linestring())
    def test_default_precision_is_six(self, wkt_string):
        """
        Feature: cartographic-displacement, Property 18: Coordinate precision consistency
        Validates: Requirements 6.3
        
        Test that default precision is 6 decimal places.
        """
        parser = WKTParser()
        printer = WKTPrettyPrinter()  # Default precision
        
        # Parse and format
        segment = parser.parse_linestring(wkt_string)
        formatted_wkt = printer.format_segment(segment)
        
        # Extract all coordinate values
        coord_pattern = r'-?\d+\.\d+'
        coordinates = re.findall(coord_pattern, formatted_wkt)
        
        # Verify all coordinates have 6 decimal places
        for coord_str in coordinates:
            decimal_part = coord_str.split('.')[1]
            assert len(decimal_part) == 6, \
                f"Default precision should be 6, but {coord_str} has {len(decimal_part)} decimal places"
    
    @given(valid_wkt_linestring(), st.integers(min_value=1, max_value=10))
    def test_precision_setting_is_respected(self, wkt_string, precision):
        """
        Feature: cartographic-displacement, Property 18: Coordinate precision consistency
        Validates: Requirements 6.3
        
        Test that the precision setting is respected in output.
        """
        parser = WKTParser()
        printer = WKTPrettyPrinter(precision=precision)
        
        # Verify printer has correct precision
        assert printer.precision == precision, \
            f"Printer precision should be {precision}, got {printer.precision}"
        
        # Parse and format
        segment = parser.parse_linestring(wkt_string)
        formatted_wkt = printer.format_segment(segment)
        
        # Extract all coordinate values
        coord_pattern = r'-?\d+\.\d+'
        coordinates = re.findall(coord_pattern, formatted_wkt)
        
        # Verify precision is respected
        assert len(coordinates) > 0, "Should have extracted some coordinates"
        for coord_str in coordinates:
            decimal_part = coord_str.split('.')[1]
            assert len(decimal_part) == precision, \
                f"Precision {precision} not respected: {coord_str} has {len(decimal_part)} decimal places"
    
    @given(valid_wkt_linestring(min_points=10, max_points=20), 
           st.integers(min_value=1, max_value=10))
    def test_precision_consistency_long_linestring(self, wkt_string, precision):
        """
        Feature: cartographic-displacement, Property 18: Coordinate precision consistency
        Validates: Requirements 6.3
        
        Test precision consistency for LINESTRING with many points.
        """
        parser = WKTParser()
        printer = WKTPrettyPrinter(precision=precision)
        
        # Parse and format
        segment = parser.parse_linestring(wkt_string)
        formatted_wkt = printer.format_segment(segment)
        
        # Extract all coordinate values
        coord_pattern = r'-?\d+\.\d+'
        coordinates = re.findall(coord_pattern, formatted_wkt)
        
        # Should have at least 20 coordinates (10 points * 2 coords per point)
        assert len(coordinates) >= 20, \
            f"Long LINESTRING should have many coordinates, got {len(coordinates)}"
        
        # Verify all have consistent precision
        for coord_str in coordinates:
            decimal_part = coord_str.split('.')[1]
            assert len(decimal_part) == precision, \
                f"Coordinate {coord_str} should have {precision} decimal places"
