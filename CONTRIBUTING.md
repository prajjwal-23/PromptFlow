# Contributing to PromptFlow

Thank you for your interest in contributing to PromptFlow! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** for your contribution
4. **Make changes** following our guidelines
5. **Test thoroughly** the changes
6. **Submit a pull request** with a clear description

### Prerequisites

- Docker and Docker Compose
- Node.js 18+
- Python 3.11+
- Git

Read our [Developer Guide](./docs/developer-guide.md) for detailed setup instructions.

## 📋 Types of Contributions

We welcome contributions in the following areas:

### 🐛 Bug Fixes

- Fix identified bugs in the codebase
- Add tests to prevent regression
- Update documentation if needed

### ✨ New Features

- Implement new node types for the canvas
- Add new API endpoints
- Enhance the user interface
- Improve performance and scalability

### 📚 Documentation

- Improve existing documentation
- Add examples and tutorials
- Fix typos and grammatical errors
- Translate content to other languages

### 🛠️ Infrastructure

- Improve CI/CD pipelines
- Optimize Docker configurations
- Add monitoring and logging
- Enhance development tools

## 🏗️ Development Workflow

### 1. Setup Development Environment

```bash
# Clone your fork
git clone https://github.com/prajjwal-23/PromptFlow.git
cd PromptFlow

# Set up the development environment
make setup
make dev
```

### 2. Branch Naming Convention

Use descriptive branch names:

- `feature/feature-name` for new features
- `bugfix/bug-description` for bug fixes
- `docs/documentation-update` for documentation changes
- `refactor/code-cleanup` for refactoring
- `test/add-tests` for adding tests

### 3. Commit Message Guidelines

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): description

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: new feature
- `fix`: bug fix
- `docs`: documentation changes
- `style`: code formatting (no functional changes)
- `refactor`: code refactoring
- `test`: adding or updating tests
- `chore`: maintenance tasks

**Examples:**
```
feat(canvas): add LLM node type
fix(auth): resolve timeout issue with JWT refresh
docs(api): update agent endpoint documentation
test(executor): add integration tests for graph execution
```

### 4. Code Quality Standards

#### Python (Backend)

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints for all functions and methods
- Write docstrings for all public functions and classes
- Use meaningful variable and function names

```bash
# Format and lint code
cd backend
black app/
isort app/
flake8 app/
mypy app/
```

#### TypeScript (Frontend)

- Use [Prettier](https://prettier.io/) for code formatting
- Follow [ESLint](https://eslint.org/) rules
- Use TypeScript strict mode
- Write interfaces for all data structures

```bash
# Format and lint code
cd frontend
npm run format
npm run lint
npm run type-check
```

### 5. Testing Requirements

#### Backend Tests

- Write unit tests for all new functions and classes
- Add integration tests for API endpoints
- Ensure minimum 80% test coverage
- Test error conditions and edge cases

```bash
cd backend
pytest tests/ -v --cov=app
```

#### Frontend Tests

- Write component tests for new UI components
- Add end-to-end tests for critical user flows
- Test both success and error states

```bash
cd frontend
npm test
npm run test:e2e
```

### 6. Documentation Updates

- Update API documentation for new endpoints
- Add user guide sections for new features
- Update developer guide for architecture changes
- Include examples and code snippets

## 🔄 Pull Request Process

### 1. Before Submitting

- [ ] Ensure all tests pass
- [ ] Update documentation if needed
- [ ] Follow code style guidelines
- [ ] Squash related commits into meaningful units
- [ ] Rebase onto the latest main branch

### 2. Pull Request Template

Use this template for your pull requests:

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
```

### 3. Review Process

1. **Automated Checks**: CI/CD pipeline will run tests and linting
2. **Code Review**: Maintainers will review your changes
3. **Feedback**: Address review comments promptly
4. **Approval**: Once approved, your PR will be merged

## 🏷️ Issue Reporting

### Bug Reports

Use the following template for bug reports:

```markdown
## Bug Description
Clear and concise description of the bug.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g. Windows 11, macOS 13.0]
- Browser: [e.g. Chrome 108, Firefox 107]
- Version: [e.g. v1.0.0]

## Additional Context
Additional information, screenshots, or logs.
```

### Feature Requests

For new feature suggestions:

```markdown
## Feature Description
Clear description of the feature.

## Problem Statement
What problem does this feature solve?

## Proposed Solution
How should the feature be implemented?

## Alternatives Considered
Other approaches you considered.

## Additional Context
Relevant examples and additional information.
```

## 🎯 Development Priorities

### Current Focus Areas

1. **Core Functionality**
   - Graph execution engine
   - Node type implementations
   - Real-time streaming

2. **User Experience**
   - Canvas interface improvements
   - Onboarding and tutorials
   - Error handling and feedback

3. **Performance**
   - Query optimization
   - Caching strategies
   - Resource management

4. **Documentation**
   - API reference
   - User guides
   - Developer tutorials

### Good First Issues

Look for issues tagged with `good first issue` for beginner-friendly contributions.

## 🏅 Recognition

Contributors will be recognized in:

- `README.md` contributors section
- Release notes for significant contributions
- Annual contributor highlights

## 📞 Get Help

### Communication Channels

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and community support
- **Discord**: [Join our Discord server](https://discord.gg/promptflow)
- **Email**: support@promptflow.dev

### Resources

- [Developer Guide](./docs/developer-guide.md)
- [API Documentation](./docs/api.md)
- [User Guide](./docs/user-guide.md)
- [Architecture Overview](./PromptFlow_Project_Plan_and_lld.md)

## 📄 Code of Conduct

### Our Pledge

In the interest of fostering an open and welcoming environment, we as contributors and maintainers pledge to make participation in our project and our community a harassment-free experience for everyone.

### Our Standards

Positive behavior includes:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

Unacceptable behavior includes:

- The use of sexualized language or imagery
- Personal attacks or political commentary
- Public or private harassment
- Publishing others' private information
- Any other conduct which could reasonably be considered inappropriate

### Enforcement

Project maintainers have the right and responsibility to remove, edit, or reject comments, commits, code, wiki edits, issues, and other contributions that are not aligned with this Code of Conduct.

---

Thank you for contributing to PromptFlow! Your contributions help make AI agent building accessible to everyone. 🚀