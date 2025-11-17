
"""
Ollama LLM Provider Implementation.

This module provides the Ollama implementation of the LLM provider interface,
supporting both synchronous and asynchronous operations, streaming, and
local model execution.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import aiohttp
from aiohttp import ClientTimeout, ClientError

from .base import (
    LLMProvider, LLMConfig, LLMResponse, LLMStreamResponse, LLMUsage,
    LLMMessage, LLMTool, LLMToolCall, LLMProviderType, MessageRole,
    LLMProviderError, LLMConfigError, LLMConnectionError, LLMRateLimitError,
    LLMTokenLimitError, LLMContentFilterError, LLMTimeoutError
)
from app.core.logging import get_logger


class OllamaProvider(LLMProvider):
    """Ollama implementation of the LLM provider interface."""
    
    # Ollama model context limits (approximate)
    MODEL_LIMITS = {
        "llama2": 4096,
        "llama2:13b": 4096,
        "llama2:70b": 4096,
        "llama3": 8192,
        "llama3:8b": 8192,
        "llama3:70b": 8192,
        "mistral": 8192,
        "mistral:7b": 8192,
        "mixtral": 32768,
        "mixtral:8x7b": 32768,
        "mixtral:8x22b": 65536,
        "codellama": 16384,
        "codellama:7b": 16384,
        "codellama:13b": 16384,
        "codellama:34b": 16384,
        "qwen": 8192,
        "qwen:7b": 8192,
        "qwen:14b": 8192,
        "gemma": 8192,
        "gemma:2b": 8192,
        "gemma:7b": 8192,
    }
    
    def __init__(self, config: LLMConfig):
        """
        Initialize the Ollama provider.
        
        Args:
            config: Ollama configuration
        """
        super().__init__(config)
        self.client: Optional[aiohttp.ClientSession] = None
        self.logger = get_logger(f"{__name__}.OllamaProvider")
        
        # Set default API base URL if not provided
        if not self.config.api_base:
            self.config.api_base = "http://localhost:11434"
        
        # Validate model
        if config.model not in self.MODEL_LIMITS:
            self.logger.warning(f"Unknown model: {config.model}, using default context limit")
    
    async def initialize(self) -> None:
        """Initialize the Ollama client."""
        try:
            # Create HTTP client session
            timeout = ClientTimeout(total=self.config.timeout)
            self.client = aiohttp.ClientSession(
                timeout=timeout,
                base_url=self.config.api_base
            )
            
            # Validate configuration
            await self.validate_config()
            
            self.logger.info(f"Ollama provider initialized with model: {self.model}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Ollama provider: {e}")
            raise LLMConfigError(f"Ollama initialization failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup Ollama client resources."""
        if self.client:
            await self.client.close()
            self.client = None
            self.logger.info("Ollama provider cleaned up")
    
    async def validate_config(self) -> bool:
        """
        Validate the Ollama configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            # Test connection by checking if model is available
            async with self.client.get("/api/tags") as response:
                if response.status != 200:
                    raise LLMConfigError(f"Ollama API not accessible: {response.status}")
                
                data = await response.json()
                available_models = [model["name"] for model in data.get("models", [])]
                
                # Check if our model is available (or a compatible version)
                model_available = any(
                    self.model in available_model or 
                    available_model.startswith(self.model + ":")
                    for available_model in available_models
                )
                
                if not model_available:
                    self.logger.warning(f"Model {self.model} not found in available models: {available_models}")
            
            return True
        except Exception as e:
            raise LLMConfigError(f"Ollama configuration validation failed: {e}")
    
    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from Ollama.
        
        Args:
            messages: List of conversation messages
            tools: Available tools for function calling (limited support in Ollama)
            tool_choice: Tool choice strategy (limited support in Ollama)
            **kwargs: Additional Ollama-specific parameters
            
        Returns:
            Ollama response
        """
        if not self.client:
            await self.initialize()
        
        try:
            # Prepare request parameters
            request_params = self._prepare_request_params(
                messages, tools, tool_choice, **kwargs
            )
            
            # Make API call
            async with self.client.post("/api/generate", json=request_params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMProviderError(f"Ollama API error: {response.status} - {error_text}")
                
                data = await response.json()
                
                # Convert to our format
                return self._convert_response(data)
                
        except ClientError as e:
            raise LLMConnectionError(f"Ollama connection error: {e}")
        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"Ollama request timeout after {self.config.timeout}s")
        except Exception as e:
            raise LLMProviderError(f"Ollama generation failed: {e}")
    
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[LLMStreamResponse, None]:
        """
        Generate a streaming response from Ollama.
        
        Args:
            messages: List of conversation messages
            tools: Available tools for function calling (limited support in Ollama)
            tool_choice: Tool choice strategy (limited support in Ollama)
            **kwargs: Additional Ollama-specific parameters
            
        Yields:
            Ollama stream response chunks
        """
        if not self.client:
            await self.initialize()
        
        try:
            # Prepare request parameters for streaming
            request_params = self._prepare_request_params(
                messages, tools, tool_choice, stream=True, **kwargs
            )
            
            # Make streaming API call
            accumulated_content = ""
            
            async with self.client.post("/api/generate", json=request_params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMProviderError(f"Ollama API error: {response.status} - {error_text}")
                
                async for line in response.content:
                    if not line.strip():
                        continue
                    
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        stream_response = self._convert_stream_chunk(
                            chunk, accumulated_content
                        )
                        
                        if stream_response.delta:
                            accumulated_content += stream_response.delta
                        
                        yield stream_response
                        
                        if stream_response.is_finished:
                            break
                            
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Failed to decode JSON chunk: {e}")
                        continue
                        
        except ClientError as e:
            raise LLMConnectionError(f"Ollama connection error: {e}")
        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"Ollama request timeout after {self.config.timeout}s")
        except Exception as e:
            raise LLMProviderError(f"Ollama streaming failed: {e}")
    
    def _prepare_request_params(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare request parameters for Ollama API."""
        params = {
            "model": self.model,
            "prompt": self._convert_messages_to_prompt(messages),
            "stream": kwargs.get("stream", self.config.stream),
            "options": {
                "temperature": self.config.temperature,
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens or 2048),
            }
        }
        
        # Add optional parameters
        if self.config.top_p:
            params["options"]["top_p"] = self.config.top_p
        
        if self.config.top_k:
            params["options"]["top_k"] = self.config.top_k
        
        if self.config.frequency_penalty is not None:
            # Ollama uses repeat_penalty instead of frequency_penalty
            params["options"]["repeat_penalty"] = 1.0 + self.config.frequency_penalty
        
        if self.config.presence_penalty is not None:
            # Ollama doesn't have direct presence_penalty, but we can approximate
            pass
        
        if self.config.stop:
            params["options"]["stop"] = self.config.stop if isinstance(self.config.stop, list) else [self.config.stop]
        
        if self.config.seed:
            params["options"]["seed"] = self.config.seed
        
        # Add tools if provided (limited support in Ollama)
        if tools:
            # Ollama has limited tool support, we'll include them in the prompt
            tools_prompt = self._format_tools_for_prompt(tools)
            params["prompt"] = tools_prompt + "\n\n" + params["prompt"]
        
        # Add provider-specific config
        params.update(self.config.provider_config)
        
        # Override with any explicit kwargs
        params.update(kwargs)
        
        return params
    
    def _convert_messages_to_prompt(self, messages: List[LLMMessage]) -> str:
        """Convert messages to a single prompt string for Ollama."""
        prompt_parts = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == MessageRole.USER:
                prompt_parts.append(f"Human: {msg.content}")
            elif msg.role == MessageRole.ASSISTANT:
                prompt_parts.append(f"Assistant: {msg.content}")
            elif msg.role == MessageRole.TOOL:
                # Include tool results in the prompt
                prompt_parts.append(f"Tool Result: {msg.content}")
        
        # Add final assistant prompt
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    def _format_tools_for_prompt(self, tools: List[LLMTool]) -> str:
        """Format tools for inclusion in the prompt."""
        tools_desc = "You have access to the following tools:\n"
        
        for tool in tools:
            tools_desc += f"- {tool.name}: {tool.description}\n"
            tools_desc += f"  Parameters: {json.dumps(tool.parameters, indent=2)}\n"
        
        tools_desc += "To use a tool, respond with a JSON object containing the tool name and parameters."
        
        return tools_desc
    
    def _convert_response(self, response: Dict[str, Any]) -> LLMResponse:
        """Convert Ollama response to our format."""
        content = response.get("response", "")
        
        # Extract usage if available
        usage = None
        if "prompt_eval_count" in response and "eval_count" in response:
            usage = LLMUsage(
                prompt_tokens=response.get("prompt_eval_count", 0),
                completion_tokens=response.get("eval_count", 0),
                total_tokens=response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
            )
            
            # Ollama is free (local), so no cost calculation
        
        # Determine finish reason
        finish_reason = response.get("done_reason", "stop")
        
        return LLMResponse(
            content=content,
            model=response.get("model", self.model),
            provider=LLMProviderType.OLLAMA,
            usage=usage,
            finish_reason=finish_reason,
            tool_calls=None,  # Ollama has limited tool support
            metadata={
                "created_at": response.get("created_at"),
                "done": response.get("done"),
                "total_duration": response.get("total_duration"),
                "load_duration": response.get("load_duration"),
                "prompt_eval_count": response.get("prompt_eval_count"),
                "prompt_eval_duration": response.get("prompt_eval_duration"),
                "eval_count": response.get("eval_count"),
                "eval_duration": response.get("eval_duration")
            }
        )
    
    def _convert_stream_chunk(
        self,
        chunk: Dict[str, Any],
        accumulated_content: str
    ) -> LLMStreamResponse:
        """Convert Ollama stream chunk to our format."""
        delta_content = chunk.get("response", "")
        is_finished = chunk.get("done", False)
        finish_reason = chunk.get("done_reason", "stop") if is_finished else None
        
        # Extract usage if available
        usage = None
        if "prompt_eval_count" in chunk and "eval_count" in chunk:
            usage = LLMUsage(
                prompt_tokens=chunk.get("prompt_eval_count", 0),
                completion_tokens=chunk.get("eval_count", 0),
                total_tokens=chunk.get("prompt_eval_count", 0) + chunk.get("eval_count", 0)
            )
        
        return LLMStreamResponse(
            content=accumulated_content + delta_content,
            delta=delta_content,
            model=chunk.get("model", self.model),
            provider=LLMProviderType.OLLAMA,
            is_finished=is_finished,
            finish_reason=finish_reason,
            usage=usage,
            tool_calls=None,  # Ollama has limited tool support
            metadata={
                "created_at": chunk.get("created_at"),
                "done": chunk.get("done")
            }
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the configured Ollama model."""
        return {
            "provider": "ollama",
            "model": self.model,
            "context_limit": self.MODEL_LIMITS.get(self.model, 4096),
            "pricing": {},  # Ollama is free (local)
            "supports_streaming": True,
            "supports_function_calling": False,  # Limited support
            "supports_vision": False,
            "supports_json_mode": False
        }
    
    def estimate_cost(self, usage: LLMUsage) -> Optional[float]:
        """
        Estimate the cost of an Ollama request.
        
        Args:
            usage: Token usage information
            
        Returns:
            Estimated cost in USD (always 0 for local Ollama)
        """
        return 0.0  # Ollama is free when running locally
    
    def format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Format messages for Ollama API."""
        # Ollama uses a single prompt string, so we convert in _convert_messages_to_prompt
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]
    
    def format_tools(self, tools: Optional[List[LLMTool]]) -> Optional[List[Dict[str, Any]]]:
        """Format tools for Ollama API."""
        # Ollama has limited tool support, so we include them in the prompt instead
        return None