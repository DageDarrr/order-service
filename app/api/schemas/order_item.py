from pydantic import BaseModel, Field


class OrderItemRequest(BaseModel):

    product_id: int = Field(..., ge=0, description="id товара")
    name: str = Field(..., min_length=2, max_length=255, description="Имя товара")
    quantity: float = Field(..., gt=0, description="Количество товара", examples=[2, 3])
    price: float = Field(
        ..., gt=0, description="Цена товара в рублях", examples=[500, 1000]
    )


class OrderItemResponse(BaseModel):

    product_id: int
    name: str
    quantity: float
    price: float
    total_price: float = Field(..., description="price * quantity")
