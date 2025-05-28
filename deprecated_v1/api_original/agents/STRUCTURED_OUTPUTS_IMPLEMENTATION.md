# Grok Structured Outputs Implementation Guide

## Overview

This guide provides a complete implementation plan for migrating News Copilot agents to use Grok's new Structured Outputs feature, ensuring 100% schema compliance and eliminating JSON parsing errors.

## Benefits of Structured Outputs

1. **Guaranteed Schema Compliance**: No more malformed JSON or missing fields
2. **Token Efficiency**: ~20% reduction in token usage
3. **Type Safety**: Compile-time validation with Pydantic
4. **Better Performance**: No need for retry loops on parsing failures
5. **Cleaner Code**: Remove JSON parsing and validation boilerplate

## Implementation Plan

### Phase 1: Foundation (Days 1-3)

#### 1.1 Create Pydantic Schema Module

```python
# api/agents/schemas.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import date
from enum import Enum

# Base classes for common patterns
class GreekContent(BaseModel):
    """Base class ensuring Greek content"""
    
    @validator('*', pre=False)
    def ensure_greek(cls, v):
        if isinstance(v, str) and v:
            # Could add Greek character validation here
            pass
        return v

# Jargon Analysis Schema
class JargonTerm(BaseModel):
    term: str = Field(description="Technical term or jargon in original form")
    explanation: str = Field(description="Simple explanation in Greek", min_length=10)
    category: Optional[str] = Field(None, description="Category: τεχνικός, πολιτικός, οικονομικός")

class JargonAnalysis(GreekContent):
    terms: List[JargonTerm] = Field(min_items=1, max_items=20)
    summary: Optional[str] = Field(None, description="Brief summary of complexity level")

# Viewpoints Schema
class NewsSource(str, Enum):
    KATHIMERINI = "Καθημερινή"
    TA_NEA = "Τα Νέα"
    PROTO_THEMA = "Πρώτο Θέμα"
    EFSYN = "Εφημερίδα των Συντακτών"
    CNN_GR = "CNN Greece"
    OTHER = "Άλλο"

class Viewpoint(BaseModel):
    perspective: str = Field(description="Brief title of perspective", max_length=100)
    argument: str = Field(description="Detailed explanation in Greek", min_length=50)
    source: NewsSource = Field(description="News source")
    source_url: Optional[str] = Field(None, description="Direct article URL if available")
    key_difference: str = Field(description="Main difference from original article")

class ViewpointsAnalysis(GreekContent):
    viewpoints: List[Viewpoint] = Field(min_items=2, max_items=6)
    consensus_points: List[str] = Field(description="Points all sources agree on")
    
# Fact Check Schema  
class Verdict(str, Enum):
    TRUE = "Αληθές"
    MOSTLY_TRUE = "Κυρίως Αληθές"  
    MIXED = "Μικτό"
    MISLEADING = "Παραπλανητικό"
    FALSE = "Ψευδές"
    UNVERIFIABLE = "Μη Επαληθεύσιμο"

class FactSource(BaseModel):
    description: str = Field(description="Source description in Greek")
    url: str = Field(description="Direct URL to source")
    reliability: str = Field(description="High/Medium/Low reliability indicator")

class FactClaim(BaseModel):
    claim: str = Field(description="Exact claim from article")
    verdict: Verdict
    explanation: str = Field(description="Detailed fact-check explanation", min_length=100)
    evidence: List[str] = Field(description="Key evidence points")
    sources: List[FactSource] = Field(min_items=1, max_items=5)

class FactCheckAnalysis(GreekContent):
    claims: List[FactClaim] = Field(min_items=1, max_items=10)
    overall_credibility: str = Field(description="Overall article credibility assessment")
    red_flags: List[str] = Field(description="Warning signs or issues found")
    missing_context: Optional[str] = Field(None, description="Important missing information")

# Bias Analysis Schema
class PoliticalPosition(str, Enum):
    FAR_LEFT = "Άκρα Αριστερά"
    LEFT = "Αριστερά"
    CENTER_LEFT = "Κεντροαριστερά"
    CENTER = "Κέντρο"
    CENTER_RIGHT = "Κεντροδεξιά"
    RIGHT = "Δεξιά"
    FAR_RIGHT = "Άκρα Δεξιά"

class BiasIndicator(BaseModel):
    indicator: str = Field(description="Specific bias indicator")
    example: str = Field(description="Example from article")
    impact: str = Field(description="How it affects objectivity")

class BiasAnalysis(GreekContent):
    political_leaning: PoliticalPosition
    economic_position: str = Field(description="Economic ideology position")
    bias_indicators: List[BiasIndicator] = Field(min_items=1, max_items=10)
    missing_perspectives: List[str] = Field(description="Viewpoints not represented")
    objectivity_score: int = Field(ge=1, le=10, description="1-10 objectivity rating")
    reasoning: str = Field(description="Detailed reasoning for assessment", min_length=200)

# Timeline Schema
class TimelineEvent(BaseModel):
    date: str = Field(description="Date in format: YYYY-MM-DD or 'περίπου YYYY-MM'")
    title: str = Field(description="Brief event title", max_length=100)
    description: str = Field(description="Detailed description in Greek")
    importance: str = Field(description="Κρίσιμο/Σημαντικό/Δευτερεύον")
    source: str = Field(description="Information source")
    verified: bool = Field(description="Whether event is verified")

class TimelineAnalysis(GreekContent):
    story_title: str = Field(description="Overall story title")
    events: List[TimelineEvent] = Field(min_items=3, max_items=20)
    duration: str = Field(description="Total timeline span")
    key_turning_points: List[str] = Field(description="Critical moments")
    future_implications: Optional[str] = Field(None, description="Potential future developments")

# Expert Opinions Schema
class ExpertCredentials(BaseModel):
    name: str = Field(description="Expert's full name")
    title: str = Field(description="Professional title in Greek")
    affiliation: str = Field(description="Organization or institution")
    expertise_area: str = Field(description="Area of expertise")

class ExpertOpinion(BaseModel):
    expert: ExpertCredentials
    stance: str = Field(description="Υπέρ/Κατά/Ουδέτερος/Μικτός")
    main_argument: str = Field(description="Core argument in Greek", min_length=100)
    key_quote: Optional[str] = Field(None, description="Notable quote if available")
    source_url: Optional[str] = Field(None, description="X post or article URL")
    date: Optional[str] = Field(None, description="Date of opinion")

class ExpertAnalysis(GreekContent):
    topic_summary: str = Field(description="Brief topic overview", max_length=200)
    experts: List[ExpertOpinion] = Field(min_items=2, max_items=10)
    consensus_level: str = Field(description="Πλήρης/Μερική/Ελάχιστη/Καμία")
    key_debates: List[str] = Field(description="Main points of disagreement")
    emerging_perspectives: Optional[List[str]] = Field(None, description="New viewpoints")

# X Pulse Schema (Complex)
class Sentiment(str, Enum):
    POSITIVE = "Θετικό"
    NEGATIVE = "Αρνητικό"
    MIXED = "Μικτό"
    NEUTRAL = "Ουδέτερο"

class XPost(BaseModel):
    content: str = Field(description="Post content (abbreviated if needed)", max_length=500)
    author_description: str = Field(description="Anonymous author type description")
    engagement_level: str = Field(description="High/Medium/Low engagement")
    timestamp_relative: Optional[str] = Field(None, description="e.g., '2 ώρες πριν'")

class DiscussionTheme(BaseModel):
    theme_title: str = Field(description="Theme title in Greek", max_length=100)
    theme_summary: str = Field(description="Detailed theme explanation", min_length=100)
    sentiment: Sentiment
    representative_posts: List[XPost] = Field(min_items=2, max_items=5)
    prevalence: str = Field(description="Κυρίαρχο/Συχνό/Μέτριο/Σπάνιο")

class XPulseAnalysis(GreekContent):
    overall_discourse_summary: str = Field(description="Executive summary", max_length=500)
    total_posts_analyzed: int = Field(ge=0, description="Approximate posts analyzed")
    discussion_themes: List[DiscussionTheme] = Field(min_items=2, max_items=8)
    trending_hashtags: Optional[List[str]] = Field(None, max_items=10)
    overall_sentiment: Sentiment
    key_influencers: Optional[List[str]] = Field(None, description="Key voices (anonymized)")
    data_caveats: str = Field(description="Important limitations or caveats")
```

