# News Copilot Development Makefile

.PHONY: help install lint format test clean run

help:
	@echo "News Copilot Development Commands:"
	@echo "  make install   - Install Python dependencies"
	@echo "  make lint      - Run linting checks"
	@echo "  make format    - Auto-format code"
	@echo "  make test      - Run Python tests"
	@echo "  make clean     - Clean cache files"
	@echo "  make run       - Start local server"

install:
	pip install -r requirements.txt
	pre-commit install

lint:
	ruff check api/

format:
	black api/
	ruff check --fix api/

test:
	pytest -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/

run:
	python explain_with_grok.py --server