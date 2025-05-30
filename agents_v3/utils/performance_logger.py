"""Enhanced performance and communication logging for agents_v3"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"
    MESSAGE_SEND = "message_send"
    MESSAGE_RECEIVE = "message_receive"
    SEARCH_START = "search_start"
    SEARCH_END = "search_end"
    PARSING_START = "parsing_start"
    PARSING_END = "parsing_end"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_METRIC = "performance_metric"


@dataclass
class LogEntry:
    """Structured log entry for performance tracking"""
    timestamp: str
    event_type: EventType
    level: LogLevel
    agent_name: str
    session_id: str
    conversation_id: Optional[str] = None
    
    # Performance metrics
    duration_ms: Optional[int] = None
    tokens_used: Optional[Dict[str, int]] = None
    cost_estimate: Optional[float] = None
    
    # Communication details
    message_preview: Optional[str] = None
    response_preview: Optional[str] = None
    citations_count: Optional[int] = None
    
    # Error information
    error_message: Optional[str] = None
    error_context: Optional[Dict[str, Any]] = None
    
    # Raw data (for debugging)
    raw_data: Optional[str] = None
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class PerformanceLogger:
    """Enhanced logger for performance evaluation and debugging"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.entries: List[LogEntry] = []
        
        # Set up file logging
        self.log_file = f"logs/performance_{self.session_id}.jsonl"
        self.console_log_file = f"logs/console_{self.session_id}.log"
        
        # Ensure logs directory exists
        import os
        os.makedirs("logs", exist_ok=True)
        
        # Set up Python logger
        self.logger = logging.getLogger(f"perf_{self.session_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for structured logs
        file_handler = logging.FileHandler(self.console_log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def log_event(self, entry: LogEntry):
        """Log a structured event"""
        entry.timestamp = datetime.now().isoformat()
        entry.session_id = self.session_id
        
        self.entries.append(entry)
        
        # Write to JSONL file immediately
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + '\n')
        
        # Also log to console for immediate feedback
        self._log_to_console(entry)
    
    def _log_to_console(self, entry: LogEntry):
        """Format and log to console"""
        msg_parts = [f"[{entry.agent_name}]"]
        
        if entry.conversation_id:
            msg_parts.append(f"Conv:{entry.conversation_id[:8]}")
        
        if entry.event_type == EventType.MESSAGE_SEND:
            preview = entry.message_preview[:50] + "..." if entry.message_preview else ""
            msg_parts.append(f"→ {preview}")
        elif entry.event_type == EventType.MESSAGE_RECEIVE:
            preview = entry.response_preview[:50] + "..." if entry.response_preview else ""
            duration = f" ({entry.duration_ms}ms)" if entry.duration_ms else ""
            msg_parts.append(f"← {preview}{duration}")
        elif entry.event_type == EventType.PERFORMANCE_METRIC:
            if entry.tokens_used:
                tokens = f"Tokens: {entry.tokens_used.get('total', 0)}"
                msg_parts.append(tokens)
            if entry.cost_estimate:
                msg_parts.append(f"Cost: ${entry.cost_estimate:.4f}")
        elif entry.event_type == EventType.ERROR_OCCURRED:
            msg_parts.append(f"ERROR: {entry.error_message}")
        
        message = " | ".join(msg_parts)
        
        # Log at appropriate level
        if entry.level == LogLevel.ERROR:
            self.logger.error(message)
        elif entry.level == LogLevel.WARNING:
            self.logger.warning(message)
        elif entry.level == LogLevel.DEBUG:
            self.logger.debug(message)
        else:
            self.logger.info(message)
    
    def log_agent_start(self, agent_name: str, agent_type: str, metadata: Dict[str, Any] = None):
        """Log agent initialization"""
        self.log_event(LogEntry(
            timestamp="",
            event_type=EventType.AGENT_START,
            level=LogLevel.INFO,
            agent_name=agent_name,
            session_id=self.session_id,
            metadata={"agent_type": agent_type, **(metadata or {})}
        ))
    
    def log_conversation_start(self, agent_name: str, conversation_id: str, conversation_type: str):
        """Log conversation start"""
        self.log_event(LogEntry(
            timestamp="",
            event_type=EventType.CONVERSATION_START,
            level=LogLevel.INFO,
            agent_name=agent_name,
            session_id=self.session_id,
            conversation_id=conversation_id,
            metadata={"conversation_type": conversation_type}
        ))
    
    def log_message_exchange(self, agent_name: str, conversation_id: str, 
                           message: str, response: str, duration_ms: int,
                           tokens_used: Dict[str, int] = None, cost: float = None,
                           citations_count: int = None):
        """Log complete message exchange with performance metrics"""
        
        # Log message send
        self.log_event(LogEntry(
            timestamp="",
            event_type=EventType.MESSAGE_SEND,
            level=LogLevel.DEBUG,
            agent_name=agent_name,
            session_id=self.session_id,
            conversation_id=conversation_id,
            message_preview=message[:100]
        ))
        
        # Log response receive with metrics
        self.log_event(LogEntry(
            timestamp="",
            event_type=EventType.MESSAGE_RECEIVE,
            level=LogLevel.INFO,
            agent_name=agent_name,
            session_id=self.session_id,
            conversation_id=conversation_id,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            cost_estimate=cost,
            response_preview=response[:100],
            citations_count=citations_count
        ))
    
    def log_parsing_attempt(self, agent_name: str, content: str, success: bool, 
                          error_msg: str = None, parsed_items: int = None):
        """Log parsing attempts with full content for debugging"""
        self.log_event(LogEntry(
            timestamp="",
            event_type=EventType.PARSING_END,
            level=LogLevel.INFO if success else LogLevel.ERROR,
            agent_name=agent_name,
            session_id=self.session_id,
            error_message=error_msg if not success else None,
            raw_data=content,  # Full content for debugging
            metadata={
                "parsing_success": success,
                "parsed_items": parsed_items,
                "content_length": len(content)
            }
        ))
    
    def log_error(self, agent_name: str, error_msg: str, error_context: Dict[str, Any] = None,
                 conversation_id: str = None):
        """Log detailed error information"""
        self.log_event(LogEntry(
            timestamp="",
            event_type=EventType.ERROR_OCCURRED,
            level=LogLevel.ERROR,
            agent_name=agent_name,
            session_id=self.session_id,
            conversation_id=conversation_id,
            error_message=error_msg,
            error_context=error_context
        ))
    
    def log_performance_summary(self, agent_name: str, metrics: Dict[str, Any]):
        """Log performance summary"""
        self.log_event(LogEntry(
            timestamp="",
            event_type=EventType.PERFORMANCE_METRIC,
            level=LogLevel.INFO,
            agent_name=agent_name,
            session_id=self.session_id,
            metadata=metrics
        ))
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Generate performance summary from logged events"""
        summary = {
            "session_id": self.session_id,
            "total_events": len(self.entries),
            "agents": {},
            "total_duration_ms": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "errors": 0,
            "conversations": 0
        }
        
        for entry in self.entries:
            agent_name = entry.agent_name
            if agent_name not in summary["agents"]:
                summary["agents"][agent_name] = {
                    "events": 0,
                    "duration_ms": 0,
                    "tokens": 0,
                    "cost": 0.0,
                    "errors": 0
                }
            
            summary["agents"][agent_name]["events"] += 1
            
            if entry.duration_ms:
                summary["agents"][agent_name]["duration_ms"] += entry.duration_ms
                summary["total_duration_ms"] += entry.duration_ms
            
            if entry.tokens_used:
                total_tokens = entry.tokens_used.get("total", 0)
                summary["agents"][agent_name]["tokens"] += total_tokens
                summary["total_tokens"] += total_tokens
            
            if entry.cost_estimate:
                summary["agents"][agent_name]["cost"] += entry.cost_estimate
                summary["total_cost"] += entry.cost_estimate
            
            if entry.level == LogLevel.ERROR:
                summary["agents"][agent_name]["errors"] += 1
                summary["errors"] += 1
            
            if entry.event_type == EventType.CONVERSATION_START:
                summary["conversations"] += 1
        
        return summary
    
    def print_performance_report(self):
        """Print a formatted performance report"""
        summary = self.get_performance_summary()
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE REPORT")
        print("="*60)
        print(f"Session: {summary['session_id']}")
        print(f"Total Events: {summary['total_events']}")
        print(f"Total Duration: {summary['total_duration_ms']/1000:.1f}s")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        print(f"Total Cost: ${summary['total_cost']:.4f}")
        print(f"Conversations: {summary['conversations']}")
        print(f"Errors: {summary['errors']}")
        
        print(f"\n📋 AGENT BREAKDOWN:")
        for agent_name, metrics in summary["agents"].items():
            print(f"\n  🤖 {agent_name}:")
            print(f"    Events: {metrics['events']}")
            print(f"    Duration: {metrics['duration_ms']/1000:.1f}s")
            print(f"    Tokens: {metrics['tokens']:,}")
            print(f"    Cost: ${metrics['cost']:.4f}")
            if metrics['errors'] > 0:
                print(f"    ❌ Errors: {metrics['errors']}")
        
        print(f"\n📁 Logs saved to:")
        print(f"  • Structured: {self.log_file}")
        print(f"  • Console: {self.console_log_file}")


# Global performance logger instance
perf_logger = None

def get_performance_logger(session_id: str = None) -> PerformanceLogger:
    """Get or create global performance logger"""
    global perf_logger
    if perf_logger is None:
        perf_logger = PerformanceLogger(session_id)
    return perf_logger

def init_performance_logging(session_id: str = None):
    """Initialize performance logging for a session"""
    global perf_logger
    perf_logger = PerformanceLogger(session_id)
    return perf_logger