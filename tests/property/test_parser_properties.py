"""
Property-based tests for WKT Parser component.

Tests universal properties that should hold for all valid WKT LINESTRING inputs.
"""

import pytest
from hypothesis import given, strategies as st, assume

from src.cartographic_displacement.parser import WKTParser, WKTParseError
from src.cartographic_displacement.models import LineSegment, Point


# Custom strategies for generating valid WKT LINESTRING strings
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
    
    # Randomly choose case variation
    keyword = draw(st.sampled_from(["LINESTRING", "linestring", "LineString", "Linestring"]))
    
    # Randomly add extra whitespace
    space_before_paren = draw(st.sampled_from(["", " ", "  "]))
    space_after_paren = draw(st.sampled_from(["", " ", "  "]))
    space_before_close = draw(st.sampled_from(["", " ", "  "]))
    
    wkt = f"{keyword}{space_before_paren}({space_after_paren}{coord_list}{space_before_close})"
    
    return wkt, coords


class TestWKTParserProperties:
    """Property-based tests for WKT Parser."""
    
    @given(valid_wkt_linestring())
    def test_valid_wkt_parsing(self, wkt_data):
        """
        Feature: cartographic-displacement, Property 1: Valid WKT parsing
        Validates: Requirements 1.1
        
        Test that all randomly generated valid WKT LINESTRING strings parse successfully.
        This property verifies that the parser can handle any valid WKT format without errors.
        """
        wkt_string, expected_coords = wkt_data
        parser = WKTParser()
        
        # Should parse without raising an exception
        segment = parser.parse_linestring(wkt_string)
        
        # Verify the result is a LineSegment
        assert isinstance(segment, LineSegment), \
            f"Parser should return LineSegment, got {type(segment)}"
        
        # Verify the number of coordinates matches
        assert len(segment.coordinates) == len(expected_coords), \
            f"Expected {len(expected_coords)} coordinates, got {len(segment.coordinates)}"
        
        # Verify coordinates are parsed correctly (with floating point tolerance)
        for i, (expected_x, expected_y) in enumerate(expected_coords):
            actual_point = segment.coordinates[i]
            assert abs(actual_point.x - expected_x) < 1e-6, \
                f"Point {i} x-coordinate mismatch: expected {expected_x}, got {actual_point.x}"
            assert abs(actual_point.y - expected_y) < 1e-6, \
                f"Point {i} y-coordinate mismatch: expected {expected_y}, got {actual_point.y}"
    
    @given(valid_wkt_linestring())
    def test_parsed_segment_has_valid_id(self, wkt_data):
        """
        Feature: cartographic-displacement, Property 1: Valid WKT parsing
        Validates: Requirements 1.1
        
        Test that parsed segments have valid non-negative IDs.
        """
        wkt_string, _ = wkt_data
        parser = WKTParser()
        
        segment = parser.parse_linestring(wkt_string)
        
        assert segment.id >= 0, \
            f"Segment ID should be non-negative, got {segment.id}"
    
    @given(valid_wkt_linestring())
    def test_parsed_segment_has_shapely_geometry(self, wkt_data):
        """
        Feature: cartographic-displacement, Property 1: Valid WKT parsing
        Validates: Requirements 1.1
        
        Test that parsed segments have valid Shapely geometry objects.
        """
        wkt_string, _ = wkt_data
        parser = WKTParser()
        
        segment = parser.parse_linestring(wkt_string)
        
        assert segment.shapely_geom is not None, \
            "Parsed segment should have Shapely geometry"
        assert segment.shapely_geom.geom_type == "LineString", \
            f"Shapely geometry should be LineString, got {segment.shapely_geom.geom_type}"
        assert not segment.shapely_geom.is_empty, \
            "Shapely geometry should not be empty"
    
    @given(valid_wkt_linestring())
    def test_parsed_segment_length_non_negative(self, wkt_data):
        """
        Feature: cartographic-displacement, Property 1: Valid WKT parsing
        Validates: Requirements 1.1
        
        Test that parsed segments have non-negative length.
        """
        wkt_string, _ = wkt_data
        parser = WKTParser()
        
        segment = parser.parse_linestring(wkt_string)
        length = segment.length()
        
        assert length >= 0.0, \
            f"Segment length should be non-negative, got {length}"
    
    @given(valid_wkt_linestring(), valid_wkt_linestring())
    def test_id_counter_increments(self, wkt_data1, wkt_data2):
        """
        Feature: cartographic-displacement, Property 1: Valid WKT parsing
        Validates: Requirements 1.1
        
        Test that segment IDs increment correctly when parsing multiple segments.
        """
        wkt_string1, _ = wkt_data1
        wkt_string2, _ = wkt_data2
        parser = WKTParser()
        
        segment1 = parser.parse_linestring(wkt_string1)
        segment2 = parser.parse_linestring(wkt_string2)
        
        assert segment2.id == segment1.id + 1, \
            f"Second segment ID should be one more than first: {segment1.id} -> {segment2.id}"
    
    @given(valid_wkt_linestring())
    def test_reset_id_counter_works(self, wkt_data):
        """
        Feature: cartographic-displacement, Property 1: Valid WKT parsing
        Validates: Requirements 1.1
        
        Test that resetting the ID counter works correctly.
        """
        wkt_string, _ = wkt_data
        parser = WKTParser()
        
        # Parse a segment
        segment1 = parser.parse_linestring(wkt_string)
        first_id = segment1.id
        
        # Reset counter
        parser.reset_id_counter()
        
        # Parse another segment
        segment2 = parser.parse_linestring(wkt_string)
        
        assert segment2.id == 0, \
            f"After reset, ID should be 0, got {segment2.id}"
    
    @given(valid_wkt_linestring(min_points=2, max_points=2))
    def test_two_point_linestring_parsing(self, wkt_data):
        """
        Feature: cartographic-displacement, Property 1: Valid WKT parsing
        Validates: Requirements 1.1
        
        Test that minimal valid LINESTRING (2 points) parses correctly.
        """
        wkt_string, expected_coords = wkt_data
        parser = WKTParser()
        
        segment = parser.parse_linestring(wkt_string)
        
        assert len(segment.coordinates) == 2, \
            f"Two-point LINESTRING should have 2 coordinates, got {len(segment.coordinates)}"
        assert segment.length() >= 0.0, \
            "Two-point LINESTRING should have non-negative length"
    
    @given(valid_wkt_linestring(min_points=10, max_points=20))
    def test_long_linestring_parsing(self, wkt_data):
        """
        Feature: cartographic-displacement, Property 1: Valid WKT parsing
        Validates: Requirements 1.1
        
        Test that LINESTRING with many points parses correctly.
        """
        wkt_string, expected_coords = wkt_data
        parser = WKTParser()
        
        segment = parser.parse_linestring(wkt_string)
        
        assert len(segment.coordinates) >= 10, \
            f"Long LINESTRING should have at least 10 coordinates, got {len(segment.coordinates)}"
        assert len(segment.coordinates) == len(expected_coords), \
            "All coordinates should be preserved"


