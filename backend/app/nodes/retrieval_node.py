"""
Retrieval Node Implementation

This module provides the retrieval node implementation for vector search
and document retrieval operations with enterprise-grade patterns.
"""

from __future__ import annotations
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid
import math

from ..execution.nodes.base_node import BaseNode, NodeInput, NodeOutput, NodeContext, NodeStatus, NodeType, ExecutionMode
from ..domain.execution.models import NodeConfiguration


@dataclass
class RetrievalQuery:
    """Retrieval query structure."""
    query: str
    collection: str
    top_k: int = 5
    score_threshold: float = 0.7
    filters: Dict[str, Any] = None
    include_metadata: bool = True
    include_vectors: bool = False
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query,
            "collection": self.collection,
            "top_k": self.top_k,
            "score_threshold": self.score_threshold,
            "filters": self.filters or {},
            "include_metadata": self.include_metadata,
            "include_vectors": self.include_vectors,
            "metadata": self.metadata or {},
        }


@dataclass
class RetrievalResult:
    """Retrieval result structure."""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    collection: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
            "collection": self.collection,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class RetrievalResponse:
    """Retrieval response structure."""
    results: List[RetrievalResult]
    query: str
    collection: str
    total_results: int
    search_time: float
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "results": [result.to_dict() for result in self.results],
            "query": self.query,
            "collection": self.collection,
            "total_results": self.total_results,
            "search_time": self.search_time,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {},
        }


