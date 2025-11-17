"""
Output Node Implementation

This module provides the output node implementation for final data output
with enterprise-grade patterns and multiple format support.
"""

from __future__ import annotations
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import uuid
import html

from ..execution.nodes.base_node import BaseNode, NodeInput, NodeOutput, NodeContext, NodeStatus, NodeType, ExecutionMode, ProcessingNode
from ..domain.execution.models import NodeConfiguration


@dataclass
class OutputNodeConfig:
    """Configuration for output node."""
    output_type: str = "text"  # text, json, markdown, html, xml
    format_options: Dict[str, Any] = None
    save_to_file: bool = False
    file_path: Optional[str] = None
    include_metadata: bool = False
    template: Optional[str] = None
    encoding: str = "utf-8"
    
    def __post_init__(self):
        if self.format_options is None:
            self.format_options = {}


class OutputNode(ProcessingNode):
    """Output node for final data output with multiple format support."""
    
    def __init__(
        self,
        node_id: str,
        config: NodeConfiguration,
        execution_mode: ExecutionMode = ExecutionMode.SYNC
    ):
        """
        Initialize output node.
        
        Args:
            node_id: Unique identifier for the node
            config: Node configuration
            execution_mode: Execution mode
        """
        super().__init__(node_id, NodeType.OUTPUT, config, execution_mode)
        self._output_config = self._extract_output_config()
    
    def _extract_output_config(self) -> OutputNodeConfig:
        """Extract output configuration from node config."""
        config_data = self.config.config if hasattr(self.config, 'config') else {}
        return OutputNodeConfig(
            output_type=config_data.get("output_type", "text"),
            format_options=config_data.get("format_options", {}),
            save_to_file=config_data.get("save_to_file", False),
            file_path=config_data.get("file_path"),
            include_metadata=config_data.get("include_metadata", False),
            template=config_data.get("template"),
            encoding=config_data.get("encoding", "utf-8")
        )
    
    def _get_required_fields(self) -> List[str]:
        """Get required fields for output node."""
        # Output nodes are flexible - they can handle various input formats
        return []
    
    async def validate_input(self, input_data: NodeInput) -> bool:
        """Validate input data for output node."""
        # Basic validation - ensure we have some data to output
        if not input_data.data:
            return False
        
        # Validate output type
        valid_types = ["text", "json", "markdown", "html", "xml", "csv"]
        if self._output_config.output_type not in valid_types:
            return False
        
        # Validate file path if saving to file
        if self._output_config.save_to_file and not self._output_config.file_path:
            return False
        
        return True
    
    async def preprocess_input(self, input_data: NodeInput) -> NodeInput:
        """Preprocess input data for output node."""
        processed_data = input_data.data.copy()
        
        # Ensure data is in a consistent format
        if "result" not in processed_data:
            # If no explicit result, use the entire data as result
            processed_data["result"] = processed_data
        
        # Add processing metadata
        enhanced_metadata = input_data.metadata.copy()
        enhanced_metadata.update({
            "output_type": self._output_config.output_type,
            "save_to_file": self._output_config.save_to_file,
            "include_metadata": self._output_config.include_metadata,
        })
        
        return NodeInput(
            data=processed_data,
            metadata=enhanced_metadata,
            source_nodes=input_data.source_nodes,
            timestamp=input_data.timestamp
        )
    
    async def execute(self, input_data: NodeInput, context: NodeContext) -> NodeOutput:
        """Execute output node."""
        start_time = datetime.now()
        
        try:
            # Get the result data
            result_data = input_data.data.get("result", input_data.data)
            
            # Format the output based on output type
            formatted_output = await self._format_output(result_data, context)
            
            # Save to file if required
            file_path = None
            if self._output_config.save_to_file and self._output_config.file_path:
                file_path = await self._save_to_file(formatted_output)
            
            # Create output data
            output_data = {
                "result": formatted_output,
                "type": self._output_config.output_type,
                "format": "formatted",
            }
            
            # Add file information if saved
            if file_path:
                output_data["file_path"] = file_path
                output_data["saved"] = True
            
            # Include metadata if requested
            if self._output_config.include_metadata:
                output_data["metadata"] = {
                    "execution_id": context.execution_id,
                    "node_id": self.node_id,
                    "timestamp": datetime.now().isoformat(),
                    "source_nodes": input_data.source_nodes,
                    "input_metadata": input_data.metadata,
                }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return NodeOutput(
                data=output_data,
                metadata={
                    "node_type": "output",
                    "output_type": self._output_config.output_type,
                    "formatted": True,
                    "saved_to_file": self._output_config.save_to_file,
                },
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return NodeOutput(
                data={},
                error=f"Output node execution failed: {str(e)}",
                execution_time=execution_time,
                timestamp=datetime.now()
            )
    
    async def _format_output(self, data: Any, context: NodeContext) -> str:
        """Format output data based on output type."""
        output_type = self._output_config.output_type
        
        if output_type == "text":
            return self._format_as_text(data)
        elif output_type == "json":
            return self._format_as_json(data)
        elif output_type == "markdown":
            return self._format_as_markdown(data)
        elif output_type == "html":
            return self._format_as_html(data)
        elif output_type == "xml":
            return self._format_as_xml(data)
        elif output_type == "csv":
            return self._format_as_csv(data)
        else:
            return str(data)
    
    def _format_as_text(self, data: Any) -> str:
        """Format data as plain text."""
        if isinstance(data, dict):
            # Use template if provided
            if self._output_config.template:
                return self._apply_template(data, self._output_config.template)
            
            # Convert dict to formatted text
            lines = []
            for key, value in data.items():
                if key != "metadata":  # Skip metadata by default
                    lines.append(f"{key}: {value}")
            return "\n".join(lines)
        elif isinstance(data, list):
            return "\n".join(str(item) for item in data)
        else:
            return str(data)
    
    def _format_as_json(self, data: Any) -> str:
        """Format data as JSON."""
        # Apply JSON formatting options
        indent = self._output_config.format_options.get("indent", 2)
        sort_keys = self._output_config.format_options.get("sort_keys", False)
        
        try:
            return json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
        except TypeError:
            # Handle non-serializable objects
            return json.dumps(str(data), indent=indent, sort_keys=sort_keys)
    
    def _format_as_markdown(self, data: Any) -> str:
        """Format data as Markdown."""
        if isinstance(data, dict):
            lines = ["# Output Result"]
            
            # Use template if provided
            if self._output_config.template:
                template_content = self._apply_template(data, self._output_config.template)
                lines.append(template_content)
            else:
                for key, value in data.items():
                    if key != "metadata":
                        lines.append(f"## {key}")
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                lines.append(f"- **{sub_key}**: {sub_value}")
                        elif isinstance(value, list):
                            for item in value:
                                lines.append(f"- {item}")
                        else:
                            lines.append(f"```\n{value}\n```")
            
            return "\n".join(lines)
        elif isinstance(data, list):
            lines = ["# Output Result"]
            for i, item in enumerate(data):
                lines.append(f"## Item {i + 1}")
                lines.append(f"```\n{item}\n```")
            return "\n".join(lines)
        else:
            return f"# Output Result\n\n```\n{data}\n```"
    
    def _format_as_html(self, data: Any) -> str:
        """Format data as HTML."""
        if isinstance(data, dict):
            # Use template if provided
            if self._output_config.template:
                return self._apply_template(data, self._output_config.template)
            
            # Generate HTML from data
            lines = ["<div class='output-result'>"]
            lines.append("<h1>Output Result</h1>")
            
            for key, value in data.items():
                if key != "metadata":
                    lines.append(f"<div class='output-section'>")
                    lines.append(f"<h2>{html.escape(str(key))}</h2>")
                    
                    if isinstance(value, dict):
                        lines.append("<table class='output-table'>")
                        for sub_key, sub_value in value.items():
                            lines.append("<tr>")
                            lines.append(f"<td>{html.escape(str(sub_key))}</td>")
                            lines.append(f"<td>{html.escape(str(sub_value))}</td>")
                            lines.append("</tr>")
                        lines.append("</table>")
                    elif isinstance(value, list):
                        lines.append("<ul>")
                        for item in value:
                            lines.append(f"<li>{html.escape(str(item))}</li>")
                        lines.append("</ul>")
                    else:
                        lines.append(f"<pre>{html.escape(str(value))}</pre>")
                    
                    lines.append("</div>")
            
            lines.append("</div>")
            return "\n".join(lines)
        else:
            return f"<div class='output-result'><h1>Output Result</h1><pre>{html.escape(str(data))}</pre></div>"
    
    def _format_as_xml(self, data: Any) -> str:
        """Format data as XML."""
        def dict_to_xml(d, root_name="output"):
            lines = [f"<{root_name}>"]
            for key, value in d.items():
                if key != "metadata":
                    if isinstance(value, dict):
                        lines.append(dict_to_xml(value, key))
                    elif isinstance(value, list):
                        lines.append(f"<{key}>")
                        for item in value:
                            lines.append(f"<item>{html.escape(str(item))}</item>")
                        lines.append(f"</{key}>")
                    else:
                        lines.append(f"<{key}>{html.escape(str(value))}</{key}>")
            lines.append(f"</{root_name}>")
            return "\n".join(lines)
        
        if isinstance(data, dict):
            return dict_to_xml(data)
        else:
            return f"<output>{html.escape(str(data))}</output>"
    
    def _format_as_csv(self, data: Any) -> str:
        """Format data as CSV."""
        import csv
        import io
        
        output = io.StringIO()
        
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # List of dictionaries - use first dict keys as headers
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        elif isinstance(data, dict):
            # Single dictionary - convert to key-value pairs
            writer = csv.writer(output)
            writer.writerow(["Key", "Value"])
            for key, value in data.items():
                if key != "metadata":
                    writer.writerow([key, value])
        else:
            # Simple value
            writer = csv.writer(output)
            writer.writerow(["Value"])
            writer.writerow([str(data)])
        
        return output.getvalue()
    
    def _apply_template(self, data: Dict[str, Any], template: str) -> str:
        """Apply template to data using simple string replacement."""
        result = template
        for key, value in data.items():
            if isinstance(value, (str, int, float, bool)):
                result = result.replace(f"{{{key}}}", str(value))
            elif isinstance(value, dict):
                # Handle nested templates
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, (str, int, float, bool)):
                        result = result.replace(f"{{{key}.{sub_key}}}", str(sub_value))
        return result
    
    async def _save_to_file(self, content: str) -> str:
        """Save content to file."""
        try:
            file_path = self._output_config.file_path
            
            # Ensure directory exists
            import os
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write content to file
            with open(file_path, 'w', encoding=self._output_config.encoding) as f:
                f.write(content)
            
            return file_path
            
        except Exception as e:
            raise RuntimeError(f"Failed to save output to file: {str(e)}")
    
    async def postprocess_output(self, output: NodeOutput, context: NodeContext) -> NodeOutput:
        """Postprocess output data for output node."""
        if output.error:
            return output
        
        # Add additional metadata
        enhanced_metadata = output.metadata.copy()
        enhanced_metadata.update({
            "node_id": self.node_id,
            "output_config": {
                "output_type": self._output_config.output_type,
                "save_to_file": self._output_config.save_to_file,
                "include_metadata": self._output_config.include_metadata,
                "encoding": self._output_config.encoding,
            },
            "processed_at": datetime.now().isoformat(),
        })
        
        return NodeOutput(
            data=output.data,
            metadata=enhanced_metadata,
            execution_time=output.execution_time,
            timestamp=output.timestamp,
            error=output.error
        )
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for this output node."""
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": ["string", "object", "array"],
                    "description": f"Result data to be formatted as {self._output_config.output_type}",
                }
            },
            "required": ["result"],
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update output node configuration."""
        # Update output config
        for key, value in new_config.items():
            if hasattr(self._output_config, key):
                setattr(self._output_config, key, value)
        
        # Update node config as well
        if hasattr(self.config, 'config'):
            self.config.config.update(new_config)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of output node configuration."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "output_type": self._output_config.output_type,
            "save_to_file": self._output_config.save_to_file,
            "has_file_path": bool(self._output_config.file_path),
            "include_metadata": self._output_config.include_metadata,
            "has_template": bool(self._output_config.template),
            "encoding": self._output_config.encoding,
        }
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        return ["text", "json", "markdown", "html", "xml", "csv"]