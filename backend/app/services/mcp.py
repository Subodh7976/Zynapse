from langchain_mcp_tools import convert_mcp_to_langchain_tools


mcp_servers = {
    "search": {  # https://github.com/nickclyde/duckduckgo-mcp-server/tree/main
        "command": "uvx",
        "args": ["duckduckgo-mcp-server"]
    },
    "arXivPaper": {  # https://github.com/daheepk/arxiv-paper-mcp
        "command": "uvx",
        "args": [
            "--from",
            "arxiv-paper-mcp",
            "arxiv-mcp"
        ]
    }
}


async def create_mcp_tools():
    tools, cleanup = await convert_mcp_to_langchain_tools(mcp_servers)
    return tools, cleanup
