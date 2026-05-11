from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, JSON
from datetime import datetime
from typing import Optional, List
from app.db.models.base import Base
from app.core.models.order import Order, OrderStatus
from app.core.models.order_item import OrderItem

# class Order(BaseModel):
#     id : Optional[int] = None
#     user_id : int
#     items : List[OrderItem]


#     subtotal: float = 0 # Товары без скидок
#     discount_amount: float = 0 # Сумма скидки
#     delivery_fee: float = 0    # Стоимость доставки
#     total : float = 0 # Общая сумма


#     applied_discounts : List[Tuple[str, float]] = Field(default_factory=list)

#     status : OrderStatus = OrderStatus.PENDING

#     created_at : datetime = Field(default_factory=datetime.now)
#     updated_at : datetime = Field(default_factory=datetime.now)


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Финансы
    subtotal: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    delivery_fee: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Статус и скидки
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    applied_discounts: Mapped[List[dict]] = mapped_column(
        JSON, nullable=False, default=list
    )

    # Время
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    # Связь с товарами
    items: Mapped[List["OrderItemModel"]] = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_pydantic(self):

        pydantic_items = [
            OrderItem(
                product_id=item.product_id,
                name=item.name,
                quantity=item.quantity,
                price=item.price,
            )
            for item in self.items
        ]
        discounts = self.applied_discounts

        return Order(
            id=self.id,
            user_id=self.user_id,
            items=pydantic_items,
            subtotal=self.subtotal,
            discount_amount=self.discount_amount,
            delivery_fee=self.delivery_fee,
            total=self.total,
            status=OrderStatus(self.status),
            applied_discounts=discounts,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
