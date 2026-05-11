from app.api.schemas.order import OrderResponse, OrderStatusResponse, DiscountInfo
from app.api.schemas.order_item import OrderItemResponse


def order_to_response(order) -> OrderResponse:

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        items=[
            OrderItemResponse(
                product_id=item.product_id,
                name=item.name,
                quantity=item.quantity,
                price=item.price,
                total_price=item.total_price,
            )
            for item in order.items
        ],
        subtotal=order.subtotal,
        discount_amount=order.discount_amount,
        delivery_fee=order.delivery_fee,
        total=order.total,
        status=OrderStatusResponse(order.status.value),
        applied_discounts=[
            DiscountInfo(name=discount["name"], amount=discount["amount"])
            for discount in order.applied_discounts
        ],
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
