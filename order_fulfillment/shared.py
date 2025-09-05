from dataclasses import dataclass, field
from typing import List


@dataclass
class Order:
    """Simple order model shared between workflow and activities."""

    order_id: str
    amount: float
    cc_expiry: str
    items: List[str] = field(default_factory=list)
