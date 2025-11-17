"""
Input Node Implementation

This module provides the input node implementation for receiving
external data with enterprise-grade patterns.
"""

from __future__ import annotations
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

from ..execution.nodes.base_node import BaseNode, NodeInput, NodeOutput, NodeContext, NodeStatus, NodeType, ExecutionMode, ProcessingNode
from ..domain.execution.models import NodeConfiguration


@dataclass
class InputNodeConfig:
    """Configuration for input node."""
    input_type: str = "text"
    default_value: Any = None
    required: bool = True
    validation_rules: List[str] = None
    placeholder: str = ""
    description: str = ""
    
    def __post_init__(self):
        if self.validation_rules is None:
            self.validation_rules = []


class InputNode(ProcessingNode):
    """Input node for receiving external data."""
    
    def __init__(
        self,
        node_id: str,
        config: NodeConfiguration,
        execution_mode: ExecutionMode = ExecutionMode.SYNC
    ):
        """
        Initialize input node.
        
        Args:
            node_id: Unique identifier for the node
            config: Node configuration
            execution_mode: Execution mode
        """
        super().__init__(node_id, NodeType.INPUT, config, execution_mode)
        self._input_config = self._extract_input_config()
    
    def _extract_input_config(self) -> InputNodeConfig:
        """Extract input configuration from node config."""
        config_data = self.config.config if hasattr(self.config, 'config') else {}
        return InputNodeConfig(
            input_type=config_data.get("input_type", "text"),
            default_value=config_data.get("default_value"),
            required=config_data.get("required", True),
            validation_rules=config_data.get("validation_rules", []),
            placeholder=config_data.get("placeholder", ""),
            description=config_data.get("description", "")
        )
    
    def _get_required_fields(self) -> List[str]:
        """Get required fields for input node."""
        # Input nodes are flexible - they can accept various input formats
        return []
    
    async def validate_input(self, input_data: NodeInput) -> bool:
        """Validate input data for input node."""
        # Basic validation
        if not input_data.data:
            if self._input_config.required:
                return False
            else:
                return True  # Empty input is OK if not required
        
        # Type-specific validation
        input_type = self._input_config.input_type
        value = input_data.data.get("value")
        
        if input_type == "text":
            if not isinstance(value, str):
                return False
        elif input_type == "number":
            if not isinstance(value, (int, float)):
                return False
        elif input_type == "boolean":
            if not isinstance(value, bool):
                return False
        elif input_type == "json":
            if isinstance(value, str):
                try:
                    json.loads(value)
                except json.JSONDecodeError:
                    return False
            elif not isinstance(value, (dict, list)):
                return False
        elif input_type == "file":
            # File validation would check for file metadata
            if not isinstance(value, dict) or "path" not in value:
                return False
        
        # Apply custom validation rules
        return await self._apply_validation_rules(value)
    
    async def _apply_validation_rules(self, value: Any) -> bool:
        """Apply custom validation rules to the input value."""
        for rule in self._input_config.validation_rules:
            if not await self._validate_rule(rule, value):
                return False
        return True
    
    async def _validate_rule(self, rule: str, value: Any) -> bool:
        """Validate a single rule against the value."""
        # Common validation rules
        if rule.startswith("min_length:"):
            min_len = int(rule.split(":")[1])
            return len(str(value)) >= min_len
        elif rule.startswith("max_length:"):
            max_len = int(rule.split(":")[1])
            return len(str(value)) <= max_len
        elif rule.startswith("regex:"):
            import re
            pattern = rule.split(":", 1)[1]
            return bool(re.match(pattern, str(value)))
        elif rule == "email":
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(email_pattern, str(value)))
        elif rule == "url":
            import re
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            return bool(re.match(url_pattern, str(value)))
        
        # Unknown rule - assume valid
        return True
    
    async def preprocess_input(self, input_data: NodeInput) -> NodeInput:
        """Preprocess input data for input node."""
        processed_data = input_data.data.copy()
        
        # Apply default value if input is empty and default is provided
        if not processed_data.get("value") and self._input_config.default_value is not None:
            processed_data["value"] = self._input_config.default_value
        
        # Type conversion
        value = processed_data.get("value")
        if value is not None:
            processed_data["value"] = await self._convert_type(value, self._input_config.input_type)
        
        # Add metadata
        enhanced_metadata = input_data.metadata.copy()
        enhanced_metadata.update({
            "input_type": self._input_config.input_type,
            "required": self._input_config.required,
            "validation_applied": True,
        })
        
        return NodeInput(
            data=processed_data,
            metadata=enhanced_metadata,
            source_nodes=input_data.source_nodes,
            timestamp=input_data.timestamp
        )
    
    async def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert value to the target type."""
        if target_type == "text":
            return str(value)
        elif target_type == "number":
            try:
                if isinstance(value, str):
                    if "." in value:
                        return float(value)
                    else:
                        return int(value)
                return float(value) if isinstance(value, float) else int(value)
            except (ValueError, TypeError):
                return value
        elif target_type == "boolean":
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
        elif target_type == "json":
            if isinstance(value, str):
                return json.loads(value)
            return value
        else:
            return value
    
    async def execute(self, input_data: NodeInput, context: NodeContext) -> NodeOutput:
        """Execute input node."""
        start_time = datetime.now()
        
        try:
            # Get the processed value
            value = input_data.data.get("value")
            
            # Create output data
            output_data = {
                "value": value,
                "type": self._input_config.input_type,
                "metadata": {
                    "source": "input_node",
                    "node_id": self.node_id,
                    "timestamp": datetime.now().isoformat(),
                }
            }
            
            # Add additional context information
            if self._input_config.description:
                output_data["metadata"]["description"] = self._input_config.description
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return NodeOutput(
                data=output_data,
                metadata={
                    "node_type": "input",
                    "input_type": self._input_config.input_type,
                    "required": self._input_config.required,
                    "processed": True,
                },
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return NodeOutput(
                data={},
                error=f"Input node execution failed: {str(e)}",
                execution_time=execution_time,
                timestamp=datetime.now()
            )
    
    async def postprocess_output(self, output: NodeOutput, context: NodeContext) -> NodeOutput:
        """Postprocess output data for input node."""
        if output.error:
            return output
        
        # Add additional metadata
        enhanced_metadata = output.metadata.copy()
        enhanced_metadata.update({
            "node_id": self.node_id,
            "input_config": {
                "input_type": self._input_config.input_type,
                "required": self._input_config.required,
                "placeholder": self._input_config.placeholder,
            },
            "processed_at": datetime.now().isoformat(),
        })
        
        # Ensure output has proper structure
        output_data = output.data.copy()
        if "value" not in output_data:
            output_data["value"] = self._input_config.default_value
        
        return NodeOutput(
            data=output_data,
            metadata=enhanced_metadata,
            execution_time=output.execution_time,
            timestamp=output.timestamp,
            error=output.error
        )
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for this input node."""
        schema = {
            "type": "object",
            "properties": {
                "value": {
                    "type": self._input_config.input_type,
                    "description": self._input_config.description or f"Input value of type {self._input_config.input_type}",
                }
            },
            "required": ["value"] if self._input_config.required else [],
        }
        
        # Add default value if specified
        if self._input_config.default_value is not None:
            schema["properties"]["value"]["default"] = self._input_config.default_value
        
        # Add placeholder for text inputs
        if self._input_config.placeholder and self._input_config.input_type == "text":
            schema["properties"]["value"]["placeholder"] = self._input_config.placeholder
        
        return schema
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update input node configuration."""
        # Update input config
        for key, value in new_config.items():
            if hasattr(self._input_config, key):
                setattr(self._input_config, key, value)
        
        # Update node config as well
        if hasattr(self.config, 'config'):
            self.config.config.update(new_config)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of input node configuration."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "input_type": self._input_config.input_type,
            "required": self._input_config.required,
            "has_default": self._input_config.default_value is not None,
            "validation_rules_count": len(self._input_config.validation_rules),
            "placeholder": self._input_config.placeholder,
            "description": self._input_config.description,
        }