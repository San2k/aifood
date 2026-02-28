"""
MCP FatSecret Service - Main Entry Point
Simplified MCP-like server for FatSecret API integration.
"""

import asyncio
import json
import logging
from typing import Dict, Any

from .client.fatsecret_client import FatSecretClient
from .server.tools import (
    search_food_tool,
    get_food_tool,
    get_servings_tool,
    SEARCH_FOOD_METADATA,
    GET_FOOD_METADATA,
    GET_SERVINGS_METADATA
)
from .config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPFatSecretServer:
    """MCP Server for FatSecret API."""
    
    def __init__(self):
        self.client = FatSecretClient()
        self.tools = {
            "search_food": {
                "handler": search_food_tool,
                "metadata": SEARCH_FOOD_METADATA
            },
            "get_food": {
                "handler": get_food_tool,
                "metadata": GET_FOOD_METADATA
            },
            "get_servings": {
                "handler": get_servings_tool,
                "metadata": GET_SERVINGS_METADATA
            }
        }
        logger.info("MCP FatSecret Server initialized")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool with given arguments.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            JSON string with result
        """
        if tool_name not in self.tools:
            return json.dumps({
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            })
        
        tool = self.tools[tool_name]
        handler = tool["handler"]
        
        try:
            # Pass client to handler
            result = await handler(**arguments, client=self.client)
            logger.info(f"Tool {tool_name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    def list_tools(self) -> Dict[str, Any]:
        """List all available tools."""
        return {
            name: tool["metadata"]
            for name, tool in self.tools.items()
        }


# Global server instance
mcp_server = MCPFatSecretServer()


async def main():
    """Main entry point for standalone testing."""
    logger.info("MCP FatSecret Server started")
    
    # Test the tools
    logger.info("Testing search_food...")
    result = await mcp_server.call_tool("search_food", {"query": "eggs", "max_results": 5})
    print("Search results:", result)
    
    # Keep server running
    logger.info("Server ready. Press Ctrl+C to stop.")
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
