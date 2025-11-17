"""
OpenAI LLM Provider Implementation.

This module provides the OpenAI implementation of the LLM provider interface,
supporting both synchronous and asynchronous operations, streaming, and
function calling capabilities.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import aiohttp
from openai import AsyncOpenAI, OpenAIError, RateLimitError, APIError

from .base import (
    LLMProvider, LLMConfig, LLMResponse, LLMStreamResponse, LLMUsage,
    LLMMessage, LLMTool, LLMToolCall, LLMProviderType, MessageRole,
    LLMProviderError, LLMConfigError, LLMConnectionError, LLMRateLimitError,
    LLMTokenLimitError, LLMContentFilterError, LLMTimeoutError
)
from app.core.logging import get_logger


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of the LLM provider interface."""
    
    # OpenAI model pricing (per 1K tokens as of 2024)
    MODEL_PRICING = {
        "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
        "gpt-3.5-turbo-16k": {"prompt": 0.003, "completion": 0.004},
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-32k": {"prompt": 0.06, "completion": 0.12},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-4-turbo-2024-04-09": {"prompt": 0.01, "completion": 0.03},
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},
        "gpt-4o-2024-05-13": {"prompt": 0.005, "completion": 0.015},
        "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
        "gpt-4o-mini-2024-07-18": {"prompt": 0.00015, "completion": 0.0006},
    }
    
    # OpenAI model context limits
    MODEL_LIMITS = {
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,
        "gpt-4-turbo-2024-04-09": 128000,
        "gpt-4o": 128000,
        "gpt-4o-2024-05-13": 128000,
        "gpt-4o-mini": 128000,
        "gpt-4o-mini-2024-07-18": 128000,
    }
    
    def __init__(self, config: LLMConfig):
        """
        Initialize the OpenAI provider.
        
        Args:
            config: OpenAI configuration
        """
        super().__init__(config)
        self.client: Optional[AsyncOpenAI] = None
        self.logger = get_logger(f"{__name__}.OpenAIProvider")
        
        # Validate model
        if config.model not in self.MODEL_LIMITS:
            self.logger.warning(f"Unknown model: {config.model}")
    
    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        try:
            # Create OpenAI client
            client_kwargs = {
                "api_key": self.config.api_key,
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries
            }
            
            if self.config.api_base:
                client_kwargs["base_url"] = self.config.api_base
            
            if self.config.organization:
                client_kwargs["organization"] = self.config.organization
            
            if self.config.api_version:
                # OpenAI doesn't use api_version, but we'll store it for compatibility
                client_kwargs["default_headers"] = {
                    "OpenAI-API-Version": self.config.api_version
                }
            
            self.client = AsyncOpenAI(**client_kwargs)
            
            # Validate configuration
            await self.validate_config()
            
            self.logger.info(f"OpenAI provider initialized with model: {self.model}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI provider: {e}")
            raise LLMConfigError(f"OpenAI initialization failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup OpenAI client resources."""
        if self.client:
            await self.client.close()
            self.client = None
            self.logger.info("OpenAI provider cleaned up")
    
    async def validate_config(self) -> bool:
        """
        Validate the OpenAI configuration.
        
        Returns:
            True if configuration is valid
        """
        if not self.config.api_key:
            raise LLMConfigError("OpenAI API key is required")
        
        # Test connection with a minimal request
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            raise LLMConfigError(f"OpenAI configuration validation failed: {e}")
    
    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from OpenAI.
        
        Args:
            messages: List of conversation messages
            tools: Available tools for function calling
            tool_choice: Tool choice strategy
            **kwargs: Additional OpenAI-specific parameters
            
        Returns:
            OpenAI response
        """
        if not self.client:
            await self.initialize()
        
        try:
            # Prepare request parameters
            request_params = self._prepare_request_params(
                messages, tools, tool_choice, **kwargs
            )
            
            # Make API call
            response = await self.client.chat.completions.create(**request_params)
            
            # Convert to our format
            return self._convert_response(response)
            
        except RateLimitError as e:
            retry_after = getattr(e, 'retry_after', None)
            raise LLMRateLimitError(str(e), retry_after)
        except APIError as e:
            if "content_filter" in str(e).lower():
                raise LLMContentFilterError(str(e))
            elif "maximum context length" in str(e).lower():
                raise LLMTokenLimitError(str(e), 0, 0)
            else:
                raise LLMProviderError(f"OpenAI API error: {e}")
        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"OpenAI request timeout after {self.config.timeout}s")
        except Exception as e:
            raise LLMProviderError(f"OpenAI generation failed: {e}")
    
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[LLMStreamResponse, None]:
        """
        Generate a streaming response from OpenAI.
        
        Args:
            messages: List of conversation messages
            tools: Available tools for function calling
            tool_choice: Tool choice strategy
            **kwargs: Additional OpenAI-specific parameters
            
        Yields:
            OpenAI stream response chunks
        """
        if not self.client:
            await self.initialize()
        
        try:
            # Prepare request parameters for streaming
            request_params = self._prepare_request_params(
                messages, tools, tool_choice, stream=True, **kwargs
            )
            
            # Make streaming API call
            stream = await self.client.chat.completions.create(**request_params)
            
            # Process stream chunks
            accumulated_content = ""
            accumulated_tool_calls = []
            
            async for chunk in stream:
                stream_response = self._convert_stream_chunk(
                    chunk, accumulated_content, accumulated_tool_calls
                )
                
                if stream_response.delta:
                    accumulated_content += stream_response.delta
                
                if stream_response.tool_calls:
                    accumulated_tool_calls.extend(stream_response.tool_calls)
                
                yield stream_response
                
                if stream_response.is_finished:
                    break
                    
        except RateLimitError as e:
            retry_after = getattr(e, 'retry_after', None)
            raise LLMRateLimitError(str(e), retry_after)
        except APIError as e:
            if "content_filter" in str(e).lower():
                raise LLMContentFilterError(str(e))
            elif "maximum context length" in str(e).lower():
                raise LLMTokenLimitError(str(e), 0, 0)
            else:
                raise LLMProviderError(f"OpenAI API error: {e}")
        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"OpenAI request timeout after {self.config.timeout}s")
        except Exception as e:
            raise LLMProviderError(f"OpenAI streaming failed: {e}")
    
    def _prepare_request_params(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare request parameters for OpenAI API."""
        params = {
            "model": self.model,
            "messages": self.format_messages(messages),
            "temperature": self.config.temperature,
            "stream": kwargs.get("stream", self.config.stream),
        }
        
        # Add optional parameters
        if self.config.max_tokens:
            params["max_tokens"] = self.config.max_tokens
        
        if self.config.top_p:
            params["top_p"] = self.config.top_p
        
        if self.config.frequency_penalty is not None:
            params["frequency_penalty"] = self.config.frequency_penalty
        
        if self.config.presence_penalty is not None:
            params["presence_penalty"] = self.config.presence_penalty
        
        if self.config.stop:
            params["stop"] = self.config.stop
        
        if self.config.seed:
            params["seed"] = self.config.seed
        
        if self.config.response_format:
            params["response_format"] = self.config.response_format
        
        # Add tools if provided
        if tools:
            params["tools"] = self.format_tools(tools)
            
            if tool_choice:
                if isinstance(tool_choice, str):
                    if tool_choice == "auto":
                        params["tool_choice"] = "auto"
                    elif tool_choice == "none":
                        params["tool_choice"] = "none"
                    elif tool_choice == "required":
                        params["tool_choice"] = "required"
                    else:
                        # Specific tool name
                        params["tool_choice"] = {"type": "function", "function": {"name": tool_choice}}
                elif isinstance(tool_choice, dict):
                    params["tool_choice"] = tool_choice
        
        # Add provider-specific config
        params.update(self.config.provider_config)
        
        # Override with any explicit kwargs
        params.update(kwargs)
        
        return params
    
    def _convert_response(self, response) -> LLMResponse:
        """Convert OpenAI response to our format."""
        choice = response.choices[0]
        message = choice.message
        
        # Extract content
        content = message.content or ""
        
        # Extract tool calls
        tool_calls = None
        if message.tool_calls:
            tool_calls = []
            for tool_call in message.tool_calls:
                tool_calls.append(LLMToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=json.loads(tool_call.function.arguments)
                ))
        
        # Extract usage
        usage = None
        if response.usage:
            usage = LLMUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            )
            
            # Calculate cost
            cost = self.estimate_cost(usage)
            if cost:
                usage.prompt_cost = cost * 0.7  # Approximate split
                usage.completion_cost = cost * 0.3
                usage.total_cost = cost
        
        return LLMResponse(
            content=content,
            model=response.model,
            provider=LLMProviderType.OPENAI,
            usage=usage,
            finish_reason=choice.finish_reason,
            tool_calls=tool_calls,
            metadata={
                "system_fingerprint": response.system_fingerprint,
                "created": response.created,
                "id": response.id
            }
        )
    
    def _convert_stream_chunk(
        self,
        chunk,
        accumulated_content: str,
        accumulated_tool_calls: List[LLMToolCall]
    ) -> LLMStreamResponse:
        """Convert OpenAI stream chunk to our format."""
        choice = chunk.choices[0] if chunk.choices else None
        delta = choice.delta if choice else None
        
        # Extract delta content
        delta_content = delta.content if delta and delta.content else ""
        
        # Extract delta tool calls
        delta_tool_calls = None
        if delta and delta.tool_calls:
            delta_tool_calls = []
            for tool_call in delta.tool_calls:
                if tool_call.function:
                    delta_tool_calls.append(LLMToolCall(
                        id=tool_call.id or "",
                        name=tool_call.function.name or "",
                        arguments=json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    ))
        
        # Check if finished
        is_finished = choice and choice.finish_reason is not None
        
        # Extract usage if available
        usage = None
        if chunk.usage:
            usage = LLMUsage(
                prompt_tokens=chunk.usage.prompt_tokens,
                completion_tokens=chunk.usage.completion_tokens,
                total_tokens=chunk.usage.total_tokens
            )
            
            # Calculate cost
            cost = self.estimate_cost(usage)
            if cost:
                usage.prompt_cost = cost * 0.7
                usage.completion_cost = cost * 0.3
                usage.total_cost = cost
        
        return LLMStreamResponse(
            content=accumulated_content + delta_content,
            delta=delta_content,
            model=chunk.model,
            provider=LLMProviderType.OPENAI,
            is_finished=is_finished,
            finish_reason=choice.finish_reason if choice else None,
            usage=usage,
            tool_calls=delta_tool_calls,
            metadata={
                "created": chunk.created,
                "id": chunk.id
            }
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the configured OpenAI model."""
        return {
            "provider": "openai",
            "model": self.model,
            "context_limit": self.MODEL_LIMITS.get(self.model, 4096),
            "pricing": self.MODEL_PRICING.get(self.model, {}),
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_vision": self.model.startswith("gpt-4-vision") or self.model.startswith("gpt-4o"),
            "supports_json_mode": self.model.startswith("gpt-4") or self.model.startswith("gpt-3.5-turbo")
        }
    
    def estimate_cost(self, usage: LLMUsage) -> Optional[float]:
        """
        Estimate the cost of an OpenAI request.
        
        Args:
            usage: Token usage information
            
        Returns:
            Estimated cost in USD
        """
        pricing = self.MODEL_PRICING.get(self.model)
        if not pricing:
            return None
        
        prompt_cost = (usage.prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (usage.completion_tokens / 1000) * pricing["completion"]
        
        return prompt_cost + completion_cost
    
    def format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Format messages for OpenAI API."""
        formatted = []
        for msg in messages:
            formatted_msg = {
                "role": msg.role.value,
                "content": msg.content
            }
            
            if msg.name:
                formatted_msg["name"] = msg.name
            
            if msg.tool_calls:
                formatted_msg["tool_calls"] = []
                for tool_call in msg.tool_calls:
                    formatted_tool_call = {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.name,
                            "arguments": json.dumps(tool_call.arguments)
                        }
                    }
                    formatted_msg["tool_calls"].append(formatted_tool_call)
            
            if msg.tool_call_id:
                formatted_msg["tool_call_id"] = msg.tool_call_id
            
            formatted.append(formatted_msg)
        
        return formatted
    
    def format_tools(self, tools: Optional[List[LLMTool]]) -> Optional[List[Dict[str, Any]]]:
        """Format tools for OpenAI API."""
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