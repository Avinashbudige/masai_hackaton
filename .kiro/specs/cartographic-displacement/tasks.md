# Implementation Plan: Cartographic Displacement System

## Overview

This implementation plan breaks down the cartographic displacement system into incremental coding tasks. Each task builds on previous work, with property-based tests integrated throughout to validate correctness early. The system will parse WKT street network data, detect spatial conflicts, apply displacement transformations using energy minimization, and output the adjusted geometry while preserving topology.

## Tasks

- [ ] 1. Set up project structure and core data models
  - Create Python package structure with `src/cartographic_displacement/` directory
  - Implement core data models: `Point`, `Vector2D`, `LineSegment`, `IntersectionPoint`, `Conflict`, `DisplacementConfig`
  - Set up testing framework (pytest) and property-based testing library (Hypothesis)
  - Create `requirements.txt` with dependencies: shapely>=2.0, numpy, matplotlib, scipy, hypothesis, pytest
  - _Requirements: 1.1, 1.3, 2.2, 3.1, 4.1, 5.1_

- [ ]* 1.1 Write property test for data model invariants
  - **Property: Data model consistency**
  - **Validates: Requirements 1.1, 1.3**
  - Test that Point distance calculations are symmetric and satisfy triangle inequality
  - Test that Vector2D normalization produces unit vectors
  - Test that LineSegment length is always non-negative

- [ ] 2. Implement WKT Parser component
  - [ ] 2.1 Create `WKTParser` class with `parse_file()` and `parse_linestring()` methods
    - Use regex to extract LINESTRING geometries from file
    - Leverage Shapely's `wkt.loads()` for parsing
    - Convert Shapely LineString to internal `LineSegment` representation
    - Handle multi-line WKT strings
    - _Requirements: 1.1, 1.2_
  
  - [ ]* 2.2 Write property test for valid WKT parsing
    - **Property 1: Valid WKT parsing**
    - **Validates: Requirements 1.1**
    - Generate random valid WKT LINESTRING strings
    - Verify all parse successfully without errors
  
  - [ ]* 2.3 Write property test for invalid WKT error handling
    - **Property 2: Invalid WKT error handling**
    - **Validates: Requirements 1.2**
    - Generate malformed WKT strings (missing keywords, invalid coordinates)
    - Verify descriptive error messages are returned

- [ ] 3. Implement Pretty Printer component
  - [ ] 3.1 Create `WKTPrettyPrinter` class with `format_segment()` and `format_network()` methods
    - Use Shapely's `wkt` property for formatting
    - Apply configurable coordinate precision
    - Preserve segment ordering
    - Implement `write_file()` method with error handling
    - _Requirements: 1.4, 6.1, 6.2, 6.3, 6.5_
  
  - [ ]* 3.2 Write property test for round-trip consistency
    - **Property 4: Round-trip consistency**
    - **Validates: Requirements 1.5**
    - Generate random internal geometry objects
    - Verify parse → print → parse produces equivalent geometry
  
  - [ ]* 3.3 Write property test for coordinate precision consistency
    - **Property 18: Coordinate precision consistency**
    - **Validates: Requirements 6.3**
    - Generate random geometries and format with various precision settings
    - Verify all coordinates have consistent decimal places

- [ ] 4. Checkpoint - Ensure parsing and serialization tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement Network Graph component
  - [ ] 5.1 Create `NetworkGraph` class with topology extraction
    - Build spatial hash map for finding shared endpoints
    - Implement `get_intersections()` to identify intersection points
    - Implement `get_connected_segments()` and `get_adjacent_segments()`
    - Build R-tree spatial index using Shapely's STRtree
    - _Requirements: 1.3, 2.2, 4.1, 4.3_
  
  - [ ]* 5.2 Write property test for intersection extraction completeness
    - **Property 3: Intersection extraction completeness**
    - **Validates: Requirements 1.3**
    - Generate random networks with known intersection points
    - Verify all shared endpoints are identified as intersections
  
  - [ ]* 5.3 Write unit tests for adjacency relationships
    - Test that adjacent segments are correctly identified
    - Test edge cases: single segment, disconnected segments
    - _Requirements: 1.3_

