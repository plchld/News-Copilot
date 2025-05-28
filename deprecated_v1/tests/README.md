# News-Copilot Test Suite

This directory contains the test suite for the News-Copilot project.

## Test Structure

### `unit/`
Unit tests for individual components and functions:
- `test_centralized_api.py` - Tests for centralized Grok API calling
- `test_grok_fix.py` - Tests for Grok API compatibility fixes
- `test_viewpoints_simple.py` - Simple ViewpointsAgent tests

### `integration/`
Integration tests for full system functionality:
- `test_optimized_architecture.py` - Main optimized architecture test suite
- `test_optimized_real.py` - Real API integration tests
- `test_async_live_search.py` - Async live search functionality tests
- `test_rate_limiting.py` - Rate limiting integration tests

### `performance/`
Performance and benchmarking tests:
- `test_parallel_execution.py` - Parallel vs sequential execution benchmarks

## Running Tests

### All Tests
```bash
python -m pytest tests/
```

### Specific Test Categories
```bash
# Unit tests only
python -m pytest tests/unit/

# Integration tests only
python -m pytest tests/integration/

# Performance tests only
python -m pytest tests/performance/
```

### Individual Test Files
```bash
# Run specific test file
python tests/unit/test_centralized_api.py

# Run with verbose output
python -m pytest tests/integration/test_optimized_architecture.py -v
```

## Test Requirements

- All tests require valid API keys in `.env`
- Integration tests require network access
- Performance tests may take longer to complete due to real API calls 