# test_integration.py
from app.core.models.order import Order, OrderStatus
from app.core.models.order_item import OrderItem
from app.core.discount.engine import DiscountEngine

# from app.core.discount.strategies import FirstOrderDiscount, FreeDeliveryDiscount

# 1. Создаём заказ
order = Order(
    user_id=1,
    items=[
        OrderItem(product_id=1, name="Пицца Маргарита", quantity=2, price=500),
        OrderItem(product_id=2, name="Кола", quantity=1, price=100),
    ],
    delivery_fee=150,
)

print("=== ЗАКАЗ ДО СКИДОК ===")
print(f"Товары: {order.subtotal}₽")
print(f"Доставка: {order.delivery_fee}₽")
print(f"Итого: {order.total}₽")
print()

# 2. Создаём движок и применяем скидки
engine = DiscountEngine()
engine.add_default_strategies(user_order_count=0, threshold=1000)

total_discount, applied = engine.calculate_total_discount(order)

# 3. Применяем скидки к заказу
order.discount_amount = total_discount
order.applied_discounts = applied
order._recalculate_total()  # Пересчитываем итог

print("=== ПОСЛЕ ПРИМЕНЕНИЯ СКИДОК ===")
print(f"Скидка: {order.discount_amount}₽")
print(f"Применено: {order.applied_discounts}")
print(f"Итого: {order.total}₽")
print(f"Процент скидки: {order.total_discount_percent:.1f}%")
print()

# 4. Проверяем методы
print("=== БИЗНЕС-МЕТОДЫ ===")
print(f"Можно отменить? {order.is_cancellable()}")

# Отменяем заказ
order.cancel()
print(f"Статус после отмены: {order.status.value}")

# Пытаемся отменить отменённый (выдаст ошибку)
try:
    order.update_status(OrderStatus.CONFIRMED)
except ValueError as e:
    print(f"Ошибка: {e}")
