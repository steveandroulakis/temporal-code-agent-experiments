import time
import uuid
from datetime import datetime, timedelta
from temporalio import activity
from shared import Order, PaymentResult, InventoryResult, DeliveryResult


@activity.defn
def process_payment(order: Order) -> PaymentResult:
    """Mock activity to process payment for an order."""
    activity.logger.info(f"Processing payment for order {order.order_id}, amount: ${order.total_amount:.2f}")

    # Simulate payment processing delay
    time.sleep(1)

    # Mock payment processing - in reality, this would call a payment gateway
    transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"

    activity.logger.info(f"Payment processed successfully. Transaction ID: {transaction_id}")

    return PaymentResult(
        success=True,
        transaction_id=transaction_id,
        message=f"Payment of ${order.total_amount:.2f} processed successfully"
    )


@activity.defn
def reserve_inventory(order: Order) -> InventoryResult:
    """Mock activity to reserve inventory for an order."""
    activity.logger.info(f"Reserving inventory for order {order.order_id}")

    # Log each item being reserved
    for item in order.items:
        activity.logger.info(
            f"  - Product {item.product_id}: {item.quantity} units at ${item.price:.2f} each"
        )

    # Simulate inventory system delay
    time.sleep(1)

    # Mock inventory reservation - in reality, this would update inventory database
    reservation_id = f"RES-{uuid.uuid4().hex[:8].upper()}"

    activity.logger.info(f"Inventory reserved successfully. Reservation ID: {reservation_id}")

    return InventoryResult(
        success=True,
        reservation_id=reservation_id,
        message=f"Reserved {len(order.items)} item(s) for order {order.order_id}"
    )


@activity.defn
def initiate_delivery(order: Order) -> DeliveryResult:
    """Mock activity to initiate delivery for an order."""
    activity.logger.info(f"Initiating delivery for order {order.order_id}")

    # Simulate delivery system delay
    time.sleep(1)

    # Mock delivery initiation - in reality, this would integrate with shipping providers
    tracking_number = f"TRACK-{uuid.uuid4().hex[:12].upper()}"
    estimated_delivery = datetime.now() + timedelta(days=3)
    estimated_delivery_str = estimated_delivery.strftime("%Y-%m-%d")

    activity.logger.info(
        f"Delivery initiated. Tracking: {tracking_number}, "
        f"Estimated delivery: {estimated_delivery_str}"
    )

    return DeliveryResult(
        success=True,
        tracking_number=tracking_number,
        estimated_delivery_date=estimated_delivery_str,
        message=f"Delivery scheduled for {estimated_delivery_str}"
    )


@activity.defn
def refund_payment(transaction_id: str, amount: float) -> PaymentResult:
    """Mock activity to refund a payment (used for compensation)."""
    activity.logger.info(f"Processing refund for transaction {transaction_id}, amount: ${amount:.2f}")

    # Simulate refund processing delay
    time.sleep(1)

    refund_id = f"REFUND-{uuid.uuid4().hex[:8].upper()}"

    activity.logger.info(f"Refund processed successfully. Refund ID: {refund_id}")

    return PaymentResult(
        success=True,
        transaction_id=refund_id,
        message=f"Refund of ${amount:.2f} processed successfully"
    )


@activity.defn
def release_inventory(reservation_id: str) -> InventoryResult:
    """Mock activity to release reserved inventory (used for compensation)."""
    activity.logger.info(f"Releasing inventory reservation {reservation_id}")

    # Simulate inventory release delay
    time.sleep(1)

    activity.logger.info(f"Inventory reservation {reservation_id} released successfully")

    return InventoryResult(
        success=True,
        reservation_id=reservation_id,
        message=f"Inventory reservation {reservation_id} released"
    )
