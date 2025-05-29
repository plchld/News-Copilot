"""
Simplified AI Enrichment for articles
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.article_processor import ProcessedArticle
from config.config import XAI_API_KEY, ENRICHED_DIR, GROK_API_BASE_URL, GROK_DEFAULT_MODEL, GROK_MINI_MODEL


@dataclass 
class SimpleEnrichedArticle:
    """Simplified enriched article"""
    original_article: ProcessedArticle
    enrichments: Dict[str, Any]
    metadata: Dict[str, Any]


class SimpleAIEnrichment:
    """Simplified AI enrichment using direct API calls"""
    
    def __init__(self):
        self.api_key = XAI_API_KEY
        self.base_url = GROK_API_BASE_URL
        
    def enrich_article(self, article: ProcessedArticle) -> SimpleEnrichedArticle:
        """Enrich article with AI analysis"""
        start_time = datetime.now()
        print(f"[SimpleAIEnrichment] Starting enrichment for: {article.title[:50]}...")
        
        enrichments = {}
        
        # 1. Extract jargon terms
        try:
            jargon = self._analyze_jargon(article.content)
            enrichments["jargon"] = jargon
            print("✓ Jargon analysis complete")
        except Exception as e:
            print(f"✗ Jargon analysis failed: {e}")
            enrichments["jargon"] = {"error": str(e)}
        
        # 2. Analyze bias
        try:
            bias = self._analyze_bias(article.content)
            enrichments["bias"] = bias
            print("✓ Bias analysis complete")
        except Exception as e:
            print(f"✗ Bias analysis failed: {e}")
            enrichments["bias"] = {"error": str(e)}
        
        # 3. Generate summary
        try:
            summary = self._generate_summary(article.content)
            enrichments["summary"] = summary
            print("✓ Summary generation complete")
        except Exception as e:
            print(f"✗ Summary generation failed: {e}")
            enrichments["summary"] = {"error": str(e)}
        
        # Create enriched article
        duration = (datetime.now() - start_time).total_seconds()
        enriched = SimpleEnrichedArticle(
            original_article=article,
            enrichments=enrichments,
            metadata={
                "enrichment_date": datetime.now().isoformat(),
                "duration_seconds": duration,
                "analyses_completed": [k for k, v in enrichments.items() if "error" not in v]
            }
        )
        
        print(f"[SimpleAIEnrichment] Completed in {duration:.1f}s")
        return enriched
    
    def _make_api_call(self, prompt: str, model: str = None) -> str:
        """Make a simple API call to Grok"""
        import requests
        
        if not self.api_key:
            raise ValueError("XAI_API_KEY not set")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model or GROK_DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": "You are a Greek news analysis assistant. Always respond in Greek."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _analyze_jargon(self, content: str) -> Dict[str, Any]:
        """Extract and explain jargon terms"""
        prompt = f"""Αναλύστε το παρακάτω άρθρο και εντοπίστε τεχνικούς όρους ή ορολογία που μπορεί να χρειάζεται επεξήγηση.

Άρθρο:
{content[:1500]}

Απαντήστε σε JSON μορφή:
{{
  "terms": [
    {{
      "term": "όρος",
      "explanation": "επεξήγηση",
      "context": "πώς χρησιμοποιείται στο άρθρο"
    }}
  ]
}}"""
        
        response = self._make_api_call(prompt, model=GROK_MINI_MODEL)
        
        # Try to parse JSON response
        try:
            return json.loads(response)
        except:
            return {"raw_response": response}
    
    def _analyze_bias(self, content: str) -> Dict[str, Any]:
        """Analyze political bias"""
        prompt = f"""Αναλύστε την πολιτική τοποθέτηση του παρακάτω άρθρου στο ελληνικό πολιτικό φάσμα.

Άρθρο:
{content[:1500]}

Απαντήστε με:
1. Πολιτική κλίση (αριστερά, κέντρο-αριστερά, κέντρο, κέντρο-δεξιά, δεξιά)
2. Στοιχεία που υποστηρίζουν την ανάλυση
3. Τόνος (ουδέτερος, θετικός, αρνητικός)"""
        
        response = self._make_api_call(prompt)
        return {"analysis": response}
    
    def _generate_summary(self, content: str) -> Dict[str, Any]:
        """Generate article summary"""
        prompt = f"""Δημιουργήστε μια σύντομη περίληψη (3-4 προτάσεις) του παρακάτω άρθρου:

{content[:2000]}

Η περίληψη πρέπει να περιλαμβάνει τα κύρια σημεία και να είναι κατανοητή."""
        
        response = self._make_api_call(prompt, model=GROK_MINI_MODEL)
        return {"summary": response}
    
    def save_enriched_article(self, enriched: SimpleEnrichedArticle) -> str:
        """Save enriched article to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in enriched.original_article.title 
                           if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        
        filename = f"{timestamp}_{safe_title}_enriched.json"
        filepath = os.path.join(ENRICHED_DIR, filename)
        
        data = {
            "article": asdict(enriched.original_article),
            "enrichments": enriched.enrichments,
            "metadata": enriched.metadata
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[SimpleAIEnrichment] Saved to: {filepath}")
        return filepath