#!/bin/bash
# FinAgent v1.0 Verification Test Runner
# Based on: V1_0_RELEASE_PLAN.md
# Purpose: Execute all checkpoint verification tests
# Date: 2025-11-19

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="/Users/weifanliao/PycharmProjects/finagent"
cd "$PROJECT_ROOT"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  FinAgent v1.0 Checkpoint Verification Test Suite           ║${NC}"
echo -e "${BLUE}║  Based on: V1_0_RELEASE_PLAN.md                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Track PIDs for cleanup
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "Stopping frontend (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
}

# Register cleanup on exit
trap cleanup EXIT

# Check if services are already running
check_backend() {
    curl -s http://localhost:8000/api/v1/wiki/overview > /dev/null 2>&1
}

check_frontend() {
    curl -s http://localhost:3000 > /dev/null 2>&1
}

# =============================================================================
# PHASE 1: BACKEND TESTS
# =============================================================================

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 1: Backend API Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Start backend if not running
if check_backend; then
    echo -e "${GREEN}✓ Backend already running${NC}"
else
    echo -e "${YELLOW}Starting backend server...${NC}"
    uv run uvicorn finagent.main:app --reload --port 8000 > /tmp/finagent_backend.log 2>&1 &
    BACKEND_PID=$!
    echo "Backend PID: $BACKEND_PID"

    # Wait for backend to start
    echo "Waiting for backend to be ready..."
    for i in {1..30}; do
        if check_backend; then
            echo -e "${GREEN}✓ Backend is ready${NC}"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""

    if ! check_backend; then
        echo -e "${RED}✗ Backend failed to start${NC}"
        cat /tmp/finagent_backend.log
        exit 1
    fi
fi

# Run backend tests
echo -e "\n${YELLOW}Running backend verification tests...${NC}"
echo ""

uv run pytest tests/test_verification_checkpoints.py -v -s --tb=short

BACKEND_EXIT_CODE=$?

if [ $BACKEND_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ Backend tests PASSED${NC}"
else
    echo -e "\n${RED}✗ Backend tests FAILED (exit code: $BACKEND_EXIT_CODE)${NC}"
fi

# =============================================================================
# PHASE 2: FRONTEND E2E TESTS
# =============================================================================

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 2: Frontend E2E Tests (Playwright)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Start frontend if not running
if check_frontend; then
    echo -e "${GREEN}✓ Frontend already running${NC}"
else
    echo -e "${YELLOW}Starting frontend dev server...${NC}"
    cd frontend
    npm run dev > /tmp/finagent_frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    echo "Frontend PID: $FRONTEND_PID"

    # Wait for frontend to start
    echo "Waiting for frontend to be ready..."
    for i in {1..60}; do
        if check_frontend; then
            echo -e "${GREEN}✓ Frontend is ready${NC}"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""

    if ! check_frontend; then
        echo -e "${RED}✗ Frontend failed to start${NC}"
        cat /tmp/finagent_frontend.log
        exit 1
    fi
fi

# Run Playwright tests
echo -e "\n${YELLOW}Running Playwright E2E tests...${NC}"
echo ""

cd frontend
npm exec playwright test e2e/verification-checkpoints.spec.ts

FRONTEND_EXIT_CODE=$?
cd ..

if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ Frontend tests PASSED${NC}"
else
    echo -e "\n${RED}✗ Frontend tests FAILED (exit code: $FRONTEND_EXIT_CODE)${NC}"
fi

# =============================================================================
# SUMMARY
# =============================================================================

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo "Backend Tests:  $([ $BACKEND_EXIT_CODE -eq 0 ] && echo -e "${GREEN}PASSED${NC}" || echo -e "${RED}FAILED${NC}")"
echo "Frontend Tests: $([ $FRONTEND_EXIT_CODE -eq 0 ] && echo -e "${GREEN}PASSED${NC}" || echo -e "${RED}FAILED${NC}")"
echo ""

TOTAL_EXIT_CODE=$((BACKEND_EXIT_CODE + FRONTEND_EXIT_CODE))

if [ $TOTAL_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ ALL VERIFICATION TESTS PASSED                            ║${NC}"
    echo -e "${GREEN}║  All checkpoints (1-6) are verified and working!            ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ✗ SOME TESTS FAILED                                         ║${NC}"
    echo -e "${RED}║  Please review the test output above for details.           ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
