import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Standardized response for every Global Rails backend tool.

    Every tool returns one of these so the MCP adapter (and any downstream
    LangChain/CrewAI/agent host) sees the same shape regardless of which
    tool was called: a success flag, a structured data payload, and an
    optional error message.
    """

    success: bool = Field(description="Whether the tool executed successfully")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured payload returned by the tool",
    )
    error: Optional[str] = Field(
        default=None, description="Error message when execution failed"
    )

    def to_string(self) -> str:
        """Serialize the result to a JSON string for LLM/agent consumption."""
        return json.dumps(self.model_dump(mode="json"), indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Return the result as a plain dict (JSON-safe) for MCP clients."""
        return self.model_dump(mode="json")


class BaseTool(ABC):
    """Abstract base class for all Global Rails backend tools.

    Every concrete tool exposes:

      * 'name'          - unique tool identifier surfaced over MCP
      * 'description'   - human/AI-facing summary of what the tool does
      * 'input_schema'  - a pydantic model describing the tool's arguments
      * 'execute()'     - the sync entry point returning a 'ToolResult'

    This contract is intentionally dependency-free (pure pydantic). The MCP
    adapter in 'backend/mcp/adapter.py' discovers 'input_schema' and
    'execute' automatically, so adding a new tool only requires subclassing
    this class and registering its instance in 'backend/__init__.py'.
    """

    name: str = ""
    description: str = ""
    input_schema: Optional[type[BaseModel]] = None

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool and return a standardized 'ToolResult'."""
        raise NotImplementedError

    # -- Async convenience: the MCP adapter calls sync 'execute' in a
    # -- thread, so subclasses only need to implement the sync method above.
    async def aexecute(self, **kwargs: Any) -> ToolResult:
        import asyncio

        return await asyncio.to_thread(self.execute, **kwargs)
