# Temporal Sample Application - Code Agent Guidance

This document provides step-by-step guidance for a code agent to run and manage the Temporal sample application.

## Application Structure

This application splits the Temporal components into separate files:
- `shared.py`: Common data structures
- `activities.py`: Activity definitions  
- `workflow.py`: Workflow definitions
- `worker.py`: Long-running worker service
- `starter.py`: Workflow starter client

## Prerequisites

### Install Temporal CLI
Check if Temporal server is available:
```bash
temporal --version
```

If not installed:
- **Mac**: `brew install temporal`
- **Windows amd64**: https://temporal.download/cli/archive/latest?platform=windows&arch=amd64
- **Windows arm64**: https://temporal.download/cli/archive/latest?platform=windows&arch=arm64
- **Linux amd64**: https://temporal.download/cli/archive/latest?platform=linux&arch=amd64
- **Linux arm64**: https://temporal.download/cli/archive/latest?platform=linux&arch=arm64

### Start Temporal Development Server
Check if server is running:
```bash
curl -f http://localhost:7233 > /dev/null 2>&1 && echo "Server running" || echo "Server not running"
```

If not running, start it:
```bash
temporal server start-dev
```

**Important**: Keep this server running throughout development. No need to clean up after workflows.

## Running Workflows - Standard Process

### Step 1: Start Worker Service
```bash
cd sample_application
./worker.py &
WORKER_PID=$!
echo $WORKER_PID > worker.pid
echo "Worker started with PID: $WORKER_PID"
```

### Step 2: Wait for Worker Ready
Monitor worker logs to ensure it's ready:
```bash
# Wait for "Worker ready" message in logs
sleep 3
echo "Checking if worker is ready..."
```

If worker fails to start, check logs and stop before proceeding:
```bash
if ! ps -p $WORKER_PID > /dev/null; then
    echo "Worker failed to start! Check logs and fix errors."
    exit 1
fi
```

### Step 3: Start Workflow
```bash
./starter.py "YourName"
```

You'll want to run this on a timeout (e.g. initially 10s) to ensure that you don't stall forever if a workflow gets stuck.

### Step 4: Clean Up Worker
```bash
# Kill worker process
kill $WORKER_PID
wait $WORKER_PID 2>/dev/null
rm -f worker.pid
echo "Worker stopped and cleaned up"
```

## Complete Workflow Execution Script

Here's a complete script that follows the above process:

```bash
#!/bin/bash
set -e

cd sample_application

# Check if Temporal server is running
if ! curl -f http://localhost:7233 > /dev/null 2>&1; then
    echo "Temporal server not running. Starting..."
    temporal server start-dev &
    sleep 5
fi

# Start worker
echo "Starting worker..."
./worker.py &
WORKER_PID=$!
echo $WORKER_PID > worker.pid

# Wait for worker to be ready
sleep 3
if ! ps -p $WORKER_PID > /dev/null; then
    echo "ERROR: Worker failed to start!"
    exit 1
fi

echo "Worker ready with PID: $WORKER_PID"

# Run workflow
echo "Starting workflow..."
./starter.py "CodeAgent"

# Cleanup
echo "Cleaning up..."
kill $WORKER_PID
wait $WORKER_PID 2>/dev/null
rm -f worker.pid
echo "Done!"
```

## Development Workflow - Code Updates

When updating code and testing changes:

### Step 1: Stop Any Running Workers
```bash
# Check for existing worker PIDs
if [ -f worker.pid ]; then
    OLD_PID=$(cat worker.pid)
    if ps -p $OLD_PID > /dev/null; then
        echo "Stopping existing worker (PID: $OLD_PID)"
        kill $OLD_PID
        wait $OLD_PID 2>/dev/null
    fi
    rm -f worker.pid
fi

# Double-check no workers are running
pkill -f "worker.py" || true
```

### Step 2: Start Fresh Worker
```bash
# Start new worker with updated code
./worker.py &
WORKER_PID=$!
echo $WORKER_PID > worker.pid
sleep 3

# Verify worker started successfully
if ! ps -p $WORKER_PID > /dev/null; then
    echo "ERROR: Updated worker failed to start!"
    exit 1
fi
```

### Step 3: Test Updated Workflow
```bash
./starter.py "TestUpdatedCode"
```

### Step 4: Clean Up
```bash
kill $WORKER_PID
wait $WORKER_PID 2>/dev/null
rm -f worker.pid
```

## Error Handling Guidelines

1. **Worker Startup Errors**: Always check if worker process is still running after startup. If not, investigate logs before starting workflows.

2. **Workflow Timeouts**: The starter script has a 30-second timeout. If workflows consistently timeout, increase the timeout value in `starter.py`.

3. **Connection Errors**: Ensure Temporal server is running on `localhost:7233`.

4. **Process Management**: Always track worker PIDs and clean up processes to avoid resource leaks.

## Logging and Debugging

- Worker logs to stdout/stderr - redirect to file if needed: `./worker.py > worker.log 2>&1 &`
- Check worker status: `ps -p $(cat worker.pid)`
- Monitor worker logs: `tail -f worker.log`

## Sample Application Development Guidance

### File Structure Best Practices
When creating Temporal sample applications, follow this component separation:
- **shared.py**: All dataclasses and shared types (enables backward-compatible schema evolution)
- **activities.py**: Activity function definitions only
- **workflow.py**: Workflow class definitions only
- **worker.py**: Long-running service with proper logging and PID management
- **starter.py**: Client script with timeout handling and error management

