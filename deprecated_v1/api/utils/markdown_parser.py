"""
Markdown Parser Utilities for News Copilot
Converts markdown-formatted AI responses to structured data
"""

import re
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MarkdownParser:
    """Base class for parsing markdown responses from AI agents"""
    
    @staticmethod
    def extract_sections(content: str) -> Dict[str, str]:
        """Extract markdown sections marked with ## headers"""
        sections = {}
        current_section = None
        current_content = []
        
        lines = content.strip().split('\n')
        
        for line in lines:
            # Check for section header
            if line.startswith('## '):
                # Save previous section if exists
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    @staticmethod
    def extract_bullet_points(content: str) -> List[str]:
        """Extract bullet points from content"""
        bullets = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
                bullets.append(line[2:].strip())
            elif re.match(r'^\d+\.\s', line):
                # Numbered list
                bullets.append(re.sub(r'^\d+\.\s', '', line).strip())
        
        return bullets
    
    @staticmethod
    def extract_key_value_pairs(content: str) -> Dict[str, str]:
        """Extract key-value pairs from content (format: **Key**: Value)"""
        pairs = {}
        
        # Pattern for **Key**: Value
        pattern = r'\*\*([^*]+)\*\*:\s*([^\n]+)'
        matches = re.findall(pattern, content)
        
        for key, value in matches:
            pairs[key.strip()] = value.strip()
        
        return pairs


