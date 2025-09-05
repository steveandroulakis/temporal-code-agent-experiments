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

### Install UV Python Package Manager
Check if UV is available:
```bash
uv --version
```

If not installed:
- **Mac**: `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows**: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **Linux**: `curl -LsSf https://astral.sh/uv/install.sh | sh`

Verify installation and Python availability:
```bash
uv --version
uv python list  # Show available Python versions
```

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

## Project Setup and Dependency Management

### Initialize Project Structure
For new Temporal projects, use UV's project initialization:
```bash
# Create new project with proper structure
uv init temporal-sample-app
cd temporal-sample-app

# Or manually in existing directory
mkdir temporal-sample-app && cd temporal-sample-app
uv init --app
```

This creates:
- `pyproject.toml`: Project configuration and dependencies
- `.python-version`: Pin Python version for the project
- `README.md`: Project documentation
- `src/` directory: Recommended code organization

### Setup Virtual Environment and Dependencies
```bash
# Create local virtual environment (recommended)
uv venv

# Activate environment (optional - uv run handles this automatically)
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate     # Windows

# Install core Temporal dependencies
uv add temporalio

# Add development dependencies
uv add --dev pytest ruff mypy

# Verify installation
uv pip list
```

### Configure pyproject.toml for Temporal Projects
```toml
[project]
name = "temporal-sample-app"
version = "0.1.0"
description = "Temporal workflow sample application"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "temporalio>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
```

### Alternative: PEP 723 Inline Scripts (for simple samples)
For standalone scripts without full project setup:
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "temporalio>=1.0.0",
# ]
# ///
```

## Running Workflows - Standard Process

### Step 1: Start Worker Service
```bash
cd sample_application
# Using UV to run the worker script
uv run worker.py &
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
uv run starter.py "YourName"
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
uv run worker.py &
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
uv run starter.py "CodeAgent"

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
uv run worker.py &
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
uv run starter.py "TestUpdatedCode"
```

### Step 4: Clean Up
```bash
kill $WORKER_PID
wait $WORKER_PID 2>/dev/null
rm -f worker.pid
```

## Error Handling Guidelines

1. **Worker Startup Errors**: Always check if worker process is still running after startup. If not, investigate logs before starting workflows.

2. **Connection Errors**: Ensure Temporal server is running on `localhost:7233`.

3. **Process Management**: Always track worker PIDs and clean up processes to avoid resource leaks.

## Logging and Debugging

- Worker logs to stdout/stderr - redirect to file if needed: `uv run worker.py > worker.log 2>&1 &`
- Check worker status: `ps -p $(cat worker.pid)`
- Monitor worker logs: `tail -f worker.log`

## Dependency Management Best Practices

### UV-Specific Recommendations for Temporal Projects

#### Fast Development Iteration
```bash
# Use UV's sync command to keep environment up to date
uv sync

# Add new dependencies during development
uv add requests httpx  # Runtime dependencies
uv add --dev black isort pytest-asyncio  # Development dependencies

# Lock dependencies for reproducible builds
# UV automatically maintains uv.lock file
```

#### Dependency Groups Organization
```bash
# Add testing dependencies
uv add --group test pytest pytest-asyncio pytest-mock

# Add linting/formatting dependencies  
uv add --group lint ruff mypy black

# Install specific groups
uv sync --group test
uv sync --group lint
```

#### Environment Management
```bash
# Check environment status
uv pip check  # Verify no dependency conflicts

# Update all dependencies
uv lock --upgrade

# Clean rebuild of environment
uv sync --reinstall

# Export requirements for other tools
uv export --format requirements-txt > requirements.txt
```

#### Performance Tips for Code Agents
```bash
# Use UV's global cache to speed up repeated setups
uv cache info  # Check cache status
uv cache clean  # Clean if needed

# Parallel processing for multiple projects
uv sync --jobs 4  # Use multiple CPU cores

# Skip unnecessary steps in CI/automation
uv sync --frozen  # Don't update lock file, just install
```

## Sample Application Development Guidance

### File Structure Best Practices
When creating Temporal sample applications, follow this component separation:
- **shared.py**: All dataclasses and shared types (enables backward-compatible schema evolution)
- **activities.py**: Activity function definitions only
- **workflow.py**: Workflow class definitions only
- **worker.py**: Long-running service with proper logging and PID management
- **starter.py**: Client script with timeout handling and error management

### Import Strategy for Standalone Scripts
Use relative imports within the same directory (e.g., `from activities import compose_greeting`) rather than absolute package imports. This allows scripts to run directly with `uv run` without complex Python path setup while using PEP 723 inline dependencies or project-based dependencies.

### Worker Service Requirements
Every worker.py should include:
- **PID file creation**: Write process ID to `worker.pid` for management
- **Startup logging**: Log connection status and ready state
- **Process verification**: Agents can check `ps -p $(cat worker.pid)` to verify worker health  
- **UV execution compatibility**: Support both `uv run worker.py` and direct execution
- **Graceful error handling**: Log failures clearly for debugging

### Starter Script Requirements  
Every starter.py should include:
- **Error handling**: Catch and log connection/execution failures
- **Exit codes**: Return non-zero on failure for script automation
- **Parameter flexibility**: Accept command-line arguments with sensible defaults
- **UV execution compatibility**: Support both `uv run starter.py` and direct execution

### Development Workflow Support
Structure code to support iterative development:
- Always stop existing workers before starting new ones
- Verify worker startup before executing workflows
- Use consistent task queue names across worker and starter
- Include logging to track execution flow and debug issues

### Timeout and Retry Policy Best Practices
Configure activities with appropriate timeouts and retry policies:
- **Activity Timeouts**: Use `schedule_to_close_timeout` for activities (typically 10-60 seconds)
- **Retry Policies**: Configure RetryPolicy with appropriate backoff and maximum attempts
- **Error Handling**: Use `non_retryable_error_types` for errors that shouldn't be retried
- **Activity Method Pattern**: For activity classes, use `workflow.execute_activity_method()` syntax

Example activity execution patterns:
```python
# Basic activity with timeout and retry
result = await workflow.execute_activity(
    my_activity,
    input_data,
    schedule_to_close_timeout=timedelta(seconds=20),
    retry_policy=RetryPolicy(
        initial_interval=timedelta(seconds=1),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(seconds=100),
        maximum_attempts=3,
    )
)

