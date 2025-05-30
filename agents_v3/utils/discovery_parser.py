"""Robust parser for discovery agent JSON outputs with fault tolerance"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParsedStory:
    """Validated story from discovery output"""
    id: int
    headline: str
    headline_greek: str
    summary: str
    source_name: str
    source_url: str
    published_date: str
    stakeholders: List[str]
    international_relevance_score: int
    relevance_reasoning: str
    category: str
    
    @property
    def needs_international_context(self) -> bool:
        """Determine if international context needed"""
        if self.category in ["Science News", "Technology News"]:
            return True
        return self.international_relevance_score >= 7
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "headline": self.headline,
            "headline_greek": self.headline_greek,
            "summary": self.summary,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "published_date": self.published_date,
            "stakeholders": self.stakeholders,
            "international_relevance_score": self.international_relevance_score,
            "relevance_reasoning": self.relevance_reasoning,
            "category": self.category,
            "needs_international_context": self.needs_international_context
        }


class DiscoveryParser:
    """Parse and validate discovery agent outputs with fault tolerance"""
    
    def __init__(self):
        self.json_extraction_patterns = [
            r'```json\s*(.*?)\s*```',  # Code block
            r'```\s*(.*?)\s*```',       # Generic code block
            r'\{.*\}',                  # Raw JSON object
        ]
    
    def parse_discovery_output(self, raw_output: str, category: str) -> Tuple[List[ParsedStory], List[str]]:
        """Parse discovery output with comprehensive error handling
        
        Args:
            raw_output: Raw agent output
            category: Category name for context
            
        Returns:
            Tuple of (parsed_stories, errors)
        """
        errors = []
        
        # Step 1: Extract JSON from output
        json_data = self._extract_json(raw_output, errors)
        if not json_data:
            return [], errors
        
        # Step 2: Validate structure
        if not self._validate_structure(json_data, errors):
            return [], errors
        
        # Step 3: Parse stories
        stories = []
        story_data = json_data.get("stories", [])
        
        # Handle case where we got less than 10 stories
        if len(story_data) < 10:
            errors.append(f"Warning: Only {len(story_data)} stories returned (expected 10)")
        
        for idx, story in enumerate(story_data[:10]):  # Cap at 10
            parsed_story = self._parse_single_story(story, idx + 1, category, errors)
            if parsed_story:
                stories.append(parsed_story)
        
        # Step 4: Ensure we have enough stories
        if len(stories) < 10:
            logger.warning(f"Only parsed {len(stories)} valid stories for {category}")
            # Could implement fallback strategies here
        
        return stories, errors
    
    def _extract_json(self, raw_output: str, errors: List[str]) -> Optional[Dict]:
        """Extract JSON from various output formats"""
        
        # Try each extraction pattern
        for pattern in self.json_extraction_patterns:
            matches = re.findall(pattern, raw_output, re.DOTALL | re.MULTILINE)
            if matches:
                for match in matches:
                    try:
                        # Clean up the match
                        json_str = match.strip()
                        # Remove any trailing commas
                        json_str = re.sub(r',\s*}', '}', json_str)
                        json_str = re.sub(r',\s*]', ']', json_str)
                        
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        errors.append(f"JSON decode error: {str(e)}")
                        continue
        
        # Last resort: try to parse the entire output
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to extract valid JSON from output: {str(e)}"
            errors.append(error_msg)
            
            # Enhanced debugging information
            print(f"\n🔴 JSON PARSING FAILED:")
            print(f"   Error: {str(e)}")
            print(f"   Content length: {len(raw_output)} characters")
            print(f"   Patterns tried: {len(self.json_extraction_patterns)}")
            
            # Check for common issues
            if "```json" in raw_output:
                print("   ✓ Found ```json marker")
            else:
                print("   ✗ No ```json marker found")
            
            if "{" in raw_output and "}" in raw_output:
                print("   ✓ Found JSON brackets")
                brace_count = raw_output.count("{") - raw_output.count("}")
                if brace_count != 0:
                    print(f"   ✗ Unbalanced braces (difference: {brace_count})")
            else:
                print("   ✗ No JSON brackets found")
            
            # Show problematic content
            print(f"\n📄 FULL CONTENT ({len(raw_output)} chars):")
            print("─" * 80)
            print(raw_output)
            print("─" * 80)
            
            return None
    
    def _validate_structure(self, data: Dict, errors: List[str]) -> bool:
        """Validate the JSON structure"""
        
        required_fields = ["stories"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
                return False
        
        if not isinstance(data["stories"], list):
            errors.append("'stories' must be a list")
            return False
        
        return True
    
    def _parse_single_story(self, story: Dict, idx: int, category: str, errors: List[str]) -> Optional[ParsedStory]:
        """Parse and validate a single story"""
        
        try:
            # Extract fields with defaults
            story_id = story.get("id", idx)
            headline = story.get("headline", "").strip()
            headline_greek = story.get("headline_greek", headline).strip()
            summary = story.get("summary", "").strip()
            source_name = story.get("source_name", "Unknown").strip()
            source_url = story.get("source_url", "").strip()
            published_date = story.get("published_date", datetime.now().strftime("%Y-%m-%d %H:%M"))
            stakeholders = story.get("stakeholders", [])
            relevance_score = story.get("international_relevance_score", 5)
            relevance_reasoning = story.get("relevance_reasoning", "").strip()
            
            # Validate required fields
            if not headline:
                errors.append(f"Story {idx}: Missing headline")
                return None
            
            if not summary:
                errors.append(f"Story {idx}: Missing summary")
                return None
            
            # Validate and fix data types
            if not isinstance(stakeholders, list):
                stakeholders = [str(stakeholders)] if stakeholders else []
            
            # Ensure score is in valid range
            try:
                relevance_score = int(relevance_score)
                relevance_score = max(1, min(10, relevance_score))
            except (ValueError, TypeError):
                relevance_score = 5
                errors.append(f"Story {idx}: Invalid relevance score, defaulting to 5")
            
            # Validate URL
            if source_url and not source_url.startswith(("http://", "https://")):
                source_url = f"https://{source_url}"
            
            return ParsedStory(
                id=story_id,
                headline=headline,
                headline_greek=headline_greek,
                summary=summary,
                source_name=source_name,
                source_url=source_url,
                published_date=published_date,
                stakeholders=stakeholders,
                international_relevance_score=relevance_score,
                relevance_reasoning=relevance_reasoning,
                category=category
            )
            
        except Exception as e:
            errors.append(f"Story {idx}: Parsing error - {str(e)}")
            logger.exception(f"Failed to parse story {idx}")
            return None
    
    def validate_story_batch(self, stories: List[ParsedStory]) -> Tuple[bool, List[str]]:
        """Validate a batch of parsed stories"""
        
        issues = []
        
        # Check story count
        if len(stories) < 10:
            issues.append(f"Only {len(stories)} stories (expected 10)")
        elif len(stories) > 10:
            issues.append(f"Too many stories: {len(stories)} (expected 10)")
        
        # Check for duplicates
        urls = [s.source_url for s in stories if s.source_url]
        if len(urls) != len(set(urls)):
            issues.append("Duplicate URLs detected")
        
        # Check for empty fields
        for idx, story in enumerate(stories):
            if not story.headline:
                issues.append(f"Story {idx+1}: Empty headline")
            if not story.summary:
                issues.append(f"Story {idx+1}: Empty summary")
        
        return len(issues) == 0, issues