### Import Strategy for Standalone Scripts
Use relative imports within the same directory (e.g., `from activities import compose_greeting`) rather than absolute package imports. This allows scripts to run directly without complex Python path setup while using PEP 723 inline dependencies.

### Worker Service Requirements
Every worker.py should include:
- **PID file creation**: Write process ID to `worker.pid` for management
- **Startup logging**: Log connection status and ready state
- **Process verification**: Agents can check `ps -p $(cat worker.pid)` to verify worker health
- **Graceful error handling**: Log failures clearly for debugging

### Starter Script Requirements  
Every starter.py should include:
- **Timeout protection**: Use `asyncio.wait_for()` with reasonable timeout (30+ seconds)
- **Error handling**: Catch and log connection/execution failures
- **Exit codes**: Return non-zero on failure for script automation
- **Parameter flexibility**: Accept command-line arguments with sensible defaults

### Development Workflow Support
Structure code to support iterative development:
- Always stop existing workers before starting new ones
- Verify worker startup before executing workflows
- Use consistent task queue names across worker and starter
- Include logging to track execution flow and debug issues

### Code Agent Automation Patterns
Design samples to be automation-friendly:
- Include verification steps (server connectivity, worker health)
- Use timeouts to prevent hanging processes
- Provide clear success/failure indicators
- Enable background process management with PID tracking

## Reference Code Examples

### Shared Data Structures (shared.py)
```python
"""Shared data structures for the Temporal greeting application."""

from dataclasses import dataclass


@dataclass
class ComposeGreetingInput:
    """Input parameters for the compose_greeting activity.
    
    While we could use multiple parameters in the activity, Temporal strongly
    encourages using a single dataclass instead which can have fields added to it
    in a backwards-compatible way.
    """
    greeting: str
    name: str
```

### Activity Definition (activities.py)
```python
"""Activity definitions for the Temporal greeting application."""

from temporalio import activity
from shared import ComposeGreetingInput


@activity.defn
def compose_greeting(input: ComposeGreetingInput) -> str:
    """Basic activity that logs and does string concatenation."""
    activity.logger.info("Running activity with parameter %s" % input)
    return f"{input.greeting}, {input.name}!"
```

### Workflow Definition (workflow.py)
```python
"""Workflow definitions for the Temporal greeting application."""

from datetime import timedelta

from temporalio import workflow
from activities import compose_greeting
from shared import ComposeGreetingInput


@workflow.defn
class GreetingWorkflow:
    """Basic workflow that logs and invokes an activity."""
    
    @workflow.run
    async def run(self, name: str) -> str:
        """Execute the greeting workflow."""
        workflow.logger.info("Running workflow with parameter %s" % name)
        return await workflow.execute_activity(
            compose_greeting,
            ComposeGreetingInput("Hello", name),
            start_to_close_timeout=timedelta(seconds=10),
        )
```

### Worker Service (worker.py)
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "temporalio>=1.0.0",
# ]
# ///

"""Worker service for the Temporal greeting application.

This runs as a long-running service that polls for tasks from the Temporal server.
Should be started before running any workflows.
"""

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker
from activities import compose_greeting
from workflow import GreetingWorkflow


async def main() -> None:
    """Start the worker service."""
    # Enable logging to track worker startup and activity
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Write PID for process management
    pid = os.getpid()
    with open("worker.pid", "w") as f:
        f.write(str(pid))
    logger.info(f"Worker starting with PID: {pid}")
    
    # Connect to Temporal server
    client = await Client.connect("localhost:7233")
    logger.info("Connected to Temporal server at localhost:7233")
    
    # Start the worker
    async with Worker(
        client,
        task_queue="hello-activity-task-queue",
        workflows=[GreetingWorkflow],
        activities=[compose_greeting],
        # Non-async activities require an executor;
        # a thread pool executor is recommended.
        activity_executor=ThreadPoolExecutor(5),
    ):
        logger.info("Worker started and polling for tasks on queue: hello-activity-task-queue")
        logger.info("Worker ready - workflows can now be started")
        
        # Keep the worker running indefinitely
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Worker shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
```

### Starter Script (starter.py)
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "temporalio>=1.0.0",
# ]
# ///

"""Workflow starter for the Temporal greeting application.

This script starts workflows and should be run after the worker is already running.
"""

import asyncio
import logging
import sys
from temporalio.client import Client
from workflow import GreetingWorkflow


async def main() -> None:
    """Start a workflow execution."""
    # Enable logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Get name from command line argument or use default
    name = sys.argv[1] if len(sys.argv) > 1 else "World"
    
    try:
        # Connect to Temporal server
        client = await Client.connect("localhost:7233")
        logger.info(f"Starting workflow for name: {name}")
        
        # Execute the workflow with timeout
        result = await asyncio.wait_for(
            client.execute_workflow(
                GreetingWorkflow.run,
                name,
                id=f"hello-activity-workflow-{name}",
                task_queue="hello-activity-task-queue",
            ),
            timeout=30.0  # 30 second timeout to prevent hanging
        )
        
        print(f"Result: {result}")
        logger.info("Workflow completed successfully")
        
    except asyncio.TimeoutError:
        logger.error("Workflow execution timed out after 30 seconds")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
```
