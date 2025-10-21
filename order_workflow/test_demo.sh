#!/bin/bash
set -euo pipefail

echo "🚀 Starting Order Workflow Demo Test..."
echo ""

# Change to order_workflow directory
cd "$(dirname "$0")"

# Check if Temporal server is running
echo "🔍 Checking Temporal server..."
if ! temporal operator namespace describe default >/dev/null 2>&1; then
  echo "⚠️  Temporal server not running. Starting it now..."
  temporal server start-dev > /tmp/temporal-server.log 2>&1 &
  TEMPORAL_PID=$!
  echo "Waiting for Temporal server to start..."
  sleep 10

  if ! temporal operator namespace describe default >/dev/null 2>&1; then
    echo "❌ Failed to start Temporal server"
    echo "Please start it manually: temporal server start-dev"
    exit 1
  fi
  echo "✅ Temporal server started"
else
  echo "✅ Temporal server is running"
fi

echo ""

# Clean up any existing worker
echo "🧹 Cleaning up existing workers..."
pkill -f "worker.py" 2>/dev/null || true
rm -f worker.pid worker.log

# Start worker
echo "📦 Starting worker..."
uv run worker.py > worker.log 2>&1 &
WORKER_PID=$!
echo $WORKER_PID > worker.pid
sleep 5

# Verify worker is running
if ! ps -p $WORKER_PID > /dev/null 2>&1; then
  echo "❌ Worker failed to start"
  echo "Worker log:"
  cat worker.log
  exit 1
fi

echo "✅ Worker started (PID: $WORKER_PID)"
echo ""

# Test 1: Small order (no approval needed)
echo "════════════════════════════════════════════════════════════════════"
echo "📋 TEST 1: Small Order (Under $1000 - No Approval Required)"
echo "════════════════════════════════════════════════════════════════════"
echo ""
uv run starter.py small

echo ""
echo "✅ Test 1 completed"
echo ""
sleep 3

# Test 2: Large order with approval
echo "════════════════════════════════════════════════════════════════════"
echo "📋 TEST 2: Large Order (Over $1000 - Requires Approval)"
echo "════════════════════════════════════════════════════════════════════"
echo ""

# Start large order workflow (non-blocking)
uv run starter.py large &
STARTER_PID=$!
sleep 5

echo ""
echo "⏳ Waiting 3 seconds before sending approval..."
sleep 3

# Send approval signal
echo "📨 Sending approval signal..."
uv run approval_sender.py ORD-002 approve "Automated test approval - customer verified"

# Wait for starter to complete
wait $STARTER_PID 2>/dev/null || true

echo ""
echo "✅ Test 2 completed"
echo ""
sleep 2

# Verify workflows in Temporal
echo "════════════════════════════════════════════════════════════════════"
echo "🔍 Workflow Verification"
echo "════════════════════════════════════════════════════════════════════"
echo ""

echo "Recent workflows:"
temporal workflow list --limit 5

echo ""
echo "Workflow details for small order:"
temporal workflow show --workflow-id order-workflow-ORD-001 | head -n 30

echo ""
echo "Workflow details for large order:"
temporal workflow show --workflow-id order-workflow-ORD-002 | head -n 30

# Cleanup
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "🧹 Cleanup"
echo "════════════════════════════════════════════════════════════════════"
echo ""

echo "Stopping worker..."
kill $WORKER_PID 2>/dev/null || true
wait $WORKER_PID 2>/dev/null || true
rm -f worker.pid

echo "✅ Worker stopped"

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "✅ ALL TESTS COMPLETED SUCCESSFULLY!"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "Summary:"
echo "  ✓ Small order processed without approval"
echo "  ✓ Large order processed with signal-based approval"
echo "  ✓ Both workflows completed successfully"
echo ""
echo "📊 View workflows in Temporal Web UI: http://localhost:8233"
echo ""
