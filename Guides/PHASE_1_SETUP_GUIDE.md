# PromptFlow Phase 1 Setup Guide

This guide walks you through setting up the PromptFlow project using standard developer tools and commands.

## 🚀 Prerequisites

Make sure you have these installed:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Python 3.11+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [Git](https://git-scm.com/)

## 📋 Phase 1 Setup Commands

### Step 1: Backend Setup with Alembic

```bash
# 1.1 Create and activate virtual environment
cd backend
python -m venv venv
venv\Scripts\activate

# 1.2 Install Python dependencies
pip install -r requirements.txt

# 1.3 Initialize Alembic for database migrations
alembic init alembic

# 1.4 Configure Alembic (this needs manual editing)
# Edit alembic.ini:
# - Change sqlalchemy.url = postgresql://promptflow:promptflow123@localhost:5432/promptflow
#
# Edit alembic/env.py:
# - Add import for our models
# - Update target_metadata

# 1.5 Create initial migration
alembic revision --autogenerate -m "Initial migration"

# 1.6 Apply migrations (run this after starting PostgreSQL)
alembic upgrade head
```

### Step 2: Frontend Setup with Next.js CLI

```bash
# 2.1 Create Next.js project
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# 2.2 Navigate to frontend
cd frontend

# 2.3 Install additional dependencies
npm install @xyflow/react @headlessui/react @heroicons/react axios clsx tailwind-merge zustand react-hook-form @hookform/resolvers zod socket.io-client react-hot-toast framer-motion date-fns recharts monaco-editor @monaco-editor/react

# 2.4 Install dev dependencies
npm install -D @types/node @typescript-eslint/eslint-plugin @typescript-eslint/parser prettier prettier-plugin-tailwindcss @playwright/test jest @testing-library/react @testing-library/jest-dom jest-environment-jsdom
```

### Step 3: Docker Services Setup

```bash
# 3.1 Start infrastructure services
docker-compose up -d postgres redis minio qdrant

# 3.2 Check service status
docker-compose ps

# 3.3 View logs if needed
docker-compose logs postgres
docker-compose logs redis
docker-compose logs minio
docker-compose logs qdrant
```

### Step 4: Environment Configuration

```bash
# 4.1 Copy environment file
cp .env.example .env

# 4.2 Edit environment file (use your preferred editor)
notepad .env
# or
code .env

# 4.3 Generate secure secrets
# Update SECRET_KEY and JWT_SECRET_KEY with strong values
```

### Step 5: Database Setup

```bash
# 5.1 Wait for PostgreSQL to be ready
docker-compose exec postgres pg_isready -U promptflow

# 5.2 Run Alembic migrations
cd backend
venv\Scripts\activate
alembic upgrade head

# 5.3 (Optional) Create seed data
# python -m app.scripts.seed_data
```

### Step 6: Configure Alembic Properly

**File: alembic/env.py**
```python
# Add these imports at the top
from app.core.database import Base
from app.models import user, workspace, agent, dataset, run  # noqa

# Update target_metadata
target_metadata = Base.metadata
```

**File: alembic.ini**
```ini
# Update the database URL
sqlalchemy.url = postgresql://promptflow:promptflow123@localhost:5432/promptflow
```

### Step 7: Development Server Startup

```bash
# Terminal 1: Backend
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Celery Worker (optional)
cd backend
venv\Scripts\activate
celery -A app.core.celery worker --loglevel=info
```

### Step 8: Git Repository Setup

```bash
# 8.1 Initialize git
git init

# 8.2 Create .gitignore (already exists)
git add .gitignore

# 8.3 Set up pre-commit hooks
pip install pre-commit
pre-commit install

# 8.4 Make initial commit
git add .
git commit -m "Initial Phase 1 setup: Backend + Frontend + Infrastructure"

# 8.5 Create development branch
git checkout -b develop
```

### Step 9: Testing the Setup

```bash
# 9.1 Test backend health
curl http://localhost:8000/health

# 9.2 Test frontend
# Open browser to http://localhost:3000

# 9.3 Test API documentation
# Open browser to http://localhost:8000/docs

# 9.4 Test database connection
# Visit http://localhost:8000/health and check database status

# 9.5 Test MinIO
# Open browser to http://localhost:9001
# Login with: promptflow / promptflow123

# 9.6 Test Qdrant
curl http://localhost:6333/health
```

## 🔧 Useful Development Commands

### Backend Commands
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Reset database
alembic downgrade base
alembic upgrade head

# Run tests
pytest

# Format code
black .
isort .

# Lint code
flake8 .
mypy .
```

### Frontend Commands
```bash
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run tests
npm test

# E2E tests
npm run test:e2e

# Lint and format
npm run lint
npm run format
```

### Docker Commands
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild services
docker-compose up --build

# Clean up everything
docker-compose down -v
docker system prune -f
```

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**: Make sure ports 3000, 8000, 5432, 6379, 9000, 6333 are free
2. **Python path issues**: Ensure virtual environment is activated
3. **Database connection**: Check PostgreSQL is running in Docker
4. **Module import errors**: Verify PYTHONPATH includes the app directory

### Health Checks

```bash
# Check all services status
make health

# Manual checks
curl http://localhost:8000/health  # Backend
curl http://localhost:3000         # Frontend
docker-compose exec postgres pg_isready -U promptflow  # PostgreSQL
docker-compose exec redis redis-cli ping               # Redis
curl http://localhost:9000/minio/health/live           # MinIO
curl http://localhost:6333/health                     # Qdrant
```

## 📝 Next Steps After Phase 1

1. Implement authentication logic
2. Set up React Flow canvas
3. Create agent execution engine
4. Add file upload functionality
5. Implement real-time streaming

---

**Remember**: This setup follows industry best practices using standard developer tools and commands pattern!