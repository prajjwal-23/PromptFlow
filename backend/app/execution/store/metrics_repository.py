"""
Metrics Repository Implementation

This module provides the concrete implementation of the MetricsRepository
interface using Redis for metrics storage and aggregation.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone, timedelta
import json
import logging

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from app.domain.execution.repositories import MetricsRepository
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MetricsRepositoryImpl(MetricsRepository):
    """Concrete implementation of MetricsRepository using Redis."""
    
    def __init__(self):
        """Initialize metrics repository."""
        self.logger = logger
        self.settings = get_settings()
        self._client = None
        self._connected = False
    
    async def _get_client(self):
        """Get Redis client, creating connection if needed."""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis is not available. Install redis-py to use metrics storage.")
        
        if not self._connected or self._client is None:
            try:
                self._client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    db=self.settings.REDIS_DB,
                    password=self.settings.REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )
                
                # Test connection
                await self._client.ping()
                self._connected = True
                self.logger.info("Connected to Redis for metrics storage")
                
            except Exception as e:
                self.logger.error(f"Failed to connect to Redis: {e}")
                self._connected = False
                raise
        
        return self._client
    
    async def record_metric(
        self, 
        metric_name: str, 
        value: Union[int, float],
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record a metric value."""
        try:
            client = await self._get_client()
            
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
            
            # Create metric key with time bucket (hourly)
            time_bucket = timestamp.strftime("%Y%m%d%H")
            metric_key = f"metric:{metric_name}:{time_bucket}"
            
            # Create metric data
            metric_data = {
                "value": value,
                "tags": tags or {},
                "timestamp": timestamp.isoformat(),
            }
            
            # Store metric in a sorted set with timestamp as score
            score = timestamp.timestamp()
            await client.zadd(metric_key, {json.dumps(metric_data): score})
            
            # Set expiration for the metric key (keep for 30 days)
            await client.expire(metric_key, 30 * 24 * 3600)
            
            # Also update real-time aggregates
            await self._update_real_time_aggregates(client, metric_name, value, tags)
            
        except Exception as e:
            self.logger.error(f"Error recording metric {metric_name}: {e}")
    
    async def get_metrics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        tags: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Get metrics within a time range."""
        try:
            client = await self._get_client()
            
            metrics = []
            
            # Get all time buckets in the range
            current_time = start_time.replace(minute=0, second=0, microsecond=0)
            end_bucket = end_time.replace(minute=0, second=0, microsecond=0)
            
            while current_time <= end_bucket:
                time_bucket = current_time.strftime("%Y%m%d%H")
                metric_key = f"metric:{metric_name}:{time_bucket}"
                
                # Get metrics in this time bucket
                start_score = start_time.timestamp()
                end_score = end_time.timestamp()
                
                results = await client.zrangebyscore(
                    metric_key,
                    start_score,
                    end_score,
                    withscores=True
                )
                
                for data, score in results:
                    try:
                        metric = json.loads(data)
                        
                        # Filter by tags if specified
                        if tags:
                            metric_tags = metric.get("tags", {})
                            if not all(metric_tags.get(k) == v for k, v in tags.items()):
                                continue
                        
                        metrics.append(metric)
                        
                    except json.JSONDecodeError:
                        continue
                
                current_time += timedelta(hours=1)
            
            # Sort by timestamp
            metrics.sort(key=lambda x: x.get("timestamp", ""))
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting metrics {metric_name}: {e}")
            return []
    
    async def get_aggregated_metrics(
        self,
        metric_name: str,
        aggregation: str,  # avg, sum, min, max, count
        start_time: datetime,
        end_time: datetime,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[Union[int, float]]:
        """Get aggregated metrics."""
        try:
            # Get all metrics in the range
            metrics = await self.get_metrics(metric_name, start_time, end_time, tags)
            
            if not metrics:
                return None
            
            values = [m["value"] for m in metrics]
            
            if aggregation == "avg":
                return sum(values) / len(values)
            elif aggregation == "sum":
                return sum(values)
            elif aggregation == "min":
                return min(values)
            elif aggregation == "max":
                return max(values)
            elif aggregation == "count":
                return len(values)
            else:
                raise ValueError(f"Unsupported aggregation: {aggregation}")
                
        except Exception as e:
            self.logger.error(f"Error getting aggregated metrics {metric_name}: {e}")
            return None
    
    async def delete_old_metrics(
        self, 
        cutoff_date: datetime
    ) -> int:
        """Delete metrics older than cutoff date. Returns count of deleted metrics."""
        try:
            client = await self._get_client()
            
            # Get all metric keys
            pattern = "metric:*"
            keys = await client.keys(pattern)
            
            deleted_count = 0
            
            for key in keys:
                # Extract timestamp from key
                parts = key.split(":")
                if len(parts) >= 3:
                    try:
                        time_bucket = parts[2]
                        bucket_time = datetime.strptime(time_bucket, "%Y%m%d%H")
                        
                        if bucket_time < cutoff_date:
                            result = await client.delete(key)
                            deleted_count += result
                            
                    except ValueError:
                        continue
            
            self.logger.info(f"Deleted {deleted_count} old metric keys")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error deleting old metrics: {e}")
            return 0
    
    async def _update_real_time_aggregates(
        self, 
        client, 
        metric_name: str, 
        value: Union[int, float], 
        tags: Optional[Dict[str, str]]
    ) -> None:
        """Update real-time aggregates for a metric."""
        try:
            # Create aggregate key
            tag_suffix = ""
            if tags:
                tag_suffix = ":" + ":".join(f"{k}={v}" for k, v in sorted(tags.items()))
            
            aggregate_key = f"aggregate:{metric_name}{tag_suffix}"
            
            # Update aggregates using Redis operations
            await client.hincrby(aggregate_key, "count", 1)
            await client.hincrbyfloat(aggregate_key, "sum", float(value))
            
            # Get current min/max
            current_min = await client.hget(aggregate_key, "min")
            current_max = await client.hget(aggregate_key, "max")
            
            # Update min
            if current_min is None or float(value) < float(current_min):
                await client.hset(aggregate_key, "min", str(value))
            
            # Update max
            if current_max is None or float(value) > float(current_max):
                await client.hset(aggregate_key, "max", str(value))
            
            # Set expiration for aggregates (keep for 7 days)
            await client.expire(aggregate_key, 7 * 24 * 3600)
            
        except Exception as e:
            self.logger.error(f"Error updating real-time aggregates: {e}")
    
    async def get_real_time_aggregates(
        self, 
        metric_name: str, 
        tags: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Get real-time aggregates for a metric."""
        try:
            client = await self._get_client()
            
            # Create aggregate key
            tag_suffix = ""
            if tags:
                tag_suffix = ":" + ":".join(f"{k}={v}" for k, v in sorted(tags.items()))
            
            aggregate_key = f"aggregate:{metric_name}{tag_suffix}"
            
            # Get all aggregate fields
            aggregates = await client.hgetall(aggregate_key)
            
            if not aggregates:
                return {}
            
            # Convert to appropriate types
            result = {}
            for key, value in aggregates.items():
                if key in ["sum", "min", "max"]:
                    result[key] = float(value)
                elif key == "count":
                    result[key] = int(value)
                else:
                    result[key] = value
            
            # Calculate average
            if "sum" in result and "count" in result and result["count"] > 0:
                result["avg"] = result["sum"] / result["count"]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting real-time aggregates: {e}")
            return {}
    
    async def close(self) -> None:
        """Close Redis connection."""
        try:
            if self._client and self._connected:
                await self._client.close()
                self._connected = False
                self.logger.info("Redis connection closed")
                
        except Exception as e:
            self.logger.error(f"Error closing Redis connection: {e}")


