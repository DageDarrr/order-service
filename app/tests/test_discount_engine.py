# test_discount_engine.py
import sys

sys.path.insert(0, ".")

from app.core.models.order import Order, OrderStatus
from app.core.models.order_item import OrderItem
from app.core.discount.engine import DiscountEngine


def test_discount_engine():
    # Создаём заказ
    order = Order(
        user_id=1,
        items=[
            OrderItem(product_id=1, name="Пицца", quantity=2, price=500),
            OrderItem(product_id=2, name="Кола", quantity=1, price=100),
        ],
        delivery_fee=150,
    )

    # Создаём движок
    engine = DiscountEngine()
    engine.add_default_strategies(user_order_count=0, threshold=1000)

    # Рассчитываем скидки
    total_discount, applied = engine.calculate_total_discount(order)

    print(f"total_discount: {total_discount}")
    print(f"applied: {applied}")
    print(f"type(applied[0]): {type(applied[0])}")

    # Конвертируем
    converted = [{"name": name, "amount": amount} for name, amount in applied]
    print(f"converted: {converted}")


if __name__ == "__main__":
    test_discount_engine()