# Custom strategies for generating invalid WKT strings
@st.composite
def invalid_wkt_missing_keyword(draw):
    """Generate WKT strings with missing or wrong LINESTRING keyword."""
    coords = [(draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False)),
               draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False)))
              for _ in range(draw(st.integers(2, 5)))]
    coord_str = ", ".join([f"{x} {y}" for x, y in coords])
    
    # Generate various invalid keyword scenarios
    invalid_keyword = draw(st.sampled_from([
        "",  # Missing keyword entirely
        "LINE",  # Wrong keyword
        "POINT",  # Wrong geometry type
        "POLYGON",  # Wrong geometry type
        "LINSTRING",  # Typo
        "LINESRING",  # Typo
        "LINESTR",  # Incomplete
    ]))
    
    if invalid_keyword:
        return f"{invalid_keyword} ({coord_str})"
    else:
        return f"({coord_str})"


@st.composite
def invalid_wkt_missing_parentheses(draw):
    """Generate WKT strings with missing or unbalanced parentheses."""
    coords = [(draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False)),
               draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False)))
              for _ in range(draw(st.integers(2, 5)))]
    coord_str = ", ".join([f"{x} {y}" for x, y in coords])
    
    # Generate various parentheses errors
    paren_error = draw(st.sampled_from([
        "LINESTRING {coord_str}",  # Missing parentheses
        "LINESTRING ({coord_str}",  # Missing closing paren
        "LINESTRING {coord_str})",  # Missing opening paren
        "LINESTRING (({coord_str})",  # Extra opening paren
        "LINESTRING ({coord_str}))",  # Extra closing paren
    ]))
    
    return paren_error.format(coord_str=coord_str)


