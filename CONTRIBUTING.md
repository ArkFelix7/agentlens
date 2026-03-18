# Contributing to AgentLens

Thank you for your interest in contributing. This document covers how to set up a development environment, run tests, and submit changes.

## Repository Structure

```
AgentLens/
├── server/          # FastAPI backend (Python)
├── dashboard/       # React frontend (TypeScript)
├── sdk-python/      # Python SDK
├── sdk-typescript/  # TypeScript/Node SDK
├── mcp-server/      # MCP protocol server
└── examples/        # Demo agents
```

## Prerequisites

- Python 3.10+
- Node.js 20+
- make

## Quick Start

```bash
# Install all dependencies
make install

# Start server + dashboard in development mode
make dev
```

The server runs on `http://localhost:8766` and the dashboard on `http://localhost:5173`.

## Development Workflow

### Server (FastAPI)

```bash
cd server
pip install -e ".[dev]"

# Run unit tests
pytest tests/ -v

# Run with auto-reload
uvicorn agentlens_server.main:app --port 8766 --reload
```

### Dashboard (React + Vite)

```bash
cd dashboard
npm install

# Dev server with hot-reload
npm run dev

# Type check
npx tsc --noEmit

# Production build
npm run build
```

### Python SDK

```bash
cd sdk-python
pip install -e .
python -c "from agentlens_sdk import init, trace; print('OK')"
```

### TypeScript SDK

```bash
cd sdk-typescript
npm install
npm run build
```

## Running the Integration Test Suite

```bash
# Start server first
cd server && uvicorn agentlens_server.main:app --port 8766 &

# Run all 38 integration tests
python tests/integration/test_runner.py

# With performance benchmarks
python tests/integration/test_runner.py --bench
```

## Adding a New Interceptor

1. Create `sdk-python/src/agentlens_sdk/interceptors/<framework>_interceptor.py`
2. Export an `instrument_<framework>()` function following the pattern in `crewai_interceptor.py`
3. Add to `sdk-python/src/agentlens_sdk/interceptors/__init__.py`
4. Add a smoke test in the CI workflow

## Code Style

- **Python**: follow PEP 8; use type hints on all function signatures; use `ruff` for linting
- **TypeScript**: strict mode; no `any` except for JSON data fields; use `eslint`
- All files start with a docstring/comment describing their purpose
- SDK must never raise exceptions to user code — wrap everything in `try/except`

## Pull Request Process

1. Fork the repository and create a feature branch from `main`
2. Write tests for any new functionality
3. Ensure `pytest tests/` passes in `server/`
4. Ensure `npx tsc --noEmit` passes in `dashboard/`
5. Open a PR with a clear description of the change and why it's needed

## Reporting Issues

Open an issue at https://github.com/ArkFelix7/agentlens/issues with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python/Node version and OS
