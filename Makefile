# Makefile for IntelliTwin Research Project
# Linux / macOS / WSL compatible; see docs/development_setup.md for PowerShell commands.

.PHONY: help install install-dev format lint typecheck test test-cov check clean

help:
	@echo "Available commands:"
	@echo "  make install       Install package in editable mode"
	@echo "  make install-dev   Install package with development dependencies"
	@echo "  make format        Format code with ruff"
	@echo "  make lint          Run linter checks with ruff"
	@echo "  make typecheck     Run static type checks with mypy"
	@echo "  make test          Run automated test suite"
	@echo "  make test-cov      Run test suite with coverage report"
	@echo "  make check         Run format-check, lint, typecheck, and tests"
	@echo "  make clean         Remove build, cache, and temporary artifacts"

install:
	pip install -e .

install-dev:
	pip install -e .[dev]

format:
	ruff format src tests
	ruff check --fix src tests

lint:
	ruff format --check src tests
	ruff check src tests

typecheck:
	mypy src tests

test:
	pytest

test-cov:
	pytest --cov=src/intellitwin --cov-report=term-missing tests

check: lint typecheck test

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
