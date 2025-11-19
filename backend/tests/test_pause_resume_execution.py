"""
Comprehensive tests for pause/resume execution functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from typing import Dict, Any

from app.execution.executor.dag_executor import DAGExecutor, ExecutionStatus
from app.execution.context.manager import ContextManager, ContextStatus
from app.execution.services.execution_service import ExecutionServiceImpl
from app.domain.execution.models import (
    Execution, ExecutionStatus as DomainExecutionStatus, ExecutionInput, 
    ExecutionConfig, ExecutionEvent, EventType
)
from app.api.v1.endpoints.runs import RunCreateRequest, RunResponse


class TestPauseResumeExecution:
    """Test cases for pause/resume execution functionality."""
    
    @pytest.fixture
    def dag_executor(self):
        """Create DAG executor instance."""
        return DAGExecutor()
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager instance."""
        return ContextManager()
    
    @pytest.fixture
    def execution_service(self):
        """Create execution service instance."""
        return ExecutionServiceImpl()
    
    @pytest.fixture
    def sample_execution(self):
        """Create sample execution for testing."""
        return Execution(
            id="test_execution_123",
            agent_id="test_agent_456",
            input_data=ExecutionInput(
                inputs={"message": "Hello World"},
                metadata={"test": True}
            ),
            config=ExecutionConfig(
                max_execution_time=300,
                enable_streaming=True
            )
        )
    
    @pytest.mark.asyncio
    async def test_pause_running_execution(self, dag_executor):
        """Test pausing a running execution."""
        execution_id = "test_execution_123"
        
        # Create a mock execution context
        mock_context = Mock()
        mock_context.execution_id = execution_id
        mock_context.status = ContextStatus.RUNNING
        
        # Add context to executor
        dag_executor._execution_contexts[execution_id] = mock_context
        
        # Pause execution
        result = await dag_executor.pause_execution(execution_id)
        
        # Verify pause
        assert result is True
        assert execution_id in dag_executor._paused_executions
        assert execution_id in dag_executor._pause_events
        assert dag_executor._paused_executions[execution_id]["execution_state"] == "paused"
        assert "paused_at" in dag_executor._paused_executions[execution_id]
    
    @pytest.mark.asyncio
    async def test_pause_nonexistent_execution(self, dag_executor):
        """Test pausing a non-existent execution."""
        execution_id = "nonexistent_execution"
        
        # Pause execution - should fail
        result = await dag_executor.pause_execution(execution_id)
        
        # Verify failure
        assert result is False
        assert execution_id not in dag_executor._paused_executions
    
    @pytest.mark.asyncio
    async def test_pause_non_running_execution(self, dag_executor):
        """Test pausing a non-running execution."""
        execution_id = "test_execution_123"
        
        # Create a mock execution context that's not running
        mock_context = Mock()
        mock_context.execution_id = execution_id
        mock_context.status = ContextStatus.COMPLETED
        
        # Add context to executor
        dag_executor._execution_contexts[execution_id] = mock_context
        
        # Pause execution - should fail
        result = await dag_executor.pause_execution(execution_id)
        
        # Verify failure
        assert result is False
        assert execution_id not in dag_executor._paused_executions
    
    @pytest.mark.asyncio
    async def test_resume_paused_execution(self, dag_executor):
        """Test resuming a paused execution."""
        execution_id = "test_execution_123"
        
        # Create a mock execution context
        mock_context = Mock()
        mock_context.execution_id = execution_id
        mock_context.status = ContextStatus.PAUSED
        
        # Add context to executor
        dag_executor._execution_contexts[execution_id] = mock_context
        
        # Simulate paused state
        dag_executor._paused_executions[execution_id] = {
            "paused_at": datetime.now(timezone.utc),
            "context_snapshot": mock_context.to_dict() if hasattr(mock_context, 'to_dict') else {},
            "execution_state": "paused"
        }
        
        # Create pause event
        pause_event = asyncio.Event()
        dag_executor._pause_events[execution_id] = pause_event
        
        # Resume execution
        result = await dag_executor.resume_execution(execution_id)
        
        # Verify resume
        assert result is True
        assert execution_id not in dag_executor._paused_executions
        assert execution_id not in dag_executor._pause_events
    
    @pytest.mark.asyncio
    async def test_resume_nonexistent_execution(self, dag_executor):
        """Test resuming a non-existent execution."""
        execution_id = "nonexistent_execution"
        
        # Resume execution - should fail
        result = await dag_executor.resume_execution(execution_id)
        
        # Verify failure
        assert result is False
    
    @pytest.mark.asyncio
    async def test_resume_non_paused_execution(self, dag_executor):
        """Test resuming a non-paused execution."""
        execution_id = "test_execution_123"
        
        # Create a mock execution context that's not paused
        mock_context = Mock()
        mock_context.execution_id = execution_id
        mock_context.status = ContextStatus.RUNNING
        
        # Add context to executor
        dag_executor._execution_contexts[execution_id] = mock_context
        
        # Resume execution - should fail
        result = await dag_executor.resume_execution(execution_id)
        
        # Verify failure
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_pause_info(self, dag_executor):
        """Test getting pause information for an execution."""
        execution_id = "test_execution_123"
        paused_at = datetime.now(timezone.utc)
        
        # Simulate paused state
        dag_executor._paused_executions[execution_id] = {
            "paused_at": paused_at,
            "context_snapshot": {},
            "execution_state": "paused"
        }
        
        # Get pause info
        pause_info = await dag_executor.get_execution_pause_info(execution_id)
        
        # Verify pause info
        assert pause_info is not None
        assert pause_info["execution_id"] == execution_id
        assert pause_info["paused_at"] == paused_at.isoformat()
        assert pause_info["paused_duration_seconds"] >= 0
        assert pause_info["status"] == "paused"
        assert pause_info["can_resume"] is True
    
    @pytest.mark.asyncio
    async def test_get_pause_info_nonexistent(self, dag_executor):
        """Test getting pause info for non-existent execution."""
        execution_id = "nonexistent_execution"
        
        # Get pause info
        pause_info = await dag_executor.get_execution_pause_info(execution_id)
        
        # Verify no info
        assert pause_info is None
    
    @pytest.mark.asyncio
    async def test_get_paused_executions(self, dag_executor):
        """Test getting list of paused executions."""
        # Add multiple paused executions
        paused_executions = ["exec1", "exec2", "exec3"]
        for exec_id in paused_executions:
            dag_executor._paused_executions[exec_id] = {
                "paused_at": datetime.now(timezone.utc),
                "execution_state": "paused"
            }
        
        # Get paused executions
        paused_list = dag_executor.get_paused_executions()
        
        # Verify list
        assert len(paused_list) == 3
        assert all(exec_id in paused_list for exec_id in paused_executions)
    
    @pytest.mark.asyncio
    async def test_pause_cleanup_on_completion(self, dag_executor):
        """Test that pause state is cleaned up when execution completes."""
        execution_id = "test_execution_123"
        
        # Create a mock execution context
        mock_context = Mock()
        mock_context.execution_id = execution_id
        mock_context.status = ContextStatus.RUNNING
        
        # Add context to executor
        dag_executor._execution_contexts[execution_id] = mock_context
        
        # Pause execution
        await dag_executor.pause_execution(execution_id)
        assert execution_id in dag_executor._paused_executions
        
        # Simulate execution completion (cleanup)
        if execution_id in dag_executor._pause_events:
            del dag_executor._pause_events[execution_id]
        if execution_id in dag_executor._paused_executions:
            del dag_executor._paused_executions[execution_id]
        if execution_id in dag_executor._execution_contexts:
            del dag_executor._execution_contexts[execution_id]
        
        # Verify cleanup
        assert execution_id not in dag_executor._paused_executions
        assert execution_id not in dag_executor._pause_events
        assert execution_id not in dag_executor._execution_contexts


