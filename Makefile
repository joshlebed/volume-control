.PHONY: help install deploy reload restart stop start status logs logs-service run debug test-qlc clean

# Default target
help:
	@echo "volume-control - Makefile commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install Python dependencies in venv"
	@echo "  make deploy       Deploy systemd service (requires sudo)"
	@echo ""
	@echo "Service Operations:"
	@echo "  make start        Start the systemd service"
	@echo "  make stop         Stop the systemd service"
	@echo "  make restart      Restart the systemd service"
	@echo "  make reload       Reload systemd after service file changes"
	@echo "  make status       Show service status"
	@echo ""
	@echo "Logs:"
	@echo "  make logs         Tail application logs"
	@echo "  make logs-service Tail systemd service logs"
	@echo ""
	@echo "Development:"
	@echo "  make run          Run in foreground (stop service first)"
	@echo "  make debug        Stop service and run in foreground"
	@echo "  make test-qlc     Test QLC+ connection"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean        Remove Python cache files"

# Paths
VENV := /home/pi/code/volume-control/.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
SRC := /home/pi/code/volume-control/src
SERVICE := volume_control.service

# ============================================================================
# Setup
# ============================================================================

install:
	@echo "Installing dependencies..."
	$(PIP) install -r $(SRC)/requirements.txt

$(VENV):
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)

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
	$(PYTHON) $(SRC)/volume_control.py

debug: stop run

test-qlc:
	@echo "Testing QLC+ connection..."
	@$(PYTHON) -c "from qlcplus import QLCPlusClient; c = QLCPlusClient(host='192.168.0.221'); c.connect(); print('Connected to QLC+'); print('Functions:', c.get_functions_list()); c.disconnect()"

# ============================================================================
# Maintenance
# ============================================================================

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
