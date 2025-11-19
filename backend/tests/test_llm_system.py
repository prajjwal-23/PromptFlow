"""
Unit tests for LLM system components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional
import json

from app.llm.providers.base import LLMProvider, LLMRequest, LLMResponse, LLMConfig
from app.llm.providers.openai import OpenAIProvider
from app.llm.providers.anthropic import AnthropicProvider
from app.llm.providers.ollama import OllamaProvider
from app.llm.factory import LLMFactory
from app.llm.service import LLMService


class TestLLMProvider:
    """Test cases for LLM Provider base class."""
    
    def test_llm_request_creation(self):
        """Test LLM request creation."""
        request = LLMRequest(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100,
            temperature=0.7
        )
        
        assert request.model == "gpt-4"
        assert len(request.messages) == 1
        assert request.messages[0]["content"] == "Hello"
        assert request.max_tokens == 100
        assert request.temperature == 0.7
    
    def test_llm_response_creation(self):
        """Test LLM response creation."""
        response = LLMResponse(
            content="Hello there!",
            model="gpt-4",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            finish_reason="stop"
        )
        
        assert response.content == "Hello there!"
        assert response.model == "gpt-4"
        assert response.usage["total_tokens"] == 15
        assert response.finish_reason == "stop"
    
    def test_llm_config_creation(self):
        """Test LLM config creation."""
        config = LLMConfig(
            api_key="test_key",
            base_url="https://api.example.com",
            timeout=30,
            max_retries=3
        )
        
        assert config.api_key == "test_key"
        assert config.base_url == "https://api.example.com"
        assert config.timeout == 30
        assert config.max_retries == 3


class TestOpenAIProvider:
    """Test cases for OpenAI Provider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = LLMConfig(
            api_key="test_openai_key",
            base_url="https://api.openai.com/v1"
        )
        self.provider = OpenAIProvider(self.config)
    
    @pytest.mark.asyncio
    async def test_generate_text(self):
        """Test generating text with OpenAI."""
        request = LLMRequest(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100
        )
        
        # Mock OpenAI client
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Hello there!"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.usage = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            mock_response.model = "gpt-4"
            
            mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
            
            # Generate text
            response = await self.provider.generate_text(request)
            
            # Verify response
            assert response.content == "Hello there!"
            assert response.model == "gpt-4"
            assert response.usage["total_tokens"] == 15
            assert response.finish_reason == "stop"
    
    @pytest.mark.asyncio
    async def test_generate_stream(self):
        """Test streaming text generation with OpenAI."""
        request = LLMRequest(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100,
            stream=True
        )
        
        # Mock OpenAI streaming
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_chunk1 = Mock()
            mock_chunk1.choices = [Mock()]
            mock_chunk1.choices[0].delta.content = "Hello "
            mock_chunk1.choices[0].finish_reason = None
            
            mock_chunk2 = Mock()
            mock_chunk2.choices = [Mock()]
            mock_chunk2.choices[0].delta.content = "there!"
            mock_chunk2.choices[0].finish_reason = "stop"
            
            async def mock_stream():
                yield mock_chunk1
                yield mock_chunk2
            
            mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_stream())
            
            # Generate stream
            chunks = []
            async for chunk in self.provider.generate_stream(request):
                chunks.append(chunk)
            
            # Verify chunks
            assert len(chunks) == 2
            assert chunks[0].content == "Hello "
            assert chunks[1].content == "there!"
    
    def test_validate_config(self):
        """Test OpenAI config validation."""
        # Valid config
        valid_config = LLMConfig(api_key="test_key")
        assert self.provider.validate_config(valid_config) is True
        
        # Invalid config (missing API key)
        invalid_config = LLMConfig(api_key="")
        assert self.provider.validate_config(invalid_config) is False
    
    def test_get_supported_models(self):
        """Test getting supported models."""
        models = self.provider.get_supported_models()
        
        assert "gpt-4" in models
        assert "gpt-3.5-turbo" in models
        assert isinstance(models, list)


