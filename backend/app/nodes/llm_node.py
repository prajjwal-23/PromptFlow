"""
LLM Node Implementation

This module provides the LLM node implementation for executing
language model operations with enterprise-grade patterns.
"""

from __future__ import annotations
import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import uuid

from ..execution.nodes.base_node import BaseNode, NodeInput, NodeOutput, NodeContext, NodeStatus, NodeType, ExecutionMode
from ..domain.execution.models import NodeConfiguration


@dataclass
class LLMRequest:
    """LLM request structure."""
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    model: str = "gpt-3.5-turbo"
    stream: bool = False
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "prompt": self.prompt,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "model": self.model,
            "stream": self.stream,
            "metadata": self.metadata or {},
        }


@dataclass
class LLMResponse:
    """LLM response structure."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "response_time": self.response_time,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {},
        }


class LLMNode(BaseNode):
    """LLM node for executing language model operations."""
    
    def __init__(
        self,
        node_id: str,
        config: NodeConfiguration,
        execution_mode: ExecutionMode = ExecutionMode.SYNC
    ):
        super().__init__(node_id, NodeType.LLM, config, execution_mode)
        self._llm_client = None
        self._model_config = self._extract_model_config()
    
    def _extract_model_config(self) -> Dict[str, Any]:
        """Extract model configuration from node config."""
        config_data = self.config.config if hasattr(self.config, 'config') else {}
        return {
            "model": config_data.get("model", "gpt-3.5-turbo"),
            "temperature": config_data.get("temperature", 0.7),
            "max_tokens": config_data.get("max_tokens", 1000),
            "system_prompt": config_data.get("system_prompt"),
            "api_key": config_data.get("api_key"),
            "base_url": config_data.get("base_url"),
            "timeout": config_data.get("timeout", 30),
            "retry_attempts": config_data.get("retry_attempts", 3),
            "stream": config_data.get("stream", False),
        }
    
    def _get_required_fields(self) -> List[str]:
        """Get required fields for LLM node."""
        return ["prompt"]
    
    async def validate_input(self, input_data: NodeInput) -> bool:
        """Validate input data for LLM node."""
        if not await super().validate_input(input_data):
            return False
        
        # Validate prompt
        prompt = input_data.data.get("prompt", "")
        if not prompt or len(prompt.strip()) == 0:
            return False
        
        # Validate temperature
        temperature = input_data.data.get("temperature", self._model_config["temperature"])
        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
            return False
        
        # Validate max_tokens
        max_tokens = input_data.data.get("max_tokens", self._model_config["max_tokens"])
        if max_tokens is not None and (not isinstance(max_tokens, int) or max_tokens <= 0):
            return False
        
        return True
    
    async def preprocess_input(self, input_data: NodeInput) -> NodeInput:
        """Preprocess input data for LLM node."""
        processed_data = input_data.data.copy()
        
        # Set default values from model config
        if "temperature" not in processed_data:
            processed_data["temperature"] = self._model_config["temperature"]
        
        if "max_tokens" not in processed_data:
            processed_data["max_tokens"] = self._model_config["max_tokens"]
        
        if "model" not in processed_data:
            processed_data["model"] = self._model_config["model"]
        
        # Process prompt template if provided
        prompt = processed_data.get("prompt", "")
        if isinstance(prompt, str):
            # Replace template variables
            for key, value in input_data.data.items():
                if key != "prompt" and isinstance(value, str):
                    prompt = prompt.replace(f"{{{key}}}", value)
            processed_data["prompt"] = prompt
        
        return NodeInput(
            data=processed_data,
            metadata=input_data.metadata,
            source_nodes=input_data.source_nodes,
            timestamp=input_data.timestamp
        )
    
    async def execute(self, input_data: NodeInput, context: NodeContext) -> NodeOutput:
        """Execute LLM node."""
        start_time = datetime.now()
        
        try:
            # Create LLM request
            request = self._create_llm_request(input_data)
            
            # Execute LLM call
            response = await self._execute_llm_request(request, context)
            
            # Create output
            output_data = {
                "content": response.content,
                "model": response.model,
                "usage": response.usage,
                "finish_reason": response.finish_reason,
                "request_id": str(uuid.uuid4()),
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return NodeOutput(
                data=output_data,
                metadata={
                    "node_type": "llm",
                    "model": response.model,
                    "usage": response.usage,
                    "request_id": output_data["request_id"],
                },
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return NodeOutput(
                data={},
                error=str(e),
                execution_time=execution_time,
                timestamp=datetime.now()
            )
    
    def _create_llm_request(self, input_data: NodeInput) -> LLMRequest:
        """Create LLM request from input data."""
        return LLMRequest(
            prompt=input_data.data["prompt"],
            system_prompt=input_data.data.get("system_prompt") or self._model_config["system_prompt"],
            temperature=input_data.data.get("temperature", self._model_config["temperature"]),
            max_tokens=input_data.data.get("max_tokens", self._model_config["max_tokens"]),
            model=input_data.data.get("model", self._model_config["model"]),
            stream=self._model_config["stream"],
            metadata=input_data.metadata
        )
    
    async def _execute_llm_request(self, request: LLMRequest, context: NodeContext) -> LLMResponse:
        """Execute LLM request with appropriate client."""
        # This is a mock implementation - in real scenario, this would use actual LLM clients
        # For now, we'll simulate a response
        
        await asyncio.sleep(0.1)  # Simulate API call latency
        
        # Mock response
        mock_content = f"This is a mock response for: {request.prompt[:100]}..."
        
        return LLMResponse(
            content=mock_content,
            model=request.model,
            usage={
                "prompt_tokens": len(request.prompt.split()),
                "completion_tokens": len(mock_content.split()),
                "total_tokens": len(request.prompt.split()) + len(mock_content.split())
            },
            finish_reason="stop",
            response_time=0.1,
            timestamp=datetime.now(),
            metadata={"mock": True}
        )
    
    async def execute_streaming(self, input_data: NodeInput, context: NodeContext) -> AsyncGenerator[NodeOutput, None]:
        """Execute LLM node with streaming output."""
        if not self._model_config["stream"]:
            # If streaming is not enabled, fall back to regular execution
            yield await self.execute(input_data, context)
            return
        
        start_time = datetime.now()
        
        try:
            # Create LLM request
            request = self._create_llm_request(input_data)
            
            # Simulate streaming response
            content_chunks = [
                "This ", "is ", "a ", "streaming ", "response ", "for: ",
                request.prompt[:50], "..."
            ]
            
            accumulated_content = ""
            for i, chunk in enumerate(content_chunks):
                accumulated_content += chunk
                
                partial_output = NodeOutput(
                    data={
                        "content": accumulated_content,
                        "model": request.model,
                        "chunk": chunk,
                        "chunk_index": i,
                        "is_final": i == len(content_chunks) - 1,
                    },
                    metadata={
                        "node_type": "llm",
                        "streaming": True,
                        "chunk_index": i,
                    },
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    timestamp=datetime.now()
                )
                
                yield partial_output
                await asyncio.sleep(0.05)  # Simulate streaming delay
            
            # Final output with complete response
            final_output = NodeOutput(
                data={
                    "content": accumulated_content,
                    "model": request.model,
                    "usage": {
                        "prompt_tokens": len(request.prompt.split()),
                        "completion_tokens": len(accumulated_content.split()),
                        "total_tokens": len(request.prompt.split()) + len(accumulated_content.split())
                    },
                    "finish_reason": "stop",
                    "request_id": str(uuid.uuid4()),
                },
                metadata={
                    "node_type": "llm",
                    "model": request.model,
                    "streaming": True,
                    "request_id": str(uuid.uuid4()),
                },
                execution_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now()
            )
            
            yield final_output
            
        except Exception as e:
            error_output = NodeOutput(
                data={},
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now()
            )
            yield error_output
    
    async def postprocess_output(self, output: NodeOutput, context: NodeContext) -> NodeOutput:
        """Postprocess output data for LLM node."""
        if output.error:
            return output
        
        # Add additional metadata
        enhanced_metadata = output.metadata.copy()
        enhanced_metadata.update({
            "node_id": self.node_id,
            "model_config": self._model_config,
            "processed_at": datetime.now().isoformat(),
        })
        
        # Format content if needed
        content = output.data.get("content", "")
        if content and not output.data.get("formatted"):
            # Apply basic formatting
            formatted_content = content.strip()
            output.data["content"] = formatted_content
            output.data["formatted"] = True
        
        return NodeOutput(
            data=output.data,
            metadata=enhanced_metadata,
            execution_time=output.execution_time,
            timestamp=output.timestamp,
            error=output.error
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model": self._model_config["model"],
            "temperature": self._model_config["temperature"],
            "max_tokens": self._model_config["max_tokens"],
            "streaming": self._model_config["stream"],
            "timeout": self._model_config["timeout"],
            "retry_attempts": self._model_config["retry_attempts"],
        }
    
    def update_model_config(self, new_config: Dict[str, Any]) -> None:
        """Update model configuration."""
        self._model_config.update(new_config)
        
        # Update node config as well
        if hasattr(self.config, 'config'):
            self.config.config.update(new_config)