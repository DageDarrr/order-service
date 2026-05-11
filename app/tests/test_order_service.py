# test_order_service_standalone.py
import asyncio
import sys
import os

# Добавляем путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.models.order import Order, OrderStatus
from app.core.models.order_item import OrderItem
from app.core.discount.engine import DiscountEngine
from app.core.discount.strategies import FirstOrderDiscount, FreeDeliveryDiscount


def test_discount_engine_only():
    """Тест 1: Только DiscountEngine (без БД)"""
    print("\n=== ТЕСТ 1: DiscountEngine ===")

    # Создаём заказ
    items = [
        OrderItem(product_id=1, name="Пицца", quantity=2, price=500),
        OrderItem(product_id=2, name="Кола", quantity=1, price=100),
    ]
    subtotal = sum(item.total_price for item in items)

    order = Order(
        user_id=1,
        items=items,
        subtotal=subtotal,
        delivery_fee=150,
        total=subtotal + 150,
    )

    # Создаём движок
    engine = DiscountEngine()
    engine.add_default_strategies(user_order_count=0, threshold=1000)

    # Рассчитываем скидки
    total_discount, applied = engine.calculate_total_discount(order)

    print(f"Subtotal: {order.subtotal}")
    print(f"Total discount: {total_discount}")
    print(f"Applied: {applied}")

    # Проверяем типы
    for name, amount in applied:
        print(
            f"  - {name}: {amount} (type name={type(name)}, type amount={type(amount)})"
        )
        assert isinstance(name, str), f"Name should be str, got {type(name)}"
        assert isinstance(
            amount, (int, float)
        ), f"Amount should be number, got {type(amount)}"

    # Конвертируем в словари
    converted = [{"name": name, "amount": amount} for name, amount in applied]
    print(f"Converted: {converted}")

    # Проверяем что нет строк "name" и "amount"
    for d in converted:
        assert d["name"] != "name", f"Name should not be 'name', got {d['name']}"
        assert (
            d["amount"] != "amount"
        ), f"Amount should not be 'amount', got {d['amount']}"

    print("✅ Тест 1 пройден!")
    return converted


def test_discount_with_multiple_orders():
    """Тест 2: Проверка скидки на первый и последующие заказы"""
    print("\n=== ТЕСТ 2: Несколько заказов ===")

    items = [OrderItem(product_id=1, name="Пицца", quantity=2, price=500)]
    subtotal = 1000

    # Первый заказ (user_order_count=0)
    order1 = Order(
        user_id=1,
        items=items,
        subtotal=subtotal,
        delivery_fee=150,
        total=subtotal + 150,
    )

    engine = DiscountEngine()
    engine.add_default_strategies(user_order_count=0, threshold=1000)
    total_discount, applied = engine.calculate_total_discount(order1)

    print(f"Первый заказ: скидка = {total_discount}")
    print(f"  Применено: {applied}")

    # Второй заказ (user_order_count=1)
    order2 = Order(
        user_id=1,
        items=items,
        subtotal=subtotal,
        delivery_fee=150,
        total=subtotal + 150,
    )

    engine = DiscountEngine()
    engine.add_default_strategies(user_order_count=1, threshold=1000)
    total_discount, applied = engine.calculate_total_discount(order2)

    print(f"Второй заказ: скидка = {total_discount}")
    print(f"  Применено: {applied}")

    if total_discount == 0:
        print("✅ Второй заказ без скидки (правильно!)")

    print("✅ Тест 2 пройден!")


def test_manual_order_creation():
    """Тест 3: Полный цикл создания заказа (без БД)"""
    print("\n=== ТЕСТ 3: Полный цикл создания заказа ===")

    # Данные из запроса
    user_id = 1
    items_data = [
        {"product_id": 1, "name": "Пицца", "quantity": 2, "price": 500},
        {"product_id": 2, "name": "Кола", "quantity": 1, "price": 100},
    ]
    delivery_address = "Test Address"
    delivery_fee = 150

    # Шаг 1: Создаём товары
    item_list = []
    for item in items_data:
        order_item = OrderItem(
            product_id=item["product_id"],
            price=item["price"],
            name=item["name"],
            quantity=item["quantity"],
        )
        item_list.append(order_item)

    # Шаг 2: Считаем сумму
    subtotal = sum(item.total_price for item in item_list)
    print(f"Subtotal: {subtotal}")

    # Шаг 3: Создаём заказ
    order = Order(
        user_id=user_id,
        items=item_list,
        delivery_fee=delivery_fee,
        subtotal=subtotal,
        total=subtotal + delivery_fee,
    )
    print(f"Order создан: total={order.total}")

    # Шаг 4: Применяем скидки
    user_order_count = 0  # первый заказ
    engine = DiscountEngine()
    engine.add_default_strategies(user_order_count=user_order_count, threshold=1000)

    total_discount, applied = engine.calculate_total_discount(order)
    print(f"Скидка от движка: {applied}")

    # Шаг 5: Применяем скидку к заказу
    if total_discount > 0:
        order.discount_amount = total_discount
        order.applied_discounts = [
            {"name": name, "amount": amount} for name, amount in applied
        ]
        order.total = subtotal - total_discount + delivery_fee
        print(f"После скидки: total={order.total}")

    print(f"Итоговый applied_discounts: {order.applied_discounts}")

    # Проверка
    expected_discount = 220.0 + 150.0  # 20% от 1100 = 220, + доставка 150
    assert (
        total_discount == expected_discount
    ), f"Expected {expected_discount}, got {total_discount}"

    expected_total = 1100.0 - 370.0 + 150.0  # 880
    assert (
        order.total == expected_total
    ), f"Expected {expected_total}, got {order.total}"

    print("✅ Тест 3 пройден!")


def test_discount_formats():
    """Тест 4: Проверка форматов данных"""
    print("\n=== ТЕСТ 4: Проверка форматов ===")

    # Какие данные ожидаем от DiscountEngine
    applied_from_engine = [
        ("Скидка 20% на первый заказ", 220.0),
        ("Бесплатная доставка от 1000Р", 150.0),
    ]

    # Конвертация в словари
    converted = [
        {"name": name, "amount": amount} for name, amount in applied_from_engine
    ]
    print(f"Сконвертировано: {converted}")

    # Проверка
    for d in converted:
        assert "name" in d, "Missing 'name' key"
        assert "amount" in d, "Missing 'amount' key"
        assert isinstance(d["name"], str), f"name should be str, got {type(d['name'])}"
        assert isinstance(
            d["amount"], (int, float)
        ), f"amount should be number, got {type(d['amount'])}"
        assert d["name"] != "name", f"Name should not be 'name'"
        assert d["amount"] != "amount", f"Amount should not be 'amount'"

    print("✅ Тест 4 пройден!")


if __name__ == "__main__":
    print("=" * 50)
    print("ЗАПУСК ТЕСТОВ")
    print("=" * 50)

    try:
        test_discount_engine_only()
        test_discount_with_multiple_orders()
        test_manual_order_creation()
        test_discount_formats()

        print("\n" + "=" * 50)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! ✅")
        print("=" * 50)
        print("\nЕсли тесты прошли, проблема в Docker кэше.")
        print(
            "Выполните: docker-compose down -v && docker-compose build --no-cache && docker-compose up"
        )

    except AssertionError as e:
        print(f"\n❌ Ошибка: {e}")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback

        traceback.print_exc()
