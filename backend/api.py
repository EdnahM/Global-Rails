from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from toolkit import TOOLKIT

app = FastAPI(title="Global Rails API")


# Allow the React/Vite frontend to communicate with the Python backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_tools():
    """Return the registered Global Rails tools by name."""
    items = TOOLKIT.values() if isinstance(TOOLKIT, dict) else TOOLKIT
    return {tool.name: tool for tool in items}


TOOLS = get_tools()


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "Global Rails API",
        "tools": list(TOOLS.keys()),
    }


@app.get("/tools")
def list_tools():
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
            }
            for tool in TOOLS.values()
        ]
    }


@app.post("/tool/{tool_name}")
def execute_tool(tool_name: str, payload: dict):
    """Execute one Global Rails tool directly."""
    tool = TOOLS.get(tool_name)

    if tool is None:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
        }

    try:
        result = tool.execute(**payload)

        if hasattr(result, "to_dict"):
            return result.to_dict()

        return result

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "tool": tool_name,
        }