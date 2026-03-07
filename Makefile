# AgentLens — Convenience commands for development

.PHONY: install dev build test clean server dashboard demo

install:
	cd dashboard && npm install
	cd server && pip install -e ".[dev]" --break-system-packages
	cd sdk-python && pip install -e ".[dev]" --break-system-packages
	cd sdk-typescript && npm install && npm run build
	cd mcp-server && pip install -e . --break-system-packages

dev:
	@echo "Starting AgentLens development servers..."
	@echo "Dashboard: http://localhost:5173"
	@echo "Server API: http://localhost:8766"
	@echo "Server WS:  ws://localhost:8766/ws"
	cd server && uvicorn agentlens_server.main:app --host 0.0.0.0 --port 8766 --reload &
	cd dashboard && npm run dev &
	wait

server:
	cd server && uvicorn agentlens_server.main:app --host 0.0.0.0 --port 8766 --reload

dashboard:
	cd dashboard && npm run dev

demo:
	cd examples && python demo_multi_step.py

test:
	cd sdk-python && pytest
	cd server && pytest
	cd dashboard && npm test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	rm -f server/agentlens.db
