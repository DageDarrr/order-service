from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey
from datetime import datetime
from typing import Optional, List
from app.db.models.base import Base

# class OrderItem(BaseModel):

#     product_id : int
#     name : str
#     quantity : int
#     price : float


#     @property
#     def total_price(self):
#         return self.quantity * self.price # Получить цену


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )

    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )

    order: Mapped["OrderModel"] = relationship(back_populates="items")
