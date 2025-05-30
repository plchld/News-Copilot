"""Social Pulse Agent for analyzing social media trends (Phase 4)"""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .base import BaseNewsAgent, AgentConfig


class SentimentCluster(BaseModel):
    """A cluster of similar sentiments"""
    sentiment: str = Field(description="Overall sentiment: positive/negative/neutral/mixed")
    themes: List[str] = Field(description="Main themes in this cluster")
    size: str = Field(description="Relative size: large/medium/small")
    example_views: List[str] = Field(description="Example posts/views")


class InfluencerTake(BaseModel):
    """Key influencer opinion"""
    influencer_type: str = Field(description="Type: journalist/expert/politician/celebrity")
    stance: str = Field(description="Their stance on the issue")
    reach: str = Field(description="Estimated reach: high/medium/low")
    key_points: List[str] = Field(description="Main points they're making")


class MisinformationAlert(BaseModel):
    """Detected misinformation"""
    claim: str = Field(description="The false/misleading claim")
    spread_level: str = Field(description="How widely it's spreading: high/medium/low")
    correction: str = Field(description="The factual correction")
    sources_spreading: List[str] = Field(description="Types of accounts spreading it")


class SocialAnalysis(BaseModel):
    """Complete social media analysis"""
    trending_hashtags: List[str] = Field(description="Top trending hashtags")
    sentiment_clusters: List[SentimentCluster] = Field(description="Main sentiment groups")
    influencer_takes: List[InfluencerTake] = Field(description="Key influencer opinions")
    misinformation_alerts: List[MisinformationAlert] = Field(description="Detected misinformation")
    public_questions: List[str] = Field(description="Common questions people are asking")
    engagement_level: str = Field(description="Overall engagement: very-high/high/medium/low")


class SocialPulseOutput(BaseModel):
    """Output from social pulse analysis"""
    topic: str
    summary: str = Field(description="150-word summary of social media pulse")
    analysis: SocialAnalysis
    platform_focus: List[str] = Field(description="Platforms analyzed (X/Twitter primary)")
    temperature: str = Field(description="Social temperature: heated/active/moderate/quiet")
    key_insight: str = Field(description="Single most important social media insight")