- [ ] 6. Implement Conflict Detector component
  - [ ] 6.1 Create `ConflictDetector` class with spatial conflict detection
    - Implement `detect_conflicts()` using R-tree for candidate pairs
    - Use Shapely's `distance()` for actual distance calculation
    - Exclude adjacent segments from conflicts
    - Store conflict locations and required displacement
    - Implement `get_conflict_zones()` for visualization
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ]* 6.2 Write property test for minimum distance validation
    - **Property 5: Minimum distance validation**
    - **Validates: Requirements 2.1**
    - Test with positive, negative, and zero distance values
    - Verify validation behavior
  
  - [ ]* 6.3 Write property test for conflict detection correctness
    - **Property 6: Conflict detection correctness**
    - **Validates: Requirements 2.2, 2.4**
    - Generate networks with known conflicts
    - Verify all conflicts are detected and reported with segment IDs
  
  - [ ]* 6.4 Write property test for adjacent segment exclusion
    - **Property 7: Adjacent segment exclusion**
    - **Validates: Requirements 2.3**
    - Generate networks with adjacent segments
    - Verify adjacent pairs never appear in conflict list

- [ ] 7. Checkpoint - Ensure conflict detection tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement Displacement Engine component
  - [ ] 8.1 Create `DisplacementEngine` class with energy minimization
    - Implement energy function (internal + external energy)
    - Implement perpendicular offset strategy using Shapely's `offset_curve()`
    - Implement iterative optimization using scipy.optimize.minimize
    - Apply displacement constraints (max_displacement)
    - Implement displacement propagation along connected segments
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 5.2_
  
  - [ ] 8.2 Implement angular adjustment and hybrid strategies
    - Add angular rotation displacement strategy
    - Add hybrid strategy combining perpendicular and angular
    - _Requirements: 3.5_
  
  - [ ]* 8.3 Write property test for multi-conflict resolution
    - **Property 8: Multi-conflict resolution**
    - **Validates: Requirements 3.3**
    - Generate segments with multiple conflicts
    - Verify all conflicts are resolved after displacement
  
  - [ ]* 8.4 Write property test for displacement vector application
    - **Property 9: Displacement vector application**
    - **Validates: Requirements 3.4**
    - Calculate displacement vectors and apply them
    - Verify displaced geometry matches expected offset
  
  - [ ]* 8.5 Write property test for maximum displacement constraint
    - **Property 14: Maximum displacement constraint**
    - **Validates: Requirements 5.2**
    - Apply displacement with max_displacement limits
    - Verify no segment moves more than maximum

- [ ] 9. Implement Topology Validator component
  - [ ] 9.1 Create `TopologyValidator` class with connectivity verification
    - Implement `validate()` to check topology preservation
    - Implement `check_connectivity()` for intersection verification
    - Compare intersection counts and adjacency relationships
    - Generate detailed validation reports with broken connections
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 9.2 Write property test for intersection connectivity preservation
    - **Property 10: Intersection connectivity preservation**
    - **Validates: Requirements 4.1**
    - Generate networks with intersections
    - Verify connected segments remain connected after displacement
  
  - [ ]* 9.3 Write property test for intersection count invariant
    - **Property 11: Intersection count invariant**
    - **Validates: Requirements 4.3**
    - Displace random networks
    - Verify intersection count is preserved
  
  - [ ]* 9.4 Write property test for topology validation error reporting
    - **Property 12: Topology validation error reporting**
    - **Validates: Requirements 4.4**
    - Create displacements that break connectivity
    - Verify validator reports broken connections
  
  - [ ]* 9.5 Write property test for segment ordering preservation
    - **Property 13: Segment ordering preservation at intersections**
    - **Validates: Requirements 4.5**
    - Verify angular ordering of segments at intersections is preserved
    - _Requirements: 4.5_

- [ ] 10. Checkpoint - Ensure displacement and topology tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement Visualizer component
  - [ ] 11.1 Create `Visualizer` class with Matplotlib plotting
    - Implement `plot_network()` for single network visualization
    - Implement `plot_comparison()` for before/after side-by-side
    - Implement `plot_displacement_vectors()` with arrows
    - Add conflict zone highlighting
    - Support saving plots to file (PNG, PDF)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ]* 11.2 Write unit tests for visualization generation
    - Test that plots are created without errors
    - Test file saving functionality
    - _Requirements: 7.1, 7.2, 7.4, 7.5_