#### 1.2 Update Base Agent Class

```python
# api/agents/base_agent.py
from typing import Type, Optional
from pydantic import BaseModel
import json

class AnalysisAgent(BaseAgent):
    """Enhanced base class with structured output support"""
    
    def __init__(
        self,
        config: AgentConfig,
        grok_client: Any,
        prompt_builder: Callable,
        response_model: Optional[Type[BaseModel]] = None,
        schema_builder: Optional[Callable] = None  # Fallback for non-structured models
    ):
        super().__init__(config, grok_client)
        self.prompt_builder = prompt_builder
        self.response_model = response_model
        self.schema_builder = schema_builder
        
    async def _call_grok_structured(
        self,
        prompt: str,
        model: ModelType,
        search_params: Optional[Dict] = None,
        context: Dict[str, Any] = None
    ) -> BaseModel:
        """Call Grok API with structured output"""
        
        # Check if model supports structured output
        structured_models = [
            ModelType.GROK_3,
            ModelType.GROK_3_FAST,
            ModelType.GROK_3_MINI,
            ModelType.GROK_3_MINI_FAST
        ]
        
        if model not in structured_models or not self.response_model:
            # Fallback to traditional JSON schema approach
            return await self._call_grok_legacy(prompt, model, search_params, context)
        
        try:
            # Log the structured call
            self._log_phase(
                "calling_grok_structured",
                model=model.value,
                has_search=bool(search_params),
                response_model=self.response_model.__name__
            )
            
            # Build messages
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            # Make structured API call
            response = await self.grok_client.async_client.beta.chat.completions.parse(
                model=model.value,
                messages=messages,
                response_format=self.response_model,
                search_parameters=search_params,
                temperature=0.7
            )
            
            # Get parsed result
            parsed_result = response.choices[0].message.parsed
            
            # Log token usage
            if hasattr(response, 'usage'):
                self.tokens_used = response.usage.total_tokens
            
            return parsed_result
            
        except Exception as e:
            self._log_phase("grok_structured_error", error=str(e), model=model.value)
            raise
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute analysis with structured output support"""
        try:
            # Standard setup
            self._prepare_execution(context)
            prompt = self._build_prompt(context)
            search_params = self._build_search_params(context)
            
            # Call Grok with structured output
            if self.response_model:
                result = await self._call_grok_structured(
                    prompt, self.selected_model, search_params, context
                )
                # Convert Pydantic model to dict
                result_data = result.model_dump()
            else:
                # Legacy JSON approach
                result_data = await self._call_grok(
                    prompt, self.schema_builder(), self.selected_model, search_params, context
                )
            
            # Validate and return
            return self._create_success_result(result_data)
            
        except Exception as e:
            return self._create_error_result(str(e))
```

