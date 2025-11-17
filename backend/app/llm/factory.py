"""
LLM Provider Factory.

This module provides a factory for creating and managing LLM providers
with support for different provider types and configurations.
"""

import asyncio
from typing import Any, Dict, List, Optional, Type

from .providers.base import LLMProvider, LLMConfig, LLMProviderType
from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider
from .providers.ollama import OllamaProvider
from app.core.logging import get_logger


class LLMProviderFactory:
    """Factory for creating and managing LLM providers."""
    
    # Registry of available providers
    _providers: Dict[LLMProviderType, Type[LLMProvider]] = {
        LLMProviderType.OPENAI: OpenAIProvider,
        LLMProviderType.ANTHROPIC: AnthropicProvider,
        LLMProviderType.OLLAMA: OllamaProvider,
    }
    
    # Cache of provider instances
    _provider_cache: Dict[str, LLMProvider] = {}
    
    def __init__(self):
        """Initialize the factory."""
        self.logger = get_logger(f"{__name__}.LLMProviderFactory")
    
    @classmethod
    def register_provider(cls, provider_type: LLMProviderType, provider_class: Type[LLMProvider]) -> None:
        """
        Register a new provider type.
        
        Args:
            provider_type: Provider type enum
            provider_class: Provider class
        """
        cls._providers[provider_type] = provider_class
    
    @classmethod
    def get_available_providers(cls) -> List[LLMProviderType]:
        """
        Get list of available provider types.
        
        Returns:
            List of available provider types
        """
        return list(cls._providers.keys())
    
    @classmethod
    def get_provider_info(cls, provider_type: LLMProviderType) -> Dict[str, Any]:
        """
        Get information about a provider type.
        
        Args:
            provider_type: Provider type
            
        Returns:
            Provider information
        """
        provider_class = cls._providers.get(provider_type)
        if not provider_class:
            return {"error": f"Provider {provider_type.value} not available"}
        
        return {
            "type": provider_type.value,
            "class": provider_class.__name__,
            "module": provider_class.__module__,
            "description": provider_class.__doc__ or "No description available"
        }
    
    def create_provider(
        self,
        config: LLMConfig,
        cache_key: Optional[str] = None,
        initialize: bool = True
    ) -> LLMProvider:
        """
        Create a provider instance.
        
        Args:
            config: Provider configuration
            cache_key: Optional cache key for reusing instances
            initialize: Whether to initialize the provider
            
        Returns:
            Provider instance
        """
        # Check cache first
        if cache_key and cache_key in self._provider_cache:
            cached_provider = self._provider_cache[cache_key]
            self.logger.debug(f"Using cached provider: {cache_key}")
            return cached_provider
        
        # Get provider class
        provider_class = self._providers.get(config.provider)
        if not provider_class:
            raise ValueError(f"Unsupported provider type: {config.provider}")
        
        # Create instance
        try:
            provider = provider_class(config)
            
            # Initialize if requested
            if initialize:
                # Note: This should be called in async context
                self.logger.info(f"Created provider: {config.provider.value} with model: {config.model}")
            else:
                self.logger.info(f"Created provider (uninitialized): {config.provider.value} with model: {config.model}")
            
            # Cache if key provided
            if cache_key:
                self._provider_cache[cache_key] = provider
                self.logger.debug(f"Cached provider: {cache_key}")
            
            return provider
            
        except Exception as e:
            self.logger.error(f"Failed to create provider {config.provider.value}: {e}")
            raise
    
    async def create_and_initialize_provider(
        self,
        config: LLMConfig,
        cache_key: Optional[str] = None
    ) -> LLMProvider:
        """
        Create and initialize a provider instance.
        
        Args:
            config: Provider configuration
            cache_key: Optional cache key for reusing instances
            
        Returns:
            Initialized provider instance
        """
        provider = self.create_provider(config, cache_key, initialize=False)
        
        try:
            await provider.initialize()
            self.logger.info(f"Initialized provider: {config.provider.value}")
            return provider
        except Exception as e:
            self.logger.error(f"Failed to initialize provider {config.provider.value}: {e}")
            # Remove from cache if initialization failed
            if cache_key and cache_key in self._provider_cache:
                del self._provider_cache[cache_key]
            raise
    
    def get_cached_provider(self, cache_key: str) -> Optional[LLMProvider]:
        """
        Get a cached provider instance.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached provider instance or None
        """
        return self._provider_cache.get(cache_key)
    
    def cache_provider(self, cache_key: str, provider: LLMProvider) -> None:
        """
        Cache a provider instance.
        
        Args:
            cache_key: Cache key
            provider: Provider instance
        """
        self._provider_cache[cache_key] = provider
        self.logger.debug(f"Cached provider: {cache_key}")
    
    def remove_cached_provider(self, cache_key: str) -> bool:
        """
        Remove a cached provider instance.
        
        Args:
            cache_key: Cache key
            
        Returns:
            True if provider was removed
        """
        if cache_key in self._provider_cache:
            del self._provider_cache[cache_key]
            self.logger.debug(f"Removed cached provider: {cache_key}")
            return True
        return False
    
    async def cleanup_provider(self, cache_key: str) -> bool:
        """
        Cleanup and remove a cached provider.
        
        Args:
            cache_key: Cache key
            
        Returns:
            True if provider was cleaned up
        """
        provider = self._provider_cache.get(cache_key)
        if provider:
            try:
                await provider.cleanup()
                del self._provider_cache[cache_key]
                self.logger.info(f"Cleaned up provider: {cache_key}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to cleanup provider {cache_key}: {e}")
                return False
        return False
    
    async def cleanup_all_providers(self) -> int:
        """
        Cleanup all cached providers.
        
        Returns:
            Number of providers cleaned up
        """
        cleanup_count = 0
        cache_keys = list(self._provider_cache.keys())
        
        for cache_key in cache_keys:
            if await self.cleanup_provider(cache_key):
                cleanup_count += 1
        
        self.logger.info(f"Cleaned up {cleanup_count} providers")
        return cleanup_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        stats = {
            "total_cached": len(self._provider_cache),
            "providers_by_type": {},
            "cache_keys": list(self._provider_cache.keys())
        }
        
        for cache_key, provider in self._provider_cache.items():
            provider_type = provider.provider_type.value
            stats["providers_by_type"][provider_type] = stats["providers_by_type"].get(provider_type, 0) + 1
        
        return stats
    
    async def health_check_all_providers(self) -> Dict[str, Any]:
        """
        Perform health check on all cached providers.
        
        Returns:
            Health check results
        """
        results = {}
        
        for cache_key, provider in self._provider_cache.items():
            try:
                health = await provider.health_check()
                results[cache_key] = health
            except Exception as e:
                results[cache_key] = {
                    "status": "error",
                    "error": str(e),
                    "provider": provider.provider_type.value,
                    "model": provider.model
                }
        
        return results


