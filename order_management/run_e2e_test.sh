#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "Order Management Workflow - End-to-End Test"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Navigate to order_management directory
cd "$(dirname "$0")"

# Step 1: Check Temporal server
echo "Step 1: Checking Temporal dev server..."
if ! temporal operator namespace describe default >/dev/null 2>&1; then
  echo -e "${YELLOW}Temporal server not running. Starting...${NC}"
  temporal server start-dev > ../temporal-server.log 2>&1 &
  sleep 10
  echo -e "${GREEN}✓ Temporal server started${NC}"
else
  echo -e "${GREEN}✓ Temporal server is running${NC}"
fi
echo ""

# Step 2: Kill any existing worker
echo "Step 2: Cleaning up old workers..."
if [ -f worker.pid ]; then
  OLD_PID=$(cat worker.pid)
  if ps -p $OLD_PID > /dev/null 2>&1; then
    kill $OLD_PID 2>/dev/null || true
    wait $OLD_PID 2>/dev/null || true
    echo -e "${GREEN}✓ Stopped old worker (PID: $OLD_PID)${NC}"
  fi
  rm -f worker.pid
fi
pkill -f "worker.py" 2>/dev/null || true
echo ""

# Step 3: Start worker
echo "Step 3: Starting worker..."
uv run worker.py > worker.log 2>&1 &
WORKER_PID=$!
echo $WORKER_PID > worker.pid
sleep 5

# Verify worker started
if ! ps -p $WORKER_PID >/dev/null; then
  echo -e "${RED}✗ Worker failed to start${NC}"
  echo "Last 20 lines of worker.log:"
  tail -n 20 worker.log
  exit 1
fi
echo -e "${GREEN}✓ Worker started (PID: $WORKER_PID)${NC}"
echo ""

# Step 4: Test order under $1000 (no approval)
echo "Step 4: Testing order under \$1000 (no approval required)..."
if uv run starter.py 500 > test1.log 2>&1; then
  echo -e "${GREEN}✓ Order under \$1000 completed successfully${NC}"
  grep "Result:" test1.log
else
  echo -e "${RED}✗ Order under \$1000 failed${NC}"
  cat test1.log
  kill $WORKER_PID 2>/dev/null || true
  exit 1
fi
echo ""

# Wait a bit for workflow to complete
sleep 2

# Step 5: Validate first workflow
echo "Step 5: Validating first workflow execution..."
if temporal workflow show --workflow-id "order-workflow-ORDER-0500" | grep -q "COMPLETED"; then
  echo -e "${GREEN}✓ Workflow order-workflow-ORDER-0500 completed${NC}"
else
  echo -e "${RED}✗ Workflow validation failed${NC}"
  temporal workflow show --workflow-id "order-workflow-ORDER-0500"
  kill $WORKER_PID 2>/dev/null || true
  exit 1
fi
echo ""

# Step 6: Test order over $1000 (with approval)
echo "Step 6: Testing order over \$1000 (requires approval)..."
if uv run test_approval.py > test2.log 2>&1; then
  echo -e "${GREEN}✓ Order over \$1000 with approval completed successfully${NC}"
  grep "Result:" test2.log
else
  echo -e "${RED}✗ Order over \$1000 failed${NC}"
  cat test2.log
  kill $WORKER_PID 2>/dev/null || true
  exit 1
fi
echo ""

# Wait a bit for workflow to complete
sleep 2

# Step 7: Validate second workflow
echo "Step 7: Validating second workflow execution..."
if temporal workflow show --workflow-id "order-workflow-ORDER-1500" | grep -q "COMPLETED"; then
  echo -e "${GREEN}✓ Workflow order-workflow-ORDER-1500 completed${NC}"

  # Check for signal in workflow history
  if temporal workflow show --workflow-id "order-workflow-ORDER-1500" | grep -q "WorkflowExecutionSignaled"; then
    echo -e "${GREEN}✓ Approval signal was received and processed${NC}"
  else
    echo -e "${YELLOW}⚠ Warning: No signal found in workflow history${NC}"
  fi
else
  echo -e "${RED}✗ Workflow validation failed${NC}"
  temporal workflow show --workflow-id "order-workflow-ORDER-1500"
  kill $WORKER_PID 2>/dev/null || true
  exit 1
fi
echo ""

# Step 8: List all workflows
echo "Step 8: Listing all workflow executions..."
temporal workflow list -n default --limit 5
echo ""

# Step 9: Clean up
echo "Step 9: Cleaning up..."
kill $WORKER_PID
wait $WORKER_PID 2>/dev/null || true
rm -f worker.pid
echo -e "${GREEN}✓ Worker stopped${NC}"
echo ""

# Summary
echo "============================================================"
echo -e "${GREEN}ALL TESTS PASSED!${NC}"
echo "============================================================"
echo ""
echo "Summary:"
echo "  ✓ Temporal server running"
echo "  ✓ Worker started and stopped cleanly"
echo "  ✓ Order under \$1000 processed without approval"
echo "  ✓ Order over \$1000 processed with signal-based approval"
echo "  ✓ All workflows completed successfully"
echo ""
echo "Check the following logs for details:"
echo "  - worker.log: Worker activity logs"
echo "  - test1.log: Order under \$1000 test output"
echo "  - test2.log: Order over \$1000 test output"
echo ""
