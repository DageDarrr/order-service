from pydantic import BaseModel, Field
from app.api.schemas.order_item import OrderItemRequest, OrderItemResponse
from typing import List, Optional
from datetime import datetime
from enum import Enum


class OrderRequest(BaseModel):
    user_id: int = Field(..., gt=0, description="ID user'а")

    delivery_address: str = Field(min_length=5, description="Адресс доставки")

    items: List[OrderItemRequest] = Field(min_length=1, description="Список товаров")


class OrderStatusResponse(str, Enum):

    PENDING = "pending"
    PAYMENT_RESERVED = "payment_reserved"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY_FOR_DELIVERY = "ready"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DiscountInfo(BaseModel):
    name: str = Field(..., description="Название скидки")
    amount: float = Field(..., description="Сумма скидки")


class OrderResponse(BaseModel):

    id: int
    user_id: int
    items: List[OrderItemResponse]
    subtotal: float = Field(..., description="Сумма товаров без скидок")
    discount_amount: float = Field(..., description="Общая сумма скидки")
    delivery_fee: float = Field(..., description="Стоимость доставки")
    total: float = Field(..., description="Итоговая сумма к оплате")
    status: OrderStatusResponse
    applied_discounts: List[DiscountInfo] = Field(
        default_factory=list, description="Применённые скидки"
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class OrderListResponse(BaseModel):

    total: int = Field(..., description="Общее кол-во заказов")
    orders: List[OrderResponse]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int


class UpdateStatusRequest(BaseModel):
    """Запрос на обновление статуса заказа"""

    status: OrderStatusResponse


class CancelOrderResponse(BaseModel):
    """Ответ при отмене заказа"""

    id: int
    status: str = "cancelled"
    message: str = "Заказ успешно отменен"