# Global factory instance
llm_factory = LLMProviderFactory()


# Convenience functions
async def create_llm_provider(
    provider_type: LLMProviderType,
    model: str,
    api_key: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Convenience function to create and initialize an LLM provider.
    
    Args:
        provider_type: Provider type
        model: Model name
        api_key: API key (if required)
        **kwargs: Additional configuration parameters
        
    Returns:
        Initialized provider instance
    """
    config = LLMConfig(
        provider=provider_type,
        model=model,
        api_key=api_key,
        **kwargs
    )
    
    return await llm_factory.create_and_initialize_provider(config)


def create_llm_config(
    provider_type: LLMProviderType,
    model: str,
    api_key: Optional[str] = None,
    **kwargs
) -> LLMConfig:
    """
    Convenience function to create an LLM configuration.
    
    Args:
        provider_type: Provider type
        model: Model name
        api_key: API key (if required)
        **kwargs: Additional configuration parameters
        
    Returns:
        LLM configuration
    """
    return LLMConfig(
        provider=provider_type,
        model=model,
        api_key=api_key,
        **kwargs
    )


def get_provider_models(provider_type: LLMProviderType) -> List[str]:
    """
    Get available models for a provider.
    
    Args:
        provider_type: Provider type
        
    Returns:
        List of available model names
    """
    if provider_type == LLMProviderType.OPENAI:
        return [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini"
        ]
    elif provider_type == LLMProviderType.ANTHROPIC:
        return [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229"
        ]
    elif provider_type == LLMProviderType.OLLAMA:
        return [
            "llama2",
            "llama3",
            "mistral",
            "mixtral",
            "codellama",
            "qwen",
            "gemma"
        ]
    else:
        return []