.PHONY: help setup install dev dev-backend dev-frontend test lint clean build push logs

# Default target
help:
	@echo "PromptFlow Development Commands"
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup      - Initialize the entire development environment"
	@echo "  install    - Install all dependencies"
	@echo ""
	@echo "Development Commands:"
	@echo "  dev        - Start all services in development mode"
	@echo "  dev-backend- Start only backend services"
	@echo "  dev-frontend- Start only frontend service"
	@echo "  logs       - Show logs from all services"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test       - Run all tests"
	@echo "  test-backend- Run backend tests"
	@echo "  test-frontend- Run frontend tests"
	@echo "  lint       - Run linting on all code"
	@echo "  lint-backend- Lint backend code"
	@echo "  lint-frontend- Lint frontend code"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean      - Clean all caches and containers"
	@echo "  build      - Build all Docker images"
	@echo "  shell      - Open shell in backend container"
	@echo "  db-migrate - Run database migrations"
	@echo "  db-seed    - Seed database with initial data"
	@echo "  health     - Check health of all services"

# Setup Commands
setup:
	@echo "🚀 Setting up PromptFlow development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "✅ Created .env file"; else echo "✅ .env file already exists"; fi
	@mkdir -p uploads minio-data qdrant-data postgres_data redis_data
	@echo "✅ Created local data directories"
	@echo "📦 Installing dependencies..."
	make install
	@echo "🎉 Setup complete! Run 'make dev' to start development"

install:
	@echo "📦 Installing dependencies..."
	@docker-compose run --rm backend pip install -r requirements.txt
	@docker-compose run --rm frontend npm install
	@echo "✅ Dependencies installed"

# Development Commands
dev:
	@echo "🚀 Starting all services..."
	docker-compose up --build

dev-backend:
	@echo "🔧 Starting backend services..."
	docker-compose up --build postgres redis minio qdrant backend celery-worker

dev-frontend:
	@echo "🎨 Starting frontend service..."
	docker-compose up --build frontend

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f postgres redis minio qdrant backend celery-worker

logs-frontend:
	docker-compose logs -f frontend

# Testing Commands
test:
	@echo "🧪 Running all tests..."
	make test-backend
	make test-frontend

test-backend:
	@echo "🐍 Running backend tests..."
	docker-compose run --rm backend pytest -v

test-frontend:
	@echo "⚛️ Running frontend tests..."
	docker-compose run --rm frontend npm test

test-e2e:
	@echo "🎭 Running E2E tests..."
	docker-compose run --rm frontend npm run test:e2e

# Linting Commands
lint:
	@echo "🔍 Linting all code..."
	make lint-backend
	make lint-frontend

lint-backend:
	@echo "🐍 Linting backend code..."
	docker-compose run --rm backend flake8 .
	docker-compose run --rm backend black --check .
	docker-compose run --rm backend isort --check-only .
	docker-compose run --rm backend mypy .

lint-frontend:
	@echo "⚛️ Linting frontend code..."
	docker-compose run --rm frontend npm run lint
	docker-compose run --rm frontend npm run type-check

lint-fix:
	@echo "🔧 Auto-fixing linting issues..."
	docker-compose run --rm backend black .
	docker-compose run --rm backend isort .
	docker-compose run --rm frontend npm run lint:fix

# Utility Commands
clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	docker system prune -f
	docker volume prune -f
	@rm -rf uploads/* minio-data/* qdrant-data/* postgres_data/* redis_data/*
	@echo "✅ Cleanup complete"

build:
	@echo "🔨 Building Docker images..."
	docker-compose build --no-cache
	@echo "✅ Build complete"

shell:
	@echo "🐚 Opening backend shell..."
	docker-compose exec backend bash

shell-frontend:
	@echo "🐚 Opening frontend shell..."
	docker-compose exec frontend bash

db-migrate:
	@echo "🗄️ Running database migrations..."
	docker-compose exec backend alembic upgrade head
	@echo "✅ Migrations complete"

db-seed:
	@echo "🌱 Seeding database..."
	docker-compose exec backend python -m app.scripts.seed_data
	@echo "✅ Database seeded"

db-reset:
	@echo "🔄 Resetting database..."
	docker-compose exec backend alembic downgrade base
	docker-compose exec backend alembic upgrade head
	make db-seed
	@echo "✅ Database reset complete"

health:
	@echo "🏥 Checking service health..."
	@echo "Backend API:"
	@curl -s http://localhost:8000/health || echo "❌ Backend not responding"
	@echo ""
	@echo "Frontend:"
	@curl -s http://localhost:3000 || echo "❌ Frontend not responding"
	@echo ""
	@echo "PostgreSQL:"
	@docker-compose exec postgres pg_isready -U promptflow || echo "❌ PostgreSQL not ready"
	@echo ""
	@echo "Redis:"
	@docker-compose exec redis redis-cli ping || echo "❌ Redis not ready"
	@echo ""
	@echo "MinIO:"
	@curl -s http://localhost:9000/minio/health/live || echo "❌ MinIO not ready"
	@echo ""
	@echo "Qdrant:"
	@curl -s http://localhost:6333/health || echo "❌ Qdrant not ready"

# Development utilities
restart-backend:
	@echo "🔄 Restarting backend services..."
	docker-compose restart backend celery-worker

restart-frontend:
	@echo "🔄 Restarting frontend service..."
	docker-compose restart frontend

pull-latest:
	@echo "📥 Pulling latest images..."
	docker-compose pull
	@echo "✅ Images updated"

backup-db:
	@echo "💾 Backing up database..."
	docker-compose exec postgres pg_dump -U promptflow promptflow > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backed up"

# Production commands (for future use)
prod-build:
	@echo "🏭 Building for production..."
	docker-compose -f docker-compose.prod.yml build

prod-deploy:
	@echo "🚀 Deploying to production..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✅ Deployment complete"