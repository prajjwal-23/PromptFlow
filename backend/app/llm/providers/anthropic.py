
"""
Anthropic LLM Provider Implementation.

This module provides the Anthropic implementation of the LLM provider interface,
supporting both synchronous and asynchronous operations, streaming, and
function calling capabilities.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import aiohttp
from anthropic import AsyncAnthropic, APIError, RateLimitError, APIConnectionError

from .base import (
    LLMProvider, LLMConfig, LLMResponse, LLMStreamResponse, LLMUsage,
    LLMMessage, LLMTool, LLMToolCall, LLMProviderType, MessageRole,
    LLMProviderError, LLMConfigError, LLMConnectionError, LLMRateLimitError,
    LLMTokenLimitError, LLMContentFilterError, LLMTimeoutError
)
from app.core.logging import get_logger


class AnthropicProvider(LLMProvider):
    """Anthropic implementation of the LLM provider interface."""
    
    # Anthropic model pricing (per 1K tokens as of 2024)
    MODEL_PRICING = {
        "claude-3-haiku-20240307": {"prompt": 0.00025, "completion": 0.00125},
        "claude-3-sonnet-20240229": {"prompt": 0.003, "completion": 0.015},
        "claude-3-opus-20240229": {"prompt": 0.015, "completion": 0.075},
        "claude-3-5-sonnet-20241022": {"prompt": 0.003, "completion": 0.015},
        "claude-3-5-haiku-20241022": {"prompt": 0.00025, "completion": 0.00125},
    }
    
    # Anthropic model context limits
    MODEL_LIMITS = {
        "claude-3-haiku-20240307": 200000,
        "claude-3-sonnet-20240229": 200000,
        "claude-3-opus-20240229": 200000,
        "claude-3-5-sonnet-20241022": 200000,
        "claude-3-5-haiku-20241022": 200000,
    }
    
    def __init__(self, config: LLMConfig):
        """
        Initialize the Anthropic provider.
        
        Args:
            config: Anthropic configuration
        """
        super().__init__(config)
        self.client: Optional[AsyncAnthropic] = None
        self.logger = get_logger(f"{__name__}.AnthropicProvider")
        
        # Validate model
        if config.model not in self.MODEL_LIMITS:
            self.logger.warning(f"Unknown model: {config.model}")
    
    async def initialize(self) -> None:
        """Initialize the Anthropic client."""
        try:
            # Create Anthropic client
            client_kwargs = {
                "api_key": self.config.api_key,
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries
            }
            
            if self.config.api_base:
                client_kwargs["base_url"] = self.config.api_base
            
            self.client = AsyncAnthropic(**client_kwargs)
            
            # Validate configuration
            await self.validate_config()
            
            self.logger.info(f"Anthropic provider initialized with model: {self.model}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Anthropic provider: {e}")
            raise LLMConfigError(f"Anthropic initialization failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup Anthropic client resources."""
        if self.client:
            await self.client.close()
            self.client = None
            self.logger.info("Anthropic provider cleaned up")
    
    async def validate_config(self) -> bool:
        """
        Validate the Anthropic configuration.
        
        Returns:
            True if configuration is valid
        """
        if not self.config.api_key:
            raise LLMConfigError("Anthropic API key is required")
        
        # Test connection with a minimal request
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception as e:
            raise LLMConfigError(f"Anthropic configuration validation failed: {e}")
    
    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from Anthropic.
        
        Args:
            messages: List of conversation messages
            tools: Available tools for function calling
            tool_choice: Tool choice strategy
            **kwargs: Additional Anthropic-specific parameters
            
        Returns:
            Anthropic response
        """
        if not self.client:
            await self.initialize()
        
        try:
            # Prepare request parameters
            request_params = self._prepare_request_params(
                messages, tools, tool_choice, **kwargs
            )
            
            # Make API call
            response = await self.client.messages.create(**request_params)
            
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
                raise LLMProviderError(f"Anthropic API error: {e}")
        except APIConnectionError as e:
            raise LLMConnectionError(f"Anthropic connection error: {e}")
        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"Anthropic request timeout after {self.config.timeout}s")
        except Exception as e:
            raise LLMProviderError(f"Anthropic generation failed: {e}")
    
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[LLMStreamResponse, None]:
        """
        Generate a streaming response from Anthropic.
        
        Args:
            messages: List of conversation messages
            tools: Available tools for function calling
            tool_choice: Tool choice strategy
            **kwargs: Additional Anthropic-specific parameters
            
        Yields:
            Anthropic stream response chunks
        """
        if not self.client:
            await self.initialize()
        
        try:
            # Prepare request parameters for streaming
            request_params = self._prepare_request_params(
                messages, tools, tool_choice, stream=True, **kwargs
            )
            
            # Make streaming API call
            with await self.client.messages.stream(**request_params) as stream:
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
                raise LLMProviderError(f"Anthropic API error: {e}")
        except APIConnectionError as e:
            raise LLMConnectionError(f"Anthropic connection error: {e}")
        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"Anthropic request timeout after {self.config.timeout}s")
        except Exception as e:
            raise LLMProviderError(f"Anthropic streaming failed: {e}")
    
    def _prepare_request_params(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare request parameters for Anthropic API."""
        params = {
            "model": self.model,
            "messages": self.format_messages(messages),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 4096),
            "temperature": self.config.temperature,
        }
        
        # Add optional parameters
        if self.config.top_p:
            # Anthropic doesn't support top_p directly, but we can approximate
            # by adjusting temperature and other parameters
            pass
        
        if self.config.stop:
            params["stop_sequences"] = self.config.stop if isinstance(self.config.stop, list) else [self.config.stop]
        
        # Add tools if provided
        if tools:
            params["tools"] = self.format_tools(tools)
            
            if tool_choice:
                if isinstance(tool_choice, str):
                    if tool_choice == "auto":
                        params["tool_choice"] = {"type": "auto"}
                    elif tool_choice == "none":
                        # Don't include tools
                        params.pop("tools", None)
                    elif tool_choice == "any":
                        params["tool_choice"] = {"type": "any"}
                    else:
                        # Specific tool name
                        params["tool_choice"] = {"type": "tool", "name": tool_choice}
                elif isinstance(tool_choice, dict):
                    params["tool_choice"] = tool_choice
        
        # Add provider-specific config
        params.update(self.config.provider_config)
        
        # Override with any explicit kwargs
        params.update(kwargs)
        
        return params
    
    def _convert_response(self, response) -> LLMResponse:
        """Convert Anthropic response to our format."""
        content = ""
        tool_calls = None
        
        # Extract content and tool calls
        for content_block in response.content:
            if content_block.type == "text":
                content += content_block.text
            elif content_block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(LLMToolCall(
                    id=content_block.id,
                    name=content_block.name,
                    arguments=content_block.input
                ))
        
        # Extract usage
        usage = None
        if response.usage:
            usage = LLMUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens
            )
            
            # Calculate cost
            cost = self.estimate_cost(usage)
            if cost:
                usage.prompt_cost = cost * 0.7  # Approximate split
                usage.completion_cost = cost * 0.3
                usage.total_cost = cost
        
        # Determine finish reason
        finish_reason = response.stop_reason
        
        return LLMResponse(
            content=content,
            model=response.model,
            provider=LLMProviderType.ANTHROPIC,
            usage=usage,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
            metadata={
                "id": response.id,
                "type": response.type,
                "role": response.role,
                "stop_sequence": response.stop_sequence
            }
        )
    
    def _convert_stream_chunk(
        self,
        chunk,
        accumulated_content: str,
        accumulated_tool_calls: List[LLMToolCall]
    ) -> LLMStreamResponse:
        """Convert Anthropic stream chunk to our format."""
        delta_content = ""
        delta_tool_calls = None
        is_finished = False
        finish_reason = None
        usage = None
        
        # Process chunk based on type
        if chunk.type == "content_block_delta":
            if chunk.delta.type == "text_delta":
                delta_content = chunk.delta.text
            elif chunk.delta.type == "input_json_delta":
                # Tool call delta
                if delta_tool_calls is None:
                    delta_tool_calls = []
                # This is a simplified handling - in practice, you'd need to accumulate
                # partial JSON deltas properly
                pass
        
        elif chunk.type == "content_block_stop":
            # Content block finished
            pass
        
        elif chunk.type == "message_stop":
            # Message finished
            is_finished = True
            finish_reason = chunk.stop_reason
        
        elif chunk.type == "message_delta":
            # Message metadata delta
            if chunk.delta.stop_reason:
                finish_reason = chunk.delta.stop_reason
        
        elif chunk.type == "message_start":
            # Message started - contains usage info
            if chunk.message.usage:
                usage = LLMUsage(
                    prompt_tokens=chunk.message.usage.input_tokens,
                    completion_tokens=chunk.message.usage.output_tokens,
                    total_tokens=chunk.message.usage.input_tokens + chunk.message.usage.output_tokens
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
            model=self.model,
            provider=LLMProviderType.ANTHROPIC,
            is_finished=is_finished,
            finish_reason=finish_reason,
            usage=usage,
            tool_calls=delta_tool_calls,
            metadata={
                "type": chunk.type,
                "index": getattr(chunk, 'index', None)
            }
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the configured Anthropic model."""
        return {
            "provider": "anthropic",
            "model": self.model,
            "context_limit": self.MODEL_LIMITS.get(self.model, 200000),
            "pricing": self.MODEL_PRICING.get(self.model, {}),
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_vision": False,  # Anthropic doesn't support vision in Claude 3
            "supports_json_mode": False  # Anthropic doesn't have explicit JSON mode
        }
    
    def estimate_cost(self, usage: LLMUsage) -> Optional[float]:
        """
        Estimate the cost of an Anthropic request.
        
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
        """Format messages for Anthropic API."""
        formatted = []
        system_message = None
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_message = msg.content
                continue
            
            formatted_msg = {
                "role": msg.role.value if msg.role != MessageRole.ASSISTANT else "assistant",
                "content": []
            }
            
            # Add text content
            if msg.content:
                formatted_msg["content"].append({
                    "type": "text",
                    "text": msg.content
                })
            
            # Add tool calls for assistant messages
            if msg.tool_calls and msg.role == MessageRole.ASSISTANT:
                for tool_call in msg.tool_calls:
                    formatted_msg["content"].append({
                        "type": "tool_use",
                        "id": tool_call.id,
                        "name": tool_call.name,
                        "input": tool_call.arguments
                    })
            
            # Add tool result for tool messages
            if msg.role == MessageRole.TOOL and msg.tool_call_id:
                formatted_msg["content"].append({
                    "type": "tool_result",
                    "tool_use_id": msg.tool_call_id,
                    "content": msg.content
                })
            
            formatted.append(formatted_msg)
        
        # Add system message if present
        if system_message:
            # Anthropic expects system message as a separate parameter
            # We'll handle this in the request preparation
            pass
        
        return formatted
    
    def format_tools(self, tools: Optional[List[LLMTool]]) -> Optional[List[Dict[str, Any]]]:
        """Format tools for Anthropic API."""
        if not tools:
            return None
        
        formatted = []
        for tool in tools:
            formatted_tool = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters
            }
            
            formatted.append(formatted_tool)
        
        return formatted