# Activity method pattern (for activity classes)
response = await workflow.execute_activity_method(
    MyActivities.process_data,
    input_data,
    schedule_to_close_timeout=timedelta(seconds=30),
    retry_policy=default_retry_policy,
)
```

### Code Agent Automation Patterns
Design samples to be automation-friendly:
- Include verification steps (server connectivity, worker health)
- Use timeouts to prevent hanging processes
- Provide clear success/failure indicators
- Enable background process management with PID tracking

## UV-Specific Troubleshooting

### Common UV Environment Issues
```bash
# UV not found
which uv  # Verify UV is in PATH
uv --version  # Check UV version

# Python version conflicts
uv python list  # Show available Python versions  
uv python install 3.11  # Install specific Python version
uv python pin 3.11  # Pin project to specific version

# Virtual environment issues
uv venv --python 3.11  # Recreate with specific Python version
rm -rf .venv && uv venv  # Clean rebuild environment
```

### Dependency Resolution Problems
```bash
# Dependency conflicts
uv pip check  # Identify conflicts
uv tree  # Visualize dependency tree
uv lock --resolve-mode lowest-direct  # Try different resolution strategy

# Lock file issues
rm uv.lock && uv lock  # Regenerate lock file
uv sync --reinstall  # Force reinstall all packages
```

### Performance Optimization
```bash
# Cache management
uv cache info  # Check cache size and location
uv cache clean --pypi  # Clean PyPI cache if needed
uv cache dir  # Show cache directory location

# Faster CI builds
uv sync --frozen  # Skip lock file updates in CI
uv export --format requirements-txt | uv pip install -r -  # For Docker builds
```

### Script Execution Debugging
```bash
# Debug script execution
uv run --verbose worker.py  # Verbose output for debugging
UV_TRACE=1 uv run worker.py  # Maximum debugging output

# Check script dependencies
uv run --no-project worker.py  # Run without project context
uv show temporalio  # Verify package installation
```

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
from temporalio.common import RetryPolicy
from activities import compose_greeting
from shared import ComposeGreetingInput


@workflow.defn
class GreetingWorkflow:
    """Basic workflow that logs and invokes an activity."""
    
    @workflow.run
    async def run(self, name: str) -> str:
        """Execute the greeting workflow."""
        workflow.logger.info("Running workflow with parameter %s" % name)
        
        # Define retry policy for activities
        default_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),      # Default: 1 second
            backoff_coefficient=2.0,                    # Default: 2.0
            maximum_interval=timedelta(seconds=100),    # Default: 100 * initial_interval
            maximum_attempts=0,                         # Default: 0 (unlimited retries)
            # non_retryable_error_types defaults to []
        )
        
        # Execute activity with timeout and retry policy
        return await workflow.execute_activity(
            compose_greeting,
            ComposeGreetingInput("Hello", name),
            schedule_to_close_timeout=timedelta(seconds=20),
            retry_policy=default_retry_policy,
        )
```

### Worker Service (worker.py)
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "temporalio>=1.7.0",
# ]
# ///

"""Worker service for the Temporal greeting application.

This runs as a long-running service that polls for tasks from the Temporal server.
Should be started with 'uv run worker.py &' or directly './worker.py &' if executable.
Supports both PEP 723 inline dependencies and project-based dependency management.
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
#   "temporalio>=1.7.0",
# ]
# ///

"""Workflow starter for the Temporal greeting application.

This script starts workflows and should be run after the worker is already running.
Execute with 'uv run starter.py "YourName"' or directly './starter.py "YourName"'.
Supports both PEP 723 inline dependencies and project-based dependency management.
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
        
        # Execute the workflow
        result = await client.execute_workflow(
            GreetingWorkflow.run,
            name,
            id=f"hello-activity-workflow-{name}",
            task_queue="hello-activity-task-queue",
        )
        
        print(f"Result: {result}")
        logger.info("Workflow completed successfully")
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
```