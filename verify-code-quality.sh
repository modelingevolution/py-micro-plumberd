#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Running Code Quality Checks"
echo "========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -e . 2>/dev/null || true
pip install -q mypy black ruff pytest pytest-cov pytest-asyncio 2>/dev/null

# Run mypy type checking
echo ""
echo -e "${YELLOW}Running mypy type checking...${NC}"
if venv/bin/python -m mypy py_micro_plumberd --strict --warn-redundant-casts --warn-unused-ignores --no-implicit-reexport --disallow-untyped-defs; then
    echo -e "${GREEN}✓ Type checking passed${NC}"
else
    echo -e "${RED}✗ Type checking failed${NC}"
    TYPE_CHECK_FAILED=1
fi

# Check code formatting with black
echo ""
echo -e "${YELLOW}Checking code formatting with black...${NC}"
if venv/bin/python -m black --check py_micro_plumberd tests; then
    echo -e "${GREEN}✓ Code formatting is correct${NC}"
else
    echo -e "${RED}✗ Code formatting issues found${NC}"
    echo "Run 'venv/bin/python -m black py_micro_plumberd tests' to auto-format"
    FORMAT_FAILED=1
fi

# Run ruff linter
echo ""
echo -e "${YELLOW}Running ruff linter...${NC}"
if venv/bin/python -m ruff check py_micro_plumberd tests; then
    echo -e "${GREEN}✓ Linting passed${NC}"
else
    echo -e "${RED}✗ Linting issues found${NC}"
    LINT_FAILED=1
fi

# Run tests with coverage
echo ""
echo -e "${YELLOW}Running tests with coverage...${NC}"
if venv/bin/python -m pytest tests/ --cov=py_micro_plumberd --cov-report=term-missing --cov-fail-under=50; then
    echo -e "${GREEN}✓ Tests passed with sufficient coverage${NC}"
else
    echo -e "${RED}✗ Tests failed or insufficient coverage${NC}"
    TEST_FAILED=1
fi

# Summary
echo ""
echo "========================================="
echo -e "${GREEN}Code Quality Summary${NC}"
echo "========================================="

if [ -z "$TYPE_CHECK_FAILED" ]; then
    echo -e "${GREEN}✓${NC} Type checking: Passed (mypy strict mode)"
else
    echo -e "${RED}✗${NC} Type checking: Failed"
fi

if [ -z "$FORMAT_FAILED" ]; then
    echo -e "${GREEN}✓${NC} Code formatting: Passed (black)"
else
    echo -e "${RED}✗${NC} Code formatting: Failed"
fi

if [ -z "$LINT_FAILED" ]; then
    echo -e "${GREEN}✓${NC} Linting: Passed (ruff)"
else
    echo -e "${RED}✗${NC} Linting: Failed"
fi

if [ -z "$TEST_FAILED" ]; then
    echo -e "${GREEN}✓${NC} Tests: Passed with coverage ≥50%"
else
    echo -e "${RED}✗${NC} Tests: Failed or coverage <50%"
fi

echo ""
echo "========================================="

# Exit with error if any check failed
if [ -n "$TYPE_CHECK_FAILED" ] || [ -n "$FORMAT_FAILED" ] || [ -n "$LINT_FAILED" ] || [ -n "$TEST_FAILED" ]; then
    echo -e "${RED}Some checks failed. Please fix the issues above.${NC}"
    echo "========================================="
    exit 1
else
    echo -e "${GREEN}All code quality checks passed!${NC}"
    echo "========================================="
    exit 0
fi