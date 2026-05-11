# app/repositories/order_repository.py
from app.db.models.order import OrderModel
from app.db.models.order_item import OrderItemModel
from typing import Optional, List
from app.core.models.order import Order, OrderStatus
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OrderRepository:
    """Асинхронный репозиторий для работы с заказами"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, order: Order) -> Order:
        """Сохранить заказ (создать или обновить)"""

        # ✅ ПРАВИЛЬНАЯ КОНВЕРТАЦИЯ СКИДОК
        discounts_data = []
        for discount in order.applied_discounts:
            if isinstance(discount, dict):
                discounts_data.append(
                    {
                        "name": discount.get("name", "Unknown"),
                        "amount": discount.get("amount", 0),
                    }
                )
            elif isinstance(discount, (list, tuple)) and len(discount) >= 2:
                discounts_data.append(
                    {"name": str(discount[0]), "amount": float(discount[1])}
                )

        if order.id:
            # Обновление существующего заказа
            result = await self.db.execute(
                select(OrderModel).where(OrderModel.id == order.id)
            )
            db_order = result.scalar_one_or_none()

            if db_order:
                # Обновляем простые поля
                db_order.user_id = order.user_id
                db_order.subtotal = order.subtotal
                db_order.discount_amount = order.discount_amount
                db_order.delivery_fee = order.delivery_fee
                db_order.total = order.total
                db_order.status = order.status.value
                db_order.updated_at = order.updated_at

                # Обновляем скидки (JSON поле)
                db_order.applied_discounts = discounts_data

                # Обновляем товары через relationship
                # Удаляем старые товары
                for old_item in db_order.items:
                    await self.db.delete(old_item)

                # Добавляем новые товары
                for item in order.items:
                    db_item = OrderItemModel(
                        order_id=db_order.id,
                        product_id=item.product_id,
                        name=item.name,
                        quantity=item.quantity,
                        price=item.price,
                    )
                    self.db.add(db_item)
        else:
            # Создание нового заказа
            db_order = OrderModel(
                user_id=order.user_id,
                subtotal=order.subtotal,
                discount_amount=order.discount_amount,
                delivery_fee=order.delivery_fee,
                total=order.total,
                status=order.status.value,
                applied_discounts=discounts_data,
            )
            self.db.add(db_order)

            # Flush чтобы получить ID заказа
            await self.db.flush()

            # Добавляем товары
            for item in order.items:
                db_item = OrderItemModel(
                    order_id=db_order.id,
                    product_id=item.product_id,
                    name=item.name,
                    quantity=item.quantity,
                    price=item.price,
                )
                self.db.add(db_item)

        await self.db.flush()
        await self.db.refresh(db_order)

        order.id = db_order.id
        return order

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        """Получить заказ по ID"""
        result = await self.db.execute(
            select(OrderModel).where(OrderModel.id == order_id)
        )
        db_order = result.scalar_one_or_none()

        if db_order:
            return db_order.to_pydantic()
        return None

    async def get_by_user_id(
        self,
        user_id: int,
    ) -> List[Order]:
        """Получить заказы пользователя"""
        result = await self.db.execute(
            select(OrderModel)
            .where(OrderModel.user_id == user_id)
            .order_by(OrderModel.created_at.desc())
        )
        db_orders = result.scalars().all()
        return [order.to_pydantic() for order in db_orders]

    async def count_by_user_id(self, user_id: int) -> int:
        """Получить количество ВСЕХ заказов пользователя"""
        result = await self.db.execute(
            select(func.count())
            .select_from(OrderModel)
            .where(OrderModel.user_id == user_id)
        )
        return result.scalar() or 0

    async def count_completed_orders_by_user_id(self, user_id: int) -> int:
        """Получить количество ЗАВЕРШЁННЫХ заказов пользователя"""
        result = await self.db.execute(
            select(func.count())
            .select_from(OrderModel)
            .where(
                OrderModel.user_id == user_id,
                OrderModel.status.in_(["delivered", "confirmed"]),
            )
        )
        return result.scalar() or 0

    async def delete(self, order_id: int) -> bool:
        """Удалить заказ (товары удаляются автоматически благодаря cascade)"""
        result = await self.db.execute(
            select(OrderModel).where(OrderModel.id == order_id)
        )
        db_order = result.scalar_one_or_none()

        if db_order:
            await self.db.delete(db_order)
            await self.db.flush()  # Добавлено
            return True
        return False