class TestAnthropicProvider:
    """Test cases for Anthropic Provider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = LLMConfig(
            api_key="test_anthropic_key",
            base_url="https://api.anthropic.com"
        )
        self.provider = AnthropicProvider(self.config)
    
    @pytest.mark.asyncio
    async def test_generate_text(self):
        """Test generating text with Anthropic."""
        request = LLMRequest(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100
        )
        
        # Mock Anthropic client
        with patch('anthropic.AsyncAnthropic') as mock_client:
            mock_response = Mock()
            mock_response.content = [Mock(text="Hello there!")]
            mock_response.usage = {"input_tokens": 10, "output_tokens": 5}
            mock_response.stop_reason = "end_turn"
            mock_response.model = "claude-3-sonnet-20240229"
            
            mock_client.return_value.messages.create = AsyncMock(return_value=mock_response)
            
            # Generate text
            response = await self.provider.generate_text(request)
            
            # Verify response
            assert response.content == "Hello there!"
            assert response.model == "claude-3-sonnet-20240229"
            assert response.usage["input_tokens"] == 10
            assert response.usage["output_tokens"] == 5
            assert response.finish_reason == "end_turn"
    
    @pytest.mark.asyncio
    async def test_generate_stream(self):
        """Test streaming text generation with Anthropic."""
        request = LLMRequest(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100,
            stream=True
        )
        
        # Mock Anthropic streaming
        with patch('anthropic.AsyncAnthropic') as mock_client:
            mock_chunk1 = Mock()
            mock_chunk1.type = "content_block_delta"
            mock_chunk1.delta.text = "Hello "
            
            mock_chunk2 = Mock()
            mock_chunk2.type = "content_block_delta"
            mock_chunk2.delta.text = "there!"
            
            async def mock_stream():
                yield mock_chunk1
                yield mock_chunk2
            
            mock_client.return_value.messages.create = AsyncMock(return_value=mock_stream())
            
            # Generate stream
            chunks = []
            async for chunk in self.provider.generate_stream(request):
                chunks.append(chunk)
            
            # Verify chunks
            assert len(chunks) == 2
            assert chunks[0].content == "Hello "
            assert chunks[1].content == "there!"
    
    def test_validate_config(self):
        """Test Anthropic config validation."""
        # Valid config
        valid_config = LLMConfig(api_key="test_key")
        assert self.provider.validate_config(valid_config) is True
        
        # Invalid config (missing API key)
        invalid_config = LLMConfig(api_key="")
        assert self.provider.validate_config(invalid_config) is False
    
    def test_get_supported_models(self):
        """Test getting supported models."""
        models = self.provider.get_supported_models()
        
        assert "claude-3-sonnet-20240229" in models
        assert "claude-3-opus-20240229" in models
        assert isinstance(models, list)


class TestOllamaProvider:
    """Test cases for Ollama Provider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = LLMConfig(
            base_url="http://localhost:11434"
        )
        self.provider = OllamaProvider(self.config)
    
    @pytest.mark.asyncio
    async def test_generate_text(self):
        """Test generating text with Ollama."""
        request = LLMRequest(
            model="llama2",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100
        )
        
        # Mock Ollama client
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "response": "Hello there!",
                "model": "llama2",
                "done": True,
                "prompt_eval_count": 10,
                "eval_count": 5
            })
            
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Generate text
            response = await self.provider.generate_text(request)
            
            # Verify response
            assert response.content == "Hello there!"
            assert response.model == "llama2"
            assert response.usage["prompt_tokens"] == 10
            assert response.usage["completion_tokens"] == 5
    
    @pytest.mark.asyncio
    async def test_generate_stream(self):
        """Test streaming text generation with Ollama."""
        request = LLMRequest(
            model="llama2",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100,
            stream=True
        )
        
        # Mock Ollama streaming
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            
            async def mock_stream():
                yield b'{"response": "Hello "}'
                yield b'{"response": "there!", "done": true}'
            
            mock_response.content.__aiter__ = AsyncMock(return_value=mock_stream())
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Generate stream
            chunks = []
            async for chunk in self.provider.generate_stream(request):
                chunks.append(chunk)
            
            # Verify chunks
            assert len(chunks) == 2
            assert chunks[0].content == "Hello "
            assert chunks[1].content == "there!"
    
    def test_validate_config(self):
        """Test Ollama config validation."""
        # Valid config (no API key required)
        valid_config = LLMConfig(base_url="http://localhost:11434")
        assert self.provider.validate_config(valid_config) is True
        
        # Invalid config (missing base URL)
        invalid_config = LLMConfig(base_url="")
        assert self.provider.validate_config(invalid_config) is False
    
    def test_get_supported_models(self):
        """Test getting supported models."""
        models = self.provider.get_supported_models()
        
        assert "llama2" in models
        assert "codellama" in models
        assert isinstance(models, list)


