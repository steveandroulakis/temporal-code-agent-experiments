from dataclasses import dataclass
from typing import List

@dataclass
class SquareNumberInput:
    """Input for squaring a single number"""
    number: int

@dataclass
class ProcessingConfig:
    """Configuration for batch processing"""
    batch_size: int = 10  # Numbers to process per leaf workflow
    max_children: int = 5  # Maximum child workflows per parent

@dataclass
class WorkflowNodeInput:
    """Input for a workflow node (can be main, intermediate, or leaf)"""
    start_number: int  # Starting number (inclusive)
    end_number: int    # Ending number (inclusive)
    config: ProcessingConfig
    depth: int = 0     # Tree depth (0 = root)

@dataclass
class NodeResult:
    """Result from processing a workflow node"""
    results: List[int]
    total_processed: int
    depth: int
