#!/usr/bin/env python3
"""
News-Copilot Agent Debugging CLI

Usage:
    python debug_agents.py <article_url> [options]
    
Options:
    --agent AGENT       Specific agent to debug (viewpoints, jargon, fact_check, etc.)
    --all               Debug all agents
    --level LEVEL       Debug level: minimal, normal, verbose, extreme (default: verbose)
    --save              Save debug report to file
    --compare           Compare results between agents
    --live              Show live execution progress
    
Examples:
    # Debug viewpoints agent with verbose output
    python debug_agents.py https://kathimerini.gr/... --agent viewpoints
    
    # Debug all agents with minimal output
    python debug_agents.py https://kathimerini.gr/... --all --level minimal
    
    # Debug with extreme verbosity and save report
    python debug_agents.py https://kathimerini.gr/... --agent viewpoints --level extreme --save
"""

import asyncio
import argparse
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Add api directory to path
# Get the absolute path to the project root (News-Copilot)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import our modules
from debug_framework import (
    AgentDebugger, CoordinatorDebugger, DebugLevel,
    debug_single_agent, debug_agent_batch
)
from api.agents.optimized_coordinator import OptimizedAgentCoordinator as AgentCoordinator, AnalysisType
from api.agents.viewpoints_agent import ViewpointsAgent
from api.agents.jargon_agent import JargonAgent
from api.agents.fact_check_agent import FactCheckAgent
from api.agents.bias_agent import BiasAnalysisAgent
from api.agents.timeline_agent import TimelineAgent
from api.agents.expert_agent import ExpertOpinionsAgent
from api.agents.x_pulse_agent import XPulseAgent
from api.core.grok_client import GrokClient
from api.core.article_extractor import fetch_text


# Configure logging
def setup_logging(debug_level: DebugLevel):
    """Configure logging based on debug level"""
    log_level = {
        DebugLevel.MINIMAL: logging.WARNING,
        DebugLevel.NORMAL: logging.INFO,
        DebugLevel.VERBOSE: logging.DEBUG,
        DebugLevel.EXTREME: logging.DEBUG
    }.get(debug_level, logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Quiet some noisy loggers
    if debug_level != DebugLevel.EXTREME:
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)


class LiveProgressHandler:
    """Handler for showing live execution progress"""
    
    def __init__(self):
        self.start_times = {}
        self.completed = []
        
    async def on_agent_start(self, agent_name: str):
        """Called when an agent starts execution"""
        self.start_times[agent_name] = datetime.now()
        print(f"⏳ {agent_name}: Starting...")
        
    async def on_agent_complete(self, agent_name: str, success: bool, error: Optional[str] = None):
        """Called when an agent completes"""
        elapsed = (datetime.now() - self.start_times[agent_name]).total_seconds()
        
        if success:
            print(f"✅ {agent_name}: Completed in {elapsed:.1f}s")
        else:
            print(f"❌ {agent_name}: Failed after {elapsed:.1f}s - {error}")
        
        self.completed.append(agent_name)


async def debug_specific_agent(
    agent_type: str,
    article_url: str,
    debug_level: DebugLevel,
    save_report: bool = False
) -> None:
    """Debug a specific agent"""
    
    # Initialize Grok client
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        print("❌ Error: XAI_API_KEY environment variable not set")
        sys.exit(1)
    
    grok_client = GrokClient()
    
    # Create agent based on type
    agent_map = {
        'viewpoints': lambda: ViewpointsAgent.create(grok_client),
        'jargon': lambda: JargonAgent.create(grok_client),
        'fact_check': lambda: FactCheckAgent.create(grok_client),
        'bias': lambda: BiasAnalysisAgent.create(grok_client),
        'timeline': lambda: TimelineAgent.create(grok_client),
        'expert': lambda: ExpertOpinionsAgent.create(grok_client),
        'x_pulse': lambda: XPulseAgent.create(grok_client)
    }
    
    if agent_type not in agent_map:
        print(f"❌ Error: Unknown agent type '{agent_type}'")
        print(f"Available agents: {', '.join(agent_map.keys())}")
        sys.exit(1)
    
    print(f"\n{'='*80}")
    print(f"🔍 Debugging {agent_type.upper()} Agent")
    print(f"📰 Article: {article_url}")
    print(f"🎚️  Debug Level: {debug_level.value}")
    print(f"{'='*80}\n")
    
    # Extract article first
    print("📥 Extracting article content...")
    try:
        article_text = fetch_text(article_url)
        extraction = {
            'success': True,
            'article': article_text,
            'title': 'Article',
            'author': 'Unknown'
        }
    except Exception as e:
        extraction = {
            'success': False,
            'error': str(e)
        }
    
    if not extraction['success']:
        print(f"❌ Failed to extract article: {extraction.get('error')}")
        sys.exit(1)
    
    print(f"✅ Article extracted successfully")
    print(f"   Title: {extraction.get('title', 'No title')}")
    print(f"   Length: {len(extraction['article'])} characters")
    print()
    
    # Create agent
    agent = agent_map[agent_type]()
    
    # Execute with debugging
    try:
        result, report = await debug_single_agent(agent, article_url, debug_level)
        
        # Display report
        print(report)
        
        # Save if requested
        if save_report:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"debug_report_{agent_type}_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Debug Report Generated: {datetime.now()}\n")
                f.write(f"Agent: {agent_type}\n")
                f.write(f"Article: {article_url}\n")
                f.write(f"Debug Level: {debug_level.value}\n")
                f.write(report)
                
                # Also save raw result data
                if result.success and result.data:
                    f.write("\n\n" + "="*80 + "\n")
                    f.write("RAW RESULT DATA (JSON)\n")
                    f.write("="*80 + "\n")
                    f.write(json.dumps(result.data, indent=2, ensure_ascii=False))
            
            print(f"\n💾 Report saved to: {filename}")
            
    except Exception as e:
        print(f"\n❌ Fatal error during debugging: {str(e)}")
        import traceback
        if debug_level in [DebugLevel.VERBOSE, DebugLevel.EXTREME]:
            traceback.print_exc()


