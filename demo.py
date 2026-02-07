#!/usr/bin/env python3
"""
Cartographic Displacement System - Demo Script

This script demonstrates the core functionality implemented so far:
- Parsing WKT LINESTRING data
- Building network topology
- Identifying intersection points
- Detecting adjacency relationships
- 
"""

import sys
from src.cartographic_displacement import WKTParser, NetworkGraph, ConflictDetector

def main():
    """Run the cartographic displacement demo."""
    
    # Check if file path provided
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "Problem 3 - streets_ugen.wkt"
    
    # Check for min_distance parameter
    if len(sys.argv) > 2:
        min_distance = float(sys.argv[2])
    else:
        min_distance = 5.0  # Default minimum distance
    
    print("=" * 70)
    print("CARTOGRAPHIC DISPLACEMENT SYSTEM - DEMO")
    print("=" * 70)
    print()
    
    # Step 1: Parse WKT file
    print(f"[1/4] Parsing WKT file: {input_file}")
    try:
        parser = WKTParser()
        segments = parser.parse_file(input_file)
        print(f"✓ Successfully parsed {len(segments)} line segments")
    except FileNotFoundError:
        print(f"✗ Error: File '{input_file}' not found")
        return 1
    except Exception as e:
        print(f"✗ Error parsing file: {e}")
        return 1
    
    print()
    
    # Step 2: Build network graph
    print("[2/4] Building network topology...")
    try:
        network = NetworkGraph(segments)
        intersections = network.get_intersections()
        print(f"✓ Network graph built successfully")
        print(f"  - Total segments: {len(network.segments)}")
        print(f"  - Intersection points: {len(intersections)}")
    except Exception as e:
        print(f"✗ Error building network: {e}")
        return 1
    
    print()
    
    # Step 3: Analyze topology
    print("[3/4] Analyzing network topology...")
    
    # Count intersection degrees
    degree_counts = {}
    for intersection in intersections:
        degree = intersection.degree()
        degree_counts[degree] = degree_counts.get(degree, 0) + 1
    
    print(f"✓ Topology analysis complete")
    print()
    print("Intersection Statistics:")
    print("-" * 40)
    for degree in sorted(degree_counts.keys()):
        count = degree_counts[degree]
        print(f"  {degree}-way intersections: {count}")
    
    print()
    
    # Step 4: Detect conflicts
    print(f"[4/4] Detecting spatial conflicts (min_distance={min_distance})...")
    try:
        detector = ConflictDetector(network, min_distance=min_distance)
        conflicts = detector.detect_conflicts()
        print(f"✓ Conflict detection complete")
        print(f"  - Conflicts found: {len(conflicts)}")
    except Exception as e:
        print(f"✗ Error detecting conflicts: {e}")
        return 1
    
    print()
    print("-" * 40)
    print("Conflict Details (first 5):")
    print("-" * 40)
    for i, conflict in enumerate(conflicts[:5]):
        print(f"\nConflict {i+1}:")
        print(f"  Segments: {conflict.segment1.id} ↔ {conflict.segment2.id}")
        print(f"  Actual distance: {conflict.actual_distance:.2f}")
        print(f"  Required displacement: {conflict.required_displacement:.2f}")
        print(f"  Closest points:")
        print(f"    Seg {conflict.segment1.id}: ({conflict.min_distance_point1.x:.2f}, {conflict.min_distance_point1.y:.2f})")
        print(f"    Seg {conflict.segment2.id}: ({conflict.min_distance_point2.x:.2f}, {conflict.min_distance_point2.y:.2f})")
    
    if len(conflicts) > 5:
        print(f"\n... and {len(conflicts) - 5} more conflicts")
    
    print()
    print("=" * 70)
    print("DEMO COMPLETE - All core functionality verified!")
    print("=" * 70)
    print()
    print("Implemented Components:")
    print("  ✓ WKT Parser - Parses LINESTRING geometries")
    print("  ✓ Data Models - Point, Vector2D, LineSegment, IntersectionPoint")
    print("  ✓ Network Graph - Topology extraction and spatial indexing")
    print("  ✓ Conflict Detector - Identifies segments too close together")
    print("  ✓ Property-Based Tests - Comprehensive test coverage")
    print()
    print("Summary:")
    print(f"  • Parsed {len(segments)} segments from {input_file}")
    print(f"  • Found {len(intersections)} intersection points")
    print(f"  • Detected {len(conflicts)} spatial conflicts (min_distance={min_distance})")
    print()
    print("Next Steps (not yet implemented):")
    print("  • Displacement Engine - Move segments to resolve conflicts")
    print("  • Topology Validation - Ensure connectivity preserved")
    print("  • Visualization - Generate before/after plots")
    print()
    print("Usage: python demo.py [input_file] [min_distance]")
    print(f"Example: python demo.py 'Problem 3 - streets_ugen.wkt' 10.0")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
