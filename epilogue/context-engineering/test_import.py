#!/usr/bin/env python3
"""Quick test to verify the import mechanism works."""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the test module functions
from test_models import import_version_graph, TEST_QUERIES

print("Testing graph import mechanism...")
print("=" * 60)

# Test v1
print("\nTesting v1 import:")
graph_v1 = import_version_graph("v1", "gpt-oss:20b")
if graph_v1:
    print("✅ v1 graph loaded successfully")
else:
    print("❌ v1 graph failed to load")

# Test v2
print("\nTesting v2 import:")
graph_v2 = import_version_graph("v2", "gpt-oss:20b")
if graph_v2:
    print("✅ v2 graph loaded successfully")
else:
    print("❌ v2 graph failed to load")

# Test v3
print("\nTesting v3 import:")
graph_v3 = import_version_graph("v3", "gpt-oss:20b")
if graph_v3:
    print("✅ v3 graph loaded successfully")
else:
    print("❌ v3 graph failed to load")

print("\n" + "=" * 60)
print("Import test complete!")
