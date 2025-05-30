"""Enhanced logging configuration for better auditability"""

import logging
import os
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Any


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'agent_id'):
            log_data['agent_id'] = record.agent_id
        if hasattr(record, 'story_id'):
            log_data['story_id'] = record.story_id
        if hasattr(record, 'conversation_id'):
            log_data['conversation_id'] = record.conversation_id
        if hasattr(record, 'phase'):
            log_data['phase'] = record.phase
        if hasattr(record, 'error_type'):
            log_data['error_type'] = record.error_type
            
        return json.dumps(log_data)


class PipelineLogger:
    """Enhanced logger for pipeline operations"""
    
    def __init__(self, session_id: str, log_dir: str = "logs"):
        self.session_id = session_id
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create session log directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.log_dir / f"{timestamp}_{session_id}"
        self.session_dir.mkdir(exist_ok=True)
        
        # Setup loggers
        self._setup_loggers()
        
    def _setup_loggers(self):
        """Setup different loggers for different aspects"""
        
        # Main pipeline logger
        self.pipeline_logger = self._create_logger(
            "pipeline",
            self.session_dir / "pipeline.log",
            level=logging.INFO
        )
        
        # Discovery logger
        self.discovery_logger = self._create_logger(
            "discovery",
            self.session_dir / "discovery.log",
            level=logging.DEBUG
        )
        
        # Agent communication logger
        self.comm_logger = self._create_logger(
            "communication",
            self.session_dir / "communication.log",
            level=logging.DEBUG
        )
        
        # Error logger
        self.error_logger = self._create_logger(
            "errors",
            self.session_dir / "errors.log",
            level=logging.WARNING
        )
        
    def _create_logger(self, name: str, log_file: Path, level: int) -> logging.Logger:
        """Create a logger with file and console handlers"""
        
        logger = logging.getLogger(f"{self.session_id}.{name}")
        logger.setLevel(level)
        
        # File handler with JSON formatting
        fh = logging.FileHandler(log_file)
        fh.setFormatter(StructuredFormatter())
        logger.addHandler(fh)
        
        # Console handler with simple formatting
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        ch.setLevel(logging.INFO)  # Less verbose on console
        logger.addHandler(ch)
        
        return logger
    
    def log_discovery_start(self, category: str, search_terms: list):
        """Log discovery phase start"""
        self.discovery_logger.info(
            f"Starting discovery for {category}",
            extra={
                "phase": "discovery",
                "category": category,
                "search_terms": search_terms
            }
        )
    
    def log_discovery_result(self, category: str, story_count: int, errors: list):
        """Log discovery results"""
        self.discovery_logger.info(
            f"Discovery complete for {category}: {story_count} stories",
            extra={
                "phase": "discovery",
                "category": category,
                "story_count": story_count,
                "has_errors": len(errors) > 0
            }
        )
        
        if errors:
            self.error_logger.warning(
                f"Discovery errors for {category}",
                extra={
                    "phase": "discovery",
                    "category": category,
                    "errors": errors,
                    "error_type": "discovery_parse"
                }
            )
    
    def log_story_processing(self, story_id: str, phase: str, agent: str, success: bool, error: str = None):
        """Log story processing steps"""
        if success:
            self.pipeline_logger.info(
                f"Story {story_id}: {phase} by {agent} completed",
                extra={
                    "story_id": story_id,
                    "phase": phase,
                    "agent_id": agent
                }
            )
        else:
            self.error_logger.error(
                f"Story {story_id}: {phase} by {agent} failed",
                extra={
                    "story_id": story_id,
                    "phase": phase,
                    "agent_id": agent,
                    "error": error,
                    "error_type": f"{phase}_failure"
                }
            )
    
    def log_agent_communication(self, sender: str, target: str, message_type: str, success: bool):
        """Log inter-agent communication"""
        self.comm_logger.info(
            f"Agent communication: {sender} -> {target}",
            extra={
                "sender": sender,
                "target": target,
                "message_type": message_type,
                "success": success
            }
        )
    
    def log_summary(self, summary: Dict[str, Any]):
        """Log final summary"""
        self.pipeline_logger.info(
            "Pipeline execution completed",
            extra={"summary": summary}
        )
        
        # Also write summary to separate file
        summary_file = self.session_dir / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors"""
        errors = []
        
        # Read error log
        error_file = self.session_dir / "errors.log"
        if error_file.exists():
            with open(error_file, 'r') as f:
                for line in f:
                    try:
                        error_data = json.loads(line)
                        errors.append(error_data)
                    except:
                        pass
        
        # Group by error type
        error_types = {}
        for error in errors:
            error_type = error.get("error_type", "unknown")
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error)
        
        return {
            "total_errors": len(errors),
            "error_types": {k: len(v) for k, v in error_types.items()},
            "errors_by_type": error_types
        }


def setup_module_logging(module_name: str, level: int = logging.INFO):
    """Setup standard logging for a module"""
    logger = logging.getLogger(module_name)
    logger.setLevel(level)
    
    # Add console handler if not already present
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(ch)
    
    return logger