@st.composite
def invalid_wkt_bad_coordinates(draw):
    """Generate WKT strings with invalid coordinate formats."""
    
    # Generate various coordinate errors
    error_type = draw(st.sampled_from([
        "missing_y",  # Only x coordinate
        "non_numeric",  # Non-numeric values
        "too_many",  # More than 2 values per point
        "empty",  # Empty coordinate list
        "single_point",  # Only one point (need at least 2)
    ]))
    
    if error_type == "missing_y":
        # Generate coordinates with missing y values (at least one invalid)
        num_coords = draw(st.integers(2, 5))
        coords = []
        for i in range(num_coords):
            if i == 0:  # Ensure at least first one is invalid
                coords.append(str(draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False))))
            else:
                # Mix valid and invalid
                if draw(st.booleans()):
                    coords.append(str(draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False))))
                else:
                    coords.append(f"{draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False))} "
                                f"{draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False))}")
        coord_str = ", ".join(coords)
    elif error_type == "non_numeric":
        # Ensure at least one non-numeric coordinate
        num_coords = draw(st.integers(2, 5))
        coords = []
        invalid_added = False
        for i in range(num_coords):
            if i == 0 or not invalid_added:
                # Add invalid coordinate
                coords.append(draw(st.sampled_from(["abc def", "x y", "NaN NaN", "inf inf"])))
                invalid_added = True
            else:
                # Mix valid and invalid
                if draw(st.booleans()):
                    coords.append(f"{draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False))} "
                                f"{draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False))}")
                else:
                    coords.append(draw(st.sampled_from(["abc def", "x y", "NaN NaN", "inf inf"])))
        coord_str = ", ".join(coords)
    elif error_type == "too_many":
        # Generate coordinates with 3 or more values
        num_coords = draw(st.integers(2, 5))
        coords = [f"{draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False))} "
                  f"{draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False))} "
                  f"{draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False))}"
                  for _ in range(num_coords)]
        coord_str = ", ".join(coords)
    elif error_type == "empty":
        coord_str = ""
    else:  # single_point - only ONE point, not two
        coord_str = f"{draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False))} " \
                   f"{draw(st.floats(-1000, 1000, allow_nan=False, allow_infinity=False))}"
    
    return f"LINESTRING ({coord_str})"


@st.composite
def invalid_wkt_string(draw):
    """Generate various types of invalid WKT strings."""
    strategy = draw(st.sampled_from([
        invalid_wkt_missing_keyword(),
        invalid_wkt_missing_parentheses(),
        invalid_wkt_bad_coordinates(),
    ]))
    return draw(strategy)