class FactCheckParser(MarkdownParser):
    """Parser for fact-check markdown responses"""
    
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse fact-check markdown to structured data"""
        try:
            result = {
                "claims": [],
                "source_quality": {
                    "primary_sources": 0,
                    "secondary_sources": 0,
                    "source_diversity": "άγνωστο"
                }
            }
            
            # Extract sections
            sections = self.extract_sections(content)
            
            # Look for claims sections
            for section_name, section_content in sections.items():
                if 'ισχυρισμ' in section_name.lower() or 'claim' in section_name.lower():
                    # Parse individual claims
                    claims = self._parse_claims_section(section_content)
                    result["claims"].extend(claims)
                elif 'πηγ' in section_name.lower() or 'source' in section_name.lower():
                    # Parse source quality
                    quality = self._parse_source_quality(section_content)
                    result["source_quality"].update(quality)
            
            # If no sections found, try to parse the whole content
            if not result["claims"]:
                claims = self._parse_claims_from_text(content)
                result["claims"] = claims
            
            logger.info(f"Parsed {len(result['claims'])} claims from markdown")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing fact-check markdown: {str(e)}")
            return self._create_fallback_response(content)
    
    def _parse_claims_section(self, content: str) -> List[Dict[str, Any]]:
        """Parse claims from a section"""
        claims = []
        
        # Split by claim markers (###, numbers, or strong text)
        claim_blocks = re.split(r'(?:^|\n)(?:###\s*|(?:\d+\.?\s*)?(?:\*\*)?Ισχυρισμός|Claim)', content)
        
        for block in claim_blocks[1:]:  # Skip first empty block
            claim_data = self._parse_single_claim(block)
            if claim_data:
                claims.append(claim_data)
        
        return claims
    
    def _parse_single_claim(self, block: str) -> Optional[Dict[str, Any]]:
        """Parse a single claim block"""
        try:
            lines = block.strip().split('\n')
            if not lines:
                return None
            
            # Extract claim text (usually first line or after colon)
            claim_text = lines[0].strip()
            if ':' in claim_text:
                claim_text = claim_text.split(':', 1)[1].strip()
            claim_text = claim_text.strip('"\'')
            
            # Extract key-value pairs
            kv_pairs = self.extract_key_value_pairs(block)
            
            # Map Greek assessments to our schema
            assessment_map = {
                'αληθές': 'ισχυρά τεκμηριωμένο',
                'μερικώς αληθές': 'μερικώς τεκμηριωμένο',
                'αμφιλεγόμενο': 'αμφιλεγόμενο',
                'παραπλανητικό': 'εκτός πλαισίου',
                'ψευδές': 'ελλιπώς τεκμηριωμένο',
                'μη επαληθεύσιμο': 'χωρίς επαρκή στοιχεία'
            }
            
            # Find assessment
            assessment = 'χωρίς επαρκή στοιχεία'  # default
            for key, value in kv_pairs.items():
                if 'αξιολόγηση' in key.lower() or 'verdict' in key.lower():
                    # Check if value matches any known assessment
                    value_lower = value.lower()
                    for check_key, mapped_value in assessment_map.items():
                        if check_key in value_lower:
                            assessment = mapped_value
                            break
                    else:
                        # Direct match
                        if value in assessment_map.values():
                            assessment = value
            
            # Find explanation/context
            context = ""
            for key, value in kv_pairs.items():
                if 'εξήγηση' in key.lower() or 'context' in key.lower() or 'επεξήγηση' in key.lower():
                    context = value
                    break
            
            # If no context found, use remaining text
            if not context and len(lines) > 1:
                context = ' '.join(lines[1:]).strip()
            
            # Extract sources (look for bullet points or listed items)
            sources = []
            # First try to find sources section with **Πηγές**: pattern
            source_section = re.search(r'\*\*Πηγές\*\*:\s*(.*?)(?:\n\n|\n###|$)', block, re.DOTALL)
            if source_section:
                source_text = source_section.group(1)
                sources = self.extract_bullet_points(source_text)
            else:
                # Fallback to simpler pattern
                source_section = re.search(r'(?:Πηγές|Sources|Πηγή):\s*(.*?)(?:\n\n|$)', block, re.DOTALL)
                if source_section:
                    source_text = source_section.group(1)
                    sources = self.extract_bullet_points(source_text)
            
            return {
                "claim": claim_text,
                "evidence_assessment": assessment,
                "context": context,
                "sources": sources
            }
            
        except Exception as e:
            logger.warning(f"Error parsing claim block: {str(e)}")
            return None
    
    def _parse_claims_from_text(self, content: str) -> List[Dict[str, Any]]:
        """Fallback: Parse claims from unstructured text"""
        claims = []
        
        # Try to find claim patterns
        # Pattern 1: "Claim: ..." or "Ισχυρισμός: ..."
        pattern1 = r'(?:Ισχυρισμός|Claim)\s*\d*\s*:\s*([^\n]+)'
        matches = re.findall(pattern1, content, re.IGNORECASE)
        
        for match in matches[:5]:  # Max 5 claims
            claims.append({
                "claim": match.strip(),
                "evidence_assessment": "χωρίς επαρκή στοιχεία",
                "context": "Δεν ήταν δυνατή η πλήρης ανάλυση από το κείμενο.",
                "sources": []
            })
        
        # If no claims found, create a generic one
        if not claims:
            claims.append({
                "claim": "Δεν εντοπίστηκαν συγκεκριμένοι ισχυρισμοί",
                "evidence_assessment": "χωρίς επαρκή στοιχεία",
                "context": content[:500] + "..." if len(content) > 500 else content,
                "sources": []
            })
        
        return claims
    
    def _parse_source_quality(self, content: str) -> Dict[str, Any]:
        """Parse source quality information"""
        quality = {}
        
        # Look for numbers
        numbers = re.findall(r'(\d+)\s*(?:πρωτογεν|primary)', content, re.IGNORECASE)
        if numbers:
            quality["primary_sources"] = int(numbers[0])
        
        numbers = re.findall(r'(\d+)\s*(?:δευτερογεν|secondary)', content, re.IGNORECASE)
        if numbers:
            quality["secondary_sources"] = int(numbers[0])
        
        # Look for diversity assessment
        if 'υψηλή' in content:
            quality["source_diversity"] = "υψηλή"
        elif 'μέτρια' in content:
            quality["source_diversity"] = "μέτρια"
        elif 'χαμηλή' in content:
            quality["source_diversity"] = "χαμηλή"
        
        return quality
    
    def _create_fallback_response(self, content: str) -> Dict[str, Any]:
        """Create fallback response for unparseable content"""
        return {
            "claims": [{
                "claim": "Σφάλμα ανάλυσης περιεχομένου",
                "evidence_assessment": "χωρίς επαρκή στοιχεία",
                "context": f"Το περιεχόμενο δεν μπόρεσε να αναλυθεί σωστά. Πρωτότυπο: {content[:300]}...",
                "sources": []
            }],
            "source_quality": {
                "primary_sources": 0,
                "secondary_sources": 0,
                "source_diversity": "άγνωστο"
            }
        }


class JargonParser(MarkdownParser):
    """Parser for jargon explanation markdown responses"""
    
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse jargon markdown to structured data"""
        try:
            result = {"terms": []}
            
            # Extract sections
            sections = self.extract_sections(content)
            
            # Look for terms sections
            for section_name, section_content in sections.items():
                if 'όρ' in section_name.lower() or 'term' in section_name.lower():
                    terms = self._parse_terms_section(section_content)
                    result["terms"].extend(terms)
            
            # If no sections, parse whole content
            if not result["terms"]:
                terms = self._parse_terms_from_text(content)
                result["terms"] = terms
            
            logger.info(f"Parsed {len(result['terms'])} terms from markdown")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing jargon markdown: {str(e)}")
            return {"terms": []}
    
    def _parse_terms_section(self, content: str) -> List[Dict[str, Any]]:
        """Parse terms from a section"""
        terms = []
        
        # Split by term markers
        term_blocks = re.split(r'(?:^|\n)(?:###\s*|\*\*)', content)
        
        for block in term_blocks[1:]:
            term_data = self._parse_single_term(block)
            if term_data:
                terms.append(term_data)
        
        return terms
    
    def _parse_single_term(self, block: str) -> Optional[Dict[str, Any]]:
        """Parse a single term block"""
        try:
            lines = block.strip().split('\n')
            if not lines:
                return None
            
            # Extract term (first line)
            term = lines[0].strip()
            if ':' in term:
                parts = term.split(':', 1)
                term = parts[0].strip().rstrip('*')
                explanation = parts[1].strip()
            else:
                term = term.rstrip('*:')
                explanation = ' '.join(lines[1:]).strip() if len(lines) > 1 else ""
            
            # Clean up explanation
            explanation = explanation.strip()
            if not explanation and len(lines) > 1:
                explanation = ' '.join(lines[1:]).strip()
            
            return {
                "term": term,
                "explanation": explanation,
                "sources": []
            }
            
        except Exception as e:
            logger.warning(f"Error parsing term block: {str(e)}")
            return None
    
    def _parse_terms_from_text(self, content: str) -> List[Dict[str, Any]]:
        """Fallback: Parse terms from unstructured text"""
        terms = []
        
        # Pattern: **Term**: Explanation
        pattern = r'\*\*([^*]+)\*\*\s*:\s*([^\n]+(?:\n(?!\*\*)[^\n]+)*)'
        matches = re.findall(pattern, content)
        
        for term, explanation in matches:
            terms.append({
                "term": term.strip(),
                "explanation": explanation.strip(),
                "sources": []
            })
        
        return terms