class TestLLMFactory:
    """Test cases for LLM Factory."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = LLMFactory()
    
    def test_create_openai_provider(self):
        """Test creating OpenAI provider."""
        config = LLMConfig(
            api_key="test_key",
            provider="openai"
        )
        
        provider = self.factory.create_provider(config)
        
        assert isinstance(provider, OpenAIProvider)
        assert provider.config.api_key == "test_key"
    
    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider."""
        config = LLMConfig(
            api_key="test_key",
            provider="anthropic"
        )
        
        provider = self.factory.create_provider(config)
        
        assert isinstance(provider, AnthropicProvider)
        assert provider.config.api_key == "test_key"
    
    def test_create_ollama_provider(self):
        """Test creating Ollama provider."""
        config = LLMConfig(
            base_url="http://localhost:11434",
            provider="ollama"
        )
        
        provider = self.factory.create_provider(config)
        
        assert isinstance(provider, OllamaProvider)
        assert provider.config.base_url == "http://localhost:11434"
    
    def test_create_provider_with_invalid_type(self):
        """Test creating provider with invalid type."""
        config = LLMConfig(
            api_key="test_key",
            provider="invalid_provider"
        )
        
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            self.factory.create_provider(config)
    
    def test_get_available_providers(self):
        """Test getting available providers."""
        providers = self.factory.get_available_providers()
        
        assert "openai" in providers
        assert "anthropic" in providers
        assert "ollama" in providers
        assert isinstance(providers, list)


class TestLLMService:
    """Test cases for LLM Service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_factory = Mock(spec=LLMFactory)
        self.service = LLMService(self.mock_factory)
    
    @pytest.mark.asyncio
    async def test_generate_text(self):
        """Test generating text through service."""
        # Mock provider
        mock_provider = Mock(spec=LLMProvider)
        mock_response = LLMResponse(
            content="Hello there!",
            model="gpt-4",
            usage={"total_tokens": 15},
            finish_reason="stop"
        )
        mock_provider.generate_text = AsyncMock(return_value=mock_response)
        
        # Mock factory
        self.mock_factory.create_provider.return_value = mock_provider
        
        # Generate text
        response = await self.service.generate_text(
            provider_type="openai",
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            config=LLMConfig(api_key="test_key")
        )
        
        # Verify response
        assert response.content == "Hello there!"
        assert response.model == "gpt-4"
        assert response.usage["total_tokens"] == 15
    
    @pytest.mark.asyncio
    async def test_generate_stream(self):
        """Test streaming text generation through service."""
        # Mock provider
        mock_provider = Mock(spec=LLMProvider)
        mock_chunk1 = LLMResponse(content="Hello ", model="gpt-4")
        mock_chunk2 = LLMResponse(content="there!", model="gpt-4")
        
        async def mock_stream():
            yield mock_chunk1
            yield mock_chunk2
        
        mock_provider.generate_stream = mock_stream
        
        # Mock factory
        self.mock_factory.create_provider.return_value = mock_provider
        
        # Generate stream
        chunks = []
        async for chunk in self.service.generate_stream(
            provider_type="openai",
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            config=LLMConfig(api_key="test_key")
        ):
            chunks.append(chunk)
        
        # Verify chunks
        assert len(chunks) == 2
        assert chunks[0].content == "Hello "
        assert chunks[1].content == "there!"
    
    @pytest.mark.asyncio
    async def test_get_available_models(self):
        """Test getting available models through service."""
        # Mock provider
        mock_provider = Mock(spec=LLMProvider)
        mock_provider.get_supported_models.return_value = ["gpt-4", "gpt-3.5-turbo"]
        
        # Mock factory
        self.mock_factory.create_provider.return_value = mock_provider
        
        # Get models
        models = await self.service.get_available_models("openai", LLMConfig(api_key="test_key"))
        
        # Verify models
        assert "gpt-4" in models
        assert "gpt-3.5-turbo" in models
        assert isinstance(models, list)
    
    @pytest.mark.asyncio
    async def test_validate_provider_config(self):
        """Test validating provider config through service."""
        # Mock provider
        mock_provider = Mock(spec=LLMProvider)
        mock_provider.validate_config.return_value = True
        
        # Mock factory
        self.mock_factory.create_provider.return_value = mock_provider
        
        # Validate config
        is_valid = await self.service.validate_provider_config(
            "openai",
            LLMConfig(api_key="test_key")
        )
        
        # Verify validation
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_handle_provider_error(self):
        """Test handling provider errors."""
        # Mock provider
        mock_provider = Mock(spec=LLMProvider)
        mock_provider.generate_text = AsyncMock(side_effect=Exception("API Error"))
        
        # Mock factory
        self.mock_factory.create_provider.return_value = mock_provider
        
        # Generate text - should handle error
        with pytest.raises(Exception, match="API Error"):
            await self.service.generate_text(
                provider_type="openai",
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}],
                config=LLMConfig(api_key="test_key")
            )


if __name__ == "__main__":
    pytest.main([__file__])