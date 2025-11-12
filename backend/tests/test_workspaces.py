"""
Workspace endpoint tests.
"""

import pytest
from fastapi import status


class TestWorkspaces:
    """Test workspace endpoints."""
    
    def test_get_workspaces(self, client, auth_headers, test_workspace):
        """Test getting user workspaces."""
        response = client.get(
            "/api/v1/workspaces",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check workspace structure
        workspace = next((w for w in data if w["id"] == str(test_workspace.id)), None)
        assert workspace is not None
        assert workspace["name"] == test_workspace.name
        assert workspace["description"] == test_workspace.description
        assert workspace["role"] == "owner"
        assert workspace["member_count"] == 1
    
    def test_get_workspaces_no_auth(self, client):
        """Test getting workspaces without authentication."""
        response = client.get("/api/v1/workspaces")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_workspace(self, client, auth_headers):
        """Test creating a new workspace."""
        response = client.post(
            "/api/v1/workspaces",
            headers=auth_headers,
            json={
                "name": "New Workspace",
                "description": "A new workspace for testing"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Workspace"
        assert data["description"] == "A new workspace for testing"
        assert data["role"] == "owner"
        assert data["member_count"] == 1
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_workspace_invalid_name(self, client, auth_headers):
        """Test creating workspace with invalid name."""
        response = client.post(
            "/api/v1/workspaces",
            headers=auth_headers,
            json={
                "name": "x",  # Too short
                "description": "A new workspace"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_workspace_no_auth(self, client):
        """Test creating workspace without authentication."""
        response = client.post(
            "/api/v1/workspaces",
            json={
                "name": "New Workspace",
                "description": "A new workspace"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_workspace(self, client, auth_headers, test_workspace):
        """Test getting a specific workspace."""
        response = client.get(
            f"/api/v1/workspaces/{test_workspace.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_workspace.id)
        assert data["name"] == test_workspace.name
        assert data["description"] == test_workspace.description
        assert data["role"] == "owner"
        assert data["member_count"] == 1
    
    def test_get_workspace_no_access(self, client, auth_headers2, test_workspace):
        """Test getting workspace without access."""
        response = client.get(
            f"/api/v1/workspaces/{test_workspace.id}",
            headers=auth_headers2
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_workspace_not_found(self, client, auth_headers):
        """Test getting nonexistent workspace."""
        response = client.get(
            "/api/v1/workspaces/nonexistent-id",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_workspace(self, client, auth_headers, test_workspace):
        """Test updating workspace."""
        response = client.put(
            f"/api/v1/workspaces/{test_workspace.id}",
            headers=auth_headers,
            json={
                "name": "Updated Workspace",
                "description": "Updated description"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Workspace"
        assert data["description"] == "Updated description"
    
    def test_update_workspace_member_access(self, client, auth_headers2, workspace_with_member):
        """Test updating workspace as member (should fail)."""
        response = client.put(
            f"/api/v1/workspaces/{workspace_with_member.workspace_id}",
            headers=auth_headers2,
            json={
                "name": "Updated Workspace"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_workspace(self, client, auth_headers, test_workspace, db_session):
        """Test deleting workspace."""
        response = client.delete(
            f"/api/v1/workspaces/{test_workspace.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_delete_workspace_member_access(self, client, auth_headers2, workspace_with_member):
        """Test deleting workspace as member (should fail)."""
        response = client.delete(
            f"/api/v1/workspaces/{workspace_with_member.workspace_id}",
            headers=auth_headers2
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestWorkspaceMembers:
    """Test workspace member management."""
    
    def test_get_workspace_members(self, client, auth_headers, test_workspace, workspace_with_member):
        """Test getting workspace members."""
        response = client.get(
            f"/api/v1/workspaces/{test_workspace.id}/members",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Check member structure
        member_emails = [member["email"] for member in data]
        assert "test@example.com" in member_emails
        assert "test2@example.com" in member_emails
    
    def test_add_workspace_member(self, client, auth_headers, test_workspace, test_user2):
        """Test adding a member to workspace."""
        response = client.post(
            f"/api/v1/workspaces/{test_workspace.id}/members",
            headers=auth_headers,
            json={
                "email": test_user2.email,
                "role": "member"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == test_user2.email
        assert data["full_name"] == test_user2.full_name
        assert data["role"] == "member"
    
    def test_add_workspace_member_admin_access(self, client, auth_headers2, test_workspace):
        """Test adding member as admin (should fail)."""
        response = client.post(
            f"/api/v1/workspaces/{test_workspace.id}/members",
            headers=auth_headers2,
            json={
                "email": "new@example.com",
                "role": "member"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_add_nonexistent_user(self, client, auth_headers, test_workspace):
        """Test adding nonexistent user."""
        response = client.post(
            f"/api/v1/workspaces/{test_workspace.id}/members",
            headers=auth_headers,
            json={
                "email": "nonexistent@example.com",
                "role": "member"
            }
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_member_role(self, client, auth_headers, workspace_with_member):
        """Test updating member role."""
        response = client.put(
            f"/api/v1/workspaces/{workspace_with_member.workspace_id}/members/{workspace_with_member.user_id}",
            headers=auth_headers,
            json={
                "role": "admin"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "admin"
    
    def test_update_member_role_admin_access(self, client, auth_headers2, workspace_with_member):
        """Test updating member role as admin."""
        response = client.put(
            f"/api/v1/workspaces/{workspace_with_member.workspace_id}/members/{workspace_with_member.user_id}",
            headers=auth_headers2,
            json={
                "role": "admin"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_remove_workspace_member(self, client, auth_headers, workspace_with_member):
        """Test removing workspace member."""
        response = client.delete(
            f"/api/v1/workspaces/{workspace_with_member.workspace_id}/members/{workspace_with_member.user_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_remove_workspace_owner(self, client, auth_headers, test_workspace):
        """Test removing workspace owner (should fail)."""
        response = client.delete(
            f"/api/v1/workspaces/{test_workspace.id}/members/{test_workspace.created_by}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot remove workspace owner" in response.json()["detail"]