class ViewpointsParser(MarkdownParser):
    """Parser for viewpoints markdown responses"""
    
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse viewpoints markdown to structured data"""
        try:
            result = {
                "topic_analysis": "",
                "alternative_perspectives": "",
                "key_sources": []
            }
            
            # Extract sections
            sections = self.extract_sections(content)
            
            # Map sections to result fields
            for section_name, section_content in sections.items():
                lower_name = section_name.lower()
                
                if 'ανάλυση' in lower_name or 'θέμα' in lower_name or 'topic' in lower_name:
                    result["topic_analysis"] = section_content.strip()
                elif 'οπτικ' in lower_name or 'perspective' in lower_name or 'άποψ' in lower_name:
                    result["alternative_perspectives"] = section_content.strip()
                elif 'πηγ' in lower_name or 'source' in lower_name:
                    sources = self._parse_sources(section_content)
                    result["key_sources"] = sources
            
            # If no specific perspectives section, use all remaining content
            if not result["alternative_perspectives"] and not result["topic_analysis"]:
                result["alternative_perspectives"] = content.strip()
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing viewpoints markdown: {str(e)}")
            return {
                "topic_analysis": "Σφάλμα ανάλυσης",
                "alternative_perspectives": content[:1000],
                "key_sources": []
            }
    
    def _parse_sources(self, content: str) -> List[Dict[str, str]]:
        """Parse source list"""
        sources = []
        bullets = self.extract_bullet_points(content)
        
        for bullet in bullets:
            # Try to split source and summary
            if ':' in bullet:
                source, summary = bullet.split(':', 1)
                sources.append({
                    "source": source.strip(),
                    "perspective_summary": summary.strip()
                })
            else:
                sources.append({
                    "source": bullet,
                    "perspective_summary": ""
                })
        
        return sources


# Export main parsers
PARSERS = {
    'fact-check': FactCheckParser(),
    'jargon': JargonParser(),
    'viewpoints': ViewpointsParser()
}


def parse_markdown_response(content: str, analysis_type: str) -> Dict[str, Any]:
    """Main entry point for parsing markdown responses"""
    parser = PARSERS.get(analysis_type)
    
    if parser:
        return parser.parse(content)
    else:
        # Generic parsing for other types
        logger.warning(f"No specific parser for {analysis_type}, returning raw content")
        return {"content": content}