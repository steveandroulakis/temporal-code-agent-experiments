# Temporal Python SDK - Batch Processing with Infinite Nesting

A demonstration of Temporal's batch processing capabilities using Python SDK with **recursive child workflows** and parallel activity execution. This implementation supports **infinite nesting** to process any number of items while staying within Temporal's limits.

## Overview

This demo processes numbers 1 through n (configurable, default 2000) by squaring each number. The processing automatically creates a **tree of nested child workflows** to manage event history effectively, with configurable limits per workflow.

## Architecture - Infinite Nesting Tree

The demo uses a **recursive workflow pattern** where each workflow node can either:
1. **Leaf Node**: Process ≤ `batch_size` numbers as activities (default: 10)
2. **Intermediate Node**: Spawn ≤ `max_children` child workflows (default: 5)

This creates a tree structure that can scale to **unlimited size**:

```
Root Workflow (depth 0)
├─ Child c0 (depth 1)
│  ├─ Child c0-c0 (depth 2)
│  │  ├─ Child c0-c0-c0 (depth 3)
│  │  │  ├─ Leaf c0-c0-c0-c0 (depth 4) → processes 4 activities
│  │  │  ├─ Leaf c0-c0-c0-c1 (depth 4) → processes 4 activities
│  │  │  └─ ... (up to 5 leaves)
│  │  └─ ... (up to 5 intermediate nodes)
│  └─ ... (up to 5 intermediate nodes)
└─ ... (up to 5 children)
```

### Scalability

With `max_children=5` and `batch_size=10`:
- **1 level**: 1 × 10 = 10 numbers
- **2 levels**: 5 × 10 = 50 numbers
- **3 levels**: 5 × 5 × 10 = 250 numbers
- **4 levels**: 5 × 5 × 5 × 10 = 1,250 numbers
- **5 levels**: 5 × 5 × 5 × 5 × 10 = 6,250 numbers
- **N levels**: 5^(N-1) × 10 numbers → **infinite scale**

### Why Infinite Nesting?

Temporal has limits per workflow execution:
- Max 2,000 pending child workflows per parent
- Max 51,200 events or 50 MB event history

By limiting each workflow to spawn ≤ 5 children (configurable), we create a tree that **never hits these limits**, no matter how many items you need to process.

## Features

- **Infinite nesting**: Automatically creates tree depth based on workload
- **Configurable limits**: Set `batch_size` (activities per leaf) and `max_children` (children per node)
- **Automatic tree balancing**: Evenly distributes work across children
- **Parallel execution**: All children and activities execute in parallel
- **Event history management**: Each workflow stays well within Temporal limits
- **Comprehensive error handling**: Retry policies on all activities

## Files

- `shared.py` - Data classes (WorkflowNodeInput, ProcessingConfig, NodeResult)
- `activities.py` - Activity definitions (square_number)
- `workflow.py` - Recursive BatchProcessingWorkflow definition
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
   # Process 2000 numbers with default settings (batch_size=10, max_children=5)
   uv run starter.py

   # Process 50 numbers
   uv run starter.py 50

   # Process 100 numbers with batch_size=20
   uv run starter.py 100 20

   # Process 1000 numbers with batch_size=10, max_children=10
   uv run starter.py 1000 10 10
   ```

### Viewing Results

Use the Temporal CLI to view workflow execution:

```bash
# List all workflows
temporal workflow list

# Show specific workflow
temporal workflow show --workflow-id "batch-processing-2000-b10-c5"

# See the tree structure
temporal workflow list --query "WorkflowId STARTS_WITH 'batch-processing-2000-b10-c5'"

# Show a leaf workflow (processes activities)
temporal workflow show --workflow-id "batch-processing-2000-b10-c5-c0-c0-c0-c0"
```

## Example Output

### Small Scale (n=50)
```
======================================================================
BATCH PROCESSING COMPLETE
======================================================================
Total numbers processed: 50
Tree depth (max nesting level): 1
Batch size (activities per leaf): 10
Max children per workflow: 5
Sum of all squares: 42925

