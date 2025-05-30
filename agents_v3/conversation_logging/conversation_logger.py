"""Comprehensive logging system for agent conversations"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class MessageType(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"


@dataclass
class LogEntry:
    """Single log entry for agent communication"""
    
    timestamp: float
    session_id: str
    conversation_id: str
    agent_name: str
    provider: str
    
    # Message details
    message_type: MessageType
    content: Union[str, Dict[str, Any]]
    role: Optional[str] = None
    
    # Performance metrics
    tokens_used: Optional[Dict[str, int]] = None
    response_time_ms: Optional[int] = None
    cost_estimate: Optional[float] = None
    
    # Caching info
    cache_hit: bool = False
    cache_tokens_read: int = 0
    cache_tokens_written: int = 0
    
    # Context
    story_id: Optional[str] = None
    analysis_type: Optional[str] = None
    batch_info: Optional[Dict[str, Any]] = None
    
    # Error handling
    error: Optional[str] = None
    level: LogLevel = LogLevel.INFO


class ConversationLogger:
    """Rich logging system for agent conversations with cost tracking"""
    
    def __init__(
        self, 
        log_dir: str = "logs/conversations",
        console_output: bool = True,
        json_output: bool = True,
        max_content_length: int = 1000
    ):
        """Initialize conversation logger
        
        Args:
            log_dir: Directory to store log files
            console_output: Whether to print to console
            json_output: Whether to write JSON log files
            max_content_length: Max characters to display in console
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.console_output = console_output
        self.json_output = json_output
        self.max_content_length = max_content_length
        
        # Session tracking
        self.session_id = f"session_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        self.conversation_logs: Dict[str, List[LogEntry]] = {}
        
        # Cost tracking
        self.total_cost = 0.0
        self.total_tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_written": 0}
        
        # Create session log file
        if self.json_output:
            self.session_log_file = self.log_dir / f"{self.session_id}.jsonl"
    
    def start_conversation(
        self,
        agent_name: str,
        provider: str,
        conversation_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new conversation and return conversation ID"""
        
        conversation_id = f"{agent_name}_{conversation_type}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        self.conversation_logs[conversation_id] = []
        
        # Log conversation start
        self.log_message(
            conversation_id=conversation_id,
            agent_name=agent_name,
            provider=provider,
            message_type=MessageType.SYSTEM,
            content=f"Starting {conversation_type} conversation",
            level=LogLevel.INFO,
            metadata={
                "conversation_start": True,
                "conversation_type": conversation_type,
                **(metadata or {})
            }
        )
        
        return conversation_id
    
    def log_message(
        self,
        conversation_id: str,
        agent_name: str,
        provider: str,
        message_type: MessageType,
        content: Union[str, Dict[str, Any]],
        role: Optional[str] = None,
        tokens_used: Optional[Dict[str, int]] = None,
        response_time_ms: Optional[int] = None,
        cost_estimate: Optional[float] = None,
        cache_hit: bool = False,
        cache_tokens_read: int = 0,
        cache_tokens_written: int = 0,
        story_id: Optional[str] = None,
        analysis_type: Optional[str] = None,
        batch_info: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        level: LogLevel = LogLevel.INFO,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a message in the conversation"""
        
        # Create log entry
        log_entry = LogEntry(
            timestamp=time.time(),
            session_id=self.session_id,
            conversation_id=conversation_id,
            agent_name=agent_name,
            provider=provider,
            message_type=message_type,
            content=content,
            role=role,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms,
            cost_estimate=cost_estimate,
            cache_hit=cache_hit,
            cache_tokens_read=cache_tokens_read,
            cache_tokens_written=cache_tokens_written,
            story_id=story_id,
            analysis_type=analysis_type,
            batch_info=batch_info,
            error=error,
            level=level
        )
        
        # Add to conversation log
        if conversation_id not in self.conversation_logs:
            self.conversation_logs[conversation_id] = []
        self.conversation_logs[conversation_id].append(log_entry)
        
        # Update totals
        if cost_estimate:
            self.total_cost += cost_estimate
        if tokens_used:
            self.total_tokens["input"] += tokens_used.get("input", 0)
            self.total_tokens["output"] += tokens_used.get("output", 0)
        self.total_tokens["cache_read"] += cache_tokens_read
        self.total_tokens["cache_written"] += cache_tokens_written
        
        # Console output
        if self.console_output:
            self._print_to_console(log_entry, metadata)
        
        # JSON output
        if self.json_output:
            self._write_to_json(log_entry, metadata)
    
    def _print_to_console(self, log_entry: LogEntry, metadata: Optional[Dict[str, Any]] = None):
        """Print formatted log entry to console"""
        
        timestamp = datetime.fromtimestamp(log_entry.timestamp).strftime("%H:%M:%S")
        
        # Color coding by level
        colors = {
            LogLevel.DEBUG: "\033[36m",    # Cyan
            LogLevel.INFO: "\033[32m",     # Green
            LogLevel.WARNING: "\033[33m",  # Yellow
            LogLevel.ERROR: "\033[31m"     # Red
        }
        reset_color = "\033[0m"
        color = colors.get(log_entry.level, "")
        
        # Format content for display
        if isinstance(log_entry.content, str):
            display_content = log_entry.content
        else:
            display_content = json.dumps(log_entry.content, indent=2)
        
        # Truncate if too long
        if len(display_content) > self.max_content_length:
            display_content = display_content[:self.max_content_length] + "..."
        
        # Build status indicators
        status_indicators = []
        if log_entry.cache_hit:
            status_indicators.append("💾 CACHE")
        if log_entry.cost_estimate:
            status_indicators.append(f"💰 ${log_entry.cost_estimate:.4f}")
        if log_entry.response_time_ms:
            status_indicators.append(f"⏱️ {log_entry.response_time_ms}ms")
        if log_entry.error:
            status_indicators.append("❌ ERROR")
        
        status_str = " ".join(status_indicators)
        
        # Print formatted log
        print(f"{color}[{timestamp}] {log_entry.provider.upper()}/{log_entry.agent_name}{reset_color}")
        print(f"  🔄 {log_entry.conversation_id[-12:]} | {log_entry.message_type.value.upper()}")
        
        if log_entry.story_id:
            print(f"  📰 Story: {log_entry.story_id}")
        
        if status_str:
            print(f"  📊 {status_str}")
        
        if log_entry.error:
            print(f"  ❌ Error: {log_entry.error}")
        else:
            # Indent content
            for line in display_content.split('\n'):
                if line.strip():
                    print(f"     {line}")
        
        print()  # Blank line for readability
    
    def _write_to_json(self, log_entry: LogEntry, metadata: Optional[Dict[str, Any]] = None):
        """Write log entry to JSON file"""
        
        log_dict = asdict(log_entry)
        log_dict["message_type"] = log_entry.message_type.value
        log_dict["level"] = log_entry.level.value
        
        if metadata:
            log_dict["metadata"] = metadata
        
        # Write to session log file
        try:
            with open(self.session_log_file, 'a') as f:
                f.write(json.dumps(log_dict) + '\n')
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def log_cache_performance(
        self,
        conversation_id: str,
        agent_name: str,
        provider: str,
        cache_stats: Dict[str, Any]
    ):
        """Log cache performance metrics"""
        
        cache_hit_ratio = cache_stats.get("cache_hit_ratio", 0)
        savings_estimate = cache_stats.get("savings_estimate", 0)
        
        self.log_message(
            conversation_id=conversation_id,
            agent_name=agent_name,
            provider=provider,
            message_type=MessageType.CACHE_HIT if cache_hit_ratio > 0.5 else MessageType.CACHE_MISS,
            content=f"Cache performance: {cache_hit_ratio:.1%} hit ratio, ~${savings_estimate:.4f} saved",
            level=LogLevel.INFO,
            cache_hit=cache_hit_ratio > 0.5,
            cache_tokens_read=cache_stats.get("cache_tokens_read", 0),
            cache_tokens_written=cache_stats.get("cache_tokens_written", 0),
            cost_estimate=-savings_estimate  # Negative cost = savings
        )
    
    def log_story_analysis(
        self,
        conversation_id: str,
        agent_name: str,
        provider: str,
        story_id: str,
        headline: str,
        analysis_result: str,
        analysis_type: str,
        tokens_used: Dict[str, int],
        response_time_ms: int,
        cost_estimate: float,
        cache_hit: bool = False
    ):
        """Log story analysis with rich context"""
        
        self.log_message(
            conversation_id=conversation_id,
            agent_name=agent_name,
            provider=provider,
            message_type=MessageType.ASSISTANT,
            content=f"Analysis for '{headline}': {analysis_result[:200]}...",
            role="assistant",
            tokens_used=tokens_used,
            response_time_ms=response_time_ms,
            cost_estimate=cost_estimate,
            cache_hit=cache_hit,
            story_id=story_id,
            analysis_type=analysis_type,
            level=LogLevel.INFO
        )
    
    def log_error(
        self,
        conversation_id: str,
        agent_name: str,
        provider: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log an error with context"""
        
        self.log_message(
            conversation_id=conversation_id,
            agent_name=agent_name,
            provider=provider,
            message_type=MessageType.SYSTEM,
            content=f"Error occurred: {error_message}",
            error=error_message,
            level=LogLevel.ERROR,
            metadata=context
        )
    
    def end_conversation(
        self,
        conversation_id: str,
        agent_name: str,
        provider: str,
        final_stats: Optional[Dict[str, Any]] = None
    ):
        """End a conversation and log final statistics"""
        
        if conversation_id not in self.conversation_logs:
            return
        
        conversation_log = self.conversation_logs[conversation_id]
        
        # Calculate conversation statistics
        total_messages = len(conversation_log)
        total_cost = sum(entry.cost_estimate or 0 for entry in conversation_log)
        total_cache_hits = sum(1 for entry in conversation_log if entry.cache_hit)
        cache_hit_ratio = total_cache_hits / max(total_messages, 1)
        
        stats_content = {
            "conversation_ended": True,
            "total_messages": total_messages,
            "total_cost": total_cost,
            "cache_hit_ratio": cache_hit_ratio,
            "duration_minutes": (conversation_log[-1].timestamp - conversation_log[0].timestamp) / 60,
            **(final_stats or {})
        }
        
        self.log_message(
            conversation_id=conversation_id,
            agent_name=agent_name,
            provider=provider,
            message_type=MessageType.SYSTEM,
            content=f"Conversation ended. {total_messages} messages, ${total_cost:.4f} cost, {cache_hit_ratio:.1%} cache hits",
            level=LogLevel.INFO,
            metadata=stats_content
        )
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of entire session"""
        
        total_conversations = len(self.conversation_logs)
        total_messages = sum(len(log) for log in self.conversation_logs.values())
        
        return {
            "session_id": self.session_id,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "cache_efficiency": {
                "cache_read_tokens": self.total_tokens["cache_read"],
                "cache_written_tokens": self.total_tokens["cache_written"],
                "cache_hit_ratio": self.total_tokens["cache_read"] / max(self.total_tokens["input"], 1)
            }
        }
    
    def export_conversation(self, conversation_id: str, format: str = "json") -> Optional[str]:
        """Export a specific conversation"""
        
        if conversation_id not in self.conversation_logs:
            return None
        
        conversation_log = self.conversation_logs[conversation_id]
        
        if format == "json":
            return json.dumps([asdict(entry) for entry in conversation_log], indent=2)
        elif format == "markdown":
            return self._export_conversation_markdown(conversation_log)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_conversation_markdown(self, conversation_log: List[LogEntry]) -> str:
        """Export conversation as readable markdown"""
        
        md_lines = [
            f"# Conversation Log: {conversation_log[0].conversation_id}",
            f"**Agent**: {conversation_log[0].agent_name}",
            f"**Provider**: {conversation_log[0].provider}",
            f"**Started**: {datetime.fromtimestamp(conversation_log[0].timestamp)}",
            ""
        ]
        
        for entry in conversation_log:
            timestamp = datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S")
            
            md_lines.append(f"## [{timestamp}] {entry.message_type.value.upper()}")
            
            if entry.cache_hit:
                md_lines.append("💾 **Cache Hit**")
            
            if entry.cost_estimate:
                md_lines.append(f"💰 **Cost**: ${entry.cost_estimate:.4f}")
            
            if isinstance(entry.content, str):
                md_lines.append(f"```\n{entry.content}\n```")
            else:
                md_lines.append(f"```json\n{json.dumps(entry.content, indent=2)}\n```")
            
            md_lines.append("")
        
        return "\n".join(md_lines)


# Global logger instance
logger = ConversationLogger()