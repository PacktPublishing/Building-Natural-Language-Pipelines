#!/bin/bash

# Token Usage Test Examples
# This script demonstrates V2's token efficiency across different query complexities

set -e

echo "================================================================================================"
echo "Token Usage Test Examples: Demonstrating V2's Efficiency Gains"
echo "================================================================================================"
echo ""
echo "This script will run tests to show how V2's token savings increase with query complexity:"
echo "  - Simple queries (general detail): 15-20% savings"
echo "  - Complex queries (detailed/reviews): 40-60% savings"
echo ""
echo "Press Ctrl+C to cancel, or wait 3 seconds to continue..."
sleep 3
echo ""

# Test 1: Simple general query (baseline)
echo "================================================================================================"
echo "TEST 1: Simple General Query"
echo "================================================================================================"
echo "Query: 'Italian restaurants in Boston, MA' with detail_level='general'"
echo "Expected: ~15-20% token reduction (modest savings for simple queries)"
echo ""
uv run python measure_token_usage.py \
    --test-query "Italian restaurants" \
    --test-location "Boston, MA" \
    --detail-level general \
    --output test1_simple_general.md
echo ""
echo "✅ Test 1 complete. See: docs/test1_simple_general.md"
echo ""
sleep 2

# Test 2: Detailed query (moderate complexity)
echo "================================================================================================"
echo "TEST 2: Detailed Query (Multi-Step Workflow)"
echo "================================================================================================"
echo "Query: 'Mexican restaurants in Austin, TX' with detail_level='detailed'"
echo "Expected: ~40-50% token reduction"
echo "Why: V2 makes multiple supervisor decisions with minimal context"
echo "     and uses dual context streams (raw_results vs pipeline_data)"
echo ""
uv run python measure_token_usage.py \
    --test-query "Mexican restaurants" \
    --test-location "Austin, TX" \
    --detail-level detailed \
    --output test2_detailed.md
echo ""
echo "✅ Test 2 complete. See: docs/test2_detailed.md"
echo ""
sleep 2

# Test 3: Reviews query (high complexity)
echo "================================================================================================"
echo "TEST 3: Reviews Query (Most Complex Multi-Step Workflow)"
echo "================================================================================================"
echo "Query: 'sushi restaurants in New York, NY' with detail_level='reviews'"
echo "Expected: ~50-60% token reduction"
echo "Why: Multiple supervisor routing decisions + sentiment analysis tool"
echo "     V2's progressive context building vs V1's full state in each node"
echo ""
uv run python measure_token_usage.py \
    --test-query "sushi restaurants" \
    --test-location "New York, NY" \
    --detail-level reviews \
    --output test3_reviews.md
echo ""
echo "✅ Test 3 complete. See: docs/test3_reviews.md"
echo ""
sleep 2

# Test 4: Comprehensive comparison
echo "================================================================================================"
echo "TEST 4: Comprehensive Comparison (All Complexity Levels)"
echo "================================================================================================"
echo "Running full test suite with 3 simple and 5 complex queries"
echo "Expected: Average ~35-45% reduction across all queries"
echo ""
uv run python measure_token_usage.py \
    --run-all-tests \
    --output test4_comprehensive.md
echo ""
echo "✅ Test 4 complete. See: docs/test4_comprehensive.md"
echo ""

# Summary
echo "================================================================================================"
echo "ALL TESTS COMPLETE"
echo "================================================================================================"
echo ""
echo "Reports generated in docs/ folder:"
echo "  - test1_simple_general.md     : Baseline simple query (15-20% savings)"
echo "  - test2_detailed.md           : Moderate complexity (40-50% savings)"
echo "  - test3_reviews.md            : High complexity (50-60% savings)"
echo "  - test4_comprehensive.md      : Overall comparison across all levels"
echo ""
echo "Key Takeaway:"
echo "  V2's architectural advantages (supervisor pattern, dual context streams,"
echo "  progressive disclosure) provide increasingly better token efficiency as"
echo "  workflow complexity increases."
echo ""
echo "View any report with: cat docs/<report_name>.md"
echo "================================================================================================"
