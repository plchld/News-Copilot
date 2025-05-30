# agents_v3 Test Suite

This directory contains test scripts for the parallel news intelligence pipeline.

## Quick Start

```bash
# Set your API keys
export ANTHROPIC_API_KEY="your-key"
export GEMINI_API_KEY="your-key"

# Run a simple test
python run_test.py
```

## Available Tests

### 1. Simple Test Runner (`run_test.py`)
Quickest way to test with configurable settings:

```bash
# Uses settings from test_config.py
python run_test.py
```

### 2. Single Category Test (`test_single_category.py`)
Test with detailed output and performance testing:

```bash
python test_single_category.py
# Option 1: Test single category
# Option 2: Performance test with different batch sizes
```

### 3. Single Story Test (`test_single_story.py`)
Deep dive into processing one story:

```bash
python test_single_story.py
# Option 1: Real story discovery
# Option 2: Mock story (no API calls)
```

### 4. Full Pipeline Test (`run_daily_analysis.py`)
Run the complete pipeline with all categories:

```bash
python run_daily_analysis.py
```

## Specialized Test Scripts

### `test_single_story.py`
Deep dive into processing a single story:

```bash
python test_single_story.py
# Option 1: Real story discovery
# Option 2: Mock story (faster)
```

### `test_one_category.py`
Test citation propagation with one category:

```bash
python test_one_category.py
```

### `test_parallel_orchestrator.py`
Architecture validation test:

```bash
python test_parallel_orchestrator.py
```

## Configuration

Edit `test_config.py` to change default settings:

```python
# Category for single tests
TEST_CATEGORY = "technology"

# Story limits
MAX_STORIES_PER_CATEGORY = 3  # None for all 10

# Concurrency
MAX_CONCURRENT_STORIES = 2  # Parallel processing batch size
```

## Categories Available

- `greek_political` - Greek Political News
- `greek_economic` - Greek Economic News
- `international_political` - International Political News
- `international_economic` - International Economic News
- `science` - Science News
- `technology` - Technology News

## Understanding the Output

### Parallel Processing
- Stories processed in configurable batches
- Each story gets its own dedicated agents
- Complete isolation between story analyses
- No context contamination

### Citations
The system tracks citations from:
- Greek context agent searches
- International context agent searches (when relevance ≥ 7)
- Fact-check verification searches

All citations are passed to the synthesis agent for the final Greek narrative.

## Troubleshooting

### No API Keys
```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export GEMINI_API_KEY="your-gemini-key"
```

### Rate Limits
Reduce concurrent processing:
```python
# In test_config.py
MAX_CONCURRENT_STORIES = 1
```

### Memory Issues
Reduce batch size:
```python
MAX_CONCURRENT_STORIES = 1
```

## Performance Tips

1. Start with single category tests
2. Use mock tests to verify architecture
3. Limit stories for initial testing
4. Monitor API usage with parallel processing
5. Save results with `SAVE_RESULTS = True`