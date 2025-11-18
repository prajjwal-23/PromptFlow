"""
Graph Validation Service

This module provides comprehensive validation for graph JSON structures
following enterprise-grade patterns with detailed error reporting and performance optimization.
"""

from __future__ import annotations
import json
import re
from typing import Dict, Any, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
from pathlib import Path

from pydantic import BaseModel, Field, validator, ValidationError
from jsonschema import validate, Draft7Validator, Draft202012Validator
import jsonschema.exceptions

from ...domain.execution.models import ExecutionConfig, NodeConfiguration


class ValidationSeverity(str, Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ValidationErrorDetail:
    """Detailed validation error information."""
    path: str
    message: str
    severity: ValidationSeverity
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    context: Dict[str, Any] = field(default_factory=dict)
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "message": self.message,
            "severity": self.severity.value,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "context": self.context,
            "suggestion": self.suggestion,
        }


@dataclass(frozen=True)
class ValidationResult:
    """Result of graph validation."""
    is_valid: bool
    errors: List[ValidationErrorDetail] = field(default_factory=list)
    warnings: List[ValidationErrorDetail] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_valid": self.is_valid,
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "metrics": self.metrics,
        }


class GraphValidator:
    """Enterprise-grade graph validation service."""
    
    def __init__(self):
        """Initialize the validator with JSON Schema."""
        self._schema = self._create_graph_schema()
        self._validator = Draft7Validator(self._schema)
        self._performance_cache = {}
        self._validation_rules = self._create_validation_rules()
    
    def _create_graph_schema(self) -> Dict[str, Any]:
        """Create comprehensive JSON Schema for graph validation."""
        return {
            "$schema": "https://json-schema.org/draft/2020-12",
            "$id": "https://promptflow.dev/schemas/graph.json",
            "title": "PromptFlow Graph Schema",
            "description": "Schema for validating PromptFlow graph JSON structures",
            "type": "object",
            "required": ["nodes", "edges"],
            "properties": {
                "nodes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "type", "position"],
                        "properties": {
                            "id": {
                                "type": "string",
                                "pattern": "^[a-zA-Z0-9_-]+$",
                                "minLength": 1,
                                "maxLength": 100
                            },
                            "type": {
                                "type": "string",
                                "enum": ["input", "llm", "retrieval", "output", "tool"]
                            },
                            "position": {
                                "type": "object",
                                "properties": {
                                    "x": {"type": "number", "minimum": 0},
                                    "y": {"type": "number", "minimum": 0}
                                },
                                "required": ["x", "y"]
                            },
                            "data": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                        "minLength": 1,
                                        "maxLength": 100
                                    },
                                    "config": {
                                        "type": "object",
                                        "additionalProperties": True
                                    }
                                },
                                "additionalProperties": True
                            }
                        },
                        "minItems": 1
                    }
                },
                "edges": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "source", "target"],
                        "properties": {
                            "id": {
                                "type": "string",
                                "pattern": "^[a-zA-Z0-9_-]+$",
                                "minLength": 1,
                                "maxLength": 100
                            },
                            "source": {
                                "type": "string",
                                "pattern": "^[a-zA-Z0-9_-]+$",
                                "minLength": 1,
                                "maxLength": 100
                            },
                            "target": {
                                "type": "string",
                                "pattern": "^[a-zA-Z0-9_-]+$",
                                "minLength": 1,
                                "maxLength": 100
                            },
                            "sourceHandle": {
                                "type": "string",
                                "maxLength": 100
                            },
                            "targetHandle": {
                                "type": "string",
                                "maxLength": 100
                            }
                        },
                        "minItems": 0
                    }
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "version": {
                            "type": "string",
                            "pattern": "^\\d+\\.\\d+\\.\\d+$"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time"
                        },
                        "updated_at": {
                            "type": "string",
                            "format": "date-time"
                        }
                    },
                    "additionalProperties": True
                }
            },
            "additionalProperties": False
        }
    
    def _create_validation_rules(self) -> List[Callable]:
        """Create validation rules for business logic."""
        return [
            self._validate_node_connections,
            self._validate_node_types,
            self._validate_graph_structure,
            self._validate_performance_limits,
            self._validate_business_rules,
            self._validate_security_constraints,
        ]
    
    async def validate_graph(
        self,
        graph_json: Dict[str, Any],
        config: Optional[ExecutionConfig] = None
    ) -> ValidationResult:
        """
        Validate graph structure and business rules.
        
        Args:
            graph_json: Graph JSON to validate
            config: Execution configuration for context
            
        Returns:
            ValidationResult with detailed error information
        """
        start_time = datetime.now()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(graph_json)
            if cache_key in self._performance_cache:
                return self._performance_cache[cache_key]
            
            # JSON Schema validation
            schema_errors = await self._validate_json_schema(graph_json)
            
            # Business rule validation
            business_errors = await self._validate_business_rules(graph_json, config)
            
            # Performance validation
            performance_errors = await self._validate_performance_limits(graph_json, config)
            
            # Security validation
            security_errors = await self._validate_security_constraints(graph_json)
            
            # Combine all errors
            all_errors = schema_errors + business_errors + performance_errors + security_errors
            
            # Create result
            result = ValidationResult(
                is_valid=len(all_errors) == 0,
                errors=[error for error in all_errors if error.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]],
                warnings=[error for error in all_errors if error.severity in [ValidationSeverity.WARNING]],
                metrics={
                    "validation_time": (datetime.now() - start_time).total_seconds(),
                    "schema_errors": len(schema_errors),
                    "business_errors": len(business_errors),
                    "performance_errors": len(performance_errors),
                    "security_errors": len(security_errors),
                    "total_nodes": len(graph_json.get("nodes", [])),
                    "total_edges": len(graph_json.get("edges", [])),
                }
            )
            
            # Cache successful validations
            if result.is_valid:
                self._performance_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[ValidationErrorDetail(
                    path="root",
                    message=f"Validation failed: {str(e)}",
                    severity=ValidationSeverity.CRITICAL,
                    suggestion="Check graph structure and try again"
                )],
                metrics={"validation_time": (datetime.now() - start_time).total_seconds()}
            )
    
    async def _validate_json_schema(
        self, 
        graph_json: Dict[str, Any]
    ) -> List[ValidationErrorDetail]:
        """Validate graph against JSON Schema."""
        errors = []
        
        try:
            validate(
                instance=graph_json,
                schema=self._schema,
                format_checker=Draft202012Validator
            )
        except ValidationError as e:
            errors.append(ValidationErrorDetail(
                path="root",
                message=str(e),
                severity=ValidationSeverity.ERROR,
                suggestion="Check JSON structure and format"
            ))
        except Exception as e:
            errors.append(ValidationErrorDetail(
                path="root",
                message=f"Schema validation failed: {str(e)}",
                severity=ValidationSeverity.CRITICAL,
                suggestion="Check JSON structure and format"
            ))
        
        return errors
    
    def _handle_json_error(self, error: ValidationError) -> None:
        """Handle JSON Schema validation errors."""
        pass
    
    async def _validate_business_rules(
        self,
        graph_json: Dict[str, Any],
        config: Optional[ExecutionConfig] = None
    ) -> List[ValidationErrorDetail]:
        """Validate business rules for graph structure."""
        errors = []
        
        # Validate node connections
        connection_errors = await self._validate_node_connections(graph_json)
        errors.extend(connection_errors)
        
        # Validate node types
        type_errors = await self._validate_node_types(graph_json)
        errors.extend(type_errors)
        
        # Validate graph structure
        structure_errors = await self._validate_graph_structure(graph_json)
        errors.extend(structure_errors)
        
        return errors
    
    async def _validate_node_connections(
        self, 
        graph_json: Dict[str, Any]
    ) -> List[ValidationErrorDetail]:
        """Validate node connections in the graph."""
        errors = []
        
        nodes = graph_json.get("nodes", [])
        edges = graph_json.get("edges", [])
        
        # Create node and edge sets for validation
        node_ids = {node["id"] for node in nodes}
        edge_sources = {edge["source"] for edge in edges}
        edge_targets = {edge["target"] for edge in edges}
        
        # Check for orphaned edges
        orphaned_sources = edge_sources - node_ids
        orphaned_targets = edge_targets - node_ids
        
        for source in orphaned_sources:
            errors.append(ValidationErrorDetail(
                path=f"edges[{source}]",
                message=f"Edge source node '{source}' does not exist",
                severity=ValidationSeverity.ERROR,
                suggestion="Create the source node or remove the edge"
            ))
        
        for target in orphaned_targets:
            errors.append(ValidationErrorDetail(
                path=f"edges[{target}]",
                message=f"Edge target node '{target}' does not exist",
                severity=ValidationSeverity.ERROR,
                suggestion="Create the target node or remove the edge"
            ))
        
        # Check for self-loops
        for edge in edges:
            if edge["source"] == edge["target"]:
                errors.append(ValidationErrorDetail(
                    path=f"edges[{edge['source']}]",
                    message="Edge cannot connect node to itself",
                    severity=ValidationSeverity.ERROR,
                    suggestion="Remove the self-loop or create a different connection"
                ))
        
        # Check for duplicate edges
        edge_pairs = [(edge["source"], edge["target"]) for edge in edges]
        seen_pairs = set()
        for source, target in edge_pairs:
            if (source, target) in seen_pairs:
                errors.append(ValidationErrorDetail(
                    path=f"edges[{source}->{target}]",
                    message=f"Duplicate edge from '{source}' to '{target}'",
                    severity=ValidationSeverity.WARNING,
                    suggestion="Remove duplicate edge"
                ))
            seen_pairs.add((source, target))
        
        return errors
    
    async def _validate_node_types(
        self, 
        graph_json: Dict[str, Any]
    ) -> List[ValidationErrorDetail]:
        """Validate node types and configurations."""
        errors = []
        
        nodes = graph_json.get("nodes", [])
        node_types = {node["type"] for node in nodes}
        
        # Check for unknown node types
        valid_types = {"input", "llm", "retrieval", "output", "tool"}
        unknown_types = node_types - valid_types
        
        for node_type in unknown_types:
            errors.append(ValidationErrorDetail(
                path=f"nodes[{node_type}]",
                message=f"Unknown node type '{node_type}'",
                severity=ValidationSeverity.ERROR,
                suggestion=f"Use one of: {', '.join(valid_types)}"
            ))
        
        # Validate node configurations
        for i, node in enumerate(nodes):
            node_errors = await self._validate_node_configuration(node, i)
            errors.extend(node_errors)
        
        return errors
    
    async def _validate_node_configuration(
        self, 
        node: Dict[str, Any],
        index: int
    ) -> List[ValidationErrorDetail]:
        """Validate individual node configuration."""
        errors = []
        
        node_id = node.get("id", "")
        node_type = node.get("type", "")
        config = node.get("data", {})
        
        # Validate required fields
        if not node_id:
            errors.append(ValidationErrorDetail(
                path=f"nodes[{index}]",
                message="Node ID is required",
                severity=ValidationSeverity.ERROR,
                suggestion="Add a valid node ID"
            ))
        
        if not node_type:
            errors.append(ValidationErrorDetail(
                path=f"nodes[{index}]",
                message="Node type is required",
                severity=ValidationSeverity.ERROR,
                suggestion="Add a valid node type"
            ))
        
        # Validate node type-specific configuration
        type_errors = await self._validate_node_type_config(node_type, config, node_id)
        errors.extend(type_errors)
        
        return errors
    
    async def _validate_node_type_config(
        self, 
        node_type: str,
        config: Dict[str, Any],
        node_id: str
    ) -> List[ValidationErrorDetail]:
        """Validate node type-specific configuration."""
        errors = []
        
        if node_type == "input":
            if not config.get("placeholder"):
                errors.append(ValidationErrorDetail(
                    path=f"nodes[{node_id}].config.placeholder",
                    message="Input node requires placeholder field",
                    severity=ValidationSeverity.ERROR,
                    suggestion="Add placeholder text for the input node"
                ))
        
        elif node_type == "llm":
            if not config.get("model"):
                errors.append(ValidationErrorDetail(
                    path=f"nodes[{node_id}].config.model",
                    message="LLM node requires model field",
                    severity=ValidationSeverity.ERROR,
                    suggestion="Select a model for the LLM node"
                ))
            if not config.get("temperature"):
                errors.append(ValidationErrorDetail(
                    path=f"nodes[{node_id}].config.temperature",
                    message="LLM node requires temperature field",
                    severity=ValidationSeverity.WARNING,
                    suggestion="Set temperature between 0.0 and 2.0"
                ))
        
        elif node_type == "retrieval":
            if not config.get("collection"):
                errors.append(ValidationErrorDetail(
                    path=f"nodes[{node_id}].config.collection",
                    message="Retrieval node requires collection field",
                    severity=ValidationSeverity.ERROR,
                    suggestion="Specify the collection name for retrieval"
                ))
        
        elif node_type == "output":
            if not config.get("output_type"):
                errors.append(ValidationErrorDetail(
                    path=f"nodes[{node_id}].config.output_type",
                    message="Output node requires output_type field",
                    severity=ValidationSeverity.WARNING,
                    suggestion="Specify the output type (text, json, markdown, html)"
                ))
        
        elif node_type == "tool":
            if not config.get("endpoint"):
                errors.append(ValidationErrorDetail(
                    path=f"nodes[{node_id}].config.endpoint",
                    message="Tool node requires endpoint field",
                    severity=ValidationSeverity.ERROR,
                    suggestion="Provide the API endpoint URL"
                ))
        
        return errors
    
    async def _validate_graph_structure(
        self, 
        graph_json: Dict[str, Any]
    ) -> List[ValidationErrorDetail]:
        """Validate overall graph structure."""
        errors = []
        
        # Check required fields
        required_fields = ["nodes", "edges"]
        for field in required_fields:
            if field not in graph_json:
                errors.append(ValidationErrorDetail(
                    path=f"$.{field}",
                    message=f"Required field '{field}' is missing",
                    severity=ValidationSeverity.CRITICAL,
                    suggestion=f"Add the '{field}' field to the graph"
                ))
        
        # Check if nodes array is not empty
        nodes = graph_json.get("nodes", [])
        if not nodes:
            errors.append(ValidationErrorDetail(
                path="$.nodes",
                message="Graph must have at least one node",
                severity=ValidationSeverity.ERROR,
                suggestion="Add at least one node to the graph"
            ))
        
        # Check for cycles
        cycle_errors = await self._detect_cycles(graph_json)
        errors.extend(cycle_errors)
        
        # Check for isolated nodes
        connected_nodes = self._get_connected_nodes(graph_json)
        isolated_nodes = set(node["id"] for node in nodes) - connected_nodes
        for node_id in isolated_nodes:
            errors.append(ValidationErrorDetail(
                path=f"nodes[{node_id}]",
                message=f"Node '{node_id}' is not connected to any other node",
                severity=ValidationSeverity.WARNING,
                suggestion="Connect this node to the graph or remove it"
            ))
        
        return errors
    
    async def _detect_cycles(
        self, 
        graph_json: Dict[str, Any]
    ) -> List[ValidationErrorDetail]:
        """Detect cycles in the graph using Tarjan's algorithm."""
        errors = []
        
        nodes = graph_json.get("nodes", [])
        edges = graph_json.get("edges", [])
        
        # Create adjacency list
        adjacency = {node["id"]: [] for node in nodes}
        for edge in edges:
            adjacency[edge["source"]].append(edge["target"])
        
        # Tarjan's algorithm for cycle detection
        index = 0
        stack = [(node["id"], iter(adjacency[node["id"]])) for node in nodes]
        indices = {node["id"]: index for index, node in enumerate(nodes)}
        lowlink = [0] * len(nodes)
        
        while stack:
            node_id, iterator = stack[-1]
            try:
                neighbor = next(iterator)
                if neighbor not in indices:
                    # Unvisited node
                    indices[neighbor] = len(indices)
                    lowlink.append(0)
                    stack.append((neighbor, iter(adjacency[neighbor])))
                elif neighbor in [item[0] for item in stack]:
                    # Back edge found - cycle detected
                    errors.append(ValidationErrorDetail(
                        path=f"nodes[{node_id}]",
                        message=f"Cycle detected involving node '{node_id}'",
                        severity=ValidationSeverity.ERROR,
                        suggestion="Break the cycle by removing or reorganizing connections"
                    ))
                    break
            except StopIteration:
                stack.pop()
        
        return errors
    
    def _get_connected_nodes(
        self, 
        graph_json: Dict[str, Any]
    ) -> Set[str]:
        """Get all nodes that are connected in the graph."""
        nodes = graph_json.get("nodes", [])
        edges = graph_json.get("edges", [])
        
        if not nodes:
            return set()
        
        # Build adjacency list
        adjacency = {node["id"]: set() for node in nodes}
        for edge in edges:
            adjacency[edge["source"]].add(edge["target"])
        
        # Find all reachable nodes using DFS
        visited = set()
        stack = [nodes[0]["id"]] if nodes else []
        
        while stack:
            node_id = stack.pop()
            if node_id not in visited:
                visited.add(node_id)
                stack.extend(adjacency[node_id])
        
        return visited
    
    async def _validate_performance_limits(
        self, 
        graph_json: Dict[str, Any],
        config: Optional[ExecutionConfig] = None
    ) -> List[ValidationErrorDetail]:
        """Validate performance constraints."""
        errors = []
        
        node_count = len(graph_json.get("nodes", []))
        edge_count = len(graph_json.get("edges", []))
        
        # Check node limits
        max_nodes = config.max_nodes_per_execution if config else 50
        if node_count > max_nodes:
            errors.append(ValidationErrorDetail(
                path="$.nodes",
                message=f"Too many nodes ({node_count}). Maximum allowed is {max_nodes}",
                severity=ValidationSeverity.WARNING,
                suggestion=f"Reduce the number of nodes or increase the limit in configuration"
            ))
        
        # Check edge limits
        max_edges = config.max_edges_per_execution if config else 100
        if edge_count > max_edges:
            errors.append(ValidationErrorDetail(
                path="$.edges",
                message=f"Too many edges ({edge_count}). Maximum allowed is {max_edges}",
                severity=ValidationSeverity.WARNING,
                suggestion=f"Reduce the number of edges or increase the limit in configuration"
            ))
        
        # Check depth limits
        max_depth = config.max_graph_depth if config else 10
        graph_depth = self._calculate_graph_depth(graph_json)
        if graph_depth > max_depth:
            errors.append(ValidationErrorDetail(
                path="$.depth",
                message=f"Graph depth ({graph_depth}) exceeds maximum allowed ({max_depth})",
                severity=ValidationSeverity.WARNING,
                suggestion=f"Simplify the graph structure or increase the depth limit in configuration"
            ))
        
        return errors
    
    def _calculate_graph_depth(self, graph_json: Dict[str, Any]) -> int:
        """Calculate the maximum depth of the graph."""
        nodes = graph_json.get("nodes", [])
        edges = graph_json.get("edges", [])
        
        if not nodes:
            return 0
        
        # Create adjacency list
        adjacency = {node["id"]: [] for node in nodes}
        for edge in edges:
            adjacency[edge["source"]].append(edge["target"])
        
        # Find longest path using DFS
        max_depth = 0
        visited = set()
        stack = [(nodes[0]["id"], iter(adjacency[nodes[0]["id"]]))] if nodes else []
        
        while stack:
            node_id, iterator = stack[-1]
            current_depth = len(stack)
            max_depth = max(max_depth, current_depth)
            
            try:
                neighbor = next(iterator)
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append((neighbor, iter(adjacency[neighbor])))
            except StopIteration:
                stack.pop()
        
        return max_depth
    
    async def _validate_business_rules(
        self, 
        graph_json: Dict[str, Any],
        config: Optional[ExecutionConfig] = None
    ) -> List[ValidationErrorDetail]:
        """Validate business rules and constraints."""
        errors = []
        
        # Check for single input node
        input_nodes = [
            node for node in graph_json.get("nodes", [])
            if node.get("type") == "input"
        ]
        
        if len(input_nodes) == 0:
            errors.append(ValidationErrorDetail(
                path="$.nodes",
                message="Graph must have at least one input node",
                severity=ValidationSeverity.ERROR,
                suggestion="Add an input node to start the workflow"
            ))
        elif len(input_nodes) > 1:
            errors.append(ValidationErrorDetail(
                path="$.nodes",
                message="Multiple input nodes found. Only one input node is allowed",
                severity=ValidationSeverity.WARNING,
                suggestion="Remove extra input nodes and keep only one"
            ))
        
        # Check for single output node
        output_nodes = [
            node for node in graph_json.get("nodes", [])
            if node.get("type") == "output"
        ]
        
        if len(output_nodes) == 0:
            errors.append(ValidationErrorDetail(
                path="$.nodes",
                message="Graph must have at least one output node",
                severity=ValidationSeverity.ERROR,
                suggestion="Add an output node to end the workflow"
            ))
        elif len(output_nodes) > 1:
            errors.append(ValidationErrorDetail(
                path="$.nodes",
                message="Multiple output nodes found. Only one output node is allowed",
                severity=ValidationSeverity.WARNING,
                suggestion="Remove extra output nodes and keep only one"
            ))
        
        # Check for LLM nodes
        llm_nodes = [
            node for node in graph_json.get("nodes", [])
            if node.get("type") == "llm"
        ]
        
        if not llm_nodes:
            errors.append(ValidationErrorDetail(
                path="$.nodes",
                message="Graph must have at least one LLM node",
                severity=ValidationSeverity.WARNING,
                suggestion="Add an LLM node to process data"
            ))
        
        # Check for proper input-output flow
        if input_nodes and output_nodes and not llm_nodes:
            errors.append(ValidationErrorDetail(
                path="$.nodes",
                message="Graph must have LLM nodes between input and output",
                severity=ValidationSeverity.WARNING,
                suggestion="Add LLM nodes to process the input data"
            ))
        
        return errors
    
    async def _validate_security_constraints(
        self, 
        graph_json: Dict[str, Any]
    ) -> List[ValidationErrorDetail]:
        """Validate security constraints."""
        errors = []
        
        # Check for potentially dangerous content in node configurations
        for i, node in enumerate(graph_json.get("nodes", [])):
            config = node.get("data", {})
            
            # Check for suspicious patterns in text fields
            text_fields = [
                config.get("prompt", ""),
                config.get("system_prompt", ""),
                config.get("endpoint", ""),
                config.get("api_key", ""),
            ]
            
            for field in text_fields:
                if field and self._contains_suspicious_content(field):
                    errors.append(ValidationErrorDetail(
                        path=f"nodes[{i}].data.{field}",
                        message=f"Potentially suspicious content detected in field '{field}'",
                        severity=ValidationSeverity.WARNING,
                        suggestion="Review and clean up the content"
                    ))
        
        # Check for large data sizes
        for i, node in enumerate(graph_json.get("nodes", [])):
            config = node.get("data", {})
            config_size = len(str(config).encode('utf-8'))
            
            max_config_size = 1024 * 1024  # 1MB
            if config_size > max_config_size:
                errors.append(ValidationErrorDetail(
                    path=f"nodes[{i}].data",
                    message=f"Node configuration too large ({config_size} bytes). Maximum allowed is {max_config_size} bytes",
                    severity=ValidationSeverity.WARNING,
                    suggestion="Reduce the size of node configuration"
                ))
        
        return errors
    
    def _contains_suspicious_content(self, text: str) -> bool:
        """Check if text contains potentially suspicious content."""
        suspicious_patterns = [
            r'<script[^>]*</script>',
            r'javascript:',
            r'eval(',
            r'exec(',
            r'system(',
            r'import os',
            r'__import__',
            r'open(',
            r'file(',
            r'read(',
            r'write(',
        ]
        
        return any(pattern.search(text.lower()) for pattern in suspicious_patterns)
    
    def _get_cache_key(self, graph_json: Dict[str, Any]) -> str:
        """Generate cache key for graph JSON."""
        # Create a hash of the graph structure for caching
        graph_str = json.dumps(graph_json, sort_keys=True)
        return f"graph_{hash(graph_str)}"
    
    def get_validation_summary(
        self, 
        validation_result: ValidationResult
    ) -> Dict[str, Any]:
        """Get a summary of validation results."""
        return {
            "validation_passed": validation_result.is_valid,
            "error_count": len(validation_result.errors),
            "warning_count": len(validation_result.warnings),
            "metrics": validation_result.metrics,
            "errors": [error.to_dict() for error in validation_result.errors],
            "warnings": [warning.to_dict() for warning in validation_result.warnings],
        }


