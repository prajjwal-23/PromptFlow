"""
Agent endpoint tests.
"""

import pytest
from fastapi import status


class TestAgents:
    """Test agent endpoints."""
    
    def test_get_agents(self, client, auth_headers, test_agent, test_workspace):
        """Test getting user agents."""
        response = client.get(
            "/api/v1/agents",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check agent structure
        agent = next((a for a in data if a["id"] == str(test_agent.id)), None)
        assert agent is not None
        assert agent["name"] == test_agent.name
        assert agent["description"] == test_agent.description
        assert agent["workspace_id"] == str(test_workspace.id)
        assert agent["is_active"] is True
        assert agent["version"] == test_agent.version
    
    def test_get_agents_workspace_filter(self, client, auth_headers, test_agent, test_workspace):
        """Test getting agents with workspace filter."""
        response = client.get(
            f"/api/v1/agents?workspace_id={test_workspace.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == str(test_agent.id)
    
    def test_get_agents_no_auth(self, client):
        """Test getting agents without authentication."""
        response = client.get("/api/v1/agents")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_agents_workspace_no_access(self, client, auth_headers2):
        """Test getting agents from workspace without access."""
        response = client.get(
            "/api/v1/agents?workspace_id=some-workspace-id",
            headers=auth_headers2
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_agent(self, client, auth_headers, test_workspace):
        """Test creating a new agent."""
        agent_data = {
            "name": "New Agent",
            "description": "A new agent for testing",
            "workspace_id": str(test_workspace.id),
            "graph_json": {
                "nodes": [
                    {"id": "node1", "type": "input", "data": {"label": "Start"}},
                    {"id": "node2", "type": "llm", "data": {"label": "LLM Node"}}
                ],
                "edges": [
                    {"id": "edge1", "source": "node1", "target": "node2"}
                ]
            }
        }
        
        response = client.post(
            "/api/v1/agents",
            headers=auth_headers,
            json=agent_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Agent"
        assert data["description"] == "A new agent for testing"
        assert data["workspace_id"] == str(test_workspace.id)
        assert data["is_active"] is True
        assert data["graph_json"] == agent_data["graph_json"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_agent_no_workspace_access(self, client, auth_headers2):
        """Test creating agent without workspace access."""
        response = client.post(
            "/api/v1/agents",
            headers=auth_headers2,
            json={
                "name": "New Agent",
                "workspace_id": "some-workspace-id",
                "graph_json": {"nodes": [], "edges": []}
            }
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_agent_invalid_graph(self, client, auth_headers, test_workspace):
        """Test creating agent with invalid graph."""
        response = client.post(
            "/api/v1/agents",
            headers=auth_headers,
            json={
                "name": "Invalid Agent",
                "workspace_id": str(test_workspace.id),
                "graph_json": {"invalid": "structure"}
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_agent(self, client, auth_headers, test_agent):
        """Test getting a specific agent."""
        response = client.get(
            f"/api/v1/agents/{test_agent.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_agent.id)
        assert data["name"] == test_agent.name
        assert data["description"] == test_agent.description
        assert data["workspace_id"] == str(test_agent.workspace_id)
    
    def test_get_agent_no_access(self, client, auth_headers2, test_agent):
        """Test getting agent without access."""
        response = client.get(
            f"/api/v1/agents/{test_agent.id}",
            headers=auth_headers2
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_agent_not_found(self, client, auth_headers):
        """Test getting nonexistent agent."""
        response = client.get(
            "/api/v1/agents/nonexistent-id",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_agent(self, client, auth_headers, test_agent):
        """Test updating agent."""
        response = client.put(
            f"/api/v1/agents/{test_agent.id}",
            headers=auth_headers,
            json={
                "name": "Updated Agent",
                "description": "Updated description",
                "is_active": False
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Agent"
        assert data["description"] == "Updated description"
        assert data["is_active"] is False
    
    def test_update_agent_no_access(self, client, auth_headers2, test_agent):
        """Test updating agent without access."""
        response = client.put(
            f"/api/v1/agents/{test_agent.id}",
            headers=auth_headers2,
            json={"name": "Updated Agent"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_agent(self, client, auth_headers, test_agent, db_session):
        """Test deleting agent."""
        response = client.delete(
            f"/api/v1/agents/{test_agent.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_delete_agent_no_access(self, client, auth_headers2, test_agent):
        """Test deleting agent without access."""
        response = client.delete(
            f"/api/v1/agents/{test_agent.id}",
            headers=auth_headers2
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_duplicate_agent(self, client, auth_headers, test_agent):
        """Test duplicating an agent."""
        response = client.post(
            f"/api/v1/agents/{test_agent.id}/duplicate",
            headers=auth_headers,
            json={"name": "Duplicated Agent"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Duplicated Agent"
        assert data["description"] == test_agent.description
        assert data["workspace_id"] == str(test_agent.workspace_id)
        assert data["graph_json"] == test_agent.graph_json
        assert data["id"] != str(test_agent.id)
        assert data["created_by"] == test_agent.created_by
    
    def test_duplicate_agent_duplicate_name(self, client, auth_headers, test_agent, test_workspace):
        """Test duplicating agent with duplicate name."""
        response = client.post(
            f"/api/v1/agents/{test_agent.id}/duplicate",
            headers=auth_headers,
            json={"name": test_agent.name}  # Same name as original
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]
    
    def test_duplicate_agent_no_access(self, client, auth_headers2, test_agent):
        """Test duplicating agent without access."""
        response = client.post(
            f"/api/v1/agents/{test_agent.id}/duplicate",
            headers=auth_headers2,
            json={"name": "Duplicated Agent"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_agent_complex_graph(self, client, auth_headers, test_workspace):
        """Test creating agent with complex graph."""
        complex_graph = {
            "nodes": [
                {
                    "id": "input_1",
                    "type": "input",
                    "data": {"label": "User Input", "type": "text"},
                    "position": {"x": 100, "y": 100}
                },
                {
                    "id": "retrieval_1",
                    "type": "retrieval",
                    "data": {"label": "Knowledge Retrieval", "dataset_id": "dataset_1"},
                    "position": {"x": 300, "y": 100}
                },
                {
                    "id": "llm_1",
                    "type": "llm",
                    "data": {"label": "Main LLM", "model": "gpt-3.5-turbo"},
                    "position": {"x": 500, "y": 100}
                },
                {
                    "id": "output_1",
                    "type": "output",
                    "data": {"label": "Final Output", "type": "text"},
                    "position": {"x": 700, "y": 100}
                }
            ],
            "edges": [
                {"id": "edge_1", "source": "input_1", "target": "retrieval_1"},
                {"id": "edge_2", "source": "retrieval_1", "target": "llm_1"},
                {"id": "edge_3", "source": "input_1", "target": "llm_1"},
                {"id": "edge_4", "source": "llm_1", "target": "output_1"}
            ]
        }
        
        response = client.post(
            "/api/v1/agents",
            headers=auth_headers,
            json={
                "name": "Complex Agent",
                "workspace_id": str(test_workspace.id),
                "graph_json": complex_graph
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Complex Agent"
        assert data["graph_json"] == complex_graph