class RetrievalNode(BaseNode):
    """Retrieval node for vector search and document retrieval operations."""
    
    def __init__(
        self,
        node_id: str,
        config: NodeConfiguration,
        execution_mode: ExecutionMode = ExecutionMode.SYNC
    ):
        super().__init__(node_id, NodeType.RETRIEVAL, config, execution_mode)
        self._retrieval_config = self._extract_retrieval_config()
        self._vector_client = None
    
    def _extract_retrieval_config(self) -> Dict[str, Any]:
        """Extract retrieval configuration from node config."""
        config_data = self.config.config if hasattr(self.config, 'config') else {}
        return {
            "collection": config_data.get("collection", "default"),
            "top_k": config_data.get("top_k", 5),
            "score_threshold": config_data.get("score_threshold", 0.7),
            "embedding_model": config_data.get("embedding_model", "text-embedding-ada-002"),
            "vector_db_url": config_data.get("vector_db_url", "http://localhost:6333"),
            "api_key": config_data.get("api_key"),
            "timeout": config_data.get("timeout", 10),
            "retry_attempts": config_data.get("retry_attempts", 3),
            "include_metadata": config_data.get("include_metadata", True),
            "include_vectors": config_data.get("include_vectors", False),
            "filters": config_data.get("filters", {}),
        }
    
    def _get_required_fields(self) -> List[str]:
        """Get required fields for retrieval node."""
        return ["query"]
    
    async def validate_input(self, input_data: NodeInput) -> bool:
        """Validate input data for retrieval node."""
        if not await super().validate_input(input_data):
            return False
        
        # Validate query
        query = input_data.data.get("query", "")
        if not query or len(query.strip()) == 0:
            return False
        
        # Validate top_k
        top_k = input_data.data.get("top_k", self._retrieval_config["top_k"])
        if not isinstance(top_k, int) or top_k <= 0 or top_k > 100:
            return False
        
        # Validate score_threshold
        score_threshold = input_data.data.get("score_threshold", self._retrieval_config["score_threshold"])
        if not isinstance(score_threshold, (int, float)) or score_threshold < 0 or score_threshold > 1:
            return False
        
        return True
    
    async def preprocess_input(self, input_data: NodeInput) -> NodeInput:
        """Preprocess input data for retrieval node."""
        processed_data = input_data.data.copy()
        
        # Set default values from retrieval config
        if "top_k" not in processed_data:
            processed_data["top_k"] = self._retrieval_config["top_k"]
        
        if "score_threshold" not in processed_data:
            processed_data["score_threshold"] = self._retrieval_config["score_threshold"]
        
        if "collection" not in processed_data:
            processed_data["collection"] = self._retrieval_config["collection"]
        
        # Process query template if provided
        query = processed_data.get("query", "")
        if isinstance(query, str):
            # Replace template variables
            for key, value in input_data.data.items():
                if key != "query" and isinstance(value, str):
                    query = query.replace(f"{{{key}}}", value)
            processed_data["query"] = query
        
        # Merge filters
        input_filters = processed_data.get("filters", {})
        config_filters = self._retrieval_config.get("filters", {})
        if input_filters or config_filters:
            merged_filters = {**config_filters, **input_filters}
            processed_data["filters"] = merged_filters
        
        return NodeInput(
            data=processed_data,
            metadata=input_data.metadata,
            source_nodes=input_data.source_nodes,
            timestamp=input_data.timestamp
        )
    
    async def execute(self, input_data: NodeInput, context: NodeContext) -> NodeOutput:
        """Execute retrieval node."""
        start_time = datetime.now()
        
        try:
            # Create retrieval query
            query = self._create_retrieval_query(input_data)
            
            # Execute retrieval
            response = await self._execute_retrieval(query, context)
            
            # Format results
            formatted_results = self._format_results(response.results)
            
            # Create output
            output_data = {
                "results": formatted_results,
                "query": response.query,
                "collection": response.collection,
                "total_results": response.total_results,
                "search_time": response.search_time,
                "request_id": str(uuid.uuid4()),
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return NodeOutput(
                data=output_data,
                metadata={
                    "node_type": "retrieval",
                    "collection": response.collection,
                    "result_count": len(response.results),
                    "search_time": response.search_time,
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
    
    def _create_retrieval_query(self, input_data: NodeInput) -> RetrievalQuery:
        """Create retrieval query from input data."""
        return RetrievalQuery(
            query=input_data.data["query"],
            collection=input_data.data.get("collection", self._retrieval_config["collection"]),
            top_k=input_data.data.get("top_k", self._retrieval_config["top_k"]),
            score_threshold=input_data.data.get("score_threshold", self._retrieval_config["score_threshold"]),
            filters=input_data.data.get("filters", {}),
            include_metadata=self._retrieval_config["include_metadata"],
            include_vectors=self._retrieval_config["include_vectors"],
            metadata=input_data.metadata
        )
    
    async def _execute_retrieval(self, query: RetrievalQuery, context: NodeContext) -> RetrievalResponse:
        """Execute retrieval with vector search."""
        # This is a mock implementation - in real scenario, this would use actual vector DB clients
        # For now, we'll simulate a response
        
        await asyncio.sleep(0.05)  # Simulate search latency
        
        # Mock results
        mock_results = []
        for i in range(min(query.top_k, 3)):  # Limit to 3 for mock
            score = query.score_threshold + (1.0 - query.score_threshold) * (1.0 - i * 0.2)
            if score > query.score_threshold:
                mock_results.append(RetrievalResult(
                    id=f"doc_{uuid.uuid4().hex[:8]}",
                    content=f"This is mock document {i+1} relevant to: {query.query[:50]}...",
                    score=score,
                    metadata={
                        "source": f"document_{i+1}",
                        "author": f"Author {i+1}",
                        "created_at": "2024-01-01T00:00:00Z",
                        "tags": [f"tag_{i+1}", "mock"],
                    },
                    collection=query.collection,
                    timestamp=datetime.now()
                ))
        
        return RetrievalResponse(
            results=mock_results,
            query=query.query,
            collection=query.collection,
            total_results=len(mock_results),
            search_time=0.05,
            timestamp=datetime.now(),
            metadata={"mock": True}
        )
    
    def _format_results(self, results: List[RetrievalResult]) -> List[Dict[str, Any]]:
        """Format retrieval results for output."""
        formatted = []
        for result in results:
            formatted_result = {
                "id": result.id,
                "content": result.content,
                "score": result.score,
                "metadata": result.metadata,
            }
            
            # Add additional formatting
            if result.metadata:
                # Extract key metadata fields
                if "source" in result.metadata:
                    formatted_result["source"] = result.metadata["source"]
                if "author" in result.metadata:
                    formatted_result["author"] = result.metadata["author"]
                if "created_at" in result.metadata:
                    formatted_result["created_at"] = result.metadata["created_at"]
                if "tags" in result.metadata:
                    formatted_result["tags"] = result.metadata["tags"]
            
            formatted.append(formatted_result)
        
        return formatted
    
    async def postprocess_output(self, output: NodeOutput, context: NodeContext) -> NodeOutput:
        """Postprocess output data for retrieval node."""
        if output.error:
            return output
        
        # Add additional metadata
        enhanced_metadata = output.metadata.copy()
        enhanced_metadata.update({
            "node_id": self.node_id,
            "retrieval_config": self._retrieval_config,
            "processed_at": datetime.now().isoformat(),
        })
        
        # Process results if needed
        results = output.data.get("results", [])
        if results:
            # Sort by score (descending)
            results.sort(key=lambda x: x.get("score", 0), reverse=True)
            output.data["results"] = results
            
            # Add summary statistics
            scores = [result.get("score", 0) for result in results]
            if scores:
                output.data["stats"] = {
                    "avg_score": sum(scores) / len(scores),
                    "max_score": max(scores),
                    "min_score": min(scores),
                    "score_distribution": self._calculate_score_distribution(scores),
                }
        
        return NodeOutput(
            data=output.data,
            metadata=enhanced_metadata,
            execution_time=output.execution_time,
            timestamp=output.timestamp,
            error=output.error
        )
    
    def _calculate_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate score distribution for statistics."""
        distribution = {
            "high (>0.8)": 0,
            "medium (0.5-0.8)": 0,
            "low (<0.5)": 0,
        }
        
        for score in scores:
            if score > 0.8:
                distribution["high (>0.8)"] += 1
            elif score >= 0.5:
                distribution["medium (0.5-0.8)"] += 1
            else:
                distribution["low (<0.5)"] += 1
        
        return distribution
    
    def get_retrieval_info(self) -> Dict[str, Any]:
        """Get retrieval configuration information."""
        return {
            "collection": self._retrieval_config["collection"],
            "top_k": self._retrieval_config["top_k"],
            "score_threshold": self._retrieval_config["score_threshold"],
            "embedding_model": self._retrieval_config["embedding_model"],
            "vector_db_url": self._retrieval_config["vector_db_url"],
            "timeout": self._retrieval_config["timeout"],
            "retry_attempts": self._retrieval_config["retry_attempts"],
            "include_metadata": self._retrieval_config["include_metadata"],
            "include_vectors": self._retrieval_config["include_vectors"],
        }
    
    def update_retrieval_config(self, new_config: Dict[str, Any]) -> None:
        """Update retrieval configuration."""
        self._retrieval_config.update(new_config)
        
        # Update node config as well
        if hasattr(self.config, 'config'):
            self.config.config.update(new_config)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to vector database."""
        try:
            # Mock connection test
            await asyncio.sleep(0.01)
            
            return {
                "status": "connected",
                "vector_db_url": self._retrieval_config["vector_db_url"],
                "collection": self._retrieval_config["collection"],
                "response_time": 0.01,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }