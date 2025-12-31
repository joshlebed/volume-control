.PHONY: help install deploy reload restart stop start status logs logs-service run debug test-qlc clean readme start-bg list kill sync update-qlc

# Default target
help:
	@echo "volume-control - Makefile commands"
	@echo ""
	@echo "Setup:"
	@echo "  make sync         Sync dependencies with uv"
	@echo "  make update-qlc   Update qlcplus library from git"
	@echo "  make deploy       Deploy systemd service (requires sudo)"
	@echo ""
	@echo "Service Operations (systemd):"
	@echo "  make start        Start the systemd service"
	@echo "  make stop         Stop the systemd service"
	@echo "  make restart      Restart the systemd service"
	@echo "  make reload       Reload systemd after service file changes"
	@echo "  make status       Show service status"
	@echo ""
	@echo "Process Operations (non-systemd):"
	@echo "  make start-bg     Start in background (nohup)"
	@echo "  make list         List running processes"
	@echo "  make kill         Kill running processes"
	@echo ""
	@echo "Logs:"
	@echo "  make logs         Tail application logs"
	@echo "  make logs-service Tail systemd service logs"
	@echo ""
	@echo "Development:"
	@echo "  make run          Run in foreground"
	@echo "  make debug        Stop service and run in foreground"
	@echo "  make test-qlc     Test QLC+ connection"
	@echo ""
	@echo "Other:"
	@echo "  make readme       Show README"
	@echo "  make clean        Remove Python cache files"

# Paths (relative to repo root)
VENV := .venv
PYTHON := $(VENV)/bin/python
SRC := src
SERVICE := volume_control.service

# ============================================================================
# Setup
# ============================================================================

sync:
	@echo "Syncing dependencies with uv..."
	uv sync

update-qlc:
	@echo "Updating qlcplus library from git..."
	uv pip install --reinstall --upgrade "qlcplus @ git+ssh://git@github.com/joshlebed/qlc-config.git"

# Keep install as alias for backwards compatibility
install: sync

# ============================================================================
# Deployment
# ============================================================================

deploy:
	@echo "Deploying systemd service..."
	sudo cp $(SRC)/$(SERVICE) /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable $(SERVICE)
	@echo "Service deployed and enabled. Run 'make start' to start it."

reload:
	@echo "Reloading systemd configuration..."
	sudo cp $(SRC)/$(SERVICE) /etc/systemd/system/
	sudo systemctl daemon-reload

# ============================================================================
# Service Operations
# ============================================================================

start:
	sudo systemctl start $(SERVICE)
	@echo "Service started"

stop:
	sudo systemctl stop $(SERVICE)
	@echo "Service stopped"

restart:
	sudo systemctl restart $(SERVICE)
	@echo "Service restarted"

status:
	@systemctl status $(SERVICE) --no-pager || true

# ============================================================================
# Logs
# ============================================================================

logs:
	tail -f /tmp/volume_controller.log

logs-service:
	journalctl -u $(SERVICE) -f

# ============================================================================
# Development
# ============================================================================

run:
	uv run python $(SRC)/volume_control.py

debug: stop run

test-qlc:
	@echo "Testing QLC+ connection..."
	@uv run python -c "from qlcplus import QLCPlusClient; c = QLCPlusClient(host='192.168.0.221'); c.connect(); print('Connected to QLC+'); print('Functions:', c.get_functions_list()); c.disconnect()"

# ============================================================================
# Process Operations (non-systemd)
# ============================================================================

start-bg:
	@echo "Starting in background..."
	@nohup $(PYTHON) $(SRC)/volume_control.py &> /tmp/nohup.out & disown
	@echo "Started. Logs: make logs"

list:
	@ps aux | grep volume_control | grep -v grep | grep -v tail || echo "No processes found"

kill:
	@pkill -f "volume_control.py" 2>/dev/null && echo "Killed" || echo "No processes to kill"

# ============================================================================
# Other
# ============================================================================

readme:
	@cat README.md

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