async def debug_all_agents(
    article_url: str,
    debug_level: DebugLevel,
    save_report: bool = False
) -> None:
    """Debug all agents in batch"""
    
    # Initialize Grok client
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        print("❌ Error: XAI_API_KEY environment variable not set")
        sys.exit(1)
    
    grok_client = GrokClient()
    
    print(f"\n{'='*80}")
    print(f"🔍 Debugging ALL Agents")
    print(f"📰 Article: {article_url}")
    print(f"🎚️  Debug Level: {debug_level.value}")
    print(f"{'='*80}\n")
    
    # Create coordinator
    coordinator = AgentCoordinator(grok_client)
    
    # All analysis types except x_pulse (it's complex)
    analysis_types = [
        AnalysisType.JARGON,
        AnalysisType.VIEWPOINTS,
        AnalysisType.FACT_CHECK,
        AnalysisType.BIAS,
        AnalysisType.TIMELINE,
        AnalysisType.EXPERT
    ]
    
    try:
        results, report = await debug_agent_batch(
            coordinator,
            analysis_types,
            article_url,
            debug_level
        )
        
        # Display report
        print(report)
        
        # Show summary of results
        print("\n" + "="*80)
        print("RESULTS SUMMARY")
        print("="*80)
        
        for analysis_type, result in results.items():
            if result.success and result.data:
                print(f"\n{analysis_type.value.upper()}:")
                
                # Show key data points based on type
                data = result.data
                if analysis_type == AnalysisType.VIEWPOINTS:
                    viewpoints = data.get('viewpoints', [])
                    print(f"  Found {len(viewpoints)} alternative viewpoints")
                    if viewpoints:
                        print(f"  First viewpoint: {viewpoints[0][:100]}...")
                        
                elif analysis_type == AnalysisType.JARGON:
                    terms = data.get('terms', [])
                    print(f"  Explained {len(terms)} terms")
                    if terms:
                        print(f"  Terms: {', '.join(t.get('term', '') for t in terms[:5])}...")
                        
                elif analysis_type == AnalysisType.FACT_CHECK:
                    claims = data.get('claims', [])
                    print(f"  Checked {len(claims)} claims")
                    
                elif analysis_type == AnalysisType.BIAS:
                    bias_analysis = data.get('analysis', 'No analysis')
                    print(f"  Analysis: {bias_analysis[:100]}...")
                    
                elif analysis_type == AnalysisType.TIMELINE:
                    events = data.get('events', [])
                    print(f"  Found {len(events)} timeline events")
                    
                elif analysis_type == AnalysisType.EXPERT:
                    experts = data.get('experts', [])
                    print(f"  Found {len(experts)} expert opinions")
            else:
                print(f"\n{analysis_type.value.upper()}: ❌ Failed")
        
        # Save if requested
        if save_report:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"debug_report_all_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Debug Report Generated: {datetime.now()}\n")
                f.write(f"Article: {article_url}\n")
                f.write(f"Debug Level: {debug_level.value}\n")
                f.write(report)
                
                # Save all result data
                f.write("\n\n" + "="*80 + "\n")
                f.write("ALL RESULTS DATA (JSON)\n")
                f.write("="*80 + "\n")
                
                results_data = {}
                for analysis_type, result in results.items():
                    if result.success and result.data:
                        results_data[analysis_type.value] = result.data
                
                f.write(json.dumps(results_data, indent=2, ensure_ascii=False))
            
            print(f"\n💾 Report saved to: {filename}")
            
    except Exception as e:
        print(f"\n❌ Fatal error during debugging: {str(e)}")
        import traceback
        if debug_level in [DebugLevel.VERBOSE, DebugLevel.EXTREME]:
            traceback.print_exc()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Debug News-Copilot agents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('article_url', help='URL of the article to analyze')
    parser.add_argument('--agent', help='Specific agent to debug')
    parser.add_argument('--all', action='store_true', help='Debug all agents')
    parser.add_argument('--level', 
                       choices=['minimal', 'normal', 'verbose', 'extreme'],
                       default='verbose',
                       help='Debug verbosity level')
    parser.add_argument('--save', action='store_true', help='Save debug report to file')
    parser.add_argument('--compare', action='store_true', help='Compare results between agents (not implemented)')
    parser.add_argument('--live', action='store_true', help='Show live execution progress (not implemented)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.agent and not args.all:
        print("❌ Error: Must specify either --agent or --all")
        sys.exit(1)
    
    if args.agent and args.all:
        print("❌ Error: Cannot specify both --agent and --all")
        sys.exit(1)
    
    # Setup logging
    debug_level = DebugLevel(args.level)
    setup_logging(debug_level)
    
    # Run debugging
    if args.agent:
        asyncio.run(debug_specific_agent(
            args.agent,
            args.article_url,
            debug_level,
            args.save
        ))
    else:
        asyncio.run(debug_all_agents(
            args.article_url,
            debug_level,
            args.save
        ))


if __name__ == "__main__":
    main()