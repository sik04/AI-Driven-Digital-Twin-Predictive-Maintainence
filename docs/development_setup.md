# Development Setup and Environment Guide

This document details the configuration of the local development environment for the IntelliTwin research project. Both Windows (PowerShell) and POSIX (Linux/macOS) workflows are fully documented.

---

## 1. Prerequisites

- **Python**: Version 3.10 or higher (Python 3.10, 3.11, 3.12, or 3.13).
- **Git**: Installed and configured with your name and email.
- **GitHub CLI (`gh`)**: Recommended for pull request workflows.

---

## 2. Environment Setup

### Windows (PowerShell)

1. Clone or navigate to the repository:
   ```powershell
   cd c:\www\AI-Driven-Digital-Twin-Predictive-Maintainence
   ```

2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   *(If script execution is disabled, enable it for your current process: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

3. Upgrade pip and install the package with development tools:
   ```powershell
   python -m pip install --upgrade pip
   pip install -e ".[dev]"
   ```

### POSIX (Linux / macOS / WSL)

1. Navigate to the repository:
   ```bash
   cd AI-Driven-Digital-Twin-Predictive-Maintainence
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Upgrade pip and install dependencies:
   ```bash
   python3 -m pip install --upgrade pip
   pip install -e ".[dev]"
   # Or using the Makefile:
   make install-dev
   ```

---

## 3. Development Commands and Quality Toolchain

The project enforces code formatting with `ruff`, strict static type checking with `mypy`, and unit testing with `pytest`.

### Code Formatting and Linting

- **Check formatting without modifying files**:
  ```powershell
  ruff format --check src tests
  ```
- **Apply automatic formatting**:
  ```powershell
  ruff format src tests
  ```
- **Run linter checks**:
  ```powershell
  ruff check src tests
  ```
- **Run linter and apply safe automated fixes**:
  ```powershell
  ruff check --fix src tests
  ```

### Static Type Checking

- **Run strict type analysis**:
  ```powershell
  mypy src tests
  ```

### Running Tests

- **Run unit tests**:
  ```powershell
  pytest
  ```
- **Run unit tests with coverage reporting**:
  ```powershell
  pytest --cov=src/intellitwin --cov-report=term-missing tests
  ```

---

## 4. Pre-Commit / Pre-PR Verification Script

Before opening any pull request or pushing commits, execute the complete quality suite:

**PowerShell**:
```powershell
ruff format --check src tests
ruff check src tests
mypy src tests
pytest
```

**Make (POSIX)**:
```bash
make check
```
