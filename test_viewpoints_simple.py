#!/usr/bin/env python3
"""Simple test to debug viewpoints agent issue"""

import os
import sys

# Add api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

# Test the debug CLI
os.system(f"python debug_agents.py https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/ --agent viewpoints --level verbose")