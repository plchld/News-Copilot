# Rate Limiting Updates - Smart Usage Tracking

## Overview

This document describes the updates made to the rate limiting system to more intelligently track API usage. The key change is that only initial Grok API calls count against user rate limits, not conversation refinement calls made by the agent coordinator.

## Changes Made

### 1. Usage Logging in Routes

Added usage logging to both main endpoints:

- **`/augment-stream`**: Logs as `basic_analysis` after successful completion
- **`/deep-analysis`**: Logs the specific analysis type (fact-check, bias, timeline, expert, x-pulse)

The logging happens AFTER successful completion to ensure we only count successful analyses.

### 2. Agent System Updates

Modified `base_agent.py` to distinguish between:
- **Initial API calls**: First call to Grok API (counts against rate limits)
- **Refinement calls**: Follow-up calls with conversation history (NOT counted)

The agent now logs when making refinement calls so we can track this behavior.

### 3. Usage Statistics Categorization

Updated both `http_supabase.py` and `supabase_auth.py` to properly categorize analysis types:

**Basic Analysis** (counts against basic_analysis limit):
- `basic_analysis` - The augment-stream endpoint (jargon + viewpoints combined)
- `jargon`, `viewpoints` - Legacy support for old logs

**Deep Analysis** (counts against deep_analysis limit):
- `fact-check` - Fact checking analysis
- `bias` - Political bias analysis  
- `timeline` - Timeline construction
- `expert` - Expert opinions
- `x-pulse` - X (Twitter) discourse analysis

## How It Works

1. User makes a request to `/augment-stream` or `/deep-analysis`
2. The auth decorator checks current usage against limits BEFORE the request
3. If under limit, the analysis proceeds
4. Agents may make multiple Grok calls:
   - First call: Counts as usage
   - Refinement calls (with conversation history): NOT counted
5. After successful completion, usage is logged ONCE per request

## Benefits

- **More generous limits**: Users get full value from their monthly allowance
- **Quality improvements**: Agents can refine results without penalty
- **Fair pricing**: Only charging for initial analysis requests, not internal improvements
- **Better UX**: Users won't hit limits as quickly with the same usage patterns

## Testing

To test the new rate limiting:

1. Make requests and check the usage logs table
2. Verify only one log entry per request (not per Grok call)
3. Check that refinement calls show in logs but don't create usage entries
4. Confirm rate limits are enforced based on the new counting method