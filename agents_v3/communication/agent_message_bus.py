"""Inter-agent communication system for collaborative analysis"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import uuid

from ..conversation_logging.agent_conversation_logger import conversation_logger


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MessageType(Enum):
    """Types of inter-agent messages"""
    REQUEST = "request"           # Agent requesting analysis from another agent
    RESPONSE = "response"         # Agent responding to a request
    BROADCAST = "broadcast"       # Agent broadcasting information to all
    NOTIFICATION = "notification" # Agent notifying others of status change
    COLLABORATION = "collaboration" # Agents working together on complex task


@dataclass
class AgentMessage:
    """Message structure for inter-agent communication"""
    
    id: str
    sender_id: str
    receiver_id: Optional[str]  # None for broadcast messages
    message_type: MessageType
    priority: MessagePriority
    
    # Content
    subject: str
    content: Dict[str, Any]
    
    # Context
    story_id: Optional[str] = None
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Metadata
    timestamp: float = None
    requires_response: bool = False
    response_timeout_seconds: int = 300  # 5 minutes default
    correlation_id: Optional[str] = None  # For tracking request-response pairs
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class AgentMessageBus:
    """Central message bus for inter-agent communication"""
    
    def __init__(self):
        """Initialize the message bus"""
        self.agents: Dict[str, 'BaseAgent'] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.message_handlers: Dict[str, Dict[MessageType, Callable]] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.collaboration_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Message routing and logging
        self.message_history: List[AgentMessage] = []
        self.running = False
        self.processing_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the message bus"""
        if self.running:
            return
        
        self.running = True
        self.processing_task = asyncio.create_task(self._process_messages())
        
        print("🚀 Agent message bus started")
    
    async def stop(self):
        """Stop the message bus"""
        self.running = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        print("🛑 Agent message bus stopped")
    
    def register_agent(self, agent_id: str, agent_instance: 'BaseAgent'):
        """Register an agent with the message bus"""
        self.agents[agent_id] = agent_instance
        self.message_queues[agent_id] = asyncio.Queue()
        self.message_handlers[agent_id] = {}
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from the message bus"""
        self.agents.pop(agent_id, None)
        self.message_queues.pop(agent_id, None)
        self.message_handlers.pop(agent_id, None)
        
        # Cancel any pending responses for this agent
        to_remove = []
        for msg_id, future in self.pending_responses.items():
            # Check if this future relates to the agent being removed
            if not future.done():
                # Cancel futures that are waiting for responses from this agent
                for msg in self.message_history:
                    if msg.id == msg_id and (msg.sender_id == agent_id or msg.receiver_id == agent_id):
                        future.cancel()
                        to_remove.append(msg_id)
                        break
        
        for msg_id in to_remove:
            self.pending_responses.pop(msg_id, None)
        
        # Remove from any active collaboration sessions
        sessions_to_update = []
        for session_id, session in self.collaboration_sessions.items():
            if agent_id in session.get("participants", []):
                session["participants"].remove(agent_id)
                if len(session["participants"]) < 2:
                    sessions_to_update.append(session_id)
        
        for session_id in sessions_to_update:
            self.collaboration_sessions.pop(session_id, None)
    
    def register_message_handler(
        self,
        agent_id: str,
        message_type: MessageType,
        handler: Callable[[AgentMessage], Any]
    ):
        """Register a message handler for an agent"""
        if agent_id not in self.message_handlers:
            self.message_handlers[agent_id] = {}
        
        self.message_handlers[agent_id][message_type] = handler
    
    async def send_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Send a message to another agent or broadcast"""
        # Add to message history
        self.message_history.append(message)
        
        # Set up response tracking if needed
        response_future = None
        if message.requires_response:
            response_future = asyncio.Future()
            self.pending_responses[message.id] = response_future
        
        # Route the message
        if message.receiver_id:
            # Direct message to specific agent
            if message.receiver_id in self.message_queues:
                await self.message_queues[message.receiver_id].put(message)
            else:
                conversation_logger.log_error("message_bus", message.receiver_id or "unknown", f"Unknown recipient: {message.receiver_id}")
        else:
            # Broadcast to all agents except sender
            for agent_id, queue in self.message_queues.items():
                if agent_id != message.sender_id:
                    await queue.put(message)
        
        # Wait for response if required
        if response_future:
            try:
                response = await asyncio.wait_for(
                    response_future,
                    timeout=message.response_timeout_seconds
                )
                return response
            except asyncio.TimeoutError:
                conversation_logger.log_error("message_bus", message.receiver_id or "timeout", f"Response timeout for message {message.id}")
                self.pending_responses.pop(message.id, None)
                return None
        
        return None
    
    async def send_response(self, original_message: AgentMessage, response_content: Dict[str, Any]):
        """Send a response to a received message"""
        response_message = AgentMessage(
            id=str(uuid.uuid4()),
            sender_id=original_message.receiver_id or "unknown",
            receiver_id=original_message.sender_id,
            message_type=MessageType.RESPONSE,
            priority=original_message.priority,
            subject=f"Re: {original_message.subject}",
            content=response_content,
            story_id=original_message.story_id,
            conversation_id=original_message.conversation_id,
            session_id=original_message.session_id,
            correlation_id=original_message.id
        )
        
        # Add to history
        self.message_history.append(response_message)
        
        # Complete the pending response future
        if original_message.id in self.pending_responses:
            future = self.pending_responses.pop(original_message.id)
            if not future.done():
                future.set_result(response_message)
    
    async def _process_messages(self):
        """Background task to process messages for all agents"""
        while self.running:
            try:
                # Process messages for each agent
                for agent_id in list(self.message_queues.keys()):
                    queue = self.message_queues[agent_id]
                    
                    try:
                        # Get message without blocking
                        message = queue.get_nowait()
                        
                        # Process the message
                        await self._handle_message(agent_id, message)
                        
                    except asyncio.QueueEmpty:
                        continue
                    except Exception as e:
                        conversation_logger.log_error("message_bus", agent_id, f"Error processing message for {agent_id}: {str(e)}")
                
                # Short sleep to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                conversation_logger.log_error("message_bus", "system", f"Error in message processing loop: {str(e)}")
                await asyncio.sleep(1)  # Longer sleep on error
    
    async def _handle_message(self, agent_id: str, message: AgentMessage):
        """Handle a message for a specific agent"""
        # Check if agent has a handler for this message type
        if (agent_id in self.message_handlers and 
            message.message_type in self.message_handlers[agent_id]):
            
            handler = self.message_handlers[agent_id][message.message_type]
            
            try:
                # Call the handler
                result = await handler(message) if asyncio.iscoroutinefunction(handler) else handler(message)
                
                # If the original message requires a response and handler returned content
                if message.requires_response and result:
                    await self.send_response(message, result)
                    
            except Exception as e:
                conversation_logger.log_error(agent_id, message.sender_id, f"Error in message handler: {str(e)}")
        else:
            # No specific handler - ignore silently for now
            pass
    
    async def request_analysis(
        self,
        requester_id: str,
        target_agent_id: str,
        analysis_type: str,
        story_data: Dict[str, Any],
        conversation_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.MEDIUM,
        timeout_seconds: int = 300
    ) -> Optional[Dict[str, Any]]:
        """Request analysis from another agent"""
        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender_id=requester_id,
            receiver_id=target_agent_id,
            message_type=MessageType.REQUEST,
            priority=priority,
            subject=f"Analysis Request: {analysis_type}",
            content={
                "analysis_type": analysis_type,
                "story_data": story_data,
                "requested_by": requester_id
            },
            story_id=story_data.get("id"),
            conversation_id=conversation_id,
            requires_response=True,
            response_timeout_seconds=timeout_seconds
        )
        
        response = await self.send_message(message)
        return response.content if response else None
    
    async def start_collaboration(
        self,
        initiator_id: str,
        participant_ids: List[str],
        collaboration_type: str,
        shared_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """Start a collaboration session between multiple agents"""
        collaboration_id = str(uuid.uuid4())
        
        # Set up collaboration session
        self.collaboration_sessions[collaboration_id] = {
            "id": collaboration_id,
            "initiator": initiator_id,
            "participants": participant_ids,
            "type": collaboration_type,
            "shared_data": shared_data,
            "session_id": session_id,
            "created_at": time.time(),
            "status": "active"
        }
        
        # Notify all participants
        for participant_id in participant_ids:
            if participant_id != initiator_id:
                notification = AgentMessage(
                    id=str(uuid.uuid4()),
                    sender_id=initiator_id,
                    receiver_id=participant_id,
                    message_type=MessageType.COLLABORATION,
                    priority=MessagePriority.HIGH,
                    subject=f"Collaboration Invitation: {collaboration_type}",
                    content={
                        "collaboration_id": collaboration_id,
                        "collaboration_type": collaboration_type,
                        "initiator": initiator_id,
                        "participants": participant_ids,
                        "shared_data": shared_data
                    },
                    session_id=session_id
                )
                
                await self.send_message(notification)
        
        return collaboration_id
    
    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        since: Optional[float] = None
    ) -> List[AgentMessage]:
        """Get message history with optional filters"""
        messages = self.message_history
        
        if agent_id:
            messages = [
                msg for msg in messages 
                if msg.sender_id == agent_id or msg.receiver_id == agent_id
            ]
        
        if message_type:
            messages = [msg for msg in messages if msg.message_type == message_type]
        
        if since:
            messages = [msg for msg in messages if msg.timestamp >= since]
        
        return messages


# Global message bus instance
message_bus = AgentMessageBus()