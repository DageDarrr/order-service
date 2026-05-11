from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.core.models.order_item import OrderItem


class OrderStatus(str, Enum):

    PENDING = "pending"  # Только что создан
    PAYMENT_RESERVED = "payment_reserved"  # Деньги зарезервированы
    CONFIRMED = "confirmed"  # Ресторан подтвердил
    PREPARING = "preparing"  # Готовится
    READY_FOR_DELIVERY = "ready"  # Ждёт курьера
    DELIVERING = "delivering"  # Курьер везёт
    DELIVERED = "delivered"  # Получен
    CANCELLED = "cancelled"  # Отменён


class Order(BaseModel):
    id: Optional[int] = None
    user_id: int
    items: List[OrderItem]

    subtotal: float = 0  # Товары без скидок
    discount_amount: float = 0  # Сумма скидки
    delivery_fee: float = 0  # Стоимость доставки
    total: float = 0  # Общая сумма

    applied_discounts: List[Dict[str, Any]] = Field(default_factory=list)

    status: OrderStatus = OrderStatus.PENDING

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def __init__(self, **data):
        super().__init__(**data)

        if not self.subtotal and self.items:
            self.subtotal = sum(item.price * item.quantity for item in self.items)

        if self.items and self.total == 0:
            self.total = self.subtotal - self.discount_amount + self.delivery_fee

    def update_status(self, new_status: OrderStatus) -> "Order":
        if self.status == OrderStatus.CANCELLED and new_status == OrderStatus.CANCELLED:
            raise ValueError(f"Нельзя обновить отмененный статус: {self.status.value}")

        if self.status == OrderStatus.CANCELLED:
            raise ValueError(f"Нельзя изменить статус отменённого заказа")

        if self.status == OrderStatus.DELIVERING and new_status == OrderStatus.PENDING:
            raise ValueError(
                f"Нельзя вернуть заказ из доставки в статус {new_status.value}"
            )

        self.status = new_status
        self.updated_at = datetime.now()

        return self

    def cancel(self) -> "Order":
        if self.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise ValueError(f"Нельзя отменить заказ в статусе {self.status.value}")

        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.now()
        return self

    def _recalculate_total(self) -> None:
        """Пересчитать итоговую сумму"""
        self.total = self.subtotal - self.discount_amount + self.delivery_fee
        self.updated_at = datetime.now()

    @property
    def total_discount_percent(self) -> float:
        """Процент скидки"""
        if self.subtotal == 0:
            return 0.0
        return (self.discount_amount / self.subtotal) * 100

    def is_cancellable(self):
        return self.status not in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]

    def __str__(self) -> str:
        return f"Order №{self.id}: Items: {self.items} Status: {self.status.value} - total: {self.total} ₽"
