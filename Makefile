## News Copilot - Development Commands

.PHONY: install
install: ## Install all dependencies
	cd backend && pip install -r requirements.txt
	cd frontend && pnpm install

.PHONY: install-dev
install-dev: ## Install development dependencies
	cd backend && pip install -r requirements-dev.txt
	cd frontend && pnpm install

.PHONY: install-minimal
install-minimal: ## Install minimal dependencies for quick setup
	cd backend && pip install -r requirements-minimal.txt

.PHONY: migrate
migrate: ## Run Django migrations
	cd backend && python manage.py makemigrations
	cd backend && python manage.py migrate

.PHONY: run-api
run-api: ## Start Django API server
	@echo "🚀 Starting Django API server on http://localhost:8000..."
	cd backend && python manage.py runserver

.PHONY: run-web
run-web: ## Start Next.js web app
	@echo "🚀 Starting Next.js app on http://localhost:3000..."
	cd frontend && pnpm run dev

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
	cd web && pnpm run lint || true

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
		if [ -f .env.example ]; then \
			cp .env.example .env; \
			echo "✅ Created .env file from .env.example"; \
			echo "⚠️  Please update the values in .env with your actual credentials"; \
		else \
			echo "❌ .env.example not found!"; \
			exit 1; \
		fi; \
	else \
		echo ".env file already exists."; \
	fi

.PHONY: db-up
db-up: ## Start database containers
	@echo "🚀 Starting PostgreSQL and MongoDB containers..."
	docker-compose up -d
	@echo "⏳ Waiting for databases to be ready..."
	@sleep 5
	@echo "✅ Databases are running!"
	@echo "PostgreSQL: localhost:5433"
	@echo "MongoDB: localhost:27018"

.PHONY: db-down
db-down: ## Stop database containers
	@echo "🛑 Stopping database containers..."
	docker-compose down
	@echo "✅ Databases stopped!"

.PHONY: db-clean
db-clean: ## Stop and remove database containers and volumes
	@echo "🧹 Cleaning up database containers and volumes..."
	docker-compose down -v
	@echo "✅ Database cleanup complete!"

.PHONY: db-logs
db-logs: ## Show database container logs
	docker-compose logs -f

.PHONY: setup
setup: setup-env db-up install ## Complete setup: env, databases, and dependencies
	@echo "✅ Setup complete! Your development environment is ready."
	@echo "📝 Don't forget to update your .env file with actual credentials!"

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