# PromptFlow – AI Agent Builder Platform

PromptFlow is an open-source, local-first AI Agent Builder Platform that allows users to visually create and execute custom AI workflows through a drag-and-drop canvas. It supports prompt engineering, retrieval-augmented generation (RAG), tool calling, and real-time streaming.

## 🚀 Features

- **Visual Canvas Editor** – Drag and drop nodes to build AI workflows
- **RAG Support** – Upload documents and retrieve context for prompts
- **Local-First** – Everything runs locally with open-source components
- **Real-time Streaming** – Watch your agents execute live
- **Tool Integration** – Extend agents with custom tools
- **Team Collaboration** – Multi-user workspaces with role-based access

## 🏗️ Architecture

- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS + React Flow
- **Backend**: FastAPI + Python 3.11
- **Databases**: PostgreSQL + Qdrant (vectors)
- **Storage**: MinIO (S3-compatible)
- **Cache/Queue**: Redis
- **LLM Runtime**: Ollama
- **Task Queue**: Celery

## 📦 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+
- Python 3.11+
- Ollama (for local LLMs)

### Installation

1. Clone the repository
```bash
git clone <https://github.com/prajjwal-23/PromptFlow.git>
cd PromptFlow
```

2. Start all services
```bash
make setup
make dev
```

3. Access the application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🛠️ Development

### Setup Development Environment

```bash
# Install dependencies
make install

# Start development servers
make dev

# Run tests
make test

# Lint code
make lint
```

### Project Structure

```
PromptFlow/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── docker-compose.yml
├── Makefile
└── docs/            # Documentation
```

## 📚 Documentation

- [API Documentation](./docs/api.md)
- [User Guide](./docs/user-guide.md)
- [Developer Guide](./docs/developer-guide.md)

## 🤝 Contributing

Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI powered by [Next.js](https://nextjs.org/) and [React Flow](https://reactflow.dev/)
- Vector search with [Qdrant](https://qdrant.tech/)
- LLMs via [Ollama](https://ollama.ai/)