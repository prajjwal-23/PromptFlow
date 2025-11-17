"""
Manual LLM System Test.

This script provides comprehensive testing of the LLM system including
all providers, factory, and service functionality.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any

from app.llm.providers.base import (
    LLMProviderType, LLMConfig, LLMMessage, MessageRole,
    create_message, create_tool
)
from app.llm.factory import llm_factory
from app.llm.service import llm_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMSystemTester:
    """Comprehensive LLM system tester."""
    
    def __init__(self):
        """Initialize the tester."""
        self.test_results = {}
        self.start_time = datetime.now()
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all LLM system tests."""
        logger.info("Starting LLM System Tests")
        
        try:
            # Test 1: Factory functionality
            await self.test_factory_functionality()
            
            # Test 2: Provider configurations
            await self.test_provider_configurations()
            
            # Test 3: Service functionality (without API calls)
            await self.test_service_functionality()
            
            # Test 4: Message and tool normalization
            await self.test_normalization()
            
            # Test 5: Error handling
            await self.test_error_handling()
            
            # Test 6: Integration with existing nodes
            await self.test_node_integration()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            self.test_results["suite_error"] = str(e)
        
        finally:
            # Cleanup
            await llm_factory.cleanup_all_providers()
            await llm_service.cleanup()
        
        # Generate summary
        self.generate_summary()
        
        return self.test_results
    
    async def test_factory_functionality(self) -> None:
        """Test LLM provider factory."""
        logger.info("Testing factory functionality")
        
        results = {
            "available_providers": [],
            "provider_info": {},
            "config_creation": {},
            "caching": {}
        }
        
        try:
            # Test available providers
            available = llm_factory.get_available_providers()
            results["available_providers"] = [p.value for p in available]
            logger.info(f"Available providers: {results['available_providers']}")
            
            # Test provider info
            for provider_type in available:
                info = llm_factory.get_provider_info(provider_type)
                results["provider_info"][provider_type.value] = info
                logger.info(f"Provider {provider_type.value}: {info['class']}")
            
            # Test config creation
            for provider_type in [LLMProviderType.OPENAI, LLMProviderType.ANTHROPIC]:
                try:
                    config = llm_factory.create_llm_config(
                        provider_type=provider_type,
                        model="test-model",
                        api_key="test-key"
                    )
                    results["config_creation"][provider_type.value] = {
                        "success": True,
                        "provider": config.provider.value,
                        "model": config.model
                    }
                except Exception as e:
                    results["config_creation"][provider_type.value] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Test caching
            try:
                config = LLMConfig(
                    provider=LLMProviderType.OPENAI,
                    model="gpt-3.5-turbo",
                    api_key="test-key"
                )
                
                provider1 = llm_factory.create_provider(config, cache_key="test-provider")
                provider2 = llm_factory.get_cached_provider("test-provider")
                
                results["caching"] = {
                    "success": provider1 is not None and provider2 is not None,
                    "same_instance": provider1 is provider2
                }
                
                # Cleanup
                llm_factory.remove_cached_provider("test-provider")
                
            except Exception as e:
                results["caching"] = {"success": False, "error": str(e)}
            
            self.test_results["factory"] = results
            logger.info("Factory functionality tests completed")
            
        except Exception as e:
            logger.error(f"Factory test failed: {e}")
            self.test_results["factory"] = {"error": str(e)}
    
    async def test_provider_configurations(self) -> None:
        """Test provider configurations."""
        logger.info("Testing provider configurations")
        
        results = {
            "openai": {},
            "anthropic": {},
            "ollama": {}
        }
        
        # Test OpenAI configuration
        try:
            config = LLMConfig(
                provider=LLMProviderType.OPENAI,
                model="gpt-3.5-turbo",
                api_key="test-key",
                temperature=0.7,
                max_tokens=100
            )
            
            results["openai"]["config_creation"] = {
                "success": True,
                "provider": config.provider.value,
                "model": config.model,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens
            }
            
            # Test model info (without initialization)
            from app.llm.providers.openai import OpenAIProvider
            provider = OpenAIProvider(config)
            model_info = provider.get_model_info()
            results["openai"]["model_info"] = {
                "success": True,
                "context_limit": model_info.get("context_limit"),
                "supports_streaming": model_info.get("supports_streaming"),
                "supports_function_calling": model_info.get("supports_function_calling")
            }
            
        except Exception as e:
            results["openai"]["error"] = str(e)
        
        # Test Anthropic configuration
        try:
            config = LLMConfig(
                provider=LLMProviderType.ANTHROPIC,
                model="claude-3-sonnet-20240229",
                api_key="test-key",
                temperature=0.5,
                max_tokens=200
            )
            
            results["anthropic"]["config_creation"] = {
                "success": True,
                "provider": config.provider.value,
                "model": config.model,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens
            }
            
            # Test model info (without initialization)
            from app.llm.providers.anthropic import AnthropicProvider
            provider = AnthropicProvider(config)
            model_info = provider.get_model_info()
            results["anthropic"]["model_info"] = {
                "success": True,
                "context_limit": model_info.get("context_limit"),
                "supports_streaming": model_info.get("supports_streaming"),
                "supports_function_calling": model_info.get("supports_function_calling")
            }
            
        except Exception as e:
            results["anthropic"]["error"] = str(e)
        
        # Test Ollama configuration
        try:
            config = LLMConfig(
                provider=LLMProviderType.OLLAMA,
                model="llama3",
                api_base="http://localhost:11434",
                temperature=0.8,
                max_tokens=150
            )
            
            results["ollama"]["config_creation"] = {
                "success": True,
                "provider": config.provider.value,
                "model": config.model,
                "api_base": config.api_base,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens
            }
            
            # Test model info (without initialization)
            from app.llm.providers.ollama import OllamaProvider
            provider = OllamaProvider(config)
            model_info = provider.get_model_info()
            results["ollama"]["model_info"] = {
                "success": True,
                "context_limit": model_info.get("context_limit"),
                "supports_streaming": model_info.get("supports_streaming"),
                "supports_function_calling": model_info.get("supports_function_calling")
            }
            
        except Exception as e:
            results["ollama"]["error"] = str(e)
        
        self.test_results["provider_configs"] = results
        logger.info("Provider configuration tests completed")
    
    async def test_service_functionality(self) -> None:
        """Test LLM service functionality."""
        logger.info("Testing service functionality")
        
        results = {
            "initialization": {},
            "message_normalization": {},
            "tool_normalization": {},
            "provider_management": {}
        }
        
        try:
            # Test service initialization
            await llm_service.initialize()
            results["initialization"]["success"] = True
            results["initialization"]["initialized"] = llm_service._initialized
            
            # Test message normalization
            test_messages = [
                "Hello, world!",
                {"role": "user", "content": "Test message"},
                create_message("system", "You are a helpful assistant"),
                [{"role": "user", "content": "Message 1"}, "Message 2"]
            ]
            
            normalized = llm_service._normalize_messages(test_messages)
            results["message_normalization"] = {
                "success": True,
                "input_count": len(test_messages),
                "output_count": len(normalized),
                "types": [type(msg).__name__ for msg in normalized]
            }
            
            # Test tool normalization
            test_tools = [
                create_tool("test_tool", "A test tool", {"param": "string"}),
                {"name": "dict_tool", "description": "A dict tool", "parameters": {"value": "number"}}
            ]
            
            normalized_tools = llm_service._normalize_tools(test_tools)
            results["tool_normalization"] = {
                "success": True,
                "input_count": len(test_tools),
                "output_count": len(normalized_tools) if normalized_tools else 0,
                "types": [type(tool).__name__ for tool in normalized_tools] if normalized_tools else []
            }
            
            # Test provider management
            try:
                # This should work without actual API calls
                provider_info = await llm_service.get_provider_info(
                    LLMProviderType.OPENAI,
                    "gpt-3.5-turbo",
                    "test-key"
                )
                results["provider_management"]["get_info"] = {
                    "success": True,
                    "provider": provider_info.get("provider"),
                    "model": provider_info.get("model")
                }
            except Exception as e:
                results["provider_management"]["get_info"] = {
                    "success": False,
                    "error": str(e)
                }
            
            # Test service stats
            stats = await llm_service.get_service_stats()
            results["provider_management"]["stats"] = {
                "success": True,
                "initialized": stats.get("initialized"),
                "default_providers": stats.get("default_providers"),
                "available_providers": [p.value for p in stats.get("available_providers", [])]
            }
            
        except Exception as e:
            logger.error(f"Service test failed: {e}")
            results["error"] = str(e)
        
        self.test_results["service"] = results
        logger.info("Service functionality tests completed")
    
    async def test_normalization(self) -> None:
        """Test message and tool normalization."""
        logger.info("Testing normalization")
        
        results = {
            "message_formats": {},
            "tool_formats": {},
            "edge_cases": {}
        }
        
        try:
            # Test different message formats
            message_formats = [
                ("string", "Hello"),
                ("dict", {"role": "user", "content": "Hello"}),
                ("llm_message", create_message("user", "Hello")),
                ("mixed", ["Hello", {"role": "assistant", "content": "Hi"}, create_message("system", "System")])
            ]
            
            for format_name, messages in message_formats:
                try:
                    if isinstance(messages, list):
                        normalized = llm_service._normalize_messages(messages)
                        results["message_formats"][format_name] = {
                            "success": True,
                            "input_count": len(messages),
                            "output_count": len(normalized)
                        }
                    else:
                        normalized = llm_service._normalize_messages([messages])
                        results["message_formats"][format_name] = {
                            "success": True,
                            "input_type": type(messages).__name__,
                            "output_count": len(normalized)
                        }
                except Exception as e:
                    results["message_formats"][format_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Test different tool formats
            tool_formats = [
                ("llm_tool", create_tool("test", "Test tool", {"param": "string"})),
                ("dict", {"name": "test", "description": "Test tool", "parameters": {"param": "string"}}),
                ("mixed", [
                    create_tool("tool1", "Tool 1", {"a": "string"}),
                    {"name": "tool2", "description": "Tool 2", "parameters": {"b": "number"}}
                ])
            ]
            
            for format_name, tools in tool_formats:
                try:
                    if isinstance(tools, list):
                        normalized = llm_service._normalize_tools(tools)
                        results["tool_formats"][format_name] = {
                            "success": True,
                            "input_count": len(tools),
                            "output_count": len(normalized) if normalized else 0
                        }
                    else:
                        normalized = llm_service._normalize_tools([tools])
                        results["tool_formats"][format_name] = {
                            "success": True,
                            "input_type": type(tools).__name__,
                            "output_count": len(normalized) if normalized else 0
                        }
                except Exception as e:
                    results["tool_formats"][format_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Test edge cases
            edge_cases = [
                ("empty_messages", []),
                ("empty_tools", []),
                ("invalid_message", {"invalid": "data"}),
                ("invalid_tool", {"name": "", "parameters": {}})
            ]
            
            for case_name, data in edge_cases:
                try:
                    if "message" in case_name:
                        normalized = llm_service._normalize_messages(data)
                        results["edge_cases"][case_name] = {
                            "success": True,
                            "output_count": len(normalized)
                        }
                    else:
                        normalized = llm_service._normalize_tools(data)
                        results["edge_cases"][case_name] = {
                            "success": True,
                            "output_count": len(normalized) if normalized else 0
                        }
                except Exception as e:
                    results["edge_cases"][case_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
        except Exception as e:
            logger.error(f"Normalization test failed: {e}")
            results["error"] = str(e)
        
        self.test_results["normalization"] = results
        logger.info("Normalization tests completed")
    
    async def test_error_handling(self) -> None:
        """Test error handling."""
        logger.info("Testing error handling")
        
        results = {
            "invalid_provider": {},
            "invalid_config": {},
            "missing_api_key": {},
            "invalid_model": {}
        }
        
        try:
            # Test invalid provider type
            try:
                # This should cause a type error - we'll test it differently
                invalid_config = {
                    "provider": "invalid_provider",
                    "model": "test-model"
                }
                # Try to create config with invalid data
                config = LLMConfig(**invalid_config)
                provider = llm_factory.create_provider(config)
                results["invalid_provider"]["success"] = False  # Should not reach here
            except Exception as e:
                results["invalid_provider"] = {
                    "success": True,  # Expected to fail
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            
            # Test missing API key for providers that require it
            for provider_type in [LLMProviderType.OPENAI, LLMProviderType.ANTHROPIC]:
                try:
                    config = LLMConfig(
                        provider=provider_type,
                        model="test-model",
                        api_key=None  # Missing API key
                    )
                    provider = llm_factory.create_provider(config)
                    # Try to validate (should fail)
                    await provider.validate_config()
                    results[f"missing_api_key_{provider_type.value}"] = {
                        "success": False  # Should not reach here
                    }
                except Exception as e:
                    results[f"missing_api_key_{provider_type.value}"] = {
                        "success": True,  # Expected to fail
                        "error_type": type(e).__name__
                    }
            
            # Test invalid model names
            try:
                config = LLMConfig(
                    provider=LLMProviderType.OPENAI,
                    model="invalid-model-name-12345",
                    api_key="test-key"
                )
                from app.llm.providers.openai import OpenAIProvider
                provider = OpenAIProvider(config)
                # This should create a warning but not fail
                model_info = provider.get_model_info()
                results["invalid_model"] = {
                    "success": True,
                    "context_limit": model_info.get("context_limit", "default")
                }
            except Exception as e:
                results["invalid_model"] = {
                    "success": False,
                    "error": str(e)
                }
            
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            results["error"] = str(e)
        
        self.test_results["error_handling"] = results
        logger.info("Error handling tests completed")
    
    async def test_node_integration(self) -> None:
        """Test integration with existing node system."""
        logger.info("Testing node integration")
        
        results = {
            "llm_node_compatibility": {},
            "message_format_compatibility": {}
        }
        
        try:
            # Test that our LLM system works with existing node structure
            from app.nodes.llm_node import LLMNode
            
            # Create a mock LLM node configuration
            node_config = {
                "id": "test_llm_node",
                "type": "llm",
                "data": {
                    "model": "gpt-3.5-turbo",
                    "provider": "openai",
                    "prompt": "Test prompt",
                    "temperature": 0.7,
                    "max_tokens": 100
                }
            }
            
            # Test that we can create LLM messages compatible with node expectations
            test_messages = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello, how are you?"},
                {"role": "assistant", "content": "I'm doing well, thank you!"}
            ]
            
            normalized = llm_service._normalize_messages(test_messages)
            results["message_format_compatibility"] = {
                "success": True,
                "input_format": "dict_list",
                "output_format": "llm_message_list",
                "count": len(normalized)
            }
            
            # Test that our provider can be used in node context
            try:
                config = LLMConfig(
                    provider=LLMProviderType.OPENAI,
                    model="gpt-3.5-turbo",
                    api_key="test-key",
                    temperature=0.7,
                    max_tokens=100
                )
                
                provider = llm_factory.create_provider(config, initialize=False)
                
                # Test that provider has required methods for node integration
                required_methods = ["generate", "generate_stream", "format_messages"]
                available_methods = [method for method in required_methods if hasattr(provider, method)]
                
                results["llm_node_compatibility"] = {
                    "success": len(available_methods) == len(required_methods),
                    "required_methods": required_methods,
                    "available_methods": available_methods,
                    "provider_type": provider.provider_type.value,
                    "model": provider.model
                }
                
            except Exception as e:
                results["llm_node_compatibility"] = {
                    "success": False,
                    "error": str(e)
                }
            
        except Exception as e:
            logger.error(f"Node integration test failed: {e}")
            results["error"] = str(e)
        
        self.test_results["node_integration"] = results
        logger.info("Node integration tests completed")
    
    def generate_summary(self) -> None:
        """Generate test summary."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Count successful tests
        total_tests = 0
        successful_tests = 0
        
        for category, results in self.test_results.items():
            if isinstance(results, dict) and "error" not in results:
                for test_name, test_result in results.items():
                    if isinstance(test_result, dict):
                        total_tests += 1
                        if test_result.get("success", False):
                            successful_tests += 1
        
        summary = {
            "test_duration_seconds": duration,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "categories_tested": list(self.test_results.keys()),
            "timestamp": end_time.isoformat()
        }
        
        self.test_results["summary"] = summary
        
        logger.info(f"Test Summary: {successful_tests}/{total_tests} tests passed ({summary['success_rate']:.1f}%)")
        logger.info(f"Test completed in {duration:.2f} seconds")


async def main():
    """Main test function."""
    print("Starting PromptFlow LLM System Tests")
    print("=" * 50)
    
    tester = LLMSystemTester()
    results = await tester.run_all_tests()
    
    # Print results
    print("\nTest Results:")
    print(json.dumps(results, indent=2, default=str))
    
    # Save results to file
    with open("llm_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: llm_test_results.json")
    
    # Print summary
    if "summary" in results:
        summary = results["summary"]
        print(f"\nSummary: {summary['successful_tests']}/{summary['total_tests']} tests passed")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Duration: {summary['test_duration_seconds']:.2f} seconds")
    
    print("\nLLM System Tests Complete!")


if __name__ == "__main__":
    asyncio.run(main())