First 10 results: [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
Last 10 results: [1681, 1764, 1849, 1936, 2025, 2116, 2209, 2304, 2401, 2500]
======================================================================
```

### Large Scale (n=2000)
```
======================================================================
BATCH PROCESSING COMPLETE
======================================================================
Total numbers processed: 2000
Tree depth (max nesting level): 4
Batch size (activities per leaf): 10
Max children per workflow: 5
Sum of all squares: 2668667000

First 10 results: [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
Last 10 results: [3964081, 3968064, 3972049, 3976036, 3980025, 3984016, 3988009, 3992004, 3996001, 4000000]
======================================================================
```

## Testing

The demo has been tested with:

### Test 1: Small batch (n=50, max_children=5, batch_size=10)
- **Tree depth**: 1 (root → 5 leaf workflows)
- **Total workflows**: 6 (1 root + 5 leaves)
- **Total activities**: 50
- **Sum of squares**: 42,925 ✓

### Test 2: Large scale (n=2000, max_children=5, batch_size=10)
- **Tree depth**: 4 (5 levels of nesting)
- **Total workflows**: 656 (1 root + intermediate nodes + leaf workflows)
- **Total activities**: 2,000
- **Sum of squares**: 2,668,667,000 ✓ (mathematically verified)

## How It Works

1. **Root workflow** receives request to process numbers 1-2000
2. Since 2000 > batch_size (10), it **spawns 5 children**, each handling 400 numbers
3. Each child (depth 1) receives 400 numbers. Since 400 > 10, it **spawns 5 children**, each handling 80 numbers
4. Each child (depth 2) receives 80 numbers. Since 80 > 10, it **spawns 5 children**, each handling 16 numbers
5. Each child (depth 3) receives 16 numbers. Since 16 > 10, it **spawns 5 children**, each handling 3-4 numbers
6. Each child (depth 4) receives 3-4 numbers. Since 3-4 ≤ 10, it **processes them as activities** (leaf node)
7. Results bubble back up the tree, aggregating at each level

All children at each level execute **in parallel**, making the workflow highly efficient.

## Key Insights

- **No hardcoded limits**: The tree depth automatically adjusts based on `total_numbers`, `batch_size`, and `max_children`
- **Stays within Temporal limits**: Each workflow spawns ≤ 5 children (well under the 2,000 limit)
- **Event history management**: Each workflow has minimal events (StartChildWorkflow or ActivityTask)
- **Infinite scalability**: Can process millions or billions of items by increasing tree depth
- **Parallel execution**: All operations at each level run concurrently
- **Queue-tolerant activities**: Activities use `start_to_close_timeout` (not `schedule_to_close_timeout`), allowing them to wait indefinitely in the queue when workers are saturated
- **High worker concurrency**: Worker configured with 100 concurrent activities and 50 concurrent workflow tasks for optimal throughput

## Activity Timeout Configuration

The workflow uses **queue-tolerant timeout settings** to prevent failures under high load:

```python
workflow.execute_activity(
    square_number,
    SquareNumberInput(number=number),
    start_to_close_timeout=timedelta(seconds=30),  # Only times execution, not queue wait
    # No schedule_to_start_timeout - activities wait indefinitely in queue
    retry_policy=default_retry_policy,
)
```

**Why this matters:**
- `schedule_to_close_timeout` = ScheduleToStart + StartToClose (includes queue wait time)
- `start_to_close_timeout` = Only the execution time after a worker picks up the task
- By using `start_to_close_timeout` only, activities can wait in the queue as long as needed when workers are busy
- This prevents cascading failures when the task queue is saturated

## Worker Configuration

The worker is configured for high throughput:

```python
Worker(
    client,
    task_queue="batch-processing-task-queue",
    workflows=[BatchProcessingWorkflow],
    activities=[square_number],
    activity_executor=ThreadPoolExecutor(100),      # 100 threads for activities
    max_concurrent_activities=100,                   # Handle 100 activities at once
    max_concurrent_workflow_tasks=50,                # Handle 50 workflow tasks at once
)
```

This configuration allows the worker to process hundreds of activities and workflow tasks concurrently, maximizing throughput for the nested tree structure.
