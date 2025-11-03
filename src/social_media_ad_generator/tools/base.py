"""Common abstractions for agent-style tools."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Type

from pydantic import BaseModel, ValidationError


class ToolInput(BaseModel):
    """Base class for tool input models."""


class ToolOutput(BaseModel):
    """Base class for tool output models."""


@dataclass
class ToolSpec:
    """Specification describing a tool for agent frameworks."""

    name: str
    description: str
    args_schema: Type[BaseModel]
    return_schema: Type[BaseModel]

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable representation of the specification."""

        return {
            "name": self.name,
            "description": self.description,
            "args_schema": self.args_schema.model_json_schema(),
            "return_schema": self.return_schema.model_json_schema(),
        }


class AgentTool(ABC):
    """Base class for async tools that can be orchestrated by agents."""

    name: str = ""
    description: str = ""
    args_model: Type[ToolInput] = ToolInput
    return_model: Type[ToolOutput] = ToolOutput

    def __init__(self, *, name: Optional[str] = None, description: Optional[str] = None) -> None:
        self.name = name or self.name or self.__class__.__name__.lower()
        self.description = description or self.description or (self.__class__.__doc__ or "")
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    def spec(self) -> ToolSpec:
        """Return a serialisable specification for this tool."""

        return ToolSpec(
            name=self.name,
            description=self.description,
            args_schema=self.args_model,
            return_schema=self.return_model,
        )

    async def ainvoke(self, params: Optional[BaseModel] = None, /, **data: Any) -> ToolOutput:
        """Validate input and execute the tool asynchronously."""

        payload: Dict[str, Any]
        if params is not None and data:
            raise ValueError("Provide either a BaseModel instance or keyword arguments, not both")

        if params is not None:
            if not isinstance(params, BaseModel):
                raise TypeError("params must be a Pydantic BaseModel instance")
            payload = params.model_dump()
        else:
            payload = data

        try:
            parsed = self.args_model(**payload)
        except ValidationError as exc:
            raise ValueError(f"Invalid input for tool '{self.name}': {exc}") from exc

        result = await self._arun(parsed)

        if isinstance(result, BaseModel):
            return self.return_model.model_validate(result.model_dump())
        if isinstance(result, dict):
            return self.return_model(**result)
        if isinstance(result, self.return_model):
            return result

        raise TypeError(
            f"Tool '{self.name}' returned unsupported type {type(result)!r}. Expected dict or BaseModel."
        )

    def invoke(self, **data: Any) -> ToolOutput:
        """Synchronous helper that runs the tool in a dedicated event loop."""

        return asyncio.run(self.ainvoke(**data))

    @abstractmethod
    async def _arun(self, params: ToolInput) -> ToolOutput:
        """Execute the tool with validated parameters."""


class ToolManager:
    """Registry and orchestrator for agent tools."""

    def __init__(self, tools: Optional[Iterable[AgentTool]] = None) -> None:
        self._tools: Dict[str, AgentTool] = {}
        if tools:
            for tool in tools:
                self.register(tool)

    def register(self, tool: AgentTool) -> None:
        """Register a tool instance."""

        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> AgentTool:
        """Retrieve a tool by name."""

        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered")
        return self._tools[name]

    def specs(self) -> List[ToolSpec]:
        """Return specifications for all registered tools."""

        return [tool.spec() for tool in self._tools.values()]

    async def ainvoke(self, name: str, **data: Any) -> ToolOutput:
        """Invoke a registered tool asynchronously."""

        tool = self.get(name)
        return await tool.ainvoke(**data)

    def invoke(self, name: str, **data: Any) -> ToolOutput:
        """Invoke a registered tool synchronously."""

        tool = self.get(name)
        return tool.invoke(**data)

    @classmethod
    def default(cls) -> "ToolManager":
        """Create a tool manager with the default tool set."""

        # Import locally to avoid circular imports
        from .ad_generator import AdGenerator
        from .image_analyzer import ImageAnalyzer
        from .question_engine import QuestionEngine

        return cls(tools=[ImageAnalyzer(), QuestionEngine(), AdGenerator()])