class GraphValidationService:
    """Enterprise-grade graph validation service with caching and performance optimization."""
    
    def __init__(self):
        """Initialize the validation service."""
        self._validator = GraphValidator()
        self._cache = {}
        self._metrics = {
            "validations_performed": 0,
            "total_validation_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_validation_time": 0.0,
        }
    
    async def validate_graph(
        self,
        graph_json: Dict[str, Any],
        config: Optional[ExecutionConfig] = None
    ) -> ValidationResult:
        """
        Validate graph with comprehensive checks.
        
        Args:
            graph_json: Graph JSON to validate
            config: Execution configuration for context
            
        Returns:
            ValidationResult with detailed error information
        """
        start_time = datetime.now()
        
        # Update metrics
        self._metrics["validations_performed"] += 1
        
        # Check cache first
        cache_key = self._validator._get_cache_key(graph_json)
        if cache_key in self._cache:
            self._metrics["cache_hits"] += 1
            return self._cache[cache_key]
        
        self._metrics["cache_misses"] += 1
        
        # Perform validation
        result = await self._validator.validate_graph(graph_json, config)
        
        # Update metrics
        validation_time = (datetime.now() - start_time).total_seconds()
        self._metrics["total_validation_time"] += validation_time
        self._metrics["average_validation_time"] = (
            self._metrics["total_validation_time"] / self._metrics["validations_performed"]
        )
        
        # Cache successful validations
        if result.is_valid:
            self._cache[cache_key] = result
        
        return result
    
    def get_validation_metrics(self) -> Dict[str, Any]:
        """Get validation performance metrics."""
        return self._metrics.copy()
    
    def clear_cache(self) -> None:
        """Clear the validation cache."""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._metrics.get("validations_performed", 0)
        cache_hits = self._metrics.get("cache_hits", 0)
        cache_misses = total_requests - cache_hits
        
        return {
            "total_requests": total_requests,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "cache_hit_rate": (cache_hits / total_requests * 100) if total_requests > 0 else 0,
            "average_validation_time": self._metrics.get("average_validation_time", 0.0),
            "cache_size": len(self._cache),
        }
    
    async def preload_common_schemas(self) -> None:
        """Preload common validation schemas for better performance."""
        # Preload validation schemas for common graph structures
        common_graphs = [
            {"nodes": [], "edges": []},
            {"nodes": [{"id": "input", "type": "input", "position": {"x": 0, "y": 0}}], "edges": []},
            {"nodes": [
                {"id": "input", "type": "input", "position": {"x": 0, "y": 0}},
                {"id": "llm", "type": "llm", "position": {"x": 100, "y": 0}},
                {"id": "output", "type": "output", "position": {"x": 200, "y": 0}},
                {"id": "tool", "type": "tool", "position": {"x": 300, "y": 0}},
                {"id": "retrieval", "type": "retrieval", "position": {"x": 150, "y": 0}},
            ], "edges": []}
        ]
        
        for graph in common_graphs:
            cache_key = self._validator._get_cache_key(graph)
            self._cache[cache_key] = await self._validator.validate_graph(graph)