class TestInvalidWKTErrorHandling:
    """Property-based tests for invalid WKT error handling."""
    
    @given(invalid_wkt_missing_keyword())
    def test_missing_keyword_error(self, invalid_wkt):
        """
        Feature: cartographic-displacement, Property 2: Invalid WKT error handling
        Validates: Requirements 1.2
        
        Test that WKT strings with missing or incorrect LINESTRING keyword
        raise WKTParseError with descriptive error messages.
        """
        parser = WKTParser()
        
        with pytest.raises(WKTParseError) as exc_info:
            parser.parse_linestring(invalid_wkt)
        
        error = exc_info.value
        # Verify error message is descriptive
        assert error.message is not None, "Error should have a message"
        assert len(error.message) > 0, "Error message should not be empty"
        # Should mention the expected keyword
        assert "LINESTRING" in error.message.upper() or "EXPECTED" in error.message.upper(), \
            f"Error message should mention expected keyword: {error.message}"
    
    @given(invalid_wkt_missing_parentheses())
    def test_missing_parentheses_error(self, invalid_wkt):
        """
        Feature: cartographic-displacement, Property 2: Invalid WKT error handling
        Validates: Requirements 1.2
        
        Test that WKT strings with missing or unbalanced parentheses
        raise WKTParseError with descriptive error messages.
        """
        parser = WKTParser()
        
        with pytest.raises(WKTParseError) as exc_info:
            parser.parse_linestring(invalid_wkt)
        
        error = exc_info.value
        # Verify error message is descriptive
        assert error.message is not None, "Error should have a message"
        assert len(error.message) > 0, "Error message should not be empty"
        # Should mention parentheses or syntax issue
        assert any(keyword in error.message.lower() for keyword in 
                  ["parenthes", "syntax", "invalid", "balanced"]), \
            f"Error message should mention syntax/parentheses issue: {error.message}"
    
    @given(invalid_wkt_bad_coordinates())
    def test_invalid_coordinates_error(self, invalid_wkt):
        """
        Feature: cartographic-displacement, Property 2: Invalid WKT error handling
        Validates: Requirements 1.2
        
        Test that WKT strings with invalid coordinate formats
        raise WKTParseError with descriptive error messages.
        """
        parser = WKTParser()
        
        with pytest.raises(WKTParseError) as exc_info:
            parser.parse_linestring(invalid_wkt)
        
        error = exc_info.value
        # Verify error message is descriptive
        assert error.message is not None, "Error should have a message"
        assert len(error.message) > 0, "Error message should not be empty"
        # Should mention coordinates, points, or syntax issue
        assert any(keyword in error.message.lower() for keyword in 
                  ["coordinate", "point", "syntax", "invalid", "empty", "must have"]), \
            f"Error message should mention coordinate/point issue: {error.message}"
    
    @given(invalid_wkt_string())
    def test_all_invalid_wkt_raises_error(self, invalid_wkt):
        """
        Feature: cartographic-displacement, Property 2: Invalid WKT error handling
        Validates: Requirements 1.2
        
        Test that all types of invalid WKT strings raise WKTParseError
        with descriptive error messages.
        """
        parser = WKTParser()
        
        with pytest.raises(WKTParseError) as exc_info:
            parser.parse_linestring(invalid_wkt)
        
        error = exc_info.value
        # Verify error has required attributes
        assert hasattr(error, 'message'), "Error should have 'message' attribute"
        assert error.message is not None, "Error message should not be None"
        assert len(error.message) > 0, "Error message should not be empty"
        
        # Verify error message is descriptive (not just generic)
        assert len(error.message) > 10, \
            f"Error message should be descriptive (>10 chars): {error.message}"
    
    @given(st.text(min_size=1, max_size=50))
    def test_random_text_raises_error(self, random_text):
        """
        Feature: cartographic-displacement, Property 2: Invalid WKT error handling
        Validates: Requirements 1.2
        
        Test that random non-WKT text raises WKTParseError with descriptive messages.
        """
        # Skip if by chance we generate something that looks like valid WKT
        if "LINESTRING" in random_text.upper() and "(" in random_text and ")" in random_text:
            return
        
        parser = WKTParser()
        
        with pytest.raises(WKTParseError) as exc_info:
            parser.parse_linestring(random_text)
        
        error = exc_info.value
        assert error.message is not None, "Error should have a message"
        assert len(error.message) > 0, "Error message should not be empty"
