#!/bin/bash

# Code quality verification script for py-micro-plumberd
# This script runs various code quality checks including type checking, linting, and tests

set -e  # Exit on error

echo "=== Code Quality Verification for py-micro-plumberd ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install package in editable mode with dev dependencies
echo "1. Installing dependencies..."
pip install -q --upgrade pip
pip install -q -e .
pip install -q -e ".[dev]"
pip install -q mypy types-python-dateutil
echo "   ✓ Dependencies installed"
echo

# Run Black formatting check
echo "2. Checking code formatting with Black..."
if black --check py_micro_plumberd tests; then
    echo -e "   ${GREEN}✓ Code formatting is correct${NC}"
else
    echo -e "   ${YELLOW}⚠ Code needs formatting. Run: black py_micro_plumberd tests${NC}"
    echo "   To see the diff, run: black --diff py_micro_plumberd tests"
fi
echo

# Run Ruff linting
echo "3. Running Ruff linter..."
if ruff check py_micro_plumberd tests; then
    echo -e "   ${GREEN}✓ No linting issues found${NC}"
else
    echo -e "   ${RED}✗ Linting issues found${NC}"
    exit 1
fi
echo

# Run MyPy type checking
echo "4. Running MyPy type checker..."
if mypy py_micro_plumberd --strict; then
    echo -e "   ${GREEN}✓ Type checking passed${NC}"
else
    echo -e "   ${RED}✗ Type checking failed${NC}"
    echo "   Fix type errors or add type: ignore comments where appropriate"
    exit 1
fi
echo

# Check that py.typed file exists
echo "5. Checking type hints support..."
if [ -f "py_micro_plumberd/py.typed" ]; then
    echo -e "   ${GREEN}✓ py.typed marker file exists${NC}"
else
    echo -e "   ${RED}✗ py.typed file missing${NC}"
    echo "   Create py_micro_plumberd/py.typed to indicate type hints support"
    exit 1
fi
echo

# Run tests
echo "6. Running tests..."
if python -m pytest tests/ -v --tb=short; then
    echo -e "   ${GREEN}✓ All tests passed${NC}"
else
    echo -e "   ${RED}✗ Tests failed${NC}"
    exit 1
fi
echo

# Check for common issues
echo "7. Checking for common issues..."
ISSUES=0

# Check for print statements in library code (excluding examples)
if grep -r "print(" py_micro_plumberd/ --exclude-dir=__pycache__ 2>/dev/null; then
    echo -e "   ${YELLOW}⚠ Found print statements in library code${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Check for TODO comments
if grep -r "TODO" py_micro_plumberd/ tests/ --exclude-dir=__pycache__ 2>/dev/null; then
    echo -e "   ${YELLOW}⚠ Found TODO comments${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Check for unused imports
if ruff check py_micro_plumberd tests --select F401 2>/dev/null; then
    :
else
    echo -e "   ${YELLOW}⚠ Found unused imports${NC}"
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "   ${GREEN}✓ No common issues found${NC}"
fi
echo

# Deactivate virtual environment
deactivate

# Summary
echo "=== Summary ==="
echo -e "${GREEN}✅ Code quality verification complete!${NC}"
echo
echo "To fix formatting issues, run:"
echo "  source venv/bin/activate && black py_micro_plumberd tests"
echo
echo "To auto-fix some linting issues, run:"
echo "  source venv/bin/activate && ruff check --fix py_micro_plumberd tests"
echo