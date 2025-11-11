
# PromptFlow Developer Guide

This guide helps developers understand, contribute to, and extend the PromptFlow codebase. Whether you're setting up the development environment or building new features, you'll find the necessary information here.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Development Setup](#development-setup)
3. [Architecture Overview](#architecture-overview)
4. [Backend Development](#backend-development)
5. [Frontend Development](#frontend-development)
6. [Database Schema](#database-schema)
7. [API Development](#api-development)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Contributing Guidelines](#contributing-guidelines)

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose** for containerized services
- **Python 3.11+** for backend development
- **Node.js 18+** and **npm** for frontend development
- **Git** for version control
- **VS Code** (recommended) with suggested extensions

### One-Command Setup

```bash
# Clone and setup everything
git clone https://github.com/prajjwal-23/PromptFlow.git
cd PromptFlow
make setup
make dev
```

This will:
1. Start all infrastructure services (PostgreSQL, Redis, MinIO, Qdrant)
2. Set up Python virtual environment and install dependencies
3. Install frontend packages
4. Start both backend and frontend development servers

## Development Setup

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create database migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Infrastructure Services

```bash
# Start all services
docker-compose up -d postgres redis minio qdrant

# Check service status
docker-compose ps

# View logs
docker-compose logs -f postgres
```

### 4. Development Environment Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Configure the following variables:

```env
# Database
DATABASE_URL=postgresql://promptflow:promptflow123@localhost:5432/promptflow

# Redis
REDIS_URL=redis://localhost:6379

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=promptflow
MINIO_SECRET_KEY=promptflow123

# Qdrant
QDRANT_URL=http://localhost:6333

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama
OLLAMA_URL=http://localhost:11434
```

## Architecture Overview

PromptFlow follows a modular microservices architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │  Infrastructure │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│     Services    │
│                 │    │                 │    │                 │
│ • React Flow    │    │ • REST APIs     │    │ • PostgreSQL    │
│ • Zustand       │    │ • WebSocket     │    │ • Redis         │
│ • Tailwind      │    │ • Graph Executor│    │ • MinIO         │
│                 │    │ • Celery        │    │ • Qdrant        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

1. **Frontend**: SPA with visual canvas for agent building
2. **Backend**: RESTful API with real-time WebSocket support
3. **Graph Executor**: Converts visual workflows to executable DAGs
4. **RAG Pipeline**: Document processing and vector search
5. **Infrastructure**: Containerized services for data and storage

## Backend Development

### Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   └
── v1/
│   │       └── endpoints/
│   ├── core/             # Core configuration
│   ├── middleware/       # Custom middleware
│   ├── models/           # SQLAlchemy models
│   └── main.py          # FastAPI application
├── alembic/              # Database migrations
├── requirements.txt      # Python dependencies
└── Dockerfile           # Container configuration
```

### Core Models

The backend uses SQLAlchemy for ORM with the following main models:

#### User Model
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### Agent Model
```python
class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    graph_json = Column(JSON)  # React Flow graph data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### API Development

#### Creating New Endpoints

1. Create a new file in `backend/app/api/v1/endpoints/`
2. Define your endpoint using FastAPI decorators

```python
# backend/app/api/v1/endpoints/example.py
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/example")
async def get_example(
    current_user: User = Depends(get_current_user)
):
    return {"message": "Hello", "user": current_user.email}
```

3. Register the router in `backend/app/api/v1/api.py`

```python
from app.api.v1.endpoints import example

api_router.include_router(example.router, prefix="/example", tags=["example"])
```

#### Dependency Injection

FastAPI's dependency injection is used for:

- **Authentication**: `get_current_user`
- **Database**: `get_db`
- **Workspace Access**: `get_workspace`
- **Rate Limiting**: `rate_limiter`

### Graph Executor

The graph executor converts React Flow JSON to executable DAGs:

```python
# Node execution interface
class Node(Protocol):
    id: str
    type: str
    config: dict
    
    async def run(self, ctx: Context, inputs: dict) -> dict:
        ...

# Context object
@dataclass
class Context:
    run_id: UUID
    workspace_id: UUID
    logger: RunLogger
    tools: ToolRegistry
    datasets: DatasetService
    model: OllamaClient
```

#### Adding New Node Types

1. Create a new node class implementing the `Node` protocol
2. Register it in the `NODE_TYPES` registry

```python
class LLMNode:
    def __init__(self, id: str, config: dict):
        self.id = id
        self.config = config
    
    async def run(self, ctx: Context, inputs: dict) -> dict:
        # LLM implementation
        response = await ctx.model.chat(
            model=self.config["model"],
            messages=inputs["messages"],
            temperature=self.config.get("temperature", 0.7)
        )
        return {"response": response}

# Register the node
NODE_TYPES["llm"] = LLMNode
```

## Frontend Development

### Project Structure

```
frontend/
├── app/
│   ├── components/       # Reusable components
│   ├── pages/           # Page components
│   ├── hooks/           # Custom hooks
│   ├── store/           # Zustand store
│   ├── types/           # TypeScript types
│   ├── utils/           # Utility functions
│   ├── layout.tsx       # Root layout
│   └── page.tsx         # Home page
├── public/              # Static assets
├── package.json         # Dependencies
└── Dockerfile          # Container configuration
```

### State Management

PromptFlow uses Zustand for state management:

```typescript
// app/store/workspaceStore.ts
interface WorkspaceState {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  isLoading: boolean;
  
  fetchWorkspaces: () => Promise<void>;
  setCurrentWorkspace: (workspace: Workspace) => void;
  createWorkspace: (data: CreateWorkspaceData) => Promise<void>;
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  workspaces: [],
  currentWorkspace: null,
  isLoading: false,
  
  fetchWorkspaces: async () => {
    set({ isLoading: true });
    try {
      const workspaces = await api.getWorkspaces();
      set({ workspaces, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
  
  // ... other methods
}));
```

### Canvas Implementation

The visual canvas is built using React Flow:

```typescript
// app/components/Canvas/AgentCanvas.tsx
import React, { useCallback, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
} from 'reactflow';

const nodeTypes = {
  llm: LLMNode,
  retrieval: RetrievalNode,
  input: InputNode,
  output: OutputNode,
};

export const AgentCanvas: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  
  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );
  
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      nodeTypes={nodeTypes}
    />
  );
};
```

### API Integration

Frontend API calls use a centralized client:

```typescript
// app/utils/api.ts
class ApiClient {
  private baseURL: string;
  private token: string | null = null;
  
  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }
  
  setToken(token: string) {
    this.token = token;
  }
  
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}/api/v1${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
      ...options.headers,
    };
    
    const response = await fetch(url, { ...options, headers });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  // Example methods
  async getWorkspaces(): Promise<Workspace[]> {
    return this.request<Workspace[]>('/workspaces');
  }
  
  async create
Agent(data: CreateAgentData): Promise<Agent> {
    return this.request<Agent>('/agents', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const api = new ApiClient(process.env.NEXT_PUBLIC_API_URL!);
```

## Database Schema

### Migrations

Database migrations are managed with Alembic:

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Model Relationships

```python
# User -> Workspace (Many-to-Many through Membership)
class Membership(Base):
    __tablename__ = "memberships"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), primary_key=True)
    role = Column(Enum(UserRole), default=UserRole.MEMBER)
    created_at = Column(DateTime, default=datetime.utcnow)

# Workspace -> Agents (One-to-Many)
class Agent(Base):
    __tablename__ = "agents"
    
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    workspace = relationship("Workspace", back_populates="agents")

# Workspace -> Datasets (One-to-Many)
class Dataset(Base):
    __tablename__ = "datasets"
    
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    workspace = relationship("Workspace", back_populates="datasets")
```

## API Development

### Authentication Flow

The API uses JWT-based authentication:

```python
# Token creation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Token verification
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
```

### WebSocket Implementation

Real-time streaming uses WebSockets:

```python
# WebSocket endpoint
@router.websocket("/runs/{run_id}/stream")
async def stream_run(
    websocket: WebSocket,
    run_id: str,
    db: Session = Depends(get_db)
):
    await websocket.accept()
    
    try:
        # Verify run exists and user has access
        run = db.query(Run).filter(Run.id == run_id).first()
        if not run:
            await websocket.close(code=4004)
            return
        
        # Stream events
        async for event in stream_run_events(run_id):
            await websocket.send_json(event)
            
    except WebSocketDisconnect:
        # Handle disconnect
        pass
    finally:
        await websocket.close()
```

### Error Handling

Centralized error handling:

```python
# Custom exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": exc.error_code if hasattr(exc, 'error_code') else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

## Testing

### Backend Testing

#### Unit Tests

```python
# tests/test_agents.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.user import User

client = TestClient(app)

@pytest.fixture
def test_user(db_session):
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}

def test_create_agent(auth_headers):
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "Test Agent",
            "description": "A test agent",
            "workspace_id": "test-workspace-id",
            "graph_json": {"nodes": [], "edges": []}
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Agent"
```

#### Integration Tests

```python
# tests/test_integration.py
import pytest
from app.services.executor import GraphExecutor
from app.models.agent import Agent

@pytest.mark.asyncio
async def test_agent_execution(db_session, test_user):
    # Create test agent
    agent = Agent(
        name="Test Agent",
        workspace_id="test-workspace",
        graph_json={
            "nodes": [
                {"id": "input", "type": "input", "data": {}},
                {"id": "llm", "type": "llm", "data": {"model": "gpt-3.5-turbo"}},
                {"id": "output", "type": "output", "data": {}}
            ],
            "edges": [
                {"id": "e1", "source": "input", "target": "llm"},
                {"id": "e2", "source": "llm", "target": "output"}
            ]
        }
    )
    
    # Execute agent
    executor = GraphExecutor()
    result = await executor.execute(agent, {"input": "Hello, world!"})
    
    assert "output" in result
```

### Frontend Testing

#### Component Tests

```typescript
// __tests__/components/AgentCanvas.test.tsx
import { render, screen } from '@testing-library/react';
import { AgentCanvas } from '@/components/Canvas/AgentCanvas';

describe('AgentCanvas', () => {
  it('renders canvas without crashing', () => {
    render(<AgentCanvas />);
    expect(screen.getByTestId('react-flow')).toBeInTheDocument();
  });

  it('adds nodes correctly', () => {
    const { getByText } = render(<AgentCanvas />);
    // Test node addition logic
  });
});
```

#### E2E Tests

```typescript
// e2e/agent-creation.spec.ts
import { test, expect } from '@playwright/test';

test('agent creation flow', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.fill('[data-testid=email]', 'test@example.com');
  await page.fill('[data-testid=password]', 'password');
  await page.click('[data-testid=login-button]');
  
  // Create agent
  await page.goto('/agents/new');
  await page.fill('[data-testid=agent-name]', 'Test Agent');
  await page.click('[data-testid=create-button]');
  
  // Verify agent created
  await expect(page.locator('h1')).toContainText('Test Agent');
});
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## Deployment

### Docker Configuration

The project uses Docker for containerization:

#### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM
node:18-alpine

WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: promptflow
      POSTGRES_USER: promptflow
      POSTGRES_PASSWORD: promptflow123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: promptflow
      MINIO_ROOT_PASSWORD: promptflow123
    volumes:
      - minio_data:/data

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - minio
      - qdrant
    environment:
      DATABASE_URL: postgresql://promptflow:promptflow123@postgres:5432/promptflow
      REDIS_URL: redis://redis:6379

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
  minio_data:
  qdrant_data:
```

### Production Deployment

#### Environment Variables

Production requires additional environment variables:

```env
# Production settings
ENVIRONMENT=production
DEBUG=false

# Security
SECRET_KEY=your-production-secret-key
CORS_ORIGINS=https://yourdomain.com

# Performance
DATABASE_POOL_SIZE=20
REDIS_POOL_SIZE=10

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
```

#### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Deployment script
          docker-compose -f docker-compose.prod.yml up -d
```

## Contributing Guidelines

### Code Style

#### Python (Backend)

Follow PEP 8 and use the following tools:

```bash
# Linting
flake8 app/
black app/
isort app/

# Type checking
mypy app/
```

#### TypeScript (Frontend)

Use ESLint and Prettier:

```bash
# Linting and formatting
npm run lint
npm run format

# Type checking
npm run type-check
```

### Git Workflow

1. **Branch Naming**: Use descriptive names like `feature/add-llm-node` or `bugfix/fix-auth-issue`
2. **Commit Messages**: Follow conventional commits

```
feat: add LLM node type
fix: resolve authentication timeout
docs: update API documentation
test: add integration tests for executor
```

3. **Pull Requests**: 
   - Include tests for new features
   - Update documentation
   - Ensure CI passes
   - Request code review

### Development Process

1. **Setup**: Follow the development setup instructions
2. **Create Branch**: `git checkout -b feature/your-feature`
3. **Develop**: Write code following the style guidelines
4. **Test**: Ensure all tests pass
5. **Document**: Update relevant documentation
6. **Submit PR**: Create pull request with clear description

### Adding New Features

#### Backend Features

1. **Model**: Add/update SQLAlchemy models
2. **Migration**: Create and apply database migration
3. **Endpoint**: Implement API endpoint with validation
4. **Tests**: Write unit and integration tests
5. **Documentation**: Update API documentation

#### Frontend Features

1. **TypeScript Types**: Define interfaces and types
2. **Components**: Create reusable components
3. **Store**: Update Zustand store if needed
4. **API**: Add API client methods
5. **Tests**: Write component tests
6. **Documentation**: Update user guide

#### Node Types

To add a new node type to the executor:

1. **Backend Node Class**:
```python
# app/nodes/custom_node.py
class CustomNode:
    node_type = "custom"
    
    def __init__(self, id: str, config: dict):
        self.id = id
        self.config = config
    
    async def run(self, ctx: Context, inputs: dict) -> dict:
        # Implement node logic
        return {"output": result}
```

2. **Register Node**:
```python
# app/nodes/registry.py
from app.nodes.custom_node import CustomNode

NODE_TYPES[CustomNode.node_type] = CustomNode
```

3. **Frontend Component**:
```typescript
// app/components/Nodes/CustomNode.tsx
import { Node } from 'reactflow';

export const CustomNode: React.FC<{ data: Node['data'] }> = ({ data }) => {
  return (
    <div className="custom-node">
      {/* Node UI */}
    </div>
  );
};
```

4. **Register Component**:
```typescript
// app/components/Canvas/AgentCanvas.tsx
const nodeTypes = {
  custom: CustomNode,
  // ... other nodes
};
```

### Performance Considerations

#### Backend Optimization

1. **Database Indexing**: Add indexes for frequently queried fields
2. **Connection Pooling**: Configure appropriate pool sizes
3. **Caching**: Use Redis for caching expensive operations
4. **Async Operations**: Use async/await for I/O operations

#### Frontend Optimization

1. **Code Splitting**: Use dynamic imports for large components
2. **Memoization**: Use React.memo and useMemo appropriately
3. **Bundle Size**: Monitor and optimize bundle size
4. **Image Optimization**: Use next/image for optimized images

### Security Best Practices

#### Backend Security

1. **Input Validation**: Use Pydantic models for validation
2. **SQL Injection**: Use SQLAlchemy ORM, avoid raw SQL
3. **Authentication**: Implement proper JWT handling
4. **Rate Limiting**: Configure rate limiting for API endpoints

#### Frontend Security

1. **XSS Prevention**: Sanitize user inputs
2. **CSRF Protection**: Use CSRF tokens for state-changing requests
3. **Environment Variables**: Never expose secrets in frontend
4. **Content Security Policy**: Implement CSP headers

### Debugging

#### Backend Debugging

```python
# Use logging
import logging
logger = logging.getLogger(__name__)

logger.info("Processing request")
logger.error(f"Error occurred: {exc}")

# Debug with pdb
import pdb; pdb.set_trace()
```

#### Frontend Debugging

```typescript
// Use console logging
console.log('Debug information', data);
console.error('Error occurred', error);

// Debug with debugger statement
debugger;
```

### Monitoring and Logging

#### Application Monitoring

- **Health Checks**: Implement `/health` endpoint
- **Metrics**: Track key performance indicators
- **Error Tracking**: Use Sentry for error monitoring
- **Performance**: Monitor response times and resource usage

#### Structured Logging

```python
# Backend structured logging
import structlog

logger = structlog.get_logger()

logger.info(
    "Agent execution started",
    agent_id=agent.id,
    user_id=user.id,
    workspace_id=workspace_id
)
```

## Getting Help

### Resources

- **Documentation**: [API Documentation](./api.md), [User Guide](./user-guide.md)
- **Code Repository**: https://github.com/prajjwal-23/PromptFlow
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and community support

### Contact

- **Technical Lead**: prajjwal@example.com
- **Community Discord**: https://discord.gg/promptflow
- **Twitter**: @PromptFlowDev

---

Thank you for contributing to PromptFlow! Your contributions help make AI agent building accessible to everyone.