# api/greek_sources_config.py
"""
Configuration file for Greek news sources and domain mappings.
This file should be regularly updated as sources change.
Note: X handles are NOT hardcoded - they are discovered dynamically by Grok.
"""

# Greek news source to domain mappings
# Used for matching source mentions to citation URLs
SOURCE_TO_DOMAINS = {
    # Major Greek newspapers
    "kathimerini": ["kathimerini.gr"],
    "καθημερινή": ["kathimerini.gr"],
    "tanea": ["tanea.gr"],
    "τα νέα": ["tanea.gr"],
    "protothema": ["protothema.gr"],
    "πρώτο θέμα": ["protothema.gr"],
    "tovima": ["tovima.gr"],
    "το βήμα": ["tovima.gr"],
    "ethnos": ["ethnos.gr"],
    "έθνος": ["ethnos.gr"],
    "naftemporiki": ["naftemporiki.gr"],
    "ναυτεμπορική": ["naftemporiki.gr"],
    
    # TV stations and their news sites
    "skai": ["skai.gr"],
    "σκαϊ": ["skai.gr"],
    "ant1": ["ant1news.gr"],
    "antenna": ["antenna.gr"],
    "mega": ["megatv.com", "mega.gr"],
    "μεγκα": ["megatv.com", "mega.gr"],
    "alpha": ["alphatv.gr"],
    "άλφα": ["alphatv.gr"],
    "star": ["star.gr"],
    "open": ["open-tv.gr"],
    "ert": ["ert.gr", "ertnews.gr"],
    "ερτ": ["ert.gr", "ertnews.gr"],
    
    # Digital-first news
    "cnn greece": ["cnn.gr"],
    "cnn ελλάδα": ["cnn.gr"],
    "in.gr": ["in.gr"],
    "in": ["in.gr"],
    "iefimerida": ["iefimerida.gr"],
    "ιεφημερίδα": ["iefimerida.gr"],
    "newsbeast": ["newsbeast.gr"],
    "news247": ["news247.gr"],
    "newsit": ["newsit.gr"],
    "enikos": ["enikos.gr"],
    "ενικός": ["enikos.gr"],
    "pronews": ["pronews.gr"],
    
    # Alternative/Political news
    "efsyn": ["efsyn.gr"],
    "εφσυν": ["efsyn.gr"],
    "εφημερίδα των συντακτών": ["efsyn.gr"],
    "avgi": ["avgi.gr"],
    "αυγή": ["avgi.gr"],
    "documento": ["documento.gr"],
    "ντοκουμέντο": ["documento.gr"],
    "liberal": ["liberal.gr"],
    "thetoc": ["thetoc.gr"],
    "the toc": ["thetoc.gr"],
    "tpp": ["thepressproject.gr"],
    "press project": ["thepressproject.gr"],
    
    # Regional
    "makedonia": ["makthes.gr"],
    "μακεδονία": ["makthes.gr"],
    "real": ["real.gr"],
    "real news": ["real.gr"],
    
    # Business/Financial
    "capital": ["capital.gr"],
    "reporter": ["reporter.gr"],
    "euro2day": ["euro2day.gr"],
    "imerisia": ["imerisia.gr"],
    "ημερησία": ["imerisia.gr"],
    
    # International
    "bloomberg": ["bloomberg.com"],
    "reuters": ["reuters.com"],
    "bbc": ["bbc.com", "bbc.co.uk"],
    "guardian": ["theguardian.com"],
    "financial times": ["ft.com"],
    "ap": ["apnews.com"],
    "associated press": ["apnews.com"],
    
    # Social Media
    "twitter": ["twitter.com", "x.com"],
    "x": ["twitter.com", "x.com"],
}

# Low-credibility sites to potentially exclude
# Note: Use with caution - exclusion should be context-dependent
LOW_CREDIBILITY_SITES = [
    # Add domains here that are known for misinformation
    # This list should be regularly reviewed and updated
    # Example: "example-fake-news.gr"
]

# RSS feeds for specific topics (optional)
RSS_FEEDS = {
    "government": [
        "https://www.primeminister.gr/feed",
        # Add more government RSS feeds
    ],
    "economy": [
        # Add economy-focused RSS feeds
    ],
    # Add more categories as needed
}