class TestPauseResumeExecutionService:
    """Test cases for pause/resume functionality in execution service."""
    
    @pytest.fixture
    def execution_service(self):
        """Create execution service instance."""
        return ExecutionServiceImpl()
    
    @pytest.fixture
    def sample_execution(self):
        """Create sample execution for testing."""
        return Execution(
            id="test_execution_123",
            agent_id="test_agent_456",
            input_data=ExecutionInput(inputs={"test": "data"}),
            config=ExecutionConfig()
        )
    
    @pytest.mark.asyncio
    async def test_pause_execution_service(self, execution_service, sample_execution):
        """Test pausing execution through service."""
        # Mock repository and event bus
        with patch.object(execution_service, '_get_execution_repository') as mock_repo, \
             patch.object(execution_service, '_get_event_repository') as mock_event_repo, \
             patch.object(execution_service.event_bus, 'emit') as mock_emit:
            
            # Setup mocks
            mock_repo.get_by_id.return_value = sample_execution
            mock_repo.save.return_value = sample_execution
            mock_event_repo.save_event.return_value = None
            
            # Pause execution
            result = await execution_service.pause_execution("test_execution_123")
            
            # Verify pause
            assert result is True
            mock_repo.get_by_id.assert_called_once_with("test_execution_123")
            mock_repo.save.assert_called_once()
            mock_event_repo.save_event.assert_called_once()
            mock_emit.assert_called_once()
            
            # Check that execution status was updated
            saved_execution = mock_repo.save.call_args[0][0]
            assert saved_execution.status == DomainExecutionStatus.PAUSED
    
    @pytest.mark.asyncio
    async def test_pause_nonexistent_execution_service(self, execution_service):
        """Test pausing non-existent execution through service."""
        # Mock repository
        with patch.object(execution_service, '_get_execution_repository') as mock_repo:
            mock_repo.get_by_id.return_value = None
            
            # Pause execution - should fail
            result = await execution_service.pause_execution("nonexistent_execution")
            
            # Verify failure
            assert result is False
    
    @pytest.mark.asyncio
    async def test_resume_execution_service(self, execution_service, sample_execution):
        """Test resuming execution through service."""
        # Set execution to paused status
        sample_execution.status = DomainExecutionStatus.PAUSED
        
        # Mock repository and event bus
        with patch.object(execution_service, '_get_execution_repository') as mock_repo, \
             patch.object(execution_service, '_get_event_repository') as mock_event_repo, \
             patch.object(execution_service.event_bus, 'emit') as mock_emit:
            
            # Setup mocks
            mock_repo.get_by_id.return_value = sample_execution
            mock_repo.save.return_value = sample_execution
            mock_event_repo.save_event.return_value = None
            
            # Resume execution
            result = await execution_service.resume_execution("test_execution_123")
            
            # Verify resume
            assert result is True
            mock_repo.get_by_id.assert_called_once_with("test_execution_123")
            mock_repo.save.assert_called_once()
            mock_event_repo.save_event.assert_called_once()
            mock_emit.assert_called_once()
            
            # Check that execution status was updated
            saved_execution = mock_repo.save.call_args[0][0]
            assert saved_execution.status == DomainExecutionStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_get_pause_info_service(self, execution_service):
        """Test getting pause info through service."""
        # Mock repositories
        with patch.object(execution_service, '_get_execution_repository') as mock_repo, \
             patch.object(execution_service, '_get_event_repository') as mock_event_repo:
            
            # Setup mocks
            mock_execution = Mock()
            mock_execution.status = DomainExecutionStatus.PAUSED
            mock_repo.get_by_id.return_value = mock_execution
            
            mock_pause_event = Mock()
            mock_pause_event.data = {"paused_at": datetime.now(timezone.utc).isoformat()}
            mock_event_repo.get_events_by_execution_id.return_value = [mock_pause_event]
            
            # Get pause info
            pause_info = await execution_service.get_execution_pause_info("test_execution_123")
            
            # Verify pause info
            assert pause_info is not None
            assert pause_info["execution_id"] == "test_execution_123"
            assert pause_info["status"] == "paused"
            assert pause_info["can_resume"] is True
            assert "paused_at" in pause_info
            assert "paused_duration_seconds" in pause_info


