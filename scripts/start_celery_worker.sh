#!/bin/bash
# Start Celery worker for FinAgent document processing

set -e

# Script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting FinAgent Celery Worker${NC}"
echo "================================"

# Check if Redis is running
echo -n "Checking Redis connection... "
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${RED}✗ Redis is not running${NC}"
    echo ""
    echo "Please start Redis first:"
    echo "  brew services start redis  (macOS)"
    echo "  sudo systemctl start redis (Linux)"
    echo "  redis-server               (manual)"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

# Start Celery worker
echo ""
echo -e "${BLUE}Starting Celery worker...${NC}"
echo ""

# Run with uv
exec uv run celery -A finagent.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=50 \
    --time-limit=600 \
    --soft-time-limit=540 \
    --logfile=logs/celery_worker.log \
    --pidfile=logs/celery_worker.pid

# Worker configuration:
# - loglevel=info: Show INFO level logs
# - concurrency=2: Run 2 worker processes
# - max-tasks-per-child=50: Restart worker after 50 tasks (prevents memory leaks)
# - time-limit=600: Hard limit 10 minutes per task
# - soft-time-limit=540: Soft limit 9 minutes (allows graceful cleanup)
# - logfile: Write logs to logs/celery_worker.log
# - pidfile: Store PID for process management