### Phase 2: Agent Migration (Days 4-7)

#### 2.1 Migrate Simple Agents First

```python
# api/agents/jargon_agent.py
from typing import Dict, Any, Optional
from .base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
from .schemas import JargonAnalysis
from ..prompt_utils import get_task_instruction

class JargonAgent(AnalysisAgent):
    """Jargon identification with structured outputs"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'JargonAgent':
        config = AgentConfig(
            name="JargonAgent",
            description="Identifies technical terms with structured output",
            default_model=ModelType.GROK_3_MINI,
            complexity=ComplexityLevel.SIMPLE,
            supports_streaming=True,
            max_retries=3,
            timeout_seconds=60
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_jargon_prompt,
            response_model=JargonAnalysis  # Pydantic model
        )
    
    @staticmethod
    def _build_jargon_prompt(context: Dict[str, Any]) -> str:
        """Build prompt using centralized utilities"""
        article_content = context.get('article_text', '')
        article_url = context.get('article_url', '')
        
        # Use centralized prompt
        base_prompt = get_task_instruction('jargon', article_content, article_url)
        
        # Add structured output guidance
        enhanced_prompt = f"""{base_prompt}

IMPORTANT: Identify technical terms, organizations, and concepts that need explanation.
Focus on terms that a general Greek audience might not understand.
Provide clear, concise explanations in simple Greek."""
        
        return enhanced_prompt
```

#### 2.2 Migrate Complex Agents

```python
# api/agents/bias_agent.py
from .schemas import BiasAnalysis, BiasIndicator, PoliticalPosition
from ..prompt_utils import get_task_instruction, SYSTEM_PREFIX

class BiasAnalysisAgent(AnalysisAgent):
    """Political bias analysis with structured outputs"""
    
    @classmethod
    def create(cls, grok_client: Any) -> 'BiasAnalysisAgent':
        config = AgentConfig(
            name="BiasAnalysisAgent",
            description="Analyzes political bias with structured output",
            default_model=ModelType.GROK_3,
            complexity=ComplexityLevel.COMPLEX,
            supports_streaming=False,
            max_retries=2,
            timeout_seconds=120
        )
        
        return cls(
            config=config,
            grok_client=grok_client,
            prompt_builder=cls._build_bias_prompt,
            response_model=BiasAnalysis
        )
    
    @staticmethod
    def _build_bias_prompt(context: Dict[str, Any]) -> str:
        """Build comprehensive bias analysis prompt"""
        article_content = context.get('article_text', '')
        article_url = context.get('article_url', '')
        
        prompt = f"""{get_task_instruction('bias', article_content, article_url)}

Analyze for:
1. Political leaning on the Greek political spectrum
2. Economic ideology (neoliberal, social democratic, etc.)
3. Specific bias indicators with examples
4. Missing perspectives that would provide balance
5. Overall objectivity score (1-10)

Provide detailed reasoning for your assessment."""
        
        return prompt
```

### Phase 3: Testing Framework (Days 8-10)

#### 3.1 Create Structured Output Tests

```python
# tests/test_structured_outputs.py
import pytest
from pydantic import ValidationError
from api.agents.schemas import *
from api.agents.jargon_agent import JargonAgent

class TestStructuredOutputs:
    
    @pytest.mark.asyncio
    async def test_jargon_agent_structured_output(self, grok_client_mock):
        """Test JargonAgent returns valid structured output"""
        agent = JargonAgent.create(grok_client_mock)
        
        context = {
            "article_text": "Η ΕΚΤ ανακοίνωσε QE μέτρα για την τόνωση του ΑΕΠ",
            "article_url": "https://example.com/article",
            "user_tier": "premium"
        }
        
        result = await agent.execute(context)
        
        # Validate result structure
        assert result.success
        assert "terms" in result.data
        
        # Validate against Pydantic model
        validated = JargonAnalysis(**result.data)
        assert len(validated.terms) > 0
        assert all(term.explanation for term in validated.terms)
    
    def test_schema_validation(self):
        """Test schema validation catches errors"""
        
        # Valid data
        valid_data = {
            "terms": [
                {"term": "ΕΚΤ", "explanation": "Ευρωπαϊκή Κεντρική Τράπεζα"}
            ]
        }
        analysis = JargonAnalysis(**valid_data)
        assert len(analysis.terms) == 1
        
        # Invalid data - missing explanation
        invalid_data = {
            "terms": [{"term": "ΕΚΤ"}]
        }
        with pytest.raises(ValidationError):
            JargonAnalysis(**invalid_data)
        
        # Invalid data - explanation too short
        invalid_data = {
            "terms": [
                {"term": "ΕΚΤ", "explanation": "Bank"}  # Less than min_length
            ]
        }
        with pytest.raises(ValidationError):
            JargonAnalysis(**invalid_data)
```

#### 3.2 Integration Tests

```python
# tests/test_agent_integration.py
class TestAgentIntegration:
    
    @pytest.mark.asyncio
    async def test_all_agents_structured(self, real_article_text):
        """Test all agents with structured outputs"""
        
        agents_to_test = [
            JargonAgent,
            ViewpointsAgent,
            FactCheckAgent,
            BiasAnalysisAgent,
            TimelineAgent,
            ExpertOpinionsAgent
        ]
        
        context = {
            "article_text": real_article_text,
            "article_url": "https://example.com/test",
            "user_tier": "premium"
        }
        
        for agent_class in agents_to_test:
            agent = agent_class.create(mock_grok_client)
            result = await agent.execute(context)
            
            # Verify structured output
            assert result.success, f"{agent_class.__name__} failed"
            assert isinstance(result.data, dict)
            
            # Verify no parsing errors
            assert "error" not in result.data
            assert "parse_error" not in result.data
```

