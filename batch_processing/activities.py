from temporalio import activity
from shared import SquareNumberInput

@activity.defn
def square_number(input: SquareNumberInput) -> int:
    """Activity that squares a number"""
    activity.logger.info(f"Squaring number: {input.number}")
    result = input.number * input.number
    activity.logger.info(f"Result: {input.number}^2 = {result}")
    return result
