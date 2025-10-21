import time
import uuid
from datetime import datetime, timedelta
from temporalio import activity
from shared import Order, PaymentResult, InventoryResult, DeliveryResult


@activity.defn
def process_payment(order: Order) -> PaymentResult:
    """
    Mock activity to process payment for an order.
    Simulates payment processing time and returns a result.
    """
    activity.logger.info(
        f"Processing payment for order {order.order_id}, "
        f"amount: ${order.total_amount:.2f}"
    )

    # Simulate payment processing delay
    time.sleep(2)

    # Mock payment logic - always succeeds for demo
    transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

    activity.logger.info(
        f"Payment successful for order {order.order_id}, "
        f"transaction ID: {transaction_id}"
    )

    return PaymentResult(
        success=True,
        transaction_id=transaction_id,
        message=f"Payment of ${order.total_amount:.2f} processed successfully"
    )


@activity.defn
def reserve_inventory(order: Order) -> InventoryResult:
    """
    Mock activity to reserve inventory for order items.
    Simulates checking and reserving inventory.
    """
    activity.logger.info(
        f"Reserving inventory for order {order.order_id}, "
        f"{len(order.items)} item(s)"
    )

    # Simulate inventory check delay
    time.sleep(1.5)

    # Log each item being reserved
    for item in order.items:
        activity.logger.info(
            f"Reserving {item.quantity}x {item.product_name} "
            f"(ID: {item.product_id})"
        )

    # Mock reservation - always succeeds for demo
    reservation_id = f"RES-{uuid.uuid4().hex[:12].upper()}"

    activity.logger.info(
        f"Inventory reserved successfully for order {order.order_id}, "
        f"reservation ID: {reservation_id}"
    )

    return InventoryResult(
        success=True,
        reservation_id=reservation_id,
        message=f"Reserved {len(order.items)} item(s) successfully"
    )


@activity.defn
def arrange_delivery(order: Order) -> DeliveryResult:
    """
    Mock activity to arrange delivery for an order.
    Simulates scheduling delivery and generating tracking info.
    """
    activity.logger.info(
        f"Arranging delivery for order {order.order_id} "
        f"to {order.shipping_address}"
    )

    # Simulate delivery arrangement delay
    time.sleep(1)

    # Mock delivery scheduling
    tracking_number = f"TRACK-{uuid.uuid4().hex[:16].upper()}"
    estimated_delivery = datetime.now() + timedelta(days=3)
    estimated_delivery_str = estimated_delivery.strftime("%Y-%m-%d")

    activity.logger.info(
        f"Delivery arranged for order {order.order_id}, "
        f"tracking: {tracking_number}, "
        f"estimated delivery: {estimated_delivery_str}"
    )

    return DeliveryResult(
        success=True,
        tracking_number=tracking_number,
        estimated_delivery_date=estimated_delivery_str,
        message=f"Delivery scheduled to {order.shipping_address}"
    )


@activity.defn
def send_confirmation_email(order: Order, order_result: dict) -> None:
    """
    Mock activity to send order confirmation email to customer.
    """
    activity.logger.info(
        f"Sending confirmation email to {order.customer_email} "
        f"for order {order.order_id}"
    )

    # Simulate email sending delay
    time.sleep(0.5)

    activity.logger.info(
        f"Confirmation email sent successfully to {order.customer_email}"
    )