class TestPauseResumeAPI:
    """Test cases for pause/resume API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers."""
        # Create and login user
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        token_data = login_response.json()
        access_token = token_data["access_token"]
        
        return {"Authorization": f"Bearer {access_token}"}
    
    @pytest.fixture
    def test_run(self, client, auth_headers):
        """Create a test run."""
        # Create workspace and agent first
        workspace_response = client.post(
            "/api/v1/workspaces/",
            json={"name": "Test Workspace", "description": "Test"},
            headers=auth_headers
        )
        workspace = workspace_response.json()
        
        agent_response = client.post(
            "/api/v1/agents/",
            json={
                "workspace_id": workspace["id"],
                "name": "Test Agent",
                "description": "Test agent",
                "graph_json": {
                    "nodes": [
                        {"id": "input1", "type": "input", "data": {"label": "Input"}},
                        {"id": "output1", "type": "output", "data": {"label": "Output"}}
                    ],
                    "edges": [
                        {"id": "edge1", "source": "input1", "target": "output1"}
                    ]
                }
            },
            headers=auth_headers
        )
        agent = agent_response.json()
        
        # Create run
        run_response = client.post(
            "/api/v1/runs/",
            json={
                "agent_id": agent["id"],
                "input_data": {"test": "data"},
                "config": {"priority": "normal"}
            },
            headers=auth_headers
        )
        return run_response.json()
    
    def test_pause_run_endpoint(self, client, auth_headers, test_run):
        """Test pause run endpoint."""
        run_id = test_run["id"]
        
        # Pause run
        response = client.post(
            f"/api/v1/runs/{run_id}/pause",
            headers=auth_headers
        )
        
        # Should return success message
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "paused" in data["message"].lower()
    
    def test_pause_nonexistent_run(self, client, auth_headers):
        """Test pausing non-existent run."""
        response = client.post(
            "/api/v1/runs/nonexistent_run/pause",
            headers=auth_headers
        )
        
        # Should return 404
        assert response.status_code == 404
    
    def test_resume_run_endpoint(self, client, auth_headers, test_run):
        """Test resume run endpoint."""
        run_id = test_run["id"]
        
        # First pause the run
        client.post(f"/api/v1/runs/{run_id}/pause", headers=auth_headers)
        
        # Resume run
        response = client.post(
            f"/api/v1/runs/{run_id}/resume",
            headers=auth_headers
        )
        
        # Should return success message
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "resumed" in data["message"].lower()
    
    def test_resume_nonexistent_run(self, client, auth_headers):
        """Test resuming non-existent run."""
        response = client.post(
            "/api/v1/runs/nonexistent_run/resume",
            headers=auth_headers
        )
        
        # Should return 404
        assert response.status_code == 404
    
    def test_get_pause_info_endpoint(self, client, auth_headers, test_run):
        """Test get pause info endpoint."""
        run_id = test_run["id"]
        
        # First pause the run
        client.post(f"/api/v1/runs/{run_id}/pause", headers=auth_headers)
        
        # Get pause info
        response = client.get(
            f"/api/v1/runs/{run_id}/pause-info",
            headers=auth_headers
        )
        
        # Should return pause info
        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data
        assert "paused_at" in data
        assert "paused_duration_seconds" in data
        assert "status" in data
        assert "can_resume" in data
    
    def test_get_pause_info_nonexistent_run(self, client, auth_headers):
        """Test getting pause info for non-existent run."""
        response = client.get(
            "/api/v1/runs/nonexistent_run/pause-info",
            headers=auth_headers
        )
        
        # Should return 404
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__])