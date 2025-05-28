# Debug Tools for News-Copilot

This folder contains comprehensive debugging and testing tools for the News-Copilot agent system.

## 🔧 Core Debug Tools

### API Endpoint Analysis
- **`debug_grok_endpoint.py`** - Complete Grok API diagnostic tool
  - Tests connectivity, model availability, live search, thinking models
  - Analyzes performance, rate limits, and error handling
  - Usage: `python debug/debug_grok_endpoint.py`

- **`debug_grok_region.py`** - Regional endpoint detection
  - Determines if connected to US East/West or CDN routing
  - Analyzes latency patterns, DNS resolution, network routes
  - Identifies Cloudflare CDN usage and regional performance
  - Usage: `python debug/debug_grok_region.py`

### Agent System Debugging
- **`debug_agents.py`** - Agent-specific debugging framework
  - Tests individual agents (jargon, viewpoints, fact-check, etc.)
  - Analyzes agent performance, output quality, and errors
  - Provides detailed timing and response analysis
  - Usage: `python debug/debug_agents.py`

- **`debug_framework.py`** - Structured debugging utilities
  - AgentDebugger class with multiple debug levels
  - Performance tracking, error analysis, output validation
  - Reusable debugging components for all agents

### Timeout Investigation
- **`debug_timeout_investigation.py`** - Timeout issue analysis
  - Tests individual agents vs coordinator execution
  - Identifies bottlenecks in the analysis pipeline
  - Provides detailed timing breakdowns
  - Usage: `python debug/debug_timeout_investigation.py`

## 🧪 Test Scripts

### Basic Testing
- **`test_simple_analysis.py`** - Simple agent functionality test
- **`test_basic_analysis.py`** - Basic analysis pipeline test
- **`test_grok_api.py`** - Direct Grok API testing
- **`test_async_issue.py`** - Async functionality testing

### Agent-Specific Tests
- **`test_viewpoints_direct.py`** - Direct ViewpointsAgent testing
- **`test_viewpoints_server.py`** - ViewpointsAgent via server testing
- **`test_viewpoints_simple.py`** - Minimal viewpoints test
- **`test_debug_viewpoints.py`** - Comprehensive viewpoints debugging

### Server Integration Tests
- **`test_server_viewpoints.py`** - Server-side viewpoints testing
- **`test_debug_endpoint.py`** - Debug endpoint testing

### Performance Tests
- **`test_timeout_fix.py`** - Timeout fix validation
  - Tests optimized ViewpointsAgent performance
  - Validates timeout improvements and model changes

## 🌐 Web Interface
- **`debug.html`** - Debug web interface
  - Accessible at `/debug` when server is running
  - Interactive debugging tools and agent testing
  - Real-time performance monitoring

## 📊 Output Files
- **`debug_output.txt`** - Sample debug output and logs

## 🚀 Quick Start

### 1. Test API Connectivity
```bash
python debug/debug_grok_endpoint.py
```

### 2. Check Regional Performance
```bash
python debug/debug_grok_region.py
```

### 3. Debug Specific Agent
```bash
python debug/debug_agents.py
```

### 4. Investigate Timeouts
```bash
python debug/debug_timeout_investigation.py
```

### 5. Test Viewpoints Fix
```bash
python debug/test_timeout_fix.py
```

## 🔍 Common Issues & Solutions

### Viewpoints Not Showing
- Run `test_viewpoints_direct.py` to test agent directly
- Check `test_viewpoints_server.py` for server integration
- Use `debug_agents.py` for comprehensive analysis

### Timeout Issues
- Use `debug_timeout_investigation.py` to identify bottlenecks
- Check `test_timeout_fix.py` for validation of fixes
- Monitor performance with `debug_grok_region.py`

### API Errors
- Run `debug_grok_endpoint.py` for complete API analysis
- Check for `response_format` parameter issues (not supported by Grok)
- Validate model availability and rate limits

### Performance Issues
- Use `debug_grok_region.py` to check CDN routing
- Monitor latency patterns during different times
- Test concurrent load with endpoint diagnostics

## 📝 Debug Levels

The debug framework supports multiple levels:
- **ERROR**: Critical issues only
- **WARNING**: Important issues and errors
- **INFO**: General information and progress
- **DEBUG**: Detailed debugging information
- **TRACE**: Maximum verbosity for deep debugging

## 🛠️ Development Tips

1. **Always test individual agents first** before testing the full pipeline
2. **Use the web debug interface** for interactive testing
3. **Monitor regional performance** if experiencing latency issues
4. **Check API endpoint status** before investigating agent issues
5. **Validate JSON parsing** when agents return unexpected results

## 📚 Related Documentation

- See `../docs/` for comprehensive system documentation
- Check `../api/agents/` for agent implementation details
- Review `../tests/` for additional test suites 