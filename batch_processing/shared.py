from dataclasses import dataclass
from typing import List

@dataclass
class SquareNumberInput:
    """Input for squaring a single number"""
    number: int

@dataclass
class BatchInput:
    """Input for processing a batch of numbers"""
    numbers: List[int]
    batch_id: int

@dataclass
class BatchResult:
    """Result from processing a batch of numbers"""
    batch_id: int
    results: List[int]

@dataclass
class BatchProcessingInput:
    """Input for the main batch processing workflow"""
    total_numbers: int
    batch_size: int = 10
