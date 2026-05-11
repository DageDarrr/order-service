from pydantic import BaseModel


class OrderItem(BaseModel):

    product_id: int
    name: str
    quantity: int
    price: float

    @property
    def total_price(self):
        return self.quantity * self.price  # Получить цену
