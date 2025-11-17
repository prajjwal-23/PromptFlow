"""
Tool Node Implementation

This module provides the tool node implementation for executing
external API calls and tool operations with enterprise-grade patterns.
"""

from __future__ import annotations
import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
import uuid
import hashlib

from ..execution.nodes.base_node import BaseNode, NodeInput, NodeOutput, NodeContext, NodeStatus, NodeType, ExecutionMode
from ..domain.execution.models import NodeConfiguration


@dataclass
class ToolRequest:
    """Tool request structure."""
    tool_name: str
    url: str
    method: str = "POST"
    headers: Dict[str, str] = None
    params: Dict[str, Any] = None
    body: Dict[str, Any] = None
    timeout: int = 30
    retry_attempts: int = 3
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tool_name": self.tool_name,
            "method": self.method,
            "url": self.url,
            "headers": self.headers or {},
            "params": self.params or {},
            "body": self.body or {},
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
            "metadata": self.metadata or {},
        }


@dataclass
class ToolResponse:
    """Tool response structure."""
    status_code: int
    headers: Dict[str, str]
    body: Union[str, Dict[str, Any]]
    response_time: float
    success: bool
    error: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
            "response_time": self.response_time,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {},
        }


class ToolNode(BaseNode):
    """Tool node for executing external API calls and tool operations."""
    
    def __init__(
        self,
        node_id: str,
        config: NodeConfiguration,
        execution_mode: ExecutionMode = ExecutionMode.SYNC
    ):
        super().__init__(node_id, NodeType.TOOL, config, execution_mode)
        self._tool_config = self._extract_tool_config()
        self._http_session = None
        self._custom_tools = {}
    
    def _extract_tool_config(self) -> Dict[str, Any]:
        """Extract tool configuration from node config."""
        config_data = self.config.config if hasattr(self.config, 'config') else {}
        return {
            "tool_name": config_data.get("tool_name", "http_request"),
            "endpoint": config_data.get("endpoint"),
            "method": config_data.get("method", "POST"),
            "headers": config_data.get("headers", {}),
            "timeout": config_data.get("timeout", 30),
            "retry_attempts": config_data.get("retry_attempts", 3),
            "auth_type": config_data.get("auth_type", "none"),
            "auth_token": config_data.get("auth_token"),
            "api_key": config_data.get("api_key"),
            "verify_ssl": config_data.get("verify_ssl", True),
            "custom_functions": config_data.get("custom_functions", {}),
        }
    
    def _get_required_fields(self) -> List[str]:
        """Get required fields for tool node."""
        return ["endpoint"]
    
    async def validate_input(self, input_data: NodeInput) -> bool:
        """Validate input data for tool node."""
        if not await super().validate_input(input_data):
            return False
        
        # Validate endpoint
        endpoint = input_data.data.get("endpoint", "")
        if not endpoint:
            endpoint = self._tool_config.get("endpoint", "")
        
        if not endpoint:
            return False
        
        # Validate method
        method = input_data.data.get("method", self._tool_config["method"])
        if method not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            return False
        
        # Validate timeout
        timeout = input_data.data.get("timeout", self._tool_config["timeout"])
        if not isinstance(timeout, int) or timeout <= 0 or timeout > 300:
            return False
        
        return True
    
    async def preprocess_input(self, input_data: NodeInput) -> NodeInput:
        """Preprocess input data for tool node."""
        processed_data = input_data.data.copy()
        
        # Set default values from tool config
        if "method" not in processed_data:
            processed_data["method"] = self._tool_config["method"]
        
        if "timeout" not in processed_data:
            processed_data["timeout"] = self._tool_config["timeout"]
        
        if "tool_name" not in processed_data:
            processed_data["tool_name"] = self._tool_config["tool_name"]
        
        # Process endpoint template
        endpoint = processed_data.get("endpoint", "")
        if isinstance(endpoint, str):
            # Replace template variables
            for key, value in input_data.data.items():
                if key != "endpoint" and isinstance(value, str):
                    endpoint = endpoint.replace(f"{{{key}}}", value)
            processed_data["endpoint"] = endpoint
        
        # Merge headers
        input_headers = processed_data.get("headers", {})
        config_headers = self._tool_config.get("headers", {})
        if input_headers or config_headers:
            merged_headers = {**config_headers, **input_headers}
            processed_data["headers"] = merged_headers
        
        # Add authentication
        auth_type = self._tool_config.get("auth_type", "none")
        if auth_type == "bearer" and self._tool_config.get("auth_token"):
            processed_data["headers"]["Authorization"] = f"Bearer {self._tool_config['auth_token']}"
        elif auth_type == "api_key" and self._tool_config.get("api_key"):
            api_key = self._tool_config["api_key"]
            api_key_header = self._tool_config.get("api_key_header", "X-API-Key")
            processed_data["headers"][api_key_header] = api_key
        
        return NodeInput(
            data=processed_data,
            metadata=input_data.metadata,
            source_nodes=input_data.source_nodes,
            timestamp=input_data.timestamp
        )
    
    async def execute(self, input_data: NodeInput, context: NodeContext) -> NodeOutput:
        """Execute tool node."""
        start_time = datetime.now()
        
        try:
            # Determine execution type
            tool_name = input_data.data.get("tool_name", self._tool_config["tool_name"])
            
            if tool_name == "http_request":
                response = await self._execute_http_request(input_data, context)
            elif tool_name in self._custom_tools:
                response = await self._execute_custom_tool(tool_name, input_data, context)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            # Create output
            output_data = {
                "result": response.body,
                "status_code": response.status_code,
                "headers": response.headers,
                "success": response.success,
                "response_time": response.response_time,
                "tool_name": tool_name,
                "request_id": str(uuid.uuid4()),
            }
            
            if response.error:
                output_data["error"] = response.error
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return NodeOutput(
                data=output_data,
                metadata={
                    "node_type": "tool",
                    "tool_name": tool_name,
                    "endpoint": input_data.data.get("endpoint"),
                    "method": input_data.data.get("method"),
                    "status_code": response.status_code,
                    "response_time": response.response_time,
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
    
    async def _execute_http_request(self, input_data: NodeInput, context: NodeContext) -> ToolResponse:
        """Execute HTTP request tool."""
        endpoint = input_data.data["endpoint"]
        method = input_data.data.get("method", "POST")
        headers = input_data.data.get("headers", {})
        params = input_data.data.get("params", {})
        body = input_data.data.get("body", {})
        timeout = input_data.data.get("timeout", self._tool_config["timeout"])
        retry_attempts = input_data.data.get("retry_attempts", self._tool_config["retry_attempts"])
        
        # Create HTTP session if needed
        if self._http_session is None:
            connector = aiohttp.TCPConnector(
                verify_ssl=self._tool_config.get("verify_ssl", True),
                limit=10,
                limit_per_host=5
            )
            self._http_session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=timeout)
            )
        
        # Prepare request
        url = endpoint
        if params:
            # Add query parameters
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_string}" if "?" not in url else f"&{query_string}"
        
        # Execute with retry logic
        last_error = None
        for attempt in range(retry_attempts + 1):
            try:
                start_time = datetime.now()
                
                async with self._http_session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if body and method in ["POST", "PUT", "PATCH"] else None,
                    params=params if method == "GET" else None
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    # Parse response body
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        response_body = await response.json()
                    else:
                        response_body = await response.text()
                    
                    return ToolResponse(
                        status_code=response.status,
                        headers=dict(response.headers),
                        body=response_body,
                        response_time=response_time,
                        success=200 <= response.status < 300,
                        timestamp=datetime.now()
                    )
                    
            except Exception as e:
                last_error = e
                if attempt < retry_attempts:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                else:
                    break
        
        # Return error response
        return ToolResponse(
            status_code=500,
            headers={},
            body={},
            response_time=timeout,
            success=False,
            error=str(last_error),
            timestamp=datetime.now()
        )
    
    async def _execute_custom_tool(self, tool_name: str, input_data: NodeInput, context: NodeContext) -> ToolResponse:
        """Execute custom tool function."""
        if tool_name not in self._custom_tools:
            # Load custom tools from config
            custom_functions = self._tool_config.get("custom_functions", {})
            if tool_name in custom_functions:
                self._register_custom_tool(tool_name, custom_functions[tool_name])
            else:
                raise ValueError(f"Custom tool '{tool_name}' not found")
        
        tool_func = self._custom_tools[tool_name]
        
        try:
            start_time = datetime.now()
            
            # Execute custom function
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(input_data.data, context)
            else:
                result = tool_func(input_data.data, context)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return ToolResponse(
                status_code=200,
                headers={},
                body=result,
                response_time=response_time,
                success=True,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return ToolResponse(
                status_code=500,
                headers={},
                body={},
                response_time=0,
                success=False,
                error=str(e),
                timestamp=datetime.now()
            )
    
    def _register_custom_tool(self, name: str, func: Callable) -> None:
        """Register a custom tool function."""
        self._custom_tools[name] = func
    
    async def postprocess_output(self, output: NodeOutput, context: NodeContext) -> NodeOutput:
        """Postprocess output data for tool node."""
        if output.error:
            return output
        
        # Add additional metadata
        enhanced_metadata = output.metadata.copy()
        enhanced_metadata.update({
            "node_id": self.node_id,
            "tool_config": self._tool_config,
            "processed_at": datetime.now().isoformat(),
        })
        
        # Process result if needed
        result = output.data.get("result", {})
        if isinstance(result, dict):
            # Add result metadata
            if "data" in result:
                output.data["extracted_data"] = result["data"]
            if "status" in result:
                output.data["tool_status"] = result["status"]
            
            # Calculate result hash for caching
            result_str = json.dumps(result, sort_keys=True)
            result_hash = hashlib.md5(result_str.encode()).hexdigest()
            output.data["result_hash"] = result_hash
        
        return NodeOutput(
            data=output.data,
            metadata=enhanced_metadata,
            execution_time=output.execution_time,
            timestamp=output.timestamp,
            error=output.error
        )
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Get tool configuration information."""
        return {
            "tool_name": self._tool_config["tool_name"],
            "endpoint": self._tool_config.get("endpoint"),
            "method": self._tool_config["method"],
            "timeout": self._tool_config["timeout"],
            "retry_attempts": self._tool_config["retry_attempts"],
            "auth_type": self._tool_config.get("auth_type", "none"),
            "verify_ssl": self._tool_config.get("verify_ssl", True),
            "custom_tools": list(self._custom_tools.keys()),
        }
    
    def update_tool_config(self, new_config: Dict[str, Any]) -> None:
        """Update tool configuration."""
        self._tool_config.update(new_config)
        
        # Update node config as well
        if hasattr(self.config, 'config'):
            self.config.config.update(new_config)
    
    def register_custom_tool(self, name: str, func: Callable) -> None:
        """Register a custom tool function."""
        self._register_custom_tool(name, func)
    
    def unregister_custom_tool(self, name: str) -> None:
        """Unregister a custom tool function."""
        if name in self._custom_tools:
            del self._custom_tools[name]
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test tool endpoint connectivity."""
        try:
            if self._tool_config.get("endpoint"):
                # Test HTTP endpoint
                test_input = NodeInput(
                    data={
                        "endpoint": self._tool_config["endpoint"],
                        "method": "GET",
                        "headers": self._tool_config.get("headers", {}),
                    },
                    metadata={"test": True}
                )
                
                response = await self._execute_http_request(test_input, None)
                
                return {
                    "status": "connected" if response.success else "failed",
                    "endpoint": self._tool_config["endpoint"],
                    "status_code": response.status_code,
                    "response_time": response.response_time,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "no_endpoint",
                    "message": "No endpoint configured for testing",
                    "timestamp": datetime.now().isoformat(),
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._http_session:
            await self._http_session.close()
            self._http_session = None
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        if hasattr(self, '_http_session') and self._http_session:
            # Note: This is not ideal, but ensures cleanup
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.cleanup())
                else:
                    loop.run_until_complete(self.cleanup())
            except:
                pass