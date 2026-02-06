"""
Unit tests for WKT Parser component.

Tests the parsing of WKT LINESTRING geometries from strings and files.
"""

import pytest
import tempfile
import os
from pathlib import Path

from cartographic_displacement import WKTParser, WKTParseError, LineSegment, Point


class TestWKTParser:
    """Test suite for WKTParser class."""
    
    def test_parse_simple_linestring(self):
        """Test parsing a simple valid LINESTRING."""
        parser = WKTParser()
        wkt = "LINESTRING (0 0, 1 1, 2 0)"
        
        segment = parser.parse_linestring(wkt)
        
        assert isinstance(segment, LineSegment)
        assert segment.id == 0
        assert len(segment.coordinates) == 3
        assert segment.coordinates[0] == Point(0, 0)
        assert segment.coordinates[1] == Point(1, 1)
        assert segment.coordinates[2] == Point(2, 0)
    
    def test_parse_linestring_case_insensitive(self):
        """Test that parsing is case-insensitive."""
        parser = WKTParser()
        wkt_lower = "linestring (0 0, 1 1)"
        wkt_upper = "LINESTRING (0 0, 1 1)"
        wkt_mixed = "LineString (0 0, 1 1)"
        
        seg1 = parser.parse_linestring(wkt_lower)
        parser.reset_id_counter()
        seg2 = parser.parse_linestring(wkt_upper)
        parser.reset_id_counter()
        seg3 = parser.parse_linestring(wkt_mixed)
        
        assert len(seg1.coordinates) == len(seg2.coordinates) == len(seg3.coordinates)
        assert seg1.coordinates[0] == seg2.coordinates[0] == seg3.coordinates[0]
    
    def test_parse_linestring_with_whitespace(self):
        """Test parsing LINESTRING with various whitespace."""
        parser = WKTParser()
        wkt = "LINESTRING  (  0  0  ,  1  1  ,  2  0  )"
        
        segment = parser.parse_linestring(wkt)
        
        assert len(segment.coordinates) == 3
        assert segment.coordinates[0] == Point(0, 0)
    
    def test_parse_linestring_multiline(self):
        """Test parsing LINESTRING with coordinates on multiple lines."""
        parser = WKTParser()
        wkt = """LINESTRING (
            0 0,
            1 1,
            2 0
        )"""
        
        segment = parser.parse_linestring(wkt)
        
        assert len(segment.coordinates) == 3
        assert segment.coordinates[0] == Point(0, 0)
        assert segment.coordinates[2] == Point(2, 0)
    
    def test_parse_linestring_with_decimals(self):
        """Test parsing LINESTRING with decimal coordinates."""
        parser = WKTParser()
        wkt = "LINESTRING (0.5 1.25, 2.75 3.125, 4.0 5.5)"
        
        segment = parser.parse_linestring(wkt)
        
        assert len(segment.coordinates) == 3
        assert segment.coordinates[0] == Point(0.5, 1.25)
        assert segment.coordinates[1] == Point(2.75, 3.125)
        assert segment.coordinates[2] == Point(4.0, 5.5)
    
    def test_parse_linestring_with_negative_coords(self):
        """Test parsing LINESTRING with negative coordinates."""
        parser = WKTParser()
        wkt = "LINESTRING (-10 -20, 0 0, 10 20)"
        
        segment = parser.parse_linestring(wkt)
        
        assert segment.coordinates[0] == Point(-10, -20)
        assert segment.coordinates[1] == Point(0, 0)
        assert segment.coordinates[2] == Point(10, 20)
    
    def test_parse_linestring_invalid_keyword(self):
        """Test that invalid geometry type raises error."""
        parser = WKTParser()
        wkt = "POLYGON ((0 0, 1 1, 2 0, 0 0))"
        
        with pytest.raises(WKTParseError) as exc_info:
            parser.parse_linestring(wkt)
        
        assert "Expected 'LINESTRING'" in str(exc_info.value)
    
    def test_parse_linestring_empty_string(self):
        """Test that empty string raises error."""
        parser = WKTParser()
        
        with pytest.raises(WKTParseError) as exc_info:
            parser.parse_linestring("")
        
        assert "Expected 'LINESTRING'" in str(exc_info.value)
    
    def test_parse_linestring_unbalanced_parentheses(self):
        """Test that unbalanced parentheses raise error."""
        parser = WKTParser()
        wkt = "LINESTRING (0 0, 1 1"
        
        with pytest.raises(WKTParseError) as exc_info:
            parser.parse_linestring(wkt)
        
        assert "Unbalanced parentheses" in str(exc_info.value)
    
    def test_parse_linestring_too_few_points(self):
        """Test that LINESTRING with only 1 point raises error."""
        parser = WKTParser()
        wkt = "LINESTRING (0 0)"
        
        with pytest.raises(WKTParseError) as exc_info:
            parser.parse_linestring(wkt)
        
        assert "at least 2 points" in str(exc_info.value)
    
    def test_parse_linestring_empty_coords(self):
        """Test that LINESTRING EMPTY raises error."""
        parser = WKTParser()
        wkt = "LINESTRING EMPTY"
        
        with pytest.raises(WKTParseError) as exc_info:
            parser.parse_linestring(wkt)
        
        assert "empty" in str(exc_info.value).lower()
    
    def test_parse_linestring_invalid_coordinates(self):
        """Test that invalid coordinate format raises error."""
        parser = WKTParser()
        wkt = "LINESTRING (0 0, abc def, 2 0)"
        
        with pytest.raises(WKTParseError) as exc_info:
            parser.parse_linestring(wkt)
        
        assert "Invalid WKT syntax" in str(exc_info.value)
    
    def test_parse_linestring_missing_comma(self):
        """Test that missing comma between coordinates raises error."""
        parser = WKTParser()
        wkt = "LINESTRING (0 0 1 1 2 0)"
        
        with pytest.raises(WKTParseError) as exc_info:
            parser.parse_linestring(wkt)
        
        # This should be caught by Shapely as invalid syntax
        assert "Invalid" in str(exc_info.value)
    
    def test_segment_id_increments(self):
        """Test that segment IDs increment correctly."""
        parser = WKTParser()
        
        seg1 = parser.parse_linestring("LINESTRING (0 0, 1 1)")
        seg2 = parser.parse_linestring("LINESTRING (2 2, 3 3)")
        seg3 = parser.parse_linestring("LINESTRING (4 4, 5 5)")
        
        assert seg1.id == 0
        assert seg2.id == 1
        assert seg3.id == 2
    
    def test_reset_id_counter(self):
        """Test that ID counter can be reset."""
        parser = WKTParser()
        
        seg1 = parser.parse_linestring("LINESTRING (0 0, 1 1)")
        assert seg1.id == 0
        
        parser.reset_id_counter()
        
        seg2 = parser.parse_linestring("LINESTRING (2 2, 3 3)")
        assert seg2.id == 0
    
    def test_parse_file_simple(self):
        """Test parsing a simple file with multiple LINESTRING entries."""
        parser = WKTParser()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.wkt') as f:
            f.write("LINESTRING (0 0, 1 1, 2 0)\n")
            f.write("LINESTRING (3 3, 4 4, 5 3)\n")
            f.write("LINESTRING (6 6, 7 7)\n")
            temp_path = f.name
        
        try:
            segments = parser.parse_file(temp_path)
            
            assert len(segments) == 3
            assert segments[0].id == 0
            assert segments[1].id == 1
            assert segments[2].id == 2
            assert len(segments[0].coordinates) == 3
            assert len(segments[1].coordinates) == 3
            assert len(segments[2].coordinates) == 2
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_multiline_coordinates(self):
        """Test parsing file with multi-line coordinate lists."""
        parser = WKTParser()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.wkt') as f:
            f.write("""LINESTRING (
                0 0,
                1 1,
                2 0
            )
            LINESTRING (
                3 3,
                4 4
            )""")
            temp_path = f.name
        
        try:
            segments = parser.parse_file(temp_path)
            
            assert len(segments) == 2
            assert len(segments[0].coordinates) == 3
            assert len(segments[1].coordinates) == 2
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_with_comments_and_whitespace(self):
        """Test parsing file with extra whitespace (comments not supported by WKT)."""
        parser = WKTParser()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.wkt') as f:
            f.write("\n\n")
            f.write("LINESTRING (0 0, 1 1)\n")
            f.write("\n")
            f.write("LINESTRING (2 2, 3 3)\n")
            f.write("\n\n")
            temp_path = f.name
        
        try:
            segments = parser.parse_file(temp_path)
            
            assert len(segments) == 2
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_not_found(self):
        """Test that non-existent file raises FileNotFoundError."""
        parser = WKTParser()
        
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.parse_file("/nonexistent/path/to/file.wkt")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_parse_file_empty(self):
        """Test that empty file raises error."""
        parser = WKTParser()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.wkt') as f:
            # Write nothing
            temp_path = f.name
        
        try:
            with pytest.raises(WKTParseError) as exc_info:
                parser.parse_file(temp_path)
            
            assert "No valid LINESTRING" in str(exc_info.value)
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_no_linestrings(self):
        """Test that file with no LINESTRING geometries raises error."""
        parser = WKTParser()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.wkt') as f:
            f.write("POINT (0 0)\n")
            f.write("POLYGON ((0 0, 1 1, 1 0, 0 0))\n")
            temp_path = f.name
        
        try:
            with pytest.raises(WKTParseError) as exc_info:
                parser.parse_file(temp_path)
            
            assert "No valid LINESTRING" in str(exc_info.value)
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_with_invalid_linestring(self):
        """Test that file with invalid LINESTRING raises error with line number."""
        parser = WKTParser()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.wkt') as f:
            f.write("LINESTRING (0 0, 1 1)\n")
            f.write("LINESTRING (2 2, abc def)\n")  # Invalid
            f.write("LINESTRING (3 3, 4 4)\n")
            temp_path = f.name
        
        try:
            with pytest.raises(WKTParseError) as exc_info:
                parser.parse_file(temp_path)
            
            error_msg = str(exc_info.value)
            assert "Line" in error_msg  # Should include line number
            assert "Invalid WKT syntax" in error_msg
        finally:
            os.unlink(temp_path)
    
    def test_shapely_geometry_created(self):
        """Test that Shapely geometry is properly created."""
        parser = WKTParser()
        wkt = "LINESTRING (0 0, 1 1, 2 0)"
        
        segment = parser.parse_linestring(wkt)
        
        assert segment.shapely_geom is not None
        assert segment.shapely_geom.geom_type == "LineString"
        assert segment.shapely_geom.length > 0
    
    def test_segment_length_calculation(self):
        """Test that segment length is calculated correctly."""
        parser = WKTParser()
        wkt = "LINESTRING (0 0, 3 4)"  # 3-4-5 triangle, length = 5
        
        segment = parser.parse_linestring(wkt)
        
        assert abs(segment.length() - 5.0) < 1e-6
