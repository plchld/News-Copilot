"""Base tool utilities"""

from typing import Dict, Any, Callable, List


def create_tool_definition(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    required_params: List[str]
) -> Dict[str, Any]:
    """Create an OpenAI-compatible tool definition
    
    Args:
        name: Tool name
        description: Tool description
        parameters: Parameter definitions
        required_params: List of required parameter names
        
    Returns:
        Tool definition in OpenAI format
    """
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required_params
            }
        }
    }


class ToolExecutor:
    """Executor for handling tool calls from agents"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
    
    def register(self, name: str, func: Callable):
        """Register a tool function"""
        self.tools[name] = func
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with given arguments"""
        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"
        
        try:
            result = await self.tools[tool_name](**arguments)
            return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"