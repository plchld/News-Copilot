#!/usr/bin/env python3
"""
Log analysis tool for agents_v3 system

This tool helps parse and analyze the verbose logs from news analysis runs,
extracting key information like errors, API calls, cache hits, and timing.
"""

import re
import sys
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple
from pathlib import Path
import json

class LogAnalyzer:
    def __init__(self):
        self.errors = []
        self.api_calls = []
        self.cache_stats = defaultdict(int)
        self.conversations = {}
        self.agent_activities = defaultdict(list)
        self.timing_info = []
        self.stories_processed = 0
        
    def parse_log_line(self, line: str):
        """Parse a single log line and extract relevant information"""
        
        # Try to parse as JSON first (for JSONL logs)
        try:
            data = json.loads(line.strip())
            self._parse_json_log(data)
            return
        except json.JSONDecodeError:
            pass
        
        # Fall back to text parsing
        # Extract timestamp
        time_match = re.search(r'\[(\d{2}:\d{2}:\d{2})\]', line)
        timestamp = time_match.group(1) if time_match else None
        
        # Check for errors
        if '❌ ERROR' in line or 'Error:' in line:
            self.errors.append({
                'timestamp': timestamp,
                'line': line.strip(),
                'error_msg': self._extract_error_message(line)
            })
        
        # Track API calls and responses
        if 'Starting' in line and 'conversation' in line:
            agent_match = re.search(r'(\w+)/(\w+_agent)', line)
            if agent_match:
                provider, agent = agent_match.groups()
                self.api_calls.append({
                    'timestamp': timestamp,
                    'provider': provider,
                    'agent': agent,
                    'action': 'conversation_start'
                })
        
        # Track cache hits/misses
        if 'cache hit' in line.lower() or 'cache_hit_ratio' in line:
            ratio_match = re.search(r'(\d+(?:\.\d+)?)\%', line)
            if ratio_match:
                self.cache_stats['cache_hit_ratios'].append(float(ratio_match.group(1)))
        
        if 'CACHE_MISS' in line:
            self.cache_stats['misses'] += 1
        elif 'CACHE_HIT' in line or '💾 CACHE' in line:
            self.cache_stats['hits'] += 1
            
        # Track story processing
        if 'stories found' in line or 'stories discovered' in line:
            count_match = re.search(r'(\d+)\s+stories', line)
            if count_match:
                self.stories_processed = max(self.stories_processed, int(count_match.group(1)))
        
        # Track timing
        if 'Processing time:' in line or 'duration_minutes' in line:
            time_match = re.search(r'(\d+(?:\.\d+)?)\s*minutes?', line)
            if time_match:
                self.timing_info.append(float(time_match.group(1)))
    
    def _extract_error_message(self, line: str) -> str:
        """Extract the actual error message from a log line"""
        # Common error patterns
        patterns = [
            r"Error: (.+?)(?:\s*\[|$)",
            r"'error': \{'type': '[^']+', 'message': '([^']+)'",
            r"Error code: \d+ - (.+)",
            r"❌ Error: (.+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1).strip()
        
        # Fallback: return the part after "Error:"
        if 'Error:' in line:
            return line.split('Error:', 1)[1].strip()
        
        return line.strip()
    
    def _parse_json_log(self, data: dict):
        """Parse a JSON log entry"""
        timestamp = data.get('timestamp')
        content = data.get('content', '')
        agent_name = data.get('agent_name', '')
        provider = data.get('provider', '')
        error = data.get('error')
        
        # Check for errors
        if error:
            self.errors.append({
                'timestamp': self._format_timestamp(timestamp),
                'line': content,
                'error_msg': str(error)
            })
        elif 'error' in content.lower() or '❌' in content:
            self.errors.append({
                'timestamp': self._format_timestamp(timestamp),
                'line': content,
                'error_msg': content
            })
        
        # Track API calls
        if 'starting' in content.lower() and 'conversation' in content.lower():
            self.api_calls.append({
                'timestamp': self._format_timestamp(timestamp),
                'provider': provider,
                'agent': agent_name,
                'action': 'conversation_start'
            })
        
        # Track cache performance
        if 'cache_hit_ratio' in data:
            ratio = data.get('cache_hit_ratio', 0) * 100
            self.cache_stats['cache_hit_ratios'].append(ratio)
        
        cache_hit = data.get('cache_hit', False)
        if cache_hit:
            self.cache_stats['hits'] += 1
        elif cache_hit is False and 'cache' in content.lower():
            self.cache_stats['misses'] += 1
        
        # Track stories
        if 'stories' in content.lower():
            count_match = re.search(r'(\d+)\s+stories', content)
            if count_match:
                self.stories_processed = max(self.stories_processed, int(count_match.group(1)))
        
        # Track timing
        if 'duration_minutes' in data:
            duration = data.get('duration_minutes', 0)
            if duration:
                self.timing_info.append(duration)
    
    def _format_timestamp(self, timestamp):
        """Format timestamp for display"""
        if isinstance(timestamp, (int, float)):
            from datetime import datetime
            return datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
        return str(timestamp) if timestamp else None
    
    def analyze_logs(self, log_content: str):
        """Analyze the full log content"""
        lines = log_content.split('\n')
        
        for line in lines:
            if line.strip():
                self.parse_log_line(line)
        
        # Generate summary
        return self.generate_summary()
    
    def generate_summary(self) -> Dict:
        """Generate a summary of the log analysis"""
        
        # Group errors by type
        error_types = defaultdict(list)
        for error in self.errors:
            msg = error['error_msg']
            # Categorize errors
            if 'credit balance' in msg.lower():
                error_types['API Credits'].append(error)
            elif '503' in msg or 'unavailable' in msg.lower():
                error_types['Service Unavailable'].append(error)
            elif 'ttl' in msg.lower() or 'cache_control' in msg.lower():
                error_types['Cache Configuration'].append(error)
            elif 'unsupported operand' in msg:
                error_types['Code Errors'].append(error)
            else:
                error_types['Other'].append(error)
        
        # Calculate cache efficiency
        total_cache_attempts = self.cache_stats['hits'] + self.cache_stats['misses']
        cache_hit_rate = (self.cache_stats['hits'] / total_cache_attempts * 100) if total_cache_attempts > 0 else 0
        
        # Calculate average timing
        avg_processing_time = sum(self.timing_info) / len(self.timing_info) if self.timing_info else 0
        
        return {
            'total_errors': len(self.errors),
            'error_breakdown': {k: len(v) for k, v in error_types.items()},
            'error_details': error_types,
            'api_calls': len(self.api_calls),
            'api_providers': self._count_by_provider(),
            'cache_performance': {
                'hits': self.cache_stats['hits'],
                'misses': self.cache_stats['misses'],
                'hit_rate': f"{cache_hit_rate:.1f}%",
                'avg_reported_hit_rate': f"{sum(self.cache_stats.get('cache_hit_ratios', [0])) / len(self.cache_stats.get('cache_hit_ratios', [1])):.1f}%"
            },
            'stories_processed': self.stories_processed,
            'processing_times': {
                'average': f"{avg_processing_time:.1f} minutes",
                'total': f"{sum(self.timing_info):.1f} minutes"
            }
        }
    
    def _count_by_provider(self) -> Dict[str, int]:
        """Count API calls by provider"""
        provider_counts = defaultdict(int)
        for call in self.api_calls:
            provider_counts[call['provider']] += 1
        return dict(provider_counts)
    
    def print_summary(self, summary: Dict):
        """Print a formatted summary"""
        print("\n" + "="*60)
        print("📊 LOG ANALYSIS SUMMARY")
        print("="*60)
        
        # Errors section
        print(f"\n❌ ERRORS: {summary['total_errors']} total")
        print("-"*40)
        for error_type, count in summary['error_breakdown'].items():
            print(f"  • {error_type}: {count}")
            
        # Show first few errors of each type
        print("\n📋 ERROR DETAILS:")
        for error_type, errors in summary['error_details'].items():
            if errors:
                print(f"\n  {error_type}:")
                for error in errors[:2]:  # Show first 2 of each type
                    print(f"    [{error['timestamp']}] {error['error_msg'][:80]}...")
        
        # API calls section
        print(f"\n🔌 API CALLS: {summary['api_calls']} total")
        print("-"*40)
        for provider, count in summary['api_providers'].items():
            print(f"  • {provider}: {count} calls")
        
        # Cache performance
        print(f"\n💾 CACHE PERFORMANCE:")
        print("-"*40)
        cache = summary['cache_performance']
        print(f"  • Hits: {cache['hits']}")
        print(f"  • Misses: {cache['misses']}")
        print(f"  • Hit Rate: {cache['hit_rate']}")
        print(f"  • Avg Reported: {cache['avg_reported_hit_rate']}")
        
        # Processing stats
        print(f"\n⚡ PROCESSING STATS:")
        print("-"*40)
        print(f"  • Stories Processed: {summary['stories_processed']}")
        print(f"  • Average Time: {summary['processing_times']['average']}")
        print(f"  • Total Time: {summary['processing_times']['total']}")
        
        print("\n" + "="*60 + "\n")


def main():
    """Main entry point for log analysis"""
    
    analyzer = LogAnalyzer()
    
    # Read from stdin or file
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], 'r') as f:
            log_content = f.read()
    else:
        # Check for logs directory first
        logs_dir = Path(__file__).parent.parent.parent / "logs" / "conversations"
        if logs_dir.exists():
            log_files = sorted(logs_dir.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)
            if log_files:
                print(f"📁 Found {len(log_files)} log files in {logs_dir}")
                print("📄 Analyzing most recent log file:", log_files[0].name)
                with open(log_files[0], 'r') as f:
                    log_content = f.read()
            else:
                print("❌ No log files found in logs/conversations/")
                print("Reading from stdin... (paste logs and press Ctrl+D when done)")
                log_content = sys.stdin.read()
        else:
            # Read from stdin
            print("📁 logs/conversations/ not found")
            print("Reading from stdin... (paste logs and press Ctrl+D when done)")
            log_content = sys.stdin.read()
    
    # Analyze logs
    summary = analyzer.analyze_logs(log_content)
    
    # Print summary
    analyzer.print_summary(summary)
    
    # Optional: Save detailed JSON report
    if len(sys.argv) > 2 and sys.argv[2] == '--json':
        with open('log_analysis.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print("Detailed analysis saved to log_analysis.json")


if __name__ == "__main__":
    main()