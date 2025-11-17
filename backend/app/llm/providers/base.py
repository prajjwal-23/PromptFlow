"""
Base LLM Provider Interface.

This module defines the abstract base class and common interfaces for all
LLM providers in the PromptFlow system.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import (
    Any, AsyncGenerator, Dict, List, Optional, Union, Callable
)
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class LLMProviderType(Enum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class LLMModelType(Enum):
    """Supported model types by provider."""
    # OpenAI models
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    
    # Anthropic models
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    
    # Ollama models (examples)
    LLAMA_2 = "llama2"
    LLAMA_3 = "llama3"
    MISTRAL = "mistral"
    CODELLAMA = "codellama"


class MessageRole(Enum):
    """Message roles in conversations."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class LLMMessage:
    """A message in a conversation."""
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


@dataclass
class LLMTool:
    """A tool/function definition for LLM function calling."""
    name: str
    description: str
    parameters: Dict[str, Any]
    strict: Optional[bool] = None


@dataclass
class LLMToolCall:
    """A tool/function call made by the LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMUsage:
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_cost: Optional[float] = None
    completion_cost: Optional[float] = None
    total_cost: Optional[float] = None


@dataclass
class LLMResponse:
    """Response from a non-streaming LLM call."""
    content: str
    model: str
    provider: LLMProviderType
    usage: Optional[LLMUsage] = None
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[LLMToolCall]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LLMStreamResponse:
    """Response chunk from a streaming LLM call."""
    content: str
    delta: str
    model: str
    provider: LLMProviderType
    is_finished: bool = False
    finish_reason: Optional[str] = None
    usage: Optional[LLMUsage] = None
    tool_calls: Optional[List[LLMToolCall]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class LLMConfig(BaseModel):
    """Configuration for LLM providers."""
    provider: LLMProviderType
    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    organization: Optional[str] = None
    
    # Generation parameters
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=None, ge=1)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = None
    
    # Advanced parameters
    seed: Optional[int] = None
    response_format: Optional[Dict[str, Any]] = None
    safe_prompt: bool = False
    
    # Connection parameters
    timeout: float = Field(default=60.0, ge=1.0)
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, ge=0.1)
    
    # Streaming parameters
    stream: bool = False
    stream_chunk_size: int = Field(default=1024, ge=1)
    
    # Provider-specific parameters
    provider_config: Dict[str, Any] = Field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        """
        Initialize the LLM provider.
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self.provider_type = config.provider
        self.model = config.model
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (e.g., validate credentials, setup client)."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of conversation messages
            tools: Available tools for function calling
            tool_choice: Tool choice strategy
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLM response
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[LLMStreamResponse, None]:
        """
        Generate a streaming response from the LLM.
        
        Args:
            messages: List of conversation messages
            tools: Available tools for function calling
            tool_choice: Tool choice strategy
            **kwargs: Additional provider-specific parameters
            
        Yields:
            LLM stream response chunks
        """
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """
        Validate the provider configuration.
        
        Returns:
            True if configuration is valid
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the configured model.
        
        Returns:
            Model information dictionary
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the provider.
        
        Returns:
            Health check result
        """
        try:
            # Simple health check with a minimal request
            test_messages = [
                LLMMessage(role=MessageRole.USER, content="Hello")
            ]
            
            start_time = datetime.utcnow()
            response = await self.generate(test_messages, max_tokens=5)
            end_time = datetime.utcnow()
            
            return {
                "status": "healthy",
                "provider": self.provider_type.value,
                "model": self.model,
                "response_time_ms": (end_time - start_time).total_seconds() * 1000,
                "timestamp": end_time.isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider_type.value,
                "model": self.model,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def estimate_cost(self, usage: LLMUsage) -> Optional[float]:
        """
        Estimate the cost of a request based on token usage.
        
        Args:
            usage: Token usage information
            
        Returns:
            Estimated cost in USD
        """
        # Default implementation - should be overridden by providers
        return None
    
    def format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """
        Format messages for the specific provider.
        
        Args:
            messages: List of LLM messages
            
        Returns:
            Provider-formatted messages
        """
        formatted = []
        for msg in messages:
            formatted_msg = {
                "role": msg.role.value,
                "content": msg.content
            }
            if msg.name:
                formatted_msg["name"] = msg.name
            if msg.tool_calls:
                formatted_msg["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                formatted_msg["tool_call_id"] = msg.tool_call_id
            formatted.append(formatted_msg)
        return formatted
    
    def format_tools(self, tools: Optional[List[LLMTool]]) -> Optional[List[Dict[str, Any]]]:
        """
        Format tools for the specific provider.
        
        Args:
            tools: List of LLM tools
            
        Returns:
            Provider-formatted tools
        """
        if not tools:
            return None
            
        formatted = []
        for tool in tools:
            formatted_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            if tool.strict is not None:
                formatted_tool["function"]["strict"] = tool.strict
            formatted.append(formatted_tool)
        return formatted


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass


class LLMConfigError(LLMProviderError):
    """Exception for configuration errors."""
    pass


class LLMConnectionError(LLMProviderError):
    """Exception for connection errors."""
    pass


class LLMRateLimitError(LLMProviderError):
    """Exception for rate limit errors."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class LLMTokenLimitError(LLMProviderError):
    """Exception for token limit errors."""
    def __init__(self, message: str, token_limit: int, token_count: int):
        super().__init__(message)
        self.token_limit = token_limit
        self.token_count = token_count


class LLMContentFilterError(LLMProviderError):
    """Exception for content filter errors."""
    pass


class LLMTimeoutError(LLMProviderError):
    """Exception for timeout errors."""
    pass


# Utility functions
def create_message(role: str, content: str, **kwargs) -> LLMMessage:
    """Create an LLM message."""
    return LLMMessage(role=MessageRole(role), content=content, **kwargs)


def create_tool(name: str, description: str, parameters: Dict[str, Any]) -> LLMTool:
    """Create an LLM tool."""
    return LLMTool(name=name, description=description, parameters=parameters)


def calculate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    prompt_cost_per_1k: float,
    completion_cost_per_1k: float
) -> float:
    """
    Calculate cost based on token usage.
    
    Args:
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        prompt_cost_per_1k: Cost per 1000 prompt tokens
        completion_cost_per_1k: Cost per 1000 completion tokens
        
    Returns:
        Total cost in USD
    """
    prompt_cost = (prompt_tokens / 1000) * prompt_cost_per_1k
    completion_cost = (completion_tokens / 1000) * completion_cost_per_1k
    return prompt_cost + completion_cost