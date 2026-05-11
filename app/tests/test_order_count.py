# app/tests/test_order_count.py
import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.db.models.base import Base
from app.db.models.order import OrderModel
from app.db.models.order_item import OrderItemModel
from app.services.order_service import OrderService
from app.repositories.order_repository import OrderRepository
from app.core.models.order import OrderStatus


async def test_order_count():
    """Асинхронный тест заказов"""

    # 1. Создаём асинхронный движок для SQLite
    engine = create_async_engine(
        "sqlite+aiosqlite:///test.db", echo=True  # Для отладки SQL запросов
    )

    # 2. Создаём таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # 3. Создаём фабрику асинхронных сессий
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # 4. Работаем с сессией
    async with async_session_maker() as db:
        # ============= СОЗДАЁМ ТЕСТОВЫЕ ЗАКАЗЫ =============

        # Первый заказ
        order1 = OrderModel(
            user_id=1,
            subtotal=100,
            discount_amount=0,
            delivery_fee=0,
            total=100,
            status="delivered",
            applied_discounts=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        item1 = OrderItemModel(
            product_id=1, name="Тест", quantity=1, price=100, created_at=datetime.now()
        )
        order1.items.append(item1)

        # Второй заказ
        order2 = OrderModel(
            user_id=1,
            subtotal=200,
            discount_amount=0,
            delivery_fee=0,
            total=200,
            status="delivered",
            applied_discounts=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        item2 = OrderItemModel(
            product_id=2, name="Тест2", quantity=1, price=200, created_at=datetime.now()
        )
        order2.items.append(item2)

        # Добавляем в БД
        db.add(order1)
        db.add(order2)
        await db.commit()

        # ============= ТЕСТИРУЕМ РЕПОЗИТОРИЙ =============

        # Создаём репозиторий
        repo = OrderRepository(db)

        # Получаем количество завершённых заказов
        count = await repo.count_completed_orders_by_user_id(1)
        print(f"Пользователь 1 сделал {count} завершённых заказов")  # Должно быть 2

        # Получаем все заказы пользователя
        orders = await repo.get_by_user_id(1)
        print(f"Всего заказов у пользователя 1: {len(orders)}")

        # ============= ТЕСТИРУЕМ СЕРВИС =============

        # Создаём сервис
        service = OrderService(db)

        # Создаём новый заказ для пользователя 1 (не первый заказ)
        print("\n=== СОЗДАЁМ ЗАКАЗ ДЛЯ ПОЛЬЗОВАТЕЛЯ 1 ===")
        new_order = await service.create_order(
            user_id=1,
            items=[{"product_id": 1, "name": "Пицца", "quantity": 2, "price": 500}],
            delivery_address="Test Address",
        )

        print(f"Заказ #{new_order.id}")
        print(f"Товары: {new_order.subtotal}₽")
        print(f"Скидка: {new_order.discount_amount}₽")
        print(f"Итого: {new_order.total}₽")

        # Проверяем, что скидка не применилась (не первый заказ)
        if new_order.discount_amount == 0:
            print("✅ Скидка на первый заказ НЕ применена (правильно)")
        else:
            print(f"⚠️ Скидка применена: {new_order.discount_amount}₽")

        # ============= ТЕСТ ПЕРВОГО ЗАКАЗА =============

        print("\n=== ТЕСТ ПЕРВОГО ЗАКАЗА ДЛЯ ПОЛЬЗОВАТЕЛЯ 2 ===")

        first_order = await service.create_order(
            user_id=2,  # Новый пользователь
            items=[
                {"product_id": 1, "name": "Пицца", "quantity": 2, "price": 500},
                {"product_id": 2, "name": "Кола", "quantity": 1, "price": 100},
            ],
            delivery_address="Test Address 2",
        )

        print(f"Пользователь 2 (первый заказ):")
        print(f"Товары: {first_order.subtotal}₽")
        print(f"Скидка: {first_order.discount_amount}₽")
        print(f"Итого: {first_order.total}₽")

        # Проверяем, что скидка применилась
        expected_discount = first_order.subtotal * 0.2 + first_order.delivery_fee
        if first_order.discount_amount > 0:
            print(
                f"✅ Скидка на первый заказ применена: {first_order.discount_amount}₽"
            )
        else:
            print(f"⚠️ Скидка на первый заказ НЕ применена")

    # Закрываем соединение
    await engine.dispose()

    print("\n✅ Все тесты пройдены!")


async def test_single_order():
    """Простой тест одного заказа"""

    engine = create_async_engine("sqlite+aiosqlite:///test_single.db", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as db:
        service = OrderService(db)

        # Создаём заказ
        order = await service.create_order(
            user_id=100,
            items=[
                {
                    "product_id": 1,
                    "name": "Пицца Маргарита",
                    "quantity": 2,
                    "price": 500,
                },
                {"product_id": 2, "name": "Кола", "quantity": 1, "price": 100},
            ],
            delivery_address="Москва, Красная площадь, д.1",
        )

        print(f"\n=== РЕЗУЛЬТАТ ===")
        print(f"Заказ #{order.id}")
        print(f"Сумма товаров: {order.subtotal}₽")
        print(f"Доставка: {order.delivery_fee}₽")
        print(f"Скидка: {order.discount_amount}₽")
        print(f"Итого к оплате: {order.total}₽")
        print(f"Статус: {order.status.value}")

        # Выводим применённые скидки
        if order.applied_discounts:
            print("\nПрименённые скидки:")
            for name, amount in order.applied_discounts:
                print(f"  - {name}: {amount}₽")

    await engine.dispose()


if __name__ == "__main__":
    # Запускаем основной тест
    asyncio.run(test_order_count())

    # Или запускаем простой тест
    # asyncio.run(test_single_order())
