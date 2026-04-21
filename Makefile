VENV = .venv
BIN = $(VENV)/bin
PYTHON = $(BIN)/python3
PIP = $(BIN)/pip
PYTEST = $(BIN)/pytest
RUFF = $(BIN)/ruff

.PHONY: init up down restart ps logs clean client health test graph lint

# Initialize the local environment (for running client/workers locally)
init:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install .[test]
	@echo "✅ Local environment ready. Use 'source $(VENV)/bin/activate' to use it."

# Start the entire stack in the background
up:
	docker compose up --build -d
	@echo "🚀 Stack is starting. Use 'make health' to check when it's ready."

# Stop the stack
down:
	docker compose down

# Restart the stack
restart: down up

# Check container status
ps:
	docker compose ps

# Follow logs of the orchestrator
logs:
	docker compose logs -f orchestrator

# Full cleanup including volumes and databases
clean:
	docker compose down -v
	rm -f avtomatika_history.db
	@echo "🧹 Environment cleaned."

# Run the test client
client:
	$(PYTHON) client.py

# Run workers locally (requires environment variables set)
worker-gpu:
	$(PYTHON) workers/gpu.py

worker-cpu-reliable:
	$(PYTHON) workers/cpu_reliable.py

worker-cpu-unreliable:
	$(PYTHON) workers/cpu_unreliable.py

# Check system readiness
health:
	@echo "🔍 Checking Orchestrator..."
	@curl -s --fail http://localhost:8080/_public/status || (echo "❌ Orchestrator is not running" && exit 1)
	@echo "🔍 Checking Workers Registration..."
	@curl -s -H "X-Client-Token: user_token_vip" http://localhost:8080/api/v1/workers | grep -q "worker_id" || (echo "❌ No workers registered" && exit 1)
	@echo "✅ System is UP and READY"

# Generate visual graphs of the blueprints (requires graphviz)
graph:
	$(PYTHON) generate_graphs.py

# Run linter (ruff)
lint:
	$(RUFF) check .
	$(RUFF) format --check .

# Run integration tests
test:
	$(PYTEST) -s tests/

# --- Full System Validation ---
full-check: lint graph
	@echo "🔍 Checking Docker Containers Health..."
	docker compose ps
	@echo "🚀 Running Comprehensive Integration Suite..."
	$(PYTEST) -s tests/test_comprehensive.py
	@echo "✅ ALL SYSTEMS VERIFIED"

