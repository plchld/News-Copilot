"""Mock response data for testing agents"""

import json
from typing import Dict, Any, List


class MockAgentResponses:
    """Mock responses for different agent types"""
    
    @staticmethod
    def discovery_response(category: str) -> str:
        """Mock discovery agent response"""
        stories = {
            "greek_politics": [
                {
                    "headline": "Υπουργικό συμβούλιο για νέα οικονομικά μέτρα",
                    "why_important": "Αναμένονται σημαντικές αλλαγές στη φορολογία και τις συντάξεις",
                    "key_facts": [
                        "Συνεδρίαση την Τετάρτη υπό τον Πρωθυπουργό",
                        "Προτάσεις για μείωση φόρων σε μεσαία εισοδήματα",
                        "Αύξηση κατώτατου μισθού κατά 5%"
                    ],
                    "greek_relevance": 1.0,
                    "initial_sources_found": 15,
                    "category_match": 0.95
                },
                {
                    "headline": "Ελληνοτουρκικά: Νέος γύρος διερευνητικών επαφών",
                    "why_important": "Κρίσιμες συνομιλίες για θαλάσσιες ζώνες και ενεργειακά",
                    "key_facts": [
                        "65ος γύρος διερευνητικών στην Αθήνα",
                        "Συζήτηση για οριοθέτηση ΑΟΖ",
                        "Παρουσία διεθνών παρατηρητών"
                    ],
                    "greek_relevance": 1.0,
                    "initial_sources_found": 22,
                    "category_match": 0.9
                }
            ],
            "global_politics": [
                {
                    "headline": "EU Proposes Sweeping AI Regulations",
                    "why_important": "Will affect all tech companies operating in Europe, including Greek startups",
                    "key_facts": [
                        "Vote scheduled for March 15",
                        "Applies to companies with over 10M users",
                        "Fines up to 7% of global revenue",
                        "Greek tech sector concerned about compliance costs"
                    ],
                    "greek_relevance": 0.7,
                    "initial_sources_found": 45,
                    "category_match": 0.85
                }
            ],
            "economy_business": [
                {
                    "headline": "Τουρισμός: Ρεκόρ κρατήσεων για το 2025",
                    "why_important": "Ο τουρισμός αποτελεί το 25% του ΑΕΠ της Ελλάδας",
                    "key_facts": [
                        "Αύξηση 15% στις προκρατήσεις vs 2024",
                        "Νέες αγορές από Ασία και Μ. Ανατολή",
                        "Επενδύσεις 2 δισ. σε ξενοδοχειακές μονάδες"
                    ],
                    "greek_relevance": 1.0,
                    "initial_sources_found": 18,
                    "category_match": 0.92
                }
            ]
        }
        
        return json.dumps({
            "stories": stories.get(category, [])[:2],
            "search_summary": f"Found top stories in {category} category",
            "category": category
        })
    
    @staticmethod
    def greek_perspective_response() -> str:
        """Mock Greek perspective response"""
        return json.dumps({
            "topic": "EU AI Regulations",
            "summary": "Greek media focuses heavily on the impact to local tech startups and the brain drain concern. Major outlets emphasize the compliance burden on small companies while seeing opportunities in the compliance services sector. There's significant concern about Greek startups relocating to non-EU countries.",
            "analysis": {
                "dominant_narrative": "EU overreach threatening Greek tech innovation",
                "unique_angles": [
                    "Brain drain acceleration fears",
                    "Opportunity for Greek compliance tech companies",
                    "Concerns about startup competitiveness"
                ],
                "emphasized_aspects": [
                    "Cost burden on small companies",
                    "Risk of talent exodus",
                    "Need for government support"
                ],
                "ignored_aspects": [
                    "Consumer protection benefits",
                    "Long-term innovation incentives"
                ],
                "political_spin": "Opposition criticizes government for not protecting tech sector",
                "source_diversity": "high",
                "public_sentiment": "Worried about economic impact"
            },
            "key_sources": ["kathimerini.gr", "tanea.gr", "capital.gr", "skai.gr"],
            "confidence": 0.85
        })
    
    @staticmethod
    def international_perspective_response() -> str:
        """Mock international perspective response"""
        return json.dumps({
            "topic": "EU AI Regulations",
            "summary": "International coverage varies significantly by region. US tech press sees it as Brussels overreach and innovation killer. Chinese media frames it as giving China competitive advantage. EU coverage is more balanced, emphasizing consumer protection.",
            "analysis": {
                "global_consensus": "Regulations will have major impact on AI development",
                "regional_differences": [
                    {
                        "region": "US",
                        "narrative": "Europe regulating itself out of AI race",
                        "emphasis": ["Innovation stifling", "Compliance costs", "Tech exodus"],
                        "cultural_context": "Silicon Valley libertarian tech culture"
                    },
                    {
                        "region": "EU",
                        "narrative": "Necessary protection for citizens",
                        "emphasis": ["Consumer rights", "Ethical AI", "Level playing field"],
                        "cultural_context": "European social market economy model"
                    },
                    {
                        "region": "China",
                        "narrative": "Opportunity for Chinese AI dominance",
                        "emphasis": ["Western self-limitation", "Chinese innovation", "Market opportunities"],
                        "cultural_context": "Tech competition narrative"
                    }
                ],
                "contested_facts": [
                    "Implementation timeline varies by source",
                    "Penalty amounts disputed"
                ],
                "missing_perspectives": ["African markets", "Latin American view"],
                "bias_patterns": {
                    "US": "Pro-business, anti-regulation",
                    "EU": "Pro-consumer, balanced",
                    "China": "Competitive advantage focus"
                }
            },
            "regions_covered": ["US", "UK", "EU", "China"],
            "confidence": 0.8
        })
    
    @staticmethod
    def opposing_view_response() -> str:
        """Mock opposing view response"""
        return json.dumps({
            "topic": "EU AI Regulations",
            "summary": "Critics argue the regulations were heavily influenced by big tech lobbying, creating loopholes for large companies while burdening small ones. Some experts claim the rules won't actually protect consumers but will stifle European innovation.",
            "analysis": {
                "mainstream_gaps": [
                    "Big tech lobbying influence on final text",
                    "Loopholes for major platforms",
                    "Enforcement challenges"
                ],
                "alternative_narratives": [
                    {
                        "viewpoint": "Regulations favor big tech over startups",
                        "source_type": "independent",
                        "key_arguments": [
                            "Compliance costs create barriers to entry",
                            "Big tech can afford legal teams",
                            "Grandfather clauses benefit incumbents"
                        ],
                        "evidence_quality": "moderate"
                    },
                    {
                        "viewpoint": "Rules won't actually protect consumers",
                        "source_type": "expert",
                        "key_arguments": [
                            "Technical requirements are outdated",
                            "Easy workarounds exist",
                            "Focus on process not outcomes"
                        ],
                        "evidence_quality": "moderate"
                    }
                ],
                "disputed_claims": [
                    "Claim: Will create 10,000 compliance jobs - Fact-checkers say unverifiable"
                ],
                "reasonable_skepticism": [
                    "Enforcement capacity questions",
                    "Technical feasibility concerns"
                ],
                "conspiracy_warnings": ["Claims about deliberate economic sabotage are unfounded"]
            },
            "credibility_assessment": "Mixed - some valid concerns, some speculation",
            "confidence": 0.7
        })
    
    @staticmethod
    def fact_verification_response() -> str:
        """Mock fact verification response"""
        return json.dumps({
            "topic": "EU AI Regulations",
            "summary": "Key facts verified: Vote date confirmed for March 15. User threshold of 10M verified. Penalty amounts disputed between sources (6-7% of revenue). Implementation timeline remains uncertain.",
            "analysis": {
                "verified_facts": [
                    {
                        "claim": "Vote scheduled for March 15",
                        "verdict": "confirmed",
                        "confidence": 0.95,
                        "sources": ["EU Parliament website", "Reuters", "Bloomberg"],
                        "notes": "Official EU Parliament schedule"
                    },
                    {
                        "claim": "Applies to companies with over 10M users",
                        "verdict": "confirmed",
                        "confidence": 0.9,
                        "sources": ["Draft legislation text", "EU Commission"],
                        "notes": "Threshold clearly stated in Article 3"
                    },
                    {
                        "claim": "Fines up to 7% of global revenue",
                        "verdict": "partially-true",
                        "confidence": 0.7,
                        "sources": ["Various news outlets"],
                        "notes": "Some sources say 6%, others 7%"
                    }
                ],
                "primary_sources": [
                    "EU Parliament official documents",
                    "European Commission statements",
                    "Draft AI Act text"
                ],
                "conflicting_reports": [
                    "Implementation timeline (18-24 months)",
                    "Exact penalty percentages"
                ],
                "data_quality": "high",
                "key_uncertainties": [
                    "Final text may change before vote",
                    "Implementation details unclear"
                ]
            },
            "overall_reliability": 0.82,
            "recommendations": [
                "Wait for final vote for definitive details",
                "Check EU official sources for updates"
            ]
        })
    
    @staticmethod
    def narrative_synthesis_response() -> str:
        """Mock narrative synthesis response"""
        return json.dumps({
            "topic": "EU AI Regulations",
            "narrative": {
                "introduction": "The European Union stands poised to implement the world's most comprehensive artificial intelligence regulations, a move that has sparked intense debate across the global tech landscape.",
                "main_narrative": "On March 15, the European Parliament will vote on sweeping AI regulations that could reshape the technology sector. The proposed rules, which would apply to companies with over 10 million users, have generated starkly different reactions worldwide. Greek media emphasizes the potential burden on local startups, with outlets like Kathimerini warning of a possible brain drain as talented engineers may flee to less regulated markets. The Greek tech sector particularly fears the compliance costs, though some see opportunities in developing compliance solutions. International perspectives vary dramatically by region. American tech publications largely frame this as European overreach that will stifle innovation, while Chinese media suggests it hands them a competitive advantage. European sources present a more balanced view, emphasizing consumer protection and ethical AI development. Critics and fact-checkers have raised important concerns. Some argue the regulations were influenced by big tech lobbying, creating loopholes that favor large companies while burdening smaller ones. Independent analysts question whether the rules will achieve their stated consumer protection goals, noting technical requirements may already be outdated. What remains undisputed is the vote date and the 10-million user threshold, though penalty amounts remain contested between 6-7% of global revenue.",
                "agreements": [
                    "Vote scheduled for March 15",
                    "Major impact on AI development",
                    "Compliance will be costly"
                ],
                "divergences": [
                    "Whether it helps or hinders innovation",
                    "Impact on competitiveness",
                    "Effectiveness of consumer protection"
                ],
                "nuances": [
                    "Greek startups face unique challenges",
                    "Big tech may benefit despite rhetoric",
                    "Implementation details remain unclear"
                ],
                "conclusion": "The EU's AI regulations represent a defining moment for technology governance, with impacts that will ripple through economies and societies, particularly affecting smaller markets like Greece."
            },
            "perspective_attribution": {
                "Greek concern": "Brain drain and startup burden",
                "US view": "Innovation killer",
                "EU view": "Necessary protection",
                "Critics": "Big tech influence"
            },
            "narrative_tone": "balanced",
            "completeness_score": 0.85
        })
    
    @staticmethod
    def social_pulse_response() -> str:
        """Mock social pulse response"""
        return json.dumps({
            "topic": "EU AI Regulations",
            "summary": "Social media discussion is highly polarized with tech workers largely opposing while privacy advocates support. Misinformation about immediate bans on AI tools is spreading. Main questions focus on how it affects everyday AI tools like ChatGPT.",
            "analysis": {
                "trending_hashtags": ["#AIAct", "#BrusselsEffect", "#EUtech", "#AIRegulation"],
                "sentiment_clusters": [
                    {
                        "sentiment": "negative",
                        "themes": ["Innovation killing", "Overregulation", "Tech exodus"],
                        "size": "large",
                        "example_views": [
                            "Europe just regulated itself out of the AI race",
                            "RIP European tech startups"
                        ]
                    },
                    {
                        "sentiment": "positive",
                        "themes": ["Consumer protection", "Ethical AI", "Level playing field"],
                        "size": "medium",
                        "example_views": [
                            "Finally some rules for AI safety",
                            "EU leading on digital rights again"
                        ]
                    }
                ],
                "influencer_takes": [
                    {
                        "influencer_type": "tech_journalist",
                        "stance": "Critical but nuanced",
                        "reach": "high",
                        "key_points": [
                            "Devil is in implementation details",
                            "Could have unintended consequences"
                        ]
                    }
                ],
                "misinformation_alerts": [
                    {
                        "claim": "ChatGPT will be banned in EU immediately",
                        "spread_level": "high",
                        "correction": "Regulations have 18-24 month implementation period",
                        "sources_spreading": ["Panic accounts", "Misinterpretation of draft"]
                    }
                ],
                "public_questions": [
                    "Will ChatGPT still work in Europe?",
                    "How will this affect AI job market?",
                    "What counts as 'high-risk' AI?"
                ],
                "engagement_level": "very-high"
            },
            "platform_focus": ["X/Twitter", "LinkedIn", "Reddit"],
            "temperature": "heated",
            "key_insight": "Tech community fears are driving negative sentiment"
        })
    
    @staticmethod
    def timeline_response() -> str:
        """Mock timeline response"""
        return json.dumps({
            "topic": "EU AI Regulations history",
            "timeline": {
                "events": [
                    {
                        "date": "2021-04",
                        "event": "First AI regulation draft proposed by European Commission",
                        "significance": "Started the regulatory process",
                        "category": "cause",
                        "confidence": 0.95
                    },
                    {
                        "date": "2022-11",
                        "event": "ChatGPT launch accelerates AI concerns",
                        "significance": "Public awareness of AI capabilities surged",
                        "category": "turning-point",
                        "confidence": 0.9
                    },
                    {
                        "date": "2023-06",
                        "event": "European Parliament approves negotiating position",
                        "significance": "Moved regulations toward final form",
                        "category": "cause",
                        "confidence": 0.85
                    },
                    {
                        "date": "2024-12",
                        "event": "Final text agreed in trilogue negotiations",
                        "significance": "Compromise between Parliament, Commission, Council",
                        "category": "turning-point",
                        "confidence": 0.9
                    },
                    {
                        "date": "2025-03",
                        "event": "Final vote scheduled",
                        "significance": "Will determine if regulations become law",
                        "category": "effect",
                        "confidence": 0.95
                    }
                ],
                "pattern_detected": "Accelerating pace as AI capabilities grew",
                "cycle_length": null,
                "key_turning_points": [
                    "ChatGPT launch changed urgency",
                    "Trilogue agreement on final text"
                ],
                "historical_context": "Part of broader EU digital sovereignty push"
            },
            "time_span": "4 years",
            "relevance_score": 0.9,
            "insights": [
                "ChatGPT was a catalyzing event",
                "Process accelerated with AI advancement",
                "Follows typical EU legislative timeline"
            ]
        })
    
    @staticmethod
    def jargon_response() -> str:
        """Mock jargon analysis response"""
        return json.dumps({
            "narrative_analyzed": True,
            "analysis": {
                "terms": [
                    {
                        "term": "AI Act",
                        "explanation": "The proposed European Union law to regulate artificial intelligence systems",
                        "greek_translation": "Νόμος για την ΤΝ",
                        "context": "Official name of the legislation",
                        "category": "political"
                    },
                    {
                        "term": "Compliance costs",
                        "explanation": "Money companies must spend to follow the new rules",
                        "greek_translation": "Κόστος συμμόρφωσης",
                        "context": null,
                        "category": "economic"
                    },
                    {
                        "term": "Brain drain",
                        "explanation": "When talented people leave a country for better opportunities elsewhere",
                        "greek_translation": "Διαρροή εγκεφάλων",
                        "context": "Concern about Greek tech talent leaving",
                        "category": "economic"
                    }
                ],
                "complexity_level": "medium",
                "reading_level": "college",
                "key_concepts": ["AI regulation", "Compliance", "Innovation impact"]
            },
            "jargon_dictionary": {
                "AI Act": "The proposed European Union law to regulate artificial intelligence systems",
                "Compliance costs": "Money companies must spend to follow the new rules",
                "Brain drain": "When talented people leave a country for better opportunities elsewhere"
            },
            "accessibility_score": 0.7,
            "recommendations": [
                "Consider adding brief explanations for technical terms",
                "Define acronyms on first use"
            ]
        })