- [ ] 12. Implement main application and CLI
  - [ ] 12.1 Create main application orchestrator
    - Implement end-to-end workflow: parse → detect → displace → validate → output
    - Add configuration loading from file or command-line arguments
    - Implement progress indicators for long operations
    - Add comprehensive error handling with clear messages
    - _Requirements: 5.1, 5.3, 5.4, 5.5, 8.5_
  
  - [ ] 12.2 Create command-line interface
    - Use argparse for CLI argument parsing
    - Support input file, output file, and configuration parameters
    - Add help text and usage examples
    - _Requirements: 5.1, 5.3, 5.4, 6.4_
  
  - [ ]* 12.3 Write property test for parameter validation
    - **Property 15: Parameter validation**
    - **Validates: Requirements 5.5**
    - Test with invalid parameter combinations
    - Verify validation errors are reported before processing

- [ ] 13. Implement error handling and edge cases
  - [ ] 13.1 Add comprehensive error handling
    - Implement `DisplacementError` dataclass for structured errors
    - Add file I/O error handling (not found, permissions, disk space)
    - Add degenerate geometry handling (zero-length segments)
    - Add graceful degradation for unresolvable conflicts
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [ ]* 13.2 Write property test for file not found error handling
    - **Property 20: File not found error handling**
    - **Validates: Requirements 8.1**
    - Test with non-existent file paths
    - Verify clear error messages without crashes
  
  - [ ]* 13.3 Write property test for no-conflict handling
    - **Property 21: No-conflict handling**
    - **Validates: Requirements 8.2**
    - Generate networks with no conflicts
    - Verify successful completion with zero conflicts reported
  
  - [ ]* 13.4 Write property test for unresolved conflict reporting
    - **Property 22: Unresolved conflict reporting**
    - **Validates: Requirements 8.3**
    - Create scenarios where constraints prevent full resolution
    - Verify unresolved conflicts are reported

- [ ] 14. Integration testing with real-world data
  - [ ] 14.1 Create integration test using streets_ugen.wkt
    - Load the provided WKT file
    - Run full displacement pipeline
    - Verify output is valid and topology is preserved
    - Generate before/after visualizations
    - _Requirements: All_
  
  - [ ]* 14.2 Write integration tests for end-to-end workflow
    - Test complete pipeline with various network configurations
    - Test with different displacement strategies
    - Test with various parameter combinations
    - _Requirements: All_

- [ ] 15. Write property tests for output properties
  - [ ]* 15.1 Write property test for WKT output validity
    - **Property 16: WKT output validity**
    - **Validates: Requirements 6.1**
    - Generate random displaced networks
    - Verify output is valid WKT that can be parsed
  
  - [ ]* 15.2 Write property test for segment ordering preservation
    - **Property 17: Segment ordering preservation**
    - **Validates: Requirements 6.2**
    - Verify output segment order matches input order
  
  - [ ]* 15.3 Write property test for file write error safety
    - **Property 19: File write error safety**
    - **Validates: Requirements 6.5**
    - Simulate file write failures
    - Verify existing files remain unchanged

- [ ] 16. Final checkpoint and documentation
  - [ ] 16.1 Ensure all tests pass
    - Run full test suite (unit + property + integration)
    - Verify all 22 correctness properties are tested
    - Check test coverage
  
  - [ ] 16.2 Create README with usage examples
    - Document installation instructions
    - Provide CLI usage examples
    - Include example with streets_ugen.wkt file
    - Document configuration parameters
  
  - [ ] 16.3 Add code documentation
    - Add docstrings to all public methods
    - Document energy function parameters
    - Document displacement strategies
    - Add inline comments for complex algorithms

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples and edge cases
- The real-world data file (streets_ugen.wkt) is used for integration testing
- All property tests should include the tag comment: `# Feature: cartographic-displacement, Property {N}: {title}`
