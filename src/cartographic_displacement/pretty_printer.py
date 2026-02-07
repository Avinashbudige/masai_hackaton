"""
WKT Pretty Printer component for formatting LINESTRING geometries.

This module provides functionality to format internal LineSegment representations
back to Well-Known Text (WKT) format with configurable precision and proper
formatting.
"""

import os
from typing import List, Union
from shapely.geometry import LineString

from .models import LineSegment


class WKTPrettyPrinter:
    """
    Pretty printer for WKT LINESTRING geometries.
    
    This class handles formatting of internal LineSegment objects back to
    WKT LINESTRING format with configurable coordinate precision and proper
    formatting conventions.
    """
    
    def __init__(self, precision: int = 6):
        """
        Initialize the WKT pretty printer.
        
        Args:
            precision: Number of decimal places for coordinate formatting (default: 6)
            
        Raises:
            ValueError: If precision is negative
        """
        if precision < 0:
            raise ValueError(f"Precision cannot be negative, got {precision}")
        self.precision = precision
    
    def format_segment(self, segment: LineSegment) -> str:
        """
        Format single segment as WKT LINESTRING.
        
        This method converts a LineSegment object to a WKT LINESTRING string
        with the configured coordinate precision.
        
        Args:
            segment: The LineSegment to format
            
        Returns:
            WKT LINESTRING string representation
            
        Raises:
            ValueError: If segment has invalid geometry
        """
        if segment.shapely_geom is None or segment.shapely_geom.is_empty:
            raise ValueError(f"Cannot format empty or invalid segment (ID: {segment.id})")
        
        if len(segment.coordinates) < 2:
            raise ValueError(
                f"Segment must have at least 2 points, got {len(segment.coordinates)} "
                f"(ID: {segment.id})"
            )
        
        # Format coordinates with specified precision
        coords_str = ", ".join(
            f"{coord[0]:.{self.precision}f} {coord[1]:.{self.precision}f}"
            for coord in segment.shapely_geom.coords
        )
        
        return f"LINESTRING ({coords_str})"
    
    def format_network(self, segments: List[LineSegment]) -> str:
        """
        Format entire network as WKT.
        
        This method formats a list of LineSegment objects as a multi-line
        WKT string, with one LINESTRING per line. Segment ordering is preserved.
        
        Args:
            segments: List of LineSegment objects to format
            
        Returns:
            Multi-line WKT string with one LINESTRING per line
            
        Raises:
            ValueError: If segments list is empty or contains invalid segments
        """
        if not segments:
            raise ValueError("Cannot format empty network (no segments provided)")
        
        # Format each segment and join with newlines
        wkt_lines = []
        for segment in segments:
            try:
                wkt_line = self.format_segment(segment)
                wkt_lines.append(wkt_line)
            except ValueError as e:
                # Re-raise with more context
                raise ValueError(f"Error formatting segment {segment.id}: {str(e)}")
        
        return "\n".join(wkt_lines)
    
    def write_file(self, segments: Union[List[LineSegment], LineSegment], 
                   filepath: str) -> None:
        """
        Write network to WKT file.
        
        This method writes LineSegment objects to a file in WKT format.
        The file is written atomically using a temporary file to prevent
        corruption of existing files in case of errors.
        
        Args:
            segments: LineSegment or list of LineSegment objects to write
            filepath: Path to the output file
            
        Raises:
            ValueError: If segments are invalid
            IOError: If file cannot be written
            PermissionError: If lacking write permissions
        """
        # Handle single segment or list of segments
        if isinstance(segments, LineSegment):
            segments = [segments]
        
        # Format the network
        try:
            wkt_content = self.format_network(segments)
        except ValueError as e:
            raise ValueError(f"Cannot write invalid geometry to file: {str(e)}")
        
        # Ensure the content ends with a newline
        if not wkt_content.endswith('\n'):
            wkt_content += '\n'
        
        # Write to temporary file first for atomic operation
        temp_filepath = filepath + '.tmp'
        
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except OSError as e:
                    raise IOError(
                        f"Cannot create directory for output file: {directory}\n"
                        f"Error: {str(e)}"
                    )
            
            # Write to temporary file
            try:
                with open(temp_filepath, 'w', encoding='utf-8') as f:
                    f.write(wkt_content)
            except PermissionError:
                raise PermissionError(
                    f"Permission denied: Cannot write to {filepath}\n"
                    f"Please check file permissions and try again."
                )
            except IOError as e:
                raise IOError(
                    f"Cannot write to file: {filepath}\n"
                    f"Error: {str(e)}"
                )
            
            # Atomic rename (replaces existing file if present)
            try:
                # On Windows, need to remove target file first if it exists
                if os.path.exists(filepath):
                    os.remove(filepath)
                os.rename(temp_filepath, filepath)
            except OSError as e:
                # Clean up temp file if rename fails
                if os.path.exists(temp_filepath):
                    try:
                        os.remove(temp_filepath)
                    except:
                        pass
                raise IOError(
                    f"Cannot write to file: {filepath}\n"
                    f"Error during file operation: {str(e)}"
                )
                
        except Exception as e:
            # Clean up temp file on any error
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except:
                    pass
            raise
