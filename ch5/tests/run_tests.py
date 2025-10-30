#!/usr/bin/env python3
"""
Test runner for all custom Haystack components in the scripts folder.

This script runs all tests for the custom components and provides a summary of results.
"""

import sys
import os
import importlib.util
from pathlib import Path

# Add the scripts directory to the Python path
# Tests are in ch5/tests/, scripts are in ch5/jupyter-notebooks/scripts/
current_dir = Path(__file__).parent  # ch5/tests/
project_root = current_dir.parent    # ch5/
scripts_dir = project_root / "jupyter-notebooks" / "scripts"
sys.path.insert(0, str(scripts_dir))

def run_test_file(test_file_path):
    """Run tests from a specific test file."""
    print(f"\n{'='*60}")
    print(f"Running tests from: {test_file_path.name}")
    print(f"{'='*60}")
    
    try:
        # Import and run the test file
        spec = importlib.util.spec_from_file_location("test_module", test_file_path)
        test_module = importlib.util.module_from_spec(spec)
        
        # Add the test module to sys.modules to handle imports correctly
        sys.modules["test_module"] = test_module
        spec.loader.exec_module(test_module)
        
        print(f"✅ Tests in {test_file_path.name} completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error running tests in {test_file_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner function."""
    print("🧪 Running Custom Component Tests for Chapter 5")
    print("=" * 60)
    
    # Find all test files in the tests directory
    tests_dir = Path(__file__).parent
    test_files = list(tests_dir.glob("test_*.py"))
    
    if not test_files:
        print("No test files found in the scripts directory.")
        return
    
    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    
    # Run each test file
    results = {}
    for test_file in test_files:
        results[test_file.name] = run_test_file(test_file)
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_file, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_file:40} {status}")
    
    print(f"\nOverall: {passed}/{total} test files passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)