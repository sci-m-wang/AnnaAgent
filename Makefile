.PHONY: all sync format lint test tests integration_tests coverage help

UV ?= $(if $(wildcard $(HOME)/.local/bin/uv),$(HOME)/.local/bin/uv,uv)

all: help

sync:
	$(UV) sync --all-groups

format:
	$(UV) run ruff format src tests

lint:
	./scripts/check_pydantic.sh . || true
	./scripts/lint_imports.sh || true
	$(UV) run ruff check src tests

coverage:
	$(UV) run pytest --cov=anna_agent \
	--cov-report xml \
	--cov-report term-missing:skip-covered tests/unit_tests

test tests:
	$(UV) run pytest tests/unit_tests

integration_tests:
	$(UV) run pytest tests/integration_tests

help:
	@echo -- LINTING --
	@echo "sync                 - create/update the uv project environment"
	@echo "format               - run code formatters"
	@echo "lint                 - run linters"
	@echo -- TESTS --
	@echo "coverage             - run unit tests with coverage"
	@echo "test                 - run unit tests"
	@echo "integration_tests    - run integration tests"
