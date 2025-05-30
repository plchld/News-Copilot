"""Inter-agent communication system"""

from .agent_message_bus import (
    AgentMessageBus,
    AgentMessage,
    MessageType,
    MessagePriority,
    message_bus
)

__all__ = [
    "AgentMessageBus",
    "AgentMessage", 
    "MessageType",
    "MessagePriority",
    "message_bus"
]