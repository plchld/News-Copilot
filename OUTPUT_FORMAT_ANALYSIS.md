# Output Format Analysis and UI Communication Mapping

## 1. Data Flow Architecture

```
Chrome Extension → Background.js → Flask API → Agent System → SSE Stream → UI Rendering
```

### Communication Patterns:
- **Basic Analysis (Jargon + Viewpoints)**: Uses SSE streaming via `/augment-stream`
- **Deep Analysis**: JSON responses via `/deep-analysis` 
- **Web Routes**: Alternative endpoints without auth using server API key

## 2. SSE Event Structure

```javascript
// Event types used:
event: progress
data: {"status": "message"}

event: final_result  
data: {complete JSON result}

event: error
data: {"message": "error message"}
```

## 3. Agent Output Schemas vs UI Expectations

### Jargon Agent
**Agent Output Schema:**
```json
{
  "terms": [
    {
      "term": "string",
      "explanation": "string"
    }
  ]
}
```
**UI Expectation:** ✅ Matches correctly

### Viewpoints Agent
**Agent Output Schema:**
```json
{
  "viewpoints": [
    {
      "perspective": "string",
      "argument": "string", 
      "source": "string"
    }
  ]
}
```
**UI Issues:**
- Legacy support expects plain text string
- New format expects structured JSON array
- UI has conditional handling for both formats

### Fact-Check Agent
**Agent Output Schema:**
```json
{
  "overall_credibility": "υψηλή|μέτρια|χαμηλή",
  "claims": [
    {
      "statement": "string",      // Agent returns this
      "verified": boolean,         // Agent returns this
      "explanation": "string",     // Agent returns this
      "sources": ["string"]
    }
  ],
  "red_flags": ["string"],
  "missing_context": "string"
}
```

**UI Expectation:**
```javascript
// UI expects these fields:
claim.statement     // ✅ Matches
claim.verified      // ✅ Matches  
claim.explanation   // ✅ Matches
claim.sources       // ✅ Matches

// UI also looks for (but agent doesn't provide):
data.source_quality // ❌ Missing - UI expects this object
```

### Bias Agent
**Agent Output Schema:**
```json
{
  "political_spectrum_analysis_greek": {
    "economic_axis_placement": "enum",
    "economic_axis_justification": "string",
    "social_axis_placement": "enum", 
    "social_axis_justification": "string",
    "overall_confidence": "enum"
  },
  "language_and_framing_analysis": {
    "emotionally_charged_terms": [
      {"term": "string", "explanation": "string"}
    ],
    "identified_framing_techniques": [
      {"technique_name": "string", "example_from_article": "string"}
    ],
    "detected_tone": "enum",
    "missing_perspectives_summary": "string"
  },
  "comparison": "string",
  "recommendations": "string"
}
```

**UI Expectation:**
```javascript
// UI expects these simplified fields:
data.political_lean     // ❌ Missing - needs mapping from spectrum analysis
data.emotional_tone     // ❌ Missing - needs mapping from detected_tone
data.confidence        // ❌ Missing - needs mapping from overall_confidence
data.language_analysis // ❌ Wrong structure - expects:
  - framing
  - loaded_words (array of strings)
  - missing_perspectives
```

### Timeline Agent
**Agent Output Schema:**
```json
{
  "story_title": "string",
  "events": [
    {
      "date": "string",
      "title": "string",
      "description": "string",
      "importance": "υψηλή|μέτρια|χαμηλή",
      "source": "string"
    }
  ],
  "context": "string",
  "future_implications": "string"
}
```
**UI Expectation:** ✅ Matches correctly

### Expert Opinions Agent
**Agent Output Schema:**
```json
{
  "topic_summary": "string",
  "experts": [
    {
      "name": "string",
      "credentials": "string",
      "opinion": "string",
      "quote": "string",
      "source": "string",
      "source_url": "string",
      "stance": "υποστηρικτική|αντίθετη|ουδέτερη"
    }
  ],
  "consensus": "string",
  "key_debates": "string"
}
```
**UI Expectation:** ✅ Matches correctly

