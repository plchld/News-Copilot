## News Copilot - Development Commands

.PHONY: install
install: ## Install all dependencies
	pip install -r requirements.txt
	cd web && npm install

.PHONY: migrate
migrate: ## Run API migration script
	python migrate_api.py

.PHONY: run-api
run-api: ## Start Flask API server only
	@echo "🚀 Starting API server on http://localhost:8080..."
	cd api && python index.py

.PHONY: run-web
run-web: ## Start Next.js web app only
	@echo "🚀 Starting web app on http://localhost:3000..."
	cd web && npm run dev

.PHONY: run-production
run-production: ## Start both servers together (mirrors Vercel deployment)
	@echo "🚀 Starting production-like deployment..."
	python dev_server.py

.PHONY: run
run: run-production ## Alias for run-production

.PHONY: test
test: ## Run all tests with coverage
	python run_tests.py

.PHONY: test-api
test-api: ## Test API endpoints
	@echo "Testing API health..."
	@curl -s http://localhost:8080/api/health | python -m json.tool
	@echo "\nTesting analysis types..."
	@curl -s http://localhost:8080/api/analysis/types | python -m json.tool

.PHONY: test-sites
test-sites: ## Test supported news sites
	python test_sites_robust.py

.PHONY: test-unit
test-unit: ## Run unit tests only
	pytest tests/unit -v

.PHONY: test-integration
test-integration: ## Run integration tests only
	pytest tests/integration -v

.PHONY: lint
lint: ## Run linters
	@echo "Linting Python code..."
	flake8 api/ --max-line-length=120 --exclude=__pycache__,venv,deprecated || true
	@echo "Linting TypeScript code..."
	cd web && npm run lint || true

.PHONY: format
format: ## Format code
	@echo "Formatting Python code..."
	black api/ --line-length=120 --exclude=venv,deprecated || true
	@echo "Formatting TypeScript code..."
	cd web && npx prettier --write "src/**/*.{ts,tsx}" || true

.PHONY: clean
clean: ## Clean temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true
	rm -rf web/.next 2>/dev/null || true
	rm -rf web/node_modules/.cache 2>/dev/null || true

.PHONY: setup-env
setup-env: ## Create .env file from example
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		echo "# API Keys" > .env; \
		echo "XAI_API_KEY=" >> .env; \
		echo "" >> .env; \
		echo "# Supabase Configuration" >> .env; \
		echo "SUPABASE_URL=" >> .env; \
		echo "SUPABASE_ANON_KEY=" >> .env; \
		echo "SUPABASE_SERVICE_KEY=" >> .env; \
		echo "" >> .env; \
		echo "# Local Development" >> .env; \
		echo "BASE_URL=http://localhost:8080" >> .env; \
		echo "FLASK_PORT=8080" >> .env; \
		echo "DEBUG_MODE=true" >> .env; \
		echo "AUTH_REQUIRED=false" >> .env; \
		echo "" >> .env; \
		echo ".env file created. Please add your API keys."; \
	else \
		echo ".env file already exists."; \
	fi

.PHONY: debug-grok
debug-grok: ## Debug Grok API connection
	python debug/debug_grok_endpoint.py

.PHONY: analyze
analyze: ## Analyze a URL (interactive)
	@read -p "Enter URL: " url; \
	curl -s "http://localhost:8080/api/analysis/stream?url=$$url"

.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)