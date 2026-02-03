#!/bin/bash
###############################################################################
# Docker-based Testing Script
# Run all tests in isolated Docker containers
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_header "Docker-based Test Suite"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Use docker-compose or docker compose
DOCKER_COMPOSE="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
fi

# Build test image
print_header "Building Test Image"
echo "Building Docker test environment..."
$DOCKER_COMPOSE -f docker-compose.test.yml build

# Run tests
print_header "Running Unit Tests"
$DOCKER_COMPOSE -f docker-compose.test.yml run --rm test

# Run linting
print_header "Running Linting"
$DOCKER_COMPOSE -f docker-compose.test.yml run --rm lint

# Run shell validation
print_header "Running Shell Validation"
$DOCKER_COMPOSE -f docker-compose.test.yml run --rm shellcheck

# Cleanup
print_header "Cleanup"
$DOCKER_COMPOSE -f docker-compose.test.yml down

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ All Docker tests completed successfully${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

echo "Coverage report generated in: coverage/htmlcov/index.html"
