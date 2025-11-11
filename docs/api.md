# PromptFlow API Documentation

## Overview

PromptFlow provides a comprehensive REST API for building AI agents through visual workflows. The API follows RESTful principles and uses JSON for data exchange.

## Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication:

### 1. Register a User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123",
  "full_name": "John Doe"
}
```

### 2. Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

### 3. Use Token in Requests
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## API Endpoints

### Authentication Endpoints

#### Register User
- **Endpoint:** `POST /api/v1/auth/register`
- **Description:** Create a new user account
- **Body:**
```json
{
  "email": "string",
  "password": "string", 
  "full_name": "string"
}
```

#### Login
- **Endpoint:** `POST /api/v1/auth/login`
- **Description:** Authenticate user and get access token
- **Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

#### Refresh Token
- **Endpoint:** `POST /api/v1/auth/refresh`
- **Description:** Get new access token using refresh token
- **Headers:** `Authorization: Bearer <refresh_token>`

#### Logout
- **Endpoint:** `POST /api/v1/auth/logout`
- **Description:** Logout user and invalidate token
- **Headers:** `Authorization: Bearer <access_token>`

### User Management Endpoints

#### Get Current User
- **Endpoint:** `GET /api/v1/users/me`
- **Description:** Get current user profile
- **Headers:** `Authorization: Bearer <access_token>`

#### Update Current User
- **Endpoint:** `PUT /api/v1/users/me`
- **Description:** Update current user profile
- **Headers:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "full_name": "string",
  "email": "string"
}
```

### Workspace Endpoints

#### List Workspaces
- **Endpoint:** `GET /api/v1/workspaces`
- **Description:** Get user's workspaces
- **Headers:** `Authorization: Bearer <access_token>`
- **Response:**
```json
[
  {
    "id": "ws_123",
    "name": "My Workspace",
    "description": "Personal workspace",
    "role": "owner",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### Create Workspace
- **Endpoint:** `POST /api/v1/workspaces`
- **Description:** Create a new workspace
- **Headers:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "name": "string",
  "description": "string"
}
```

#### Get Workspace
- **Endpoint:** `GET /api/v1/workspaces/{workspace_id}`
- **Description:** Get workspace by ID
- **Headers:** `Authorization: Bearer <access_token>`

### Agent Endpoints

#### List Agents
- **Endpoint:** `GET /api/v1/agents`
- **Description:** Get agents in workspace
- **Headers:** `Authorization: Bearer <access_token>`
- **Query Parameters:**
  - `workspace_id` (string): Filter by workspace

#### Create Agent
- **Endpoint:** `POST /api/v1/agents`
- **Description:** Create a new AI agent
- **Headers:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "name": "string",
  "description": "string",
  "workspace_id": "string",
  "graph_json": {
    "nodes": [],
    "edges": []
  }
}
```

#### Get Agent
- **Endpoint:** `GET /api/v1/agents/{agent_id}`
- **Description:** Get agent by ID
- **Headers:** `Authorization: Bearer <access_token>`

#### Update Agent
- **Endpoint:** `PUT /api/v1/agents/{agent_id}`
- **Description:** Update agent configuration
- **Headers:** `Authorization: Bearer <access_token>`

#### Delete Agent
- **Endpoint:** `DELETE /api/v1/agents/{agent_id}`
- **Description:** Delete an agent
- **Headers:** `Authorization: Bearer <access_token>`

### Dataset Endpoints

#### List Datasets
- **Endpoint:** `GET /api/v1/datasets`
- **Description:** Get datasets in workspace
- **Headers:** `Authorization: Bearer <access_token>`

#### Create Dataset
- **Endpoint:** `POST /api/v1/datasets`
- **Description:** Create a new dataset
- **Headers:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "name": "string",
  "description": "string",
  "workspace_id": "string",
  "vector_store": "qdrant",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

#### Upload File to Dataset
- **Endpoint:** `POST /api/v1/datasets/{dataset_id}/upload`
- **Description:** Upload files to dataset
- **Headers:** `Authorization: Bearer <access_token>`
- **Content-Type:** `multipart/form-data`
- **Body:**
```
file: <binary_data>
```

#### Ingest Dataset
- **Endpoint:** `POST /api/v1/datasets/{dataset_id}/ingest`
- **Description:** Start document processing and embedding
- **Headers:** `Authorization: Bearer <access_token>`

### Run Endpoints

#### Create Agent Run
- **Endpoint:** `POST /api/v1/runs`
- **Description:** Execute an agent
- **Headers:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "agent_id": "string",
  "input_data": {
    "query": "string",
    "variables": {}
  }
}
```

#### Get Run
- **Endpoint:** `GET /api/v1/runs/{run_id}`
- **Description:** Get run status and results
- **Headers:** `Authorization: Bearer <access_token>`

#### List Runs
- **Endpoint:** `GET /api/v1/runs`
- **Description:** Get runs for an agent
- **Headers:** `Authorization: Bearer <access_token>`
- **Query Parameters:**
  - `agent_id` (string): Filter by agent
  - `status` (string): Filter by status

#### Get Run Events
- **Endpoint:** `GET /api/v1/runs/{run_id}/events`
- **Description:** Get detailed execution events
- **Headers:** `Authorization: Bearer <access_token>`

#### Cancel Run
- **Endpoint:** `POST /api/v1/runs/{run_id}/cancel`
- **Description:** Cancel a running agent
- **Headers:** `Authorization: Bearer <access_token>`

## WebSocket Streaming

For real-time agent execution, use WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/runs/{run_id}/stream');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Event:', data);
};
```

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Rate Limiting

- **Limit:** 60 requests per minute
- **Burst:** 10 requests per second
- **Headers:** Rate limit info included in responses

## Pagination

List endpoints support pagination:

```http
GET /api/v1/agents?page=1&size=20&sort=created_at&order=desc
```

**Response:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

## Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive API exploration with OpenAPI/Swagger.