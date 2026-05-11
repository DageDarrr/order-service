from app.core.discount.base import DiscountStrategy
from app.core.models.order import Order


class FirstOrderDiscount(DiscountStrategy):

    def __init__(self, user_order_count: int) -> None:

        self.user_order_count = user_order_count

    @property
    def name(self) -> str:
        return "Скидка 20% на первый заказ"

    def is_applicable(self, order: Order) -> bool:
        # Если True то скидка приминима
        return self.user_order_count == 0

    def discount(self, order: Order) -> float:
        return order.subtotal * 0.2

    @property
    def priority(self):
        return 10


class FreeDeliveryDiscount(DiscountStrategy):

    def __init__(self, threshold: float = 1000) -> None:

        self.threshold = threshold

    @property
    def name(self) -> str:
        return "Бесплатная доставка от 1000Р"

    def is_applicable(self, order: Order) -> bool:
        return order.subtotal >= self.threshold and order.delivery_fee > 0

    def discount(self, order: Order) -> float:
        return order.delivery_fee

    @property
    def priority(self):
        return 5