# In-memory metrics implementation as fallback
class InMemoryMetricsRepositoryImpl(MetricsRepository):
    """In-memory metrics implementation for development/testing."""
    
    def __init__(self):
        """Initialize in-memory metrics repository."""
        self.logger = logger
        self._metrics = []
        self._aggregates = {}
    
    async def record_metric(
        self, 
        metric_name: str, 
        value: Union[int, float],
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record a metric value."""
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
            
            metric_data = {
                "name": metric_name,
                "value": value,
                "tags": tags or {},
                "timestamp": timestamp,
            }
            
            self._metrics.append(metric_data)
            
            # Update aggregates
            await self._update_aggregates(metric_name, value, tags)
            
        except Exception as e:
            self.logger.error(f"Error recording in-memory metric {metric_name}: {e}")
    
    async def get_metrics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        tags: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Get metrics within a time range."""
        try:
            filtered_metrics = []
            
            for metric in self._metrics:
                if metric["name"] != metric_name:
                    continue
                
                metric_time = metric["timestamp"]
                if not (start_time <= metric_time <= end_time):
                    continue
                
                if tags:
                    metric_tags = metric.get("tags", {})
                    if not all(metric_tags.get(k) == v for k, v in tags.items()):
                        continue
                
                filtered_metrics.append({
                    "value": metric["value"],
                    "tags": metric["tags"],
                    "timestamp": metric["timestamp"].isoformat(),
                })
            
            return sorted(filtered_metrics, key=lambda x: x["timestamp"])
            
        except Exception as e:
            self.logger.error(f"Error getting in-memory metrics {metric_name}: {e}")
            return []
    
    async def get_aggregated_metrics(
        self,
        metric_name: str,
        aggregation: str,
        start_time: datetime,
        end_time: datetime,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[Union[int, float]]:
        """Get aggregated metrics."""
        try:
            metrics = await self.get_metrics(metric_name, start_time, end_time, tags)
            
            if not metrics:
                return None
            
            values = [m["value"] for m in metrics]
            
            if aggregation == "avg":
                return sum(values) / len(values)
            elif aggregation == "sum":
                return sum(values)
            elif aggregation == "min":
                return min(values)
            elif aggregation == "max":
                return max(values)
            elif aggregation == "count":
                return len(values)
            else:
                raise ValueError(f"Unsupported aggregation: {aggregation}")
                
        except Exception as e:
            self.logger.error(f"Error getting in-memory aggregated metrics {metric_name}: {e}")
            return None
    
    async def delete_old_metrics(
        self, 
        cutoff_date: datetime
    ) -> int:
        """Delete metrics older than cutoff date. Returns count of deleted metrics."""
        try:
            original_count = len(self._metrics)
            
            self._metrics = [
                m for m in self._metrics 
                if m["timestamp"] >= cutoff_date
            ]
            
            deleted_count = original_count - len(self._metrics)
            self.logger.info(f"Deleted {deleted_count} old in-memory metrics")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error deleting old in-memory metrics: {e}")
            return 0
    
    async def _update_aggregates(
        self, 
        metric_name: str, 
        value: Union[int, float], 
        tags: Optional[Dict[str, str]]
    ) -> None:
        """Update in-memory aggregates."""
        try:
            tag_suffix = ""
            if tags:
                tag_suffix = ":" + ":".join(f"{k}={v}" for k, v in sorted(tags.items()))
            
            aggregate_key = f"{metric_name}{tag_suffix}"
            
            if aggregate_key not in self._aggregates:
                self._aggregates[aggregate_key] = {
                    "count": 0,
                    "sum": 0.0,
                    "min": float('inf'),
                    "max": float('-inf'),
                }
            
            agg = self._aggregates[aggregate_key]
            agg["count"] += 1
            agg["sum"] += float(value)
            agg["min"] = min(agg["min"], float(value))
            agg["max"] = max(agg["max"], float(value))
            
        except Exception as e:
            self.logger.error(f"Error updating in-memory aggregates: {e}")


def create_metrics_repository() -> MetricsRepository:
    """Create appropriate metrics repository based on availability."""
    if REDIS_AVAILABLE:
        try:
            return MetricsRepositoryImpl()
        except Exception as e:
            logger.warning(f"Redis not available, falling back to in-memory metrics: {e}")
    
    logger.info("Using in-memory metrics")
    return InMemoryMetricsRepositoryImpl()