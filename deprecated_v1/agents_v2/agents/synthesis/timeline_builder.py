"""Timeline Agent for building historical context"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..base import BaseNewsAgent, AgentConfig
from ...tools.search import search_web_tool


class TimelineEvent(BaseModel):
    """A single event in the timeline"""
    date: str = Field(description="Date in YYYY-MM-DD format or 'YYYY-MM' for month")
    event: str = Field(description="Brief description of what happened")
    significance: str = Field(description="Why this event matters to current story")
    category: str = Field(description="Category: cause/effect/turning-point/context")
    confidence: float = Field(description="Confidence in date accuracy (0.0-1.0)", ge=0.0, le=1.0)


class TimelineAnalysis(BaseModel):
    """Analysis of historical timeline"""
    events: List[TimelineEvent] = Field(description="Chronological list of events")
    pattern_detected: Optional[str] = Field(description="Any historical pattern identified")
    cycle_length: Optional[str] = Field(description="If cyclical, how often it repeats")
    key_turning_points: List[str] = Field(description="Most significant moments")
    historical_context: str = Field(description="Brief historical context summary")


class TimelineOutput(BaseModel):
    """Output from timeline building"""
    topic: str
    timeline: TimelineAnalysis
    time_span: str = Field(description="Time span covered (e.g., '5 years', '2 decades')")
    relevance_score: float = Field(description="How relevant history is to current event (0.0-1.0)", ge=0.0, le=1.0)
    insights: List[str] = Field(description="Key insights from timeline")


class TimelineAgent(BaseNewsAgent):
    """Agent for building historical timelines and context"""
    
    def __init__(self, provider: str = "grok"):
        """Initialize timeline agent
        
        Args:
            provider: AI provider to use
        """
        instructions = """You are an expert historian and timeline analyst.

Your task is to research and build a historical timeline that provides context for current news.

Your responsibilities:
1. Find key events leading to the current situation
2. Identify cause-effect relationships
3. Note any repeating patterns or cycles
4. Mark crucial turning points
5. Keep to 5-7 most important events
6. Explain each event's significance

Timeline construction guidelines:
- Start from the earliest relevant event
- Focus on direct connections to current story
- Include both immediate and root causes
- Note accelerating factors
- Identify decision points that could have changed outcomes

Event categories:
- cause: Direct cause of current situation
- effect: Result of earlier events
- turning-point: Moment that changed trajectory
- context: Important background information

Quality markers:
- Clear cause-effect chains
- Accurate dates (month/year precision minimum)
- Concise but informative descriptions
- Obvious relevance to current story
- Pattern identification where applicable

Special considerations:
- For political stories: Include election dates, policy changes
- For conflicts: Include escalation points, failed negotiations
- For economic stories: Include market events, policy decisions
- For social issues: Include movements, legislation, cultural shifts

Output as structured JSON matching the TimelineOutput schema."""
        
        config = AgentConfig(
            name="timeline_builder",
            description="Builds historical timelines for context",
            category="synthesis",
            provider=provider,
            temperature=0.5
        )
        
        super().__init__(
            config=config,
            instructions=instructions,
            tools=[search_web_tool]
        )
    
    async def build_timeline(self,
                           topic_summary: str,
                           current_date: Optional[str] = None,
                           focus_period: Optional[str] = None,
                           key_actors: Optional[List[str]] = None) -> TimelineOutput:
        """Build historical timeline for a topic
        
        Args:
            topic_summary: Summary of the current topic/event
            current_date: Current date for reference
            focus_period: Specific period to focus on (e.g., "last 5 years")
            key_actors: Key people/organizations to track
            
        Returns:
            TimelineOutput with historical timeline
        """
        if not current_date:
            current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Build research prompt
        prompt = f"Build a historical timeline for: {topic_summary}\n"
        prompt += f"Current date: {current_date}\n"
        
        if focus_period:
            prompt += f"Focus on: {focus_period}\n"
        
        if key_actors:
            prompt += f"Track these key actors: {', '.join(key_actors)}\n"
        
        prompt += """
Tasks:
1. Research the historical background
2. Identify 5-7 most important events
3. Find clear cause-effect relationships
4. Note any patterns or cycles
5. Mark turning points

Focus on events that directly relate to the current situation.
Be precise with dates and concise with descriptions."""
        
        # Get timeline
        response = await self.run(
            messages=prompt,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        try:
            data = json.loads(response.content)
            
            # Build events
            events = []
            for event_data in data.get("timeline", {}).get("events", []):
                event = TimelineEvent(
                    date=event_data.get("date", ""),
                    event=event_data.get("event", ""),
                    significance=event_data.get("significance", ""),
                    category=event_data.get("category", "context"),
                    confidence=float(event_data.get("confidence", 0.8))
                )
                events.append(event)
            
            # Sort by date
            events = self._sort_events(events)
            
            timeline = TimelineAnalysis(
                events=events,
                pattern_detected=data.get("timeline", {}).get("pattern_detected"),
                cycle_length=data.get("timeline", {}).get("cycle_length"),
                key_turning_points=data.get("timeline", {}).get("key_turning_points", []),
                historical_context=data.get("timeline", {}).get("historical_context", "")
            )
            
            # Calculate time span
            time_span = self._calculate_time_span(events)
            
            return TimelineOutput(
                topic=topic_summary,
                timeline=timeline,
                time_span=time_span,
                relevance_score=float(data.get("relevance_score", 0.8)),
                insights=data.get("insights", [])
            )
            
        except Exception as e:
            # Fallback
            return TimelineOutput(
                topic=topic_summary,
                timeline=TimelineAnalysis(
                    events=[],
                    pattern_detected=None,
                    cycle_length=None,
                    key_turning_points=[],
                    historical_context=f"Timeline construction failed: {str(e)}"
                ),
                time_span="unknown",
                relevance_score=0.0,
                insights=[]
            )
    
    def _sort_events(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """Sort events chronologically
        
        Args:
            events: List of timeline events
            
        Returns:
            Sorted list
        """
        def parse_date(date_str: str) -> datetime:
            """Parse flexible date formats"""
            try:
                # Try full date
                return datetime.strptime(date_str, "%Y-%m-%d")
            except:
                try:
                    # Try month-year
                    return datetime.strptime(date_str, "%Y-%m")
                except:
                    try:
                        # Try year only
                        return datetime.strptime(date_str, "%Y")
                    except:
                        # Fallback to current date
                        return datetime.now()
        
        return sorted(events, key=lambda e: parse_date(e.date))
    
    def _calculate_time_span(self, events: List[TimelineEvent]) -> str:
        """Calculate the time span covered by events
        
        Args:
            events: List of timeline events
            
        Returns:
            Human-readable time span
        """
        if not events:
            return "no timeline"
        
        # Get first and last dates
        try:
            first_year = int(events[0].date.split("-")[0])
            last_year = int(events[-1].date.split("-")[0])
            
            span_years = last_year - first_year
            
            if span_years == 0:
                return "less than 1 year"
            elif span_years == 1:
                return "1 year"
            elif span_years < 5:
                return f"{span_years} years"
            elif span_years < 10:
                return "nearly a decade"
            elif span_years < 20:
                return f"{span_years} years"
            elif span_years < 30:
                return "over 2 decades"
            else:
                decades = span_years // 10
                return f"{decades} decades"
                
        except:
            return "multiple years"