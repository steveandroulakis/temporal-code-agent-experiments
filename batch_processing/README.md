# Temporal Python SDK - Batch Processing Demo

A demonstration of Temporal's batch processing capabilities using Python SDK with child workflows and parallel activity execution.

## Overview

This demo processes numbers 1 through n (configurable, default 2000) by squaring each number. The processing is divided into batches using child workflows to manage event history effectively.

## Architecture

- **Main Workflow** (`BatchProcessingWorkflow`): Orchestrates the entire batch processing operation
- **Child Workflows** (`NumberBatchWorkflow`): Each child workflow processes a batch of 10 numbers
- **Activities** (`square_number`): Each activity squares a single number

## Features

- Configurable batch size (default: 10 numbers per batch)
- Configurable total numbers to process (default: 2000)
- Parallel processing of numbers within each batch
- Event history management through child workflows
- Comprehensive error handling with retry policies

## Files

- `shared.py` - Data classes and types
- `activities.py` - Activity definitions (square_number)
- `workflow.py` - Workflow definitions (main and child workflows)
- `worker.py` - Worker process
- `starter.py` - Workflow starter client

## Usage

### Prerequisites

1. Install UV (Python package manager)
2. Install Temporal CLI
3. Start Temporal dev server:
   ```bash
   temporal server start-dev
   ```

### Running the Demo

1. Start the worker:
   ```bash
   cd batch_processing
   uv run worker.py
   ```

2. In another terminal, run the starter:
   ```bash
   # Process 2000 numbers (default)
   uv run starter.py

   # Process custom number of numbers
   uv run starter.py 100

   # Process with custom batch size
   uv run starter.py 100 20
   ```

### Viewing Results

Use the Temporal CLI to view workflow execution:

```bash
# List workflows
temporal workflow list

# Show specific workflow
temporal workflow show --workflow-id "batch-processing-workflow-2000"
```

## Example Output

```
============================================================
BATCH PROCESSING COMPLETE
============================================================
Total numbers processed: 2000
Total batches: 200
Batch size: 10
Sum of all squares: 2668667000

First 10 results: [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
Last 10 results: [3964081, 3968064, 3972049, 3976036, 3980025, 3984016, 3988009, 3992004, 3996001, 4000000]
============================================================
```

## Testing

The demo has been tested with:
- n=50 (5 child workflows, 50 activities)
- n=2000 (200 child workflows, 2000 activities)

All tests completed successfully with mathematically verified results.
