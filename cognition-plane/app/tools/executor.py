"""Tool executor"""
from typing import Dict, Any, Optional
from app.tools.builtin import calculator, web_search


class ToolExecutor:
    """Tool executor for running various tools"""
    
    def __init__(self):
        self.tools = {
            "calculator": calculator.execute,
            "web_search": web_search.execute,
            # Add more tools as needed
        }
    
    async def execute(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool"""
        tool_func = self.tools.get(tool_name)
        
        if not tool_func:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "tool": tool_name
            }
        
        try:
            result = await tool_func(**tool_args)
            return {
                "success": True,
                "result": result,
                "tool": tool_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }
    
    def register_tool(self, name: str, func):
        """Register a new tool"""
        self.tools[name] = func
    
    def list_tools(self):
        """List available tools"""
        return list(self.tools.keys())
