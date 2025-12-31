.PHONY: help install test run-paper dashboard clean lint format

# Default target
help:
	@echo "AlphaWEEX - Makefile Commands"
	@echo "=============================="
	@echo ""
	@echo "Available commands:"
	@echo "  make install      - Install all dependencies"
	@echo "  make test         - Run all tests with pytest"
	@echo "  make run-paper    - Run AlphaWEEX in paper trading mode"
	@echo "  make dashboard    - Launch the Streamlit dashboard"
	@echo "  make lint         - Run code quality checks"
	@echo "  make format       - Format code with autopep8"
	@echo "  make clean        - Clean up temporary files and caches"
	@echo ""

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed successfully"

# Run tests
test:
	@echo "Running tests..."
	python -m pytest tests/ -v --tb=short
	@echo "✅ Tests completed"

# Run in paper trading mode
run-paper:
	@echo "Starting AlphaWEEX in paper trading mode..."
	@echo "⚠️  Make sure .env file is configured with API credentials"
	python main.py

# Launch dashboard
dashboard:
	@echo "Launching Streamlit dashboard..."
	@echo "Dashboard will open at http://localhost:8501"
	streamlit run dashboard/app.py

# Run linting
lint:
	@echo "Running linting checks..."
	@pip install flake8 > /dev/null 2>&1 || true
	@flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
	@flake8 . --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics || true
	@echo "✅ Linting completed"

# Format code
format:
	@echo "Formatting code with autopep8..."
	@pip install autopep8 > /dev/null 2>&1 || true
	@autopep8 --in-place --aggressive --aggressive -r . || true
	@echo "✅ Code formatting completed"

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Quick start (install + test)
quickstart: install test
	@echo ""
	@echo "✅ AlphaWEEX is ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Configure .env file with your API credentials"
	@echo "  2. Run 'make run-paper' to start trading"
	@echo "  3. Run 'make dashboard' to view the dashboard"
	@echo ""