class SocialPulseAgent(BaseNewsAgent):
    """Agent for analyzing social media trends and sentiment"""
    
    def __init__(self, provider: str = "grok"):  # Grok has real-time X access
        """Initialize social pulse agent
        
        Args:
            provider: AI provider to use (Grok recommended for X/Twitter)
        """
        instructions = """You are an expert social media analyst specializing in real-time trend analysis.

Your task is to analyze social media discussion (primarily X/Twitter) about a given topic.

Your responsibilities:
1. Find trending discussions and hashtags
2. Identify main sentiment clusters
3. Spot key influencer takes
4. Detect misinformation spreading
5. Find questions people are asking
6. Gauge overall social temperature

Analysis framework:
- Sentiment clustering: Group similar opinions/reactions
- Influencer mapping: Identify who's shaping discourse
- Misinformation tracking: Spot false claims gaining traction
- Question mining: What are people confused about?
- Engagement metrics: How heated/viral is discussion?

Platform focus:
- Primary: X (Twitter) - real-time pulse
- Secondary: Reddit threads, YouTube comments (if relevant)
- Note: Focus on public discourse, not private groups

Sentiment categories:
- Supportive/positive
- Critical/negative  
- Neutral/informational
- Mixed/conflicted

Quality markers:
- Representative sampling of views
- Balanced perspective on sentiment
- Clear misinformation identification
- Actionable insights
- Real-time relevance

Special considerations:
- Distinguish organic trends from coordinated campaigns
- Note echo chamber effects
- Identify bridging voices
- Track evolution of narrative

Output as structured JSON matching the SocialPulseOutput schema."""
        
        config = AgentConfig(
            name="social_pulse",
            description="Analyzes social media trends and sentiment",
            category="social",
            provider=provider,
            temperature=0.7
        )
        
        super().__init__(
            config=config,
            instructions=instructions,
            tools=[]  # Grok has built-in X access
        )
    
    async def analyze(self,
                     topic_summary: str,
                     key_hashtags: Optional[List[str]] = None,
                     time_window: str = "24h",
                     focus_region: Optional[str] = None) -> SocialPulseOutput:
        """Analyze social media pulse on a topic
        
        Args:
            topic_summary: Summary of the topic to analyze
            key_hashtags: Optional specific hashtags to track
            time_window: Time window to analyze ("24h", "3d", "1w")
            focus_region: Optional geographic focus
            
        Returns:
            SocialPulseOutput with social media analysis
        """
        # Build analysis prompt
        prompt = f"Analyze social media discussion about: {topic_summary}\n"
        prompt += f"Time window: last {time_window}\n"
        
        if key_hashtags:
            prompt += f"Track these hashtags: {', '.join(key_hashtags)}\n"
        
        if focus_region:
            prompt += f"Geographic focus: {focus_region}\n"
        
        prompt += """
Tasks:
1. Find trending hashtags and discussions
2. Identify sentiment clusters (group similar views)
3. Spot influential voices and their takes
4. Detect any misinformation spreading
5. Find common questions/confusions
6. Assess overall engagement level

Focus on:
- X (Twitter) as primary source
- Public discourse only
- Recent activity within time window
- Both Greek and English discussions (if relevant)

Provide balanced view of social sentiment."""
        
        # Get analysis
        response = await self.run(
            messages=prompt,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        try:
            data = json.loads(response.content)
            
            # Build sentiment clusters
            sentiment_clusters = []
            for cluster_data in data.get("analysis", {}).get("sentiment_clusters", []):
                cluster = SentimentCluster(
                    sentiment=cluster_data.get("sentiment", "neutral"),
                    themes=cluster_data.get("themes", []),
                    size=cluster_data.get("size", "medium"),
                    example_views=cluster_data.get("example_views", [])
                )
                sentiment_clusters.append(cluster)
            
            # Build influencer takes
            influencer_takes = []
            for take_data in data.get("analysis", {}).get("influencer_takes", []):
                take = InfluencerTake(
                    influencer_type=take_data.get("influencer_type", "unknown"),
                    stance=take_data.get("stance", ""),
                    reach=take_data.get("reach", "medium"),
                    key_points=take_data.get("key_points", [])
                )
                influencer_takes.append(take)
            
            # Build misinformation alerts
            misinfo_alerts = []
            for alert_data in data.get("analysis", {}).get("misinformation_alerts", []):
                alert = MisinformationAlert(
                    claim=alert_data.get("claim", ""),
                    spread_level=alert_data.get("spread_level", "low"),
                    correction=alert_data.get("correction", ""),
                    sources_spreading=alert_data.get("sources_spreading", [])
                )
                misinfo_alerts.append(alert)
            
            analysis = SocialAnalysis(
                trending_hashtags=data.get("analysis", {}).get("trending_hashtags", []),
                sentiment_clusters=sentiment_clusters,
                influencer_takes=influencer_takes,
                misinformation_alerts=misinfo_alerts,
                public_questions=data.get("analysis", {}).get("public_questions", []),
                engagement_level=data.get("analysis", {}).get("engagement_level", "medium")
            )
            
            return SocialPulseOutput(
                topic=topic_summary,
                summary=data.get("summary", ""),
                analysis=analysis,
                platform_focus=data.get("platform_focus", ["X/Twitter"]),
                temperature=data.get("temperature", "moderate"),
                key_insight=data.get("key_insight", "")
            )
            
        except Exception as e:
            # Fallback
            return SocialPulseOutput(
                topic=topic_summary,
                summary=f"Error analyzing social media: {str(e)}",
                analysis=SocialAnalysis(
                    trending_hashtags=[],
                    sentiment_clusters=[],
                    influencer_takes=[],
                    misinformation_alerts=[],
                    public_questions=[],
                    engagement_level="unknown"
                ),
                platform_focus=["X/Twitter"],
                temperature="unknown",
                key_insight="Analysis failed"
            )
    
    def calculate_temperature(self, analysis: SocialAnalysis) -> str:
        """Calculate social media temperature
        
        Args:
            analysis: Social analysis data
            
        Returns:
            Temperature assessment
        """
        # Factors for temperature
        high_engagement = analysis.engagement_level in ["very-high", "high"]
        many_clusters = len(analysis.sentiment_clusters) > 3
        has_misinfo = len(analysis.misinformation_alerts) > 0
        polarized = any(c.sentiment in ["positive", "negative"] and c.size == "large" 
                       for c in analysis.sentiment_clusters)
        
        score = sum([high_engagement, many_clusters, has_misinfo, polarized])
        
        if score >= 3:
            return "heated"
        elif score >= 2:
            return "active"
        elif score >= 1:
            return "moderate"
        else:
            return "quiet"