### Phase 4: Rollout Strategy (Days 11-14)

#### 4.1 Feature Flag Implementation

```python
# api/config.py
STRUCTURED_OUTPUT_ENABLED = {
    "jargon": True,      # Start with simple agents
    "viewpoints": True,
    "fact_check": False,  # Gradual rollout
    "bias": False,
    "timeline": False,
    "expert": False,
    "x_pulse": False
}

# api/agents/base_agent.py
def should_use_structured_output(self, agent_name: str) -> bool:
    """Check if structured output is enabled for this agent"""
    from ..config import STRUCTURED_OUTPUT_ENABLED
    return STRUCTURED_OUTPUT_ENABLED.get(agent_name.lower(), False)
```

#### 4.2 Monitoring and Metrics

```python
# api/agents/metrics.py
from dataclasses import dataclass
from typing import Dict
import time

@dataclass
class StructuredOutputMetrics:
    agent_name: str
    success_count: int = 0
    failure_count: int = 0
    fallback_count: int = 0
    avg_response_time_ms: float = 0.0
    validation_errors: Dict[str, int] = None
    
    def record_success(self, response_time_ms: float):
        self.success_count += 1
        self._update_avg_time(response_time_ms)
    
    def record_validation_error(self, error_type: str):
        if self.validation_errors is None:
            self.validation_errors = {}
        self.validation_errors[error_type] = self.validation_errors.get(error_type, 0) + 1
```

### Phase 5: UI Updates (Days 15-16)

#### 5.1 Type-Safe UI Rendering

```javascript
// extension/content_script_clean.js

// Type definitions matching Pydantic schemas
const AgentSchemas = {
    jargon: {
        validate: (data) => {
            return data.terms && Array.isArray(data.terms) &&
                   data.terms.every(t => t.term && t.explanation);
        }
    },
    factCheck: {
        validate: (data) => {
            return data.claims && Array.isArray(data.claims) &&
                   data.overall_credibility && data.red_flags;
        }
    }
};

// Enhanced formatter with validation
function formatAnalysisResult(analysisType, data) {
    // Validate schema first
    const schema = AgentSchemas[analysisType];
    if (schema && !schema.validate(data)) {
        console.error(`Invalid ${analysisType} data structure:`, data);
        return formatErrorMessage(analysisType, "Invalid data format");
    }
    
    // Type-safe rendering
    switch(analysisType) {
        case 'jargon':
            return formatJargonTerms(data);
        case 'factCheck':
            return formatFactCheck(data);
        // ... other cases
    }
}
```

## Migration Checklist

### Week 1
- [ ] Create schemas.py with all Pydantic models
- [ ] Update base_agent.py with structured output support
- [ ] Migrate JargonAgent
- [ ] Migrate ViewpointsAgent
- [ ] Create basic tests
- [ ] Deploy with feature flags (jargon only)

### Week 2
- [ ] Migrate FactCheckAgent
- [ ] Migrate BiasAnalysisAgent
- [ ] Migrate TimelineAgent
- [ ] Migrate ExpertOpinionsAgent
- [ ] Comprehensive testing
- [ ] Enable structured output for 50% of users

### Week 3
- [ ] Migrate X-Pulse sub-agents
- [ ] Performance optimization
- [ ] UI type safety updates
- [ ] Full rollout
- [ ] Documentation updates

## Success Metrics

1. **Zero JSON Parsing Errors**: Complete elimination of parsing failures
2. **20% Token Reduction**: Measured across all agents
3. **UI Rendering Errors**: Reduced by 95%
4. **Response Time**: 10-15% improvement
5. **Developer Experience**: Reduced debugging time by 50%

## Conclusion

Implementing Grok's Structured Outputs will fundamentally improve the reliability and maintainability of the News Copilot agent system. The phased approach ensures minimal disruption while maximizing the benefits of guaranteed schema compliance and type safety.