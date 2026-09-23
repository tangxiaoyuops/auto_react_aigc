"""Tool routes"""
from typing import List
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ToolResponse(BaseModel):
    """Tool response"""
    name: str
    display_name: str
    description: str
    category: str
    input_schema: dict


# Mock tools for demo
AVAILABLE_TOOLS = [
    {
        "name": "web_search",
        "display_name": "Web Search",
        "description": "Search the web for information",
        "category": "search",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "calculator",
        "display_name": "Calculator",
        "description": "Perform mathematical calculations",
        "category": "utility",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Mathematical expression"}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "code_runner",
        "display_name": "Code Runner",
        "description": "Execute Python code",
        "category": "code",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout": {"type": "integer", "default": 30}
            },
            "required": ["code"]
        }
    }
]


@router.get("", response_model=List[ToolResponse])
async def list_tools():
    """List available tools"""
    return [
        ToolResponse(
            name=tool["name"],
            display_name=tool["display_name"],
            description=tool["description"],
            category=tool["category"],
            input_schema=tool["input_schema"]
        )
        for tool in AVAILABLE_TOOLS
    ]


@router.get("/{name}", response_model=ToolResponse)
async def get_tool(name: str):
    """Get tool by name"""
    tool = next((t for t in AVAILABLE_TOOLS if t["name"] == name), None)
    
    if not tool:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return ToolResponse(
        name=tool["name"],
        display_name=tool["display_name"],
        description=tool["description"],
        category=tool["category"],
        input_schema=tool["input_schema"]
    )
