"""
Basic usage example for cartographic displacement core data models.

This example demonstrates how to create and use the core data models:
Point, Vector2D, LineSegment, IntersectionPoint, Conflict, and DisplacementConfig.
"""

from cartographic_displacement import (
    Point,
    Vector2D,
    LineSegment,
    IntersectionPoint,
    Conflict,
    DisplacementConfig,
)


def main():
    print("=" * 60)
    print("Cartographic Displacement System - Basic Usage Example")
    print("=" * 60)
    
    # 1. Create Points
    print("\n1. Creating Points:")
    p1 = Point(0.0, 0.0)
    p2 = Point(10.0, 0.0)
    p3 = Point(10.0, 10.0)
    print(f"   Point 1: ({p1.x}, {p1.y})")
    print(f"   Point 2: ({p2.x}, {p2.y})")
    print(f"   Point 3: ({p3.x}, {p3.y})")
    print(f"   Distance from P1 to P2: {p1.distance_to(p2):.2f}")
    
    # 2. Create Vectors
    print("\n2. Creating Vectors:")
    v1 = Vector2D(3.0, 4.0)
    print(f"   Vector: ({v1.dx}, {v1.dy})")
    print(f"   Magnitude: {v1.magnitude():.2f}")
    normalized = v1.normalize()
    print(f"   Normalized: ({normalized.dx:.2f}, {normalized.dy:.2f})")
    print(f"   Normalized magnitude: {normalized.magnitude():.2f}")
    
    # 3. Create Line Segments
    print("\n3. Creating Line Segments:")
    segment1 = LineSegment(
        id=1,
        coordinates=[Point(0.0, 0.0), Point(10.0, 0.0), Point(10.0, 10.0)]
    )
    segment2 = LineSegment(
        id=2,
        coordinates=[Point(0.0, 5.0), Point(10.0, 5.0)]
    )
    print(f"   Segment 1 (ID={segment1.id}): {len(segment1.coordinates)} points, length={segment1.length():.2f}")
    print(f"   Segment 2 (ID={segment2.id}): {len(segment2.coordinates)} points, length={segment2.length():.2f}")
    
    # 4. Create Intersection Point
    print("\n4. Creating Intersection Point:")
    intersection = IntersectionPoint(
        location=Point(10.0, 0.0),
        connected_segment_ids=[1, 3, 5]
    )
    print(f"   Location: ({intersection.location.x}, {intersection.location.y})")
    print(f"   Connected segments: {intersection.connected_segment_ids}")
    print(f"   Degree (number of connections): {intersection.degree()}")
    
    # 5. Create Conflict
    print("\n5. Creating Conflict:")
    conflict = Conflict(
        segment1=segment1,
        segment2=segment2,
        min_distance_point1=Point(5.0, 0.0),
        min_distance_point2=Point(5.0, 5.0),
        actual_distance=5.0,
        required_displacement=5.0
    )
    print(f"   Conflict between segments {conflict.segment1.id} and {conflict.segment2.id}")
    print(f"   Actual distance: {conflict.actual_distance:.2f}")
    print(f"   Required displacement: {conflict.required_displacement:.2f}")
    
    # 6. Create Displacement Configuration
    print("\n6. Creating Displacement Configuration:")
    config = DisplacementConfig(
        min_distance=10.0,
        max_displacement=50.0,
        strategy="perpendicular",
        energy_alpha=0.3,
        energy_beta=0.7
    )
    print(f"   Minimum distance: {config.min_distance}")
    print(f"   Maximum displacement: {config.max_displacement}")
    print(f"   Strategy: {config.strategy}")
    print(f"   Energy weights: α={config.energy_alpha}, β={config.energy_beta}")
    print(f"   Max iterations: {config.max_iterations}")
    print(f"   Convergence threshold: {config.convergence_threshold}")
    
    # 7. Demonstrate perpendicular vector calculation
    print("\n7. Perpendicular Vector Calculation:")
    perp = segment1.get_perpendicular_vector(Point(5.0, 0.0))
    print(f"   Perpendicular to segment 1 at (5.0, 0.0): ({perp.dx:.2f}, {perp.dy:.2f})")
    print(f"   Perpendicular magnitude: {perp.magnitude():.2f}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
