# api/citation_processor.py
"""
Citation processing utilities to match Grok's returned citations with source mentions.
Validates that citations are real and not hallucinated.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse


def extract_source_mentions(text: str) -> List[str]:
    """
    Extract source mentions from text (e.g., "according to Kathimerini", "SKAI reported").
    
    Args:
        text: Text containing source mentions
        
    Returns:
        List of source names mentioned in the text
    """
    # Common Greek news source patterns
    patterns = [
        r"σύμφωνα με (?:το |την |τον )?([Α-Ωα-ωA-Za-z0-9\s\.]+)",  # according to
        r"όπως (?:αναφέρει|αναφέρουν|μετέδωσε) (?:το |την |τον )?([Α-Ωα-ωA-Za-z0-9\s\.]+)",  # as reported by
        r"(?:το |την |τον )?([Α-Ωα-ωA-Za-z0-9\s\.]+) (?:ανέφερε|μετέδωσε|δημοσίευσε)",  # X reported
        r"πηγή: ([Α-Ωα-ωA-Za-z0-9\s\.]+)",  # source: X
        r"από (?:το |την |τον )?([Α-Ωα-ωA-Za-z0-9\s\.]+)",  # from X
    ]
    
    sources = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        sources.extend([match.strip() for match in matches])
    
    # Normalize and deduplicate
    normalized = []
    for source in sources:
        # Remove articles and clean up
        source = source.replace("το ", "").replace("την ", "").replace("τον ", "")
        source = source.strip(" .")
        if source and source not in normalized:
            normalized.append(source)
    
    return normalized


def match_citations_to_sources(
    response_text: str, 
    citations: List[str],
    source_mentions: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """
    Match Grok's returned citations to source mentions in the text.
    
    Args:
        response_text: The AI's response text
        citations: List of citation URLs from Grok
        source_mentions: Optional pre-extracted source mentions
        
    Returns:
        Dict mapping source mentions to their citation URLs
    """
    if source_mentions is None:
        source_mentions = extract_source_mentions(response_text)
    
    # Create mapping of domains to citations
    domain_to_citations = {}
    for citation in citations:
        try:
            parsed = urlparse(citation)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            domain = domain.replace("www.", "")
            if domain not in domain_to_citations:
                domain_to_citations[domain] = []
            domain_to_citations[domain].append(citation)
        except:
            continue
    
    # Import source mappings from config file
    from .greek_sources_config import SOURCE_TO_DOMAINS
    source_to_domains = SOURCE_TO_DOMAINS
    
    # Match sources to citations
    source_citations = {}
    for source in source_mentions:
        source_lower = source.lower()
        matched_citations = []
        
        # Check if source matches known mappings
        for known_source, domains in source_to_domains.items():
            if known_source in source_lower or source_lower in known_source:
                for domain in domains:
                    if domain in domain_to_citations:
                        matched_citations.extend(domain_to_citations[domain])
        
        # Also check if source directly matches a domain
        for domain, cites in domain_to_citations.items():
            if source_lower in domain or domain in source_lower:
                matched_citations.extend(cites)
        
        if matched_citations:
            source_citations[source] = list(set(matched_citations))  # Deduplicate
    
    return source_citations


def validate_citations(
    analysis_result: Dict[str, Any],
    citations: List[str]
) -> Tuple[bool, List[str]]:
    """
    Validate that the analysis result properly references real citations.
    
    Args:
        analysis_result: The analysis result dictionary
        citations: List of citation URLs from Grok
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Extract all text that might contain source mentions
    all_text = ""
    
    def extract_text(obj):
        if isinstance(obj, str):
            return obj
        elif isinstance(obj, dict):
            text = ""
            for value in obj.values():
                text += " " + extract_text(value)
            return text
        elif isinstance(obj, list):
            text = ""
            for item in obj:
                text += " " + extract_text(item)
            return text
        return ""
    
    all_text = extract_text(analysis_result)
    
    # Extract source mentions
    source_mentions = extract_source_mentions(all_text)
    
    if not source_mentions and citations:
        issues.append("Δεν βρέθηκαν αναφορές σε πηγές στο κείμενο παρόλο που υπάρχουν citations")
    
    # Match citations to sources
    source_citation_map = match_citations_to_sources(all_text, citations, source_mentions)
    
    # Check for unmatched sources
    unmatched_sources = [s for s in source_mentions if s not in source_citation_map]
    if unmatched_sources:
        issues.append(f"Πηγές χωρίς αντίστοιχα citations: {', '.join(unmatched_sources)}")
    
    # Check if we have orphaned citations (citations not matched to any source)
    matched_citations = set()
    for cites in source_citation_map.values():
        matched_citations.update(cites)
    
    orphaned_citations = [c for c in citations if c not in matched_citations]
    if len(orphaned_citations) > len(citations) * 0.5:  # More than 50% unmatched
        issues.append(f"Πολλά citations ({len(orphaned_citations)}/{len(citations)}) δεν αντιστοιχούν σε αναφορές πηγών")
    
    is_valid = len(issues) == 0
    return is_valid, issues


def enrich_response_with_citations(
    analysis_result: Dict[str, Any],
    citations: List[str]
) -> Dict[str, Any]:
    """
    Enrich the analysis result by adding citation URLs to source mentions.
    
    Args:
        analysis_result: The original analysis result
        citations: List of citation URLs from Grok
        
    Returns:
        Enriched analysis result with citation URLs added
    """
    # Deep copy the result
    import copy
    enriched = copy.deepcopy(analysis_result)
    
    # Extract all text and match citations
    all_text = ""
    def extract_text(obj):
        if isinstance(obj, str):
            return obj
        elif isinstance(obj, dict):
            return " ".join(extract_text(v) for v in obj.values())
        elif isinstance(obj, list):
            return " ".join(extract_text(item) for item in obj)
        return ""
    
    all_text = extract_text(analysis_result)
    source_citation_map = match_citations_to_sources(all_text, citations)
    
    # Add a citations section to the enriched result
    enriched["_citations"] = {
        "all_citations": citations,
        "source_mapping": source_citation_map,
        "unmatched_citations": [
            c for c in citations 
            if c not in sum(source_citation_map.values(), [])
        ]
    }
    
    return enriched


