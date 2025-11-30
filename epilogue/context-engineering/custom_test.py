#!/usr/bin/env python3
"""
Configurable test runner - easily adjust what gets tested.
Edit the configuration section below to customize your test run.
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the test module
import test_models

# ============================================================================
# CONFIGURATION - Edit these to customize your test run
# ============================================================================

# Choose which models to test (comment out to skip)
MODELS = [
    {"name": "gpt-oss:20b", "size": "14GB", "context": "128K"},
    {"name": "deepseek-r1:latest", "size": "5.2GB", "context": "128K"},
    {"name": "qwen3:latest", "size": "5.2GB", "context": "40K"},
]

# Choose which versions to test (comment out to skip)
VERSIONS = [
    "v1",
    "v2",
    "v3",
]

# Choose which queries to test (comment out to skip)
QUERIES = [
    "best pizza places in Chicago",
    "best pizza places in Chicago and what reviewers said",
    "best pizza places in Chicago and website information",
]

# ============================================================================
# END CONFIGURATION
# ============================================================================

# Override the test configuration
test_models.MODELS_TO_TEST = MODELS
test_models.VERSIONS = VERSIONS
test_models.TEST_QUERIES = QUERIES

# Calculate test count
total_tests = len(MODELS) * len(VERSIONS) * len(QUERIES)

print("=" * 80)
print("🧪 Custom Test Configuration")
print("=" * 80)
print(f"Models: {len(MODELS)}")
for model in MODELS:
    print(f"  - {model['name']}")
print(f"\nVersions: {len(VERSIONS)}")
for version in VERSIONS:
    print(f"  - {version}")
print(f"\nQueries: {len(QUERIES)}")
for i, query in enumerate(QUERIES, 1):
    print(f"  {i}. {query}")
print(f"\nTotal tests: {total_tests}")
print("=" * 80)

# Ask for confirmation
if total_tests > 10:
    response = input("\nThis will run many tests. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)

# Run the tests
test_models.main()
