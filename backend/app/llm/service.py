"""
LLM Service.

This module provides a high-level service for working with LLM providers,
including provider management, request handling, and response processing.
"""

import asyncio
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from .providers.base import (
    LLMProvider, LLMConfig, LLMResponse, LLMStreamResponse, LLMUsage,
    LLMMessage, LLMTool, LLMToolCall, LLMProviderType, MessageRole,
    create_message, create_tool
)
from .factory import llm_factory, create_llm_provider, create_llm_config
from app.core.logging import get_logger


class LLMService:
    """High-level service for LLM operations."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.logger = get_logger(f"{__name__}.LLMService")
        self._default_providers: Dict[LLMProviderType, LLMProvider] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the LLM service."""
        if self._initialized:
            return
        
        try:
            # Initialize default providers if configured
            await self._initialize_default_providers()
            self._initialized = True
            self.logger.info("LLM service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM service: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Cleanup the LLM service."""
        try:
            # Cleanup all cached providers
            await llm_factory.cleanup_all_providers()
            
            # Cleanup default providers
            for provider in self._default_providers.values():
                await provider.cleanup()
            
            self._default_providers.clear()
            self._initialized = False
            self.logger.info("LLM service cleaned up")
        except Exception as e:
            self.logger.error(f"Error during LLM service cleanup: {e}")
    
    async def _initialize_default_providers(self) -> None:
        """Initialize default providers based on environment configuration."""
        # This could be enhanced to read from environment variables or config
        pass
    
    async def get_provider(
        self,
        provider_type: LLMProviderType,
        model: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """
        Get or create a provider instance.
        
        Args:
            provider_type: Provider type
            model: Model name
            api_key: API key (if required)
            **kwargs: Additional configuration parameters
            
        Returns:
            Provider instance
        """
        cache_key = f"{provider_type.value}:{model}"
        
        # Check if we have a default provider
        if cache_key in self._default_providers:
            return self._default_providers[cache_key]
        
        # Create new provider
        config = create_llm_config(provider_type, model, api_key, **kwargs)
        provider = await llm_factory.create_and_initialize_provider(config, cache_key)
        
        # Store as default if no API key (shared provider)
        if not api_key:
            self._default_providers[cache_key] = provider
        
        return provider
    
    async def generate_response(
        self,
        messages: List[Union[LLMMessage, Dict[str, Any], str]],
        provider_type: LLMProviderType = LLMProviderType.OPENAI,
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        tools: Optional[List[Union[LLMTool, Dict[str, Any]]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from an LLM.
        
        Args:
            messages: List of messages (can be LLMMessage, dict, or string)
            provider_type: Provider type
            model: Model name
            api_key: API key (if required)
            tools: Available tools for function calling
            tool_choice: Tool choice strategy
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLM response
        """
        # Get provider
        provider = await self.get_provider(provider_type, model, api_key, **kwargs)
        
        # Normalize messages
        normalized_messages = self._normalize_messages(messages)
        
        # Normalize tools
        normalized_tools = self._normalize_tools(tools)
        
        # Generate response
        return await provider.generate(
            normalized_messages,
            normalized_tools,
            tool_choice,
            **kwargs
        )
    
    async def generate_stream(
        self,
        messages: List[Union[LLMMessage, Dict[str, Any], str]],
        provider_type: LLMProviderType = LLMProviderType.OPENAI,
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        tools: Optional[List[Union[LLMTool, Dict[str, Any]]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[LLMStreamResponse, None]:
        """
        Generate a streaming response from an LLM.
        
        Args:
            messages: List of messages (can be LLMMessage, dict, or string)
            provider_type: Provider type
            model: Model name
            api_key: API key (if required)
            tools: Available tools for function calling
            tool_choice: Tool choice strategy
            **kwargs: Additional provider-specific parameters
            
        Yields:
            LLM stream response chunks
        """
        # Get provider
        provider = await self.get_provider(provider_type, model, api_key, **kwargs)
        
        # Normalize messages
        normalized_messages = self._normalize_messages(messages)
        
        # Normalize tools
        normalized_tools = self._normalize_tools(tools)
        
        # Generate streaming response
        async for chunk in provider.generate_stream(
            normalized_messages,
            normalized_tools,
            tool_choice,
            **kwargs
        ):
            yield chunk
    
    async def chat(
        self,
        message: str,
        conversation: Optional[List[Union[LLMMessage, Dict[str, Any], str]]] = None,
        provider_type: LLMProviderType = LLMProviderType.OPENAI,
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Simple chat interface.
        
        Args:
            message: User message
            conversation: Previous conversation history
            provider_type: Provider type
            model: Model name
            api_key: API key (if required)
            system_prompt: System prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLM response
        """
        messages = []
        
        # Add system prompt
        if system_prompt:
            messages.append(create_message("system", system_prompt))
        
        # Add conversation history
        if conversation:
            messages.extend(self._normalize_messages(conversation))
        
        # Add current message
        messages.append(create_message("user", message))
        
        return await self.generate_response(
            messages,
            provider_type,
            model,
            api_key,
            **kwargs
        )
    
    async def chat_stream(
        self,
        message: str,
        conversation: Optional[List[Union[LLMMessage, Dict[str, Any], str]]] = None,
        provider_type: LLMProviderType = LLMProviderType.OPENAI,
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[LLMStreamResponse, None]:
        """
        Simple streaming chat interface.
        
        Args:
            message: User message
            conversation: Previous conversation history
            provider_type: Provider type
            model: Model name
            api_key: API key (if required)
            system_prompt: System prompt
            **kwargs: Additional provider-specific parameters
            
        Yields:
            LLM stream response chunks
        """
        messages = []
        
        # Add system prompt
        if system_prompt:
            messages.append(create_message("system", system_prompt))
        
        # Add conversation history
        if conversation:
            messages.extend(self._normalize_messages(conversation))
        
        # Add current message
        messages.append(create_message("user", message))
        
        async for chunk in self.generate_stream(
            messages,
            provider_type,
            model,
            api_key,
            **kwargs
        ):
            yield chunk
    
    def _normalize_messages(
        self,
        messages: List[Union[LLMMessage, Dict[str, Any], str]]
    ) -> List[LLMMessage]:
        """Normalize messages to LLMMessage format."""
        normalized = []
        
        for msg in messages:
            if isinstance(msg, LLMMessage):
                normalized.append(msg)
            elif isinstance(msg, dict):
                # Convert dict to LLMMessage
                role = msg.get("role", "user")
                content = msg.get("content", "")
                name = msg.get("name")
                tool_calls = msg.get("tool_calls")
                tool_call_id = msg.get("tool_call_id")
                
                normalized.append(create_message(
                    role, content, name=name, tool_calls=tool_calls, tool_call_id=tool_call_id
                ))
            elif isinstance(msg, str):
                # Convert string to user message
                normalized.append(create_message("user", msg))
            else:
                raise ValueError(f"Unsupported message type: {type(msg)}")
        
        return normalized
    
    def _normalize_tools(
        self,
        tools: Optional[List[Union[LLMTool, Dict[str, Any]]]]
    ) -> Optional[List[LLMTool]]:
        """Normalize tools to LLMTool format."""
        if not tools:
            return None
        
        normalized = []
        
        for tool in tools:
            if isinstance(tool, LLMTool):
                normalized.append(tool)
            elif isinstance(tool, dict):
                # Convert dict to LLMTool
                name = tool.get("name")
                description = tool.get("description", "")
                parameters = tool.get("parameters", {})
                strict = tool.get("strict")
                
                if not name:
                    raise ValueError("Tool name is required")
                
                normalized.append(create_tool(name, description, parameters, strict))
            else:
                raise ValueError(f"Unsupported tool type: {type(tool)}")
        
        return normalized
    
    async def get_provider_info(
        self,
        provider_type: LLMProviderType,
        model: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get information about a provider.
        
        Args:
            provider_type: Provider type
            model: Model name
            api_key: API key (if required)
            **kwargs: Additional configuration parameters
            
        Returns:
            Provider information
        """
        provider = await self.get_provider(provider_type, model, api_key, **kwargs)
        return provider.get_model_info()
    
    async def health_check(
        self,
        provider_type: LLMProviderType,
        model: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform health check on a provider.
        
        Args:
            provider_type: Provider type
            model: Model name
            api_key: API key (if required)
            **kwargs: Additional configuration parameters
            
        Returns:
            Health check result
        """
        provider = await self.get_provider(provider_type, model, api_key, **kwargs)
        return await provider.health_check()
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.
        
        Returns:
            Service statistics
        """
        cache_stats = llm_factory.get_cache_stats()
        health_results = await llm_factory.health_check_all_providers()
        
        return {
            "initialized": self._initialized,
            "default_providers": len(self._default_providers),
            "cache_stats": cache_stats,
            "health_checks": health_results,
            "available_providers": llm_factory.get_available_providers()
        }


# Global service instance
llm_service = LLMService()


# Convenience functions
async def chat_with_llm(
    message: str,
    provider_type: LLMProviderType = LLMProviderType.OPENAI,
    model: str = "gpt-3.5-turbo",
    api_key: Optional[str] = None,
    **kwargs
) -> str:
    """
    Convenience function for simple chat.
    
    Args:
        message: User message
        provider_type: Provider type
        model: Model name
        api_key: API key (if required)
        **kwargs: Additional parameters
        
    Returns:
        Response text
    """
    response = await llm_service.chat(message, provider_type=provider_type, model=model, api_key=api_key, **kwargs)
    return response.content


async def stream_chat_with_llm(
    message: str,
    provider_type: LLMProviderType = LLMProviderType.OPENAI,
    model: str = "gpt-3.5-turbo",
    api_key: Optional[str] = None,
    **kwargs
) -> AsyncGenerator[str, None]:
    """
    Convenience function for streaming chat.
    
    Args:
        message: User message
        provider_type: Provider type
        model: Model name
        api_key: API key (if required)
        **kwargs: Additional parameters
        
    Yields:
        Response text chunks
    """
    async for chunk in llm_service.chat_stream(message, provider_type=provider_type, model=model, api_key=api_key, **kwargs):
        if chunk.delta:
            yield chunk.delta