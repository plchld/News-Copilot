#!/usr/bin/env python
"""
Test runner script for News Copilot
"""
import sys
import subprocess
import os


def run_tests():
    """Run all tests with coverage report"""
    print("Running News Copilot tests...")
    print("-" * 50)
    
    # Set environment variables for testing
    os.environ['TESTING'] = 'true'
    
    # Run pytest with coverage
    result = subprocess.run([
        sys.executable, '-m', 'pytest',
        '--cov=api',
        '--cov-report=term-missing',
        '--cov-report=html',
        '-v'
    ])
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
        print("\nCoverage report generated in htmlcov/index.html")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


def run_specific_test(test_path):
    """Run a specific test file or test case"""
    print(f"Running specific test: {test_path}")
    print("-" * 50)
    
    result = subprocess.run([
        sys.executable, '-m', 'pytest',
        test_path,
        '-v'
    ])
    
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        exit_code = run_specific_test(sys.argv[1])
        sys.exit(exit_code)
    else:
        # Run all tests
        run_tests()