from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models.order import Order, OrderStatus
from app.core.models.order_item import OrderItem
from app.db.models.order import OrderModel
from app.db.models.order_item import OrderItemModel
from app.repositories.order_repository import OrderRepository
from app.core.discount.engine import DiscountEngine
from typing import List, Optional


from app.utils.logger import get_logger

logger = get_logger(__name__)


class OrderService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = OrderRepository(db)
        self.discount_engine = DiscountEngine()

    def _calculate_delivery_fee(self):
        """Расчет стоимости доставки сейчас базовая доставка 150р, потом можно будет сделать
        расчет по расстоянию от ресторана в сервисе доставки
        """

        return 150.0

    async def create_order(
        self,
        user_id: int,
        items: List[dict],
        delivery_address: str,
    ) -> Order:
        """Создать новый заказ для определенного пользователя

        *args: user_id : id пользователя в int,
        items: [{'name': 'Пицца Пеперони', 'product_id': 153, 'quantity': 326, 'price': 745}...]
        delivery_address : Lenina 14,
        delivery_fee : Цена в рублях float

        """

        try:

            logger.info(f"Создаю заказ для пользователя {user_id}")

            logger.info(f"Адресс доставки: {delivery_address}")

            item_list = []

            for item in items:
                order_item = OrderItem(
                    product_id=item.get("product_id"),
                    price=item.get("price"),
                    name=item.get("name"),
                    quantity=item.get("quantity"),
                )
                item_list.append(order_item)

            subtotal = sum(item.total_price for item in item_list)
            delivery_fee = self._calculate_delivery_fee()

            order = Order(
                user_id=user_id,
                items=item_list,
                delivery_fee=delivery_fee,
                subtotal=subtotal,
                total=subtotal + delivery_fee,
            )

            user_order_count = await self.repo.count_completed_orders_by_user_id(
                user_id
            )

            self.discount_engine.add_default_strategies(
                user_order_count=user_order_count, threshold=1000
            )

            total_discount, applied = self.discount_engine.calculate_total_discount(
                order
            )

            if total_discount > 0:
                order.discount_amount = total_discount
                order.applied_discounts = [
                    {"name": name, "amount": amount} for name, amount in applied
                ]
                order.total = subtotal - total_discount + delivery_fee

            logger.info(f"К заказу приминена скидка: {total_discount}")

            order = await self.repo.save(order)

            await self.db.commit()

            logger.info(
                f"Заказ: {order.id} по адрессу {delivery_address} успешно сохранен"
            )

            return order

        except Exception as e:
            logger.error(f"Произошла ошибка создания заказа: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def get_orders_by_user_id(self, user_id) -> List[Order]:
        try:
            orders = await self.repo.get_by_user_id(user_id)

            if not orders:
                logger.warning(f"Заказы для пользователя: {user_id} не найдены")
                return []

            return orders

        except Exception as e:
            logger.error(
                f"Произошла ошибка получения списка заказов для пользователя: {user_id}: {e}"
            )

    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        try:

            order = await self.repo.get_by_id(order_id)

            if not order:
                logger.warning(f"Заказ с ID: {order_id} не найден")

            return order

        except Exception as e:
            logger.error(f"Ошибка получения заказа: {order_id}: {e}")

    async def update_order_status(
        self, order_id: int, new_status: OrderStatus
    ) -> Optional[Order]:

        try:
            order = await self.get_order_by_id(order_id)
            if not order:
                raise ValueError(f"Заказ: {order_id} не найден")

            order.update_status(new_status)
            updated_order = await self.repo.save(order)
            await self.db.commit()

            return updated_order

        except Exception as e:
            logger.error(f"Ошибка, не удалось обновить заказ: {order_id}: {e}")
            await self.db.rollback()
            raise

    async def delete_order(self, order_id):

        try:
            success = await self.repo.delete(order_id)

            if not success:
                logger.warning(f"Заказ с ID: {order_id} не найден")

            await self.db.commit()

            return success

        except Exception as e:
            logger.error(f"Ошибка при удалении заказа:{order_id}:{e}")
            await self.db.rollback()

    async def cancel_order(self, order_id):

        try:
            order = await self.repo.get_by_id(order_id)

        

            if not order:
                logger.warning(f"Заказ: {order_id} не найден")
                raise ValueError(f"Заказ: {order_id} не найден")

            if not order.is_cancellable():
                raise ValueError(f"Нельзя отменить заказ в статусе: {order.status.value}")
            
            order.cancel()

            canceled_order = await self.repo.save(order)

            await self.db.commit()

            return canceled_order

        except Exception as e:
            logger.error(f"Ошибка, не удалось отменить заказ: {order_id}: {e}")
            await self.db.rollback()
            raise

            