### X Pulse Agent
**Agent Output Schema:**
```json
{
  "overall_discourse_summary": "string",
  "discussion_themes": [
    {
      "theme_title": "string",
      "theme_summary": "string",
      "representative_posts": [
        {
          "post_content": "string",
          "post_source_description": "string"
        }
      ],
      "sentiment_around_theme": "string"
    }
  ],
  "data_caveats": "string"
}
```
**UI Issues:**
- X Pulse rendering function not found in UI code
- Nested agent structure may need flattening
- Sub-agent results need proper aggregation

## 4. Critical Issues Identified

### 1. Schema Mismatches
- **Fact-Check**: UI expects `source_quality` object that agent doesn't provide
- **Bias Analysis**: Complete mismatch between complex agent schema and simplified UI expectations
- **X Pulse**: No UI handler found for this analysis type

### 2. Data Flow Issues
- **Citation Handling**: Agents don't return citations directly; handled separately by `analysis_handlers.py`
- **Progress Messages**: UI interpolates fake messages when server is slow
- **Async/Sync Conversion**: Complex conversion from async generators to Flask SSE

### 3. Result Aggregation Problems
- **Coordinator Structure**: Returns nested results with metadata
- **Flattening Logic**: `analysis_handlers.py` must flatten agent results for UI
- **Error Handling**: Partial failures not clearly communicated

### 4. Missing Transformations

The UI expects simplified field names while agents return complex nested structures. Need adapter functions:

```python
# Example transformation needed for bias analysis
def transform_bias_for_ui(agent_result):
    return {
        'political_lean': extract_political_lean(agent_result),
        'emotional_tone': agent_result.get('language_and_framing_analysis', {}).get('detected_tone'),
        'confidence': agent_result.get('political_spectrum_analysis_greek', {}).get('overall_confidence'),
        'language_analysis': {
            'framing': extract_framing_summary(agent_result),
            'loaded_words': extract_loaded_words(agent_result),
            'missing_perspectives': agent_result.get('language_and_framing_analysis', {}).get('missing_perspectives_summary')
        },
        'comparison': agent_result.get('comparison'),
        'recommendations': agent_result.get('recommendations')
    }
```

## 5. Recommendations

### Immediate Fixes Needed:
1. **Add Response Adapters**: Create transformation functions in `analysis_handlers.py` to convert agent outputs to UI-expected formats
2. **Fix Bias Schema Mismatch**: Either update UI to handle new schema or add adapter
3. **Add X Pulse UI Handler**: Implement missing formatting function for X Pulse results
4. **Standardize Citation Format**: Ensure citations are passed consistently

### Backend Updates:
1. **Schema Validation**: Add runtime validation between agent output and UI expectations
2. **Error Response Format**: Standardize error structure across all agents
3. **Progress Event Consistency**: Remove UI interpolation, use only real server events

### UI Improvements:
1. **Add Missing Handlers**: Implement formatXPulseResults function
2. **Update Field Mappings**: Fix bias analysis field expectations
3. **Better Error Display**: Show partial failures clearly
4. **Loading States**: Show which agents are running

### Testing:
1. **Integration Tests**: Test full data flow from agent to UI rendering
2. **Schema Contract Tests**: Validate agent outputs match UI expectations
3. **Error Scenario Tests**: Test partial failures and error handling

## 6. File Locations

- **Backend Routes**: `api/routes.py`, `api/web_routes.py`
- **Analysis Handler**: `api/analysis_handlers.py` (needs adapter functions)
- **Agent Schemas**: Individual agent files in `api/agents/`
- **UI Formatters**: `extension/content_script_OLD.js` (reference implementation)
- **UI Implementation**: `extension/content_script_clean.js` (current, but appears corrupted/empty)