# Makefile for SzalasApp - Quick Commands

.PHONY: help install update clean test run docker-build docker-run docker-stop deploy

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies with Poetry
	cd app && poetry install --with dev,prod

update:  ## Update dependencies
	cd app && poetry update

lock:  ## Regenerate poetry.lock
	cd app && poetry lock --no-update

clean:  ## Clean cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache htmlcov .tox

test:  ## Run tests
	cd app && poetry run pytest

format:  ## Format code with Black
	cd app && poetry run black src/ app.py scripts/

lint:  ## Lint code with Flake8
	cd app && poetry run flake8 src/ app.py scripts/

type-check:  ## Type check with mypy
	cd app && poetry run mypy src/ app.py

run:  ## Run Flask development server
	cd app && poetry run python app.py

run-prod:  ## Run with Gunicorn (production mode)
	cd app && poetry run gunicorn --bind 0.0.0.0:8080 --workers 4 app:app

docker-build:  ## Build Docker image
	docker build -t szalasapp:latest .

docker-run:  ## Run Docker container
	docker-compose up -d

docker-stop:  ## Stop Docker container
	docker-compose down

docker-logs:  ## View Docker logs
	docker-compose logs -f

docker-shell:  ## Open shell in running container
	docker exec -it szalasapp /bin/bash

deploy-gcr:  ## Build and push to Google Container Registry
	@if [ -z "$(PROJECT_ID)" ]; then echo "Error: PROJECT_ID not set. Use: make deploy-gcr PROJECT_ID=your-project-id"; exit 1; fi
	gcloud builds submit --tag gcr.io/$(PROJECT_ID)/szalasapp

deploy-cloud-run:  ## Deploy to Google Cloud Run
	@if [ -z "$(PROJECT_ID)" ]; then echo "Error: PROJECT_ID not set. Use: make deploy-cloud-run PROJECT_ID=your-project-id"; exit 1; fi
	gcloud run deploy szalasapp \
		--image gcr.io/$(PROJECT_ID)/szalasapp:latest \
		--platform managed \
		--region europe-central2 \
		--allow-unauthenticated

setup-env:  ## Create .env from template
	@if [ ! -f .env ]; then cp .env.example .env; echo ".env file created. Please edit it with your values."; else echo ".env already exists."; fi

check:  ## Run all checks (format, lint, type-check, test)
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) test

dev-setup:  ## Complete development setup
	$(MAKE) install
	$(MAKE) setup-env
	@echo "Development setup complete! Edit .env and run 'make run' to start."

