"""
WKT Parser component for reading LINESTRING geometries.

This module provides functionality to parse Well-Known Text (WKT) format
LINESTRING geometries from files and convert them to internal LineSegment
representations.
"""

import re
from typing import List, Optional
from shapely import wkt
from shapely.geometry import LineString
from shapely.errors import WKTReadingError

from .models import LineSegment, Point


class WKTParseError(Exception):
    """Exception raised when WKT parsing fails."""
    
    def __init__(self, message: str, line_number: Optional[int] = None, 
                 wkt_string: Optional[str] = None):
        """
        Initialize WKT parse error.
        
        Args:
            message: Human-readable error description
            line_number: Line number where error occurred (if parsing from file)
            wkt_string: The problematic WKT string
        """
        self.message = message
        self.line_number = line_number
        self.wkt_string = wkt_string
        
        error_msg = message
        if line_number is not None:
            error_msg = f"Line {line_number}: {message}"
        if wkt_string:
            # Truncate long strings for readability
            truncated = wkt_string[:100] + "..." if len(wkt_string) > 100 else wkt_string
            error_msg += f"\nProblematic WKT: {truncated}"
        
        super().__init__(error_msg)


class WKTParser:
    """
    Parser for WKT LINESTRING geometries.
    
    This class handles parsing of WKT format LINESTRING data from files
    and individual strings, converting them to internal LineSegment objects.
    """
    
    # Regex pattern to extract LINESTRING geometries
    # Matches LINESTRING(...) including multi-line coordinate lists
    LINESTRING_PATTERN = re.compile(
        r'LINESTRING\s*\(\s*([^)]+)\s*\)',
        re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    
    def __init__(self):
        """Initialize the WKT parser."""
        self._segment_id_counter = 0
    
    def parse_file(self, filepath: str) -> List[LineSegment]:
        """
        Parse WKT file and return list of line segments.
        
        This method reads a file containing WKT LINESTRING geometries and
        converts each one to a LineSegment object. The file can contain
        multiple LINESTRING entries, and coordinates can span multiple lines.
        
        Args:
            filepath: Path to the WKT file
            
        Returns:
            List of LineSegment objects parsed from the file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If the file cannot be read
            WKTParseError: If WKT parsing fails
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"WKT file not found: {filepath}\n"
                f"Please check that the file exists and the path is correct."
            )
        except IOError as e:
            raise IOError(
                f"Cannot read WKT file: {filepath}\n"
                f"Error: {str(e)}"
            )
        
        # Find all LINESTRING geometries in the file
        matches = self.LINESTRING_PATTERN.finditer(content)
        
        segments = []
        line_numbers = {}  # Track line numbers for error reporting
        
        # Build a map of character positions to line numbers
        lines = content.split('\n')
        char_pos = 0
        for line_num, line in enumerate(lines, start=1):
            for i in range(len(line) + 1):  # +1 for newline
                line_numbers[char_pos] = line_num
                char_pos += 1
        
        for match in matches:
            wkt_string = match.group(0)
            line_num = line_numbers.get(match.start(), None)
            
            try:
                segment = self.parse_linestring(wkt_string)
                segments.append(segment)
            except WKTParseError as e:
                # Re-raise with line number information
                raise WKTParseError(e.message, line_number=line_num, wkt_string=wkt_string)
        
        if not segments:
            raise WKTParseError(
                "No valid LINESTRING geometries found in file. "
                "Expected format: LINESTRING (x1 y1, x2 y2, ...)"
            )
        
        return segments
    
    def parse_linestring(self, wkt_string: str) -> LineSegment:
        """
        Parse single WKT LINESTRING to LineSegment object.
        
        This method converts a WKT LINESTRING string to an internal
        LineSegment representation. It uses Shapely for the actual WKT
        parsing and then converts to our internal format.
        
        Args:
            wkt_string: WKT LINESTRING string (e.g., "LINESTRING (0 0, 1 1, 2 0)")
            
        Returns:
            LineSegment object representing the parsed geometry
            
        Raises:
            WKTParseError: If the WKT string is invalid or malformed
        """
        # Clean up the string
        wkt_string = wkt_string.strip()
        
        # Validate basic format
        if not wkt_string.upper().startswith('LINESTRING'):
            raise WKTParseError(
                f"Expected 'LINESTRING' but found '{wkt_string.split()[0] if wkt_string else 'empty string'}'",
                wkt_string=wkt_string
            )
        
        # Check for balanced parentheses
        if wkt_string.count('(') != wkt_string.count(')'):
            raise WKTParseError(
                "Unbalanced parentheses in WKT string",
                wkt_string=wkt_string
            )
        
        try:
            # Use Shapely to parse the WKT
            geom = wkt.loads(wkt_string)
            
            # Verify it's a LineString
            if not isinstance(geom, LineString):
                raise WKTParseError(
                    f"Expected LINESTRING but got {geom.geom_type}",
                    wkt_string=wkt_string
                )
            
            # Check for valid geometry
            if geom.is_empty:
                raise WKTParseError(
                    "LINESTRING is empty (no coordinates)",
                    wkt_string=wkt_string
                )
            
            if len(geom.coords) < 2:
                raise WKTParseError(
                    f"LINESTRING must have at least 2 points, got {len(geom.coords)}",
                    wkt_string=wkt_string
                )
            
            # Convert Shapely LineString to internal representation
            coordinates = [Point(x, y) for x, y in geom.coords]
            
            # Create LineSegment with auto-incremented ID
            segment = LineSegment(
                id=self._get_next_id(),
                coordinates=coordinates,
                shapely_geom=geom
            )
            
            return segment
            
        except WKTReadingError as e:
            # Shapely couldn't parse the WKT
            raise WKTParseError(
                f"Invalid WKT syntax: {str(e)}",
                wkt_string=wkt_string
            )
        except ValueError as e:
            # Other validation errors
            raise WKTParseError(
                f"Invalid geometry: {str(e)}",
                wkt_string=wkt_string
            )
    
    def _get_next_id(self) -> int:
        """
        Get the next segment ID.
        
        Returns:
            Next available segment ID
        """
        segment_id = self._segment_id_counter
        self._segment_id_counter += 1
        return segment_id
    
    def reset_id_counter(self):
        """Reset the segment ID counter to 0."""
        self._segment_id_counter = 0
