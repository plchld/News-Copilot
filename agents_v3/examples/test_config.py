"""
Test configuration for agents_v3 examples
"""

# Category selection for single-category tests
TEST_CATEGORY = "technology"  # Options: greek_political, greek_economic, international_political, international_economic, science, technology

# Story limits for testing
MAX_STORIES_PER_CATEGORY = 3  # Set to None for all 10 stories

# Concurrency settings
MAX_CONCURRENT_STORIES = 2  # How many stories to process in parallel

# Debug settings
VERBOSE_LOGGING = True  # Show detailed progress
SAVE_RESULTS = True  # Save results to JSON files

# Mock data for testing without API calls
USE_MOCK_DATA = False  # Set to True to test architecture without API calls

# Performance testing
MEASURE_PERFORMANCE = True  # Track timing and resource usage