"""Simplified inter-agent communication with clear audit trails"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

module_logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages between agents"""
    ANALYSIS_REQUEST = "analysis_request"
    ANALYSIS_RESPONSE = "analysis_response"
    FACT_CHECK_REQUEST = "fact_check_request"
    FACT_CHECK_RESPONSE = "fact_check_response"


@dataclass
class AgentMessage:
    """Simple message structure for clarity and auditability"""
    message_id: str
    sender_agent: str
    target_agent: str
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "message_id": self.message_id,
            "sender_agent": self.sender_agent,
            "target_agent": self.target_agent,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp
        }


class SimpleMessageBus:
    """Simplified message bus focusing on clarity and auditability"""
    
    def __init__(self, log_messages: bool = True):
        """Initialize the message bus
        
        Args:
            log_messages: Whether to log all messages for audit
        """
        self.agents: Dict[str, Any] = {}  # agent_id -> agent instance
        self.message_handlers: Dict[str, Callable] = {}  # agent_id -> handler function
        self.message_log: List[AgentMessage] = []
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.log_messages = log_messages
        self.running = False
        
    def register_agent(self, agent_id: str, agent_instance: Any, handler: Callable):
        """Register an agent with its message handler
        
        Args:
            agent_id: Unique agent identifier
            agent_instance: The agent object
            handler: Async function to handle messages
        """
        self.agents[agent_id] = agent_instance
        self.message_handlers[agent_id] = handler
        module_logger.info(f"Registered agent: {agent_id}")
        
    async def send_message(
        self, 
        sender: str, 
        target: str, 
        message_type: MessageType, 
        payload: Dict[str, Any],
        timeout: int = 60
    ) -> Optional[Dict[str, Any]]:
        """Send a message and optionally wait for response
        
        Args:
            sender: Sender agent ID
            target: Target agent ID
            message_type: Type of message
            payload: Message content
            timeout: Response timeout in seconds
            
        Returns:
            Response payload if applicable
        """
        # Create message
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_agent=sender,
            target_agent=target,
            message_type=message_type,
            payload=payload
        )
        
        # Log for audit
        if self.log_messages:
            self.message_log.append(message)
            module_logger.info(
                f"Message sent: {sender} -> {target} | "
                f"Type: {message_type.value} | ID: {message.message_id}"
            )
            module_logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Check if target exists
        if target not in self.agents:
            module_logger.error(f"Target agent not found: {target}")
            return None
            
        # Get handler
        handler = self.message_handlers.get(target)
        if not handler:
            module_logger.error(f"No handler registered for agent: {target}")
            return None
            
        try:
            # Call handler
            response = await asyncio.wait_for(
                handler(message),
                timeout=timeout
            )
            
            # Log response
            if response and self.log_messages:
                module_logger.info(
                    f"Response received: {target} -> {sender} | "
                    f"Message ID: {message.message_id}"
                )
                module_logger.debug(f"Response: {json.dumps(response, indent=2)}")
                
            return response
            
        except asyncio.TimeoutError:
            module_logger.error(
                f"Timeout waiting for response from {target} "
                f"(Message ID: {message.message_id})"
            )
            return None
        except Exception as e:
            module_logger.exception(
                f"Error handling message from {sender} to {target}: {e}"
            )
            return None
    
    async def request_analysis(
        self,
        requester: str,
        provider: str,
        story_data: Dict[str, Any],
        analysis_type: str
    ) -> Optional[str]:
        """Request analysis from another agent
        
        Args:
            requester: Requesting agent ID
            provider: Provider agent ID
            story_data: Story information
            analysis_type: Type of analysis needed
            
        Returns:
            Analysis result as string
        """
        payload = {
            "story_data": story_data,
            "analysis_type": analysis_type,
            "request_time": time.time()
        }
        
        response = await self.send_message(
            sender=requester,
            target=provider,
            message_type=MessageType.ANALYSIS_REQUEST,
            payload=payload
        )
        
        if response:
            return response.get("analysis", "")
        return None
    
    async def request_fact_check(
        self,
        requester: str,
        provider: str,
        claim: str,
        context: str,
        search_query: str
    ) -> Optional[Dict[str, Any]]:
        """Request fact-check from context agent
        
        Args:
            requester: Requesting agent (fact-checker)
            provider: Provider agent (context agent)
            claim: Claim to verify
            context: Context where claim appeared
            search_query: Suggested search query
            
        Returns:
            Fact-check results
        """
        payload = {
            "claim": claim,
            "context": context,
            "search_query": search_query,
            "request_time": time.time()
        }
        
        response = await self.send_message(
            sender=requester,
            target=provider,
            message_type=MessageType.FACT_CHECK_REQUEST,
            payload=payload,
            timeout=120  # Longer timeout for searches
        )
        
        return response
    
    def get_message_log(self, 
                       agent_id: Optional[str] = None,
                       message_type: Optional[MessageType] = None,
                       last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get message log for audit
        
        Args:
            agent_id: Filter by agent (sender or target)
            message_type: Filter by message type
            last_n: Get last N messages
            
        Returns:
            List of messages as dictionaries
        """
        messages = self.message_log
        
        # Filter by agent
        if agent_id:
            messages = [
                m for m in messages 
                if m.sender_agent == agent_id or m.target_agent == agent_id
            ]
        
        # Filter by type
        if message_type:
            messages = [
                m for m in messages
                if m.message_type == message_type
            ]
        
        # Get last N
        if last_n:
            messages = messages[-last_n:]
            
        return [m.to_dict() for m in messages]
    
    def print_audit_summary(self):
        """Print summary of all messages for audit"""
        print("\n📊 Message Bus Audit Summary")
        print("=" * 50)
        
        # Count by type
        type_counts = {}
        for msg in self.message_log:
            msg_type = msg.message_type.value
            type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
        
        print("\nMessage Types:")
        for msg_type, count in type_counts.items():
            print(f"  • {msg_type}: {count}")
        
        # Count by agent pairs
        pair_counts = {}
        for msg in self.message_log:
            pair = f"{msg.sender_agent} -> {msg.target_agent}"
            pair_counts[pair] = pair_counts.get(pair, 0) + 1
        
        print("\nAgent Communications:")
        for pair, count in sorted(pair_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {pair}: {count} messages")
        
        print(f"\nTotal messages: {len(self.message_log)}")
        
        # Show recent messages
        print("\nRecent Messages (last 5):")
        for msg in self.message_log[-5:]:
            print(f"  [{msg.timestamp:.0f}] {msg.sender_agent} -> {msg.target_agent}: {msg.message_type.value}")


# Global instance
simple_message_bus = SimpleMessageBus()