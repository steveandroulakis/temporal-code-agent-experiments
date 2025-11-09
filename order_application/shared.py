from dataclasses import dataclass


@dataclass
class Order:
    """Order information passed between activities."""

    id: str
    item: str
    quantity: int
    credit_card_number: str
    credit_card_expiry: str  # format MM/YY
