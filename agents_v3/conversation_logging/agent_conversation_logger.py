"""
Simple, clean logging system for debugging agent conversations
Focused on who said what to whom and when
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class ConversationType(Enum):
    """Types of conversations"""
    DISCOVERY = "discovery"
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"


@dataclass
class AgentMessage:
    """Simple agent message for logging"""
    timestamp: str
    session_id: str
    conversation_type: ConversationType
    from_agent: str
    to_agent: str
    message: str
    response: Optional[str] = None
    error: Optional[str] = None


class AgentConversationLogger:
    """Clean, simple logger for agent conversations"""
    
    def __init__(self):
        # Save logs in multiple easy-to-access locations
        self.log_dir = Path(__file__).parent.parent / "logs" / "agent_conversations"
        self.debug_dir = Path(__file__).parent.parent / "debug_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.current_session = None
        self.conversation_log: List[AgentMessage] = []
        
    def start_session(self, session_id: str):
        """Start a new conversation session"""
        self.current_session = session_id
        self.conversation_log = []
        
        print(f"\n🎬 STARTING SESSION: {session_id}")
        print("=" * 80)
        
    def log_discovery(self, agent: str, content_preview: str):
        """Log discovery phase"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        msg = AgentMessage(
            timestamp=timestamp,
            session_id=self.current_session,
            conversation_type=ConversationType.DISCOVERY,
            from_agent=agent,
            to_agent="ALL",
            message=f"Discovered {len(content_preview)} chars of content",
            response=content_preview[:100] + "..." if len(content_preview) > 100 else content_preview
        )
        
        self.conversation_log.append(msg)
        
        print(f"[{timestamp}] 🔍 {agent} → ALL")
        print(f"   📋 Discovery: {msg.message}")
        print()
        
    def log_agent_request(self, from_agent: str, to_agent: str, question: str):
        """Log when one agent asks another agent something"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        msg = AgentMessage(
            timestamp=timestamp,
            session_id=self.current_session,
            conversation_type=ConversationType.REQUEST,
            from_agent=from_agent,
            to_agent=to_agent,
            message=question
        )
        
        self.conversation_log.append(msg)
        
        print(f"[{timestamp}] ❓ {from_agent} → {to_agent}")
        print(f"   Q: {question}")
        
    def log_agent_response(self, from_agent: str, to_agent: str, response: str):
        """Log when an agent responds to another agent"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Find the corresponding request
        for msg in reversed(self.conversation_log):
            if (msg.from_agent == to_agent and 
                msg.to_agent == from_agent and 
                msg.conversation_type == ConversationType.REQUEST and
                msg.response is None):
                msg.response = response
                break
        
        print(f"[{timestamp}] ✅ {from_agent} → {to_agent}")
        print(f"   A: {response[:150]}{'...' if len(response) > 150 else ''}")
        print()
        
    def log_error(self, from_agent: str, to_agent: str, error: str):
        """Log communication errors"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        msg = AgentMessage(
            timestamp=timestamp,
            session_id=self.current_session,
            conversation_type=ConversationType.ERROR,
            from_agent=from_agent,
            to_agent=to_agent,
            message="Communication error",
            error=error
        )
        
        self.conversation_log.append(msg)
        
        print(f"[{timestamp}] ❌ {from_agent} → {to_agent}")
        print(f"   ERROR: {error}")
        print()
        
    def log_phase_start(self, phase: str, description: str):
        """Log the start of a new phase"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n[{timestamp}] 🚀 PHASE: {phase}")
        print(f"   {description}")
        print("-" * 60)
        
    def log_agent_thinking(self, agent: str, thinking: str):
        """Log what an agent is thinking/processing"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"[{timestamp}] 🤔 {agent} thinking...")
        print(f"   💭 {thinking[:100]}{'...' if len(thinking) > 100 else ''}")
        
    def save_session_log(self):
        """Save the conversation log to multiple easy-to-access formats"""
        if not self.current_session:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{timestamp}_{self.current_session}"
        
        # 1. Save JSON log (for programmatic access)
        json_filepath = self.log_dir / f"{base_filename}_conversation_log.json"
        log_data = {
            "session_id": self.current_session,
            "timestamp": timestamp,
            "conversations": [
                {
                    "timestamp": msg.timestamp,
                    "type": msg.conversation_type.value,
                    "from_agent": msg.from_agent,
                    "to_agent": msg.to_agent,
                    "message": msg.message,
                    "response": msg.response,
                    "error": msg.error
                }
                for msg in self.conversation_log
            ]
        }
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        # 2. Save readable markdown log (for easy viewing)
        md_filepath = self.debug_dir / f"{base_filename}_conversation_debug.md"
        self._save_markdown_log(md_filepath, timestamp)
        
        # 3. Save simple text log (for quick scanning)
        txt_filepath = self.debug_dir / f"{base_filename}_conversation_simple.txt"
        self._save_text_log(txt_filepath)
        
        print(f"\n💾 Conversation logs saved:")
        print(f"   📄 Readable: {md_filepath.name}")
        print(f"   📋 Simple:   {txt_filepath.name}")
        print(f"   📊 JSON:     {json_filepath.name}")
        
    def _save_markdown_log(self, filepath: Path, timestamp: str):
        """Save a readable markdown log"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Agent Conversation Debug Log\n\n")
            f.write(f"**Session:** {self.current_session}  \n")
            f.write(f"**Time:** {timestamp}  \n")
            f.write(f"**Total Conversations:** {len(self.conversation_log)}\n\n")
            
            f.write("## Conversation Flow\n\n")
            
            current_phase = None
            for msg in self.conversation_log:
                if msg.conversation_type == ConversationType.DISCOVERY:
                    f.write(f"### 🔍 Discovery Phase\n")
                    f.write(f"**[{msg.timestamp}] {msg.from_agent}** discovered content\n")
                    f.write(f"```\n{msg.response[:200]}...\n```\n\n")
                    
                elif msg.conversation_type == ConversationType.REQUEST:
                    f.write(f"### ❓ {msg.from_agent} → {msg.to_agent}\n")
                    f.write(f"**[{msg.timestamp}] Question:**\n")
                    f.write(f"{msg.message}\n\n")
                    
                    if msg.response:
                        f.write(f"**Response:**\n")
                        f.write(f"{msg.response[:300]}...\n\n")
                    
                elif msg.conversation_type == ConversationType.ERROR:
                    f.write(f"### ❌ Error: {msg.from_agent} → {msg.to_agent}\n")
                    f.write(f"**[{msg.timestamp}]** {msg.error}\n\n")
                    
            f.write("---\n*Generated by Agent Conversation Logger*\n")
            
    def _save_text_log(self, filepath: Path):
        """Save a simple text log for quick scanning"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"AGENT CONVERSATION LOG - {self.current_session}\n")
            f.write("=" * 60 + "\n\n")
            
            for msg in self.conversation_log:
                if msg.conversation_type == ConversationType.DISCOVERY:
                    f.write(f"[{msg.timestamp}] 🔍 DISCOVERY: {msg.from_agent}\n")
                    f.write(f"  Content: {len(msg.response or '')} chars\n\n")
                    
                elif msg.conversation_type == ConversationType.REQUEST:
                    f.write(f"[{msg.timestamp}] ❓ {msg.from_agent} → {msg.to_agent}\n")
                    f.write(f"  Q: {msg.message[:100]}...\n")
                    if msg.response:
                        f.write(f"  A: {msg.response[:100]}...\n")
                    f.write("\n")
                    
                elif msg.conversation_type == ConversationType.ERROR:
                    f.write(f"[{msg.timestamp}] ❌ ERROR: {msg.from_agent} → {msg.to_agent}\n")
                    f.write(f"  {msg.error}\n\n")
        
    def print_conversation_summary(self):
        """Print a summary of all conversations in this session"""
        if not self.conversation_log:
            return
            
        print(f"\n📊 CONVERSATION SUMMARY for {self.current_session}")
        print("=" * 80)
        
        # Group by agent pairs
        conversations = {}
        for msg in self.conversation_log:
            if msg.conversation_type in [ConversationType.REQUEST, ConversationType.RESPONSE]:
                key = f"{msg.from_agent} ↔ {msg.to_agent}"
                if key not in conversations:
                    conversations[key] = []
                conversations[key].append(msg)
                
        for pair, messages in conversations.items():
            print(f"\n🗣️  {pair}")
            request_count = len([m for m in messages if m.conversation_type == ConversationType.REQUEST])
            print(f"   📝 {request_count} questions asked")
            
            # Show first question as example
            first_request = next((m for m in messages if m.conversation_type == ConversationType.REQUEST), None)
            if first_request:
                print(f"   💭 Example: {first_request.message[:80]}...")
                
        error_count = len([m for m in self.conversation_log if m.conversation_type == ConversationType.ERROR])
        if error_count > 0:
            print(f"\n❌ {error_count} errors occurred")
            
        print()


# Global logger instance
conversation_logger = AgentConversationLogger()