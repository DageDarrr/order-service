from fastapi import Depends, HTTPException, APIRouter, status
from app.api.dependencies.db_session import get_db
from app.api.dependencies.order_service import get_order_service
from app.utils.logger import get_logger
from app.api.dependencies.converter import order_to_response
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.order_service import OrderService
from app.core.models.order import OrderStatus

from app.api.schemas.order import (
    OrderItemRequest,
    OrderItemResponse,
    OrderListResponse,
    OrderRequest,
    OrderResponse,
    OrderStatusResponse,
    CancelOrderResponse,
    UpdateStatusRequest,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get(
    "/user/{user_id}", response_model=OrderListResponse, status_code=status.HTTP_200_OK
)
async def get_user_orders(
    user_id: int,
    order_service: OrderService = Depends(get_order_service),
):

    try:
        orders = await order_service.get_orders_by_user_id(user_id)

        return OrderListResponse(
            total=len(orders), orders=[order_to_response(order) for order in orders]
        )

    except Exception as e:
        logger.error(f"Произошла ошибка получения заказов для юзера: {user_id}:{e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка получения заказов"
        )


@router.get("/{order_id}", response_model=OrderResponse, status_code=status.HTTP_200_OK)
async def get_order_by_id(
    order_id: int,
    order_service: OrderService = Depends(get_order_service),
):

    try:
        order = await order_service.get_order_by_id(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Заказ с ID: {order_id} не найден",
            )

        return order_to_response(order)

    except Exception as e:
        logger.error(f"Произошла ошибка получения заказа {order_id}:{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения заказа по ID",
        )


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: OrderRequest, order_service: OrderService = Depends(get_order_service)
):

    try:
        items_data = [item.model_dump() for item in request.items]

        order = await order_service.create_order(
            user_id=request.user_id,
            delivery_address=request.delivery_address,
            items=items_data,
        )

        logger.info(f"Заказ:{order.id} успешно создан")

        return order_to_response(order)

    except ValueError as e:
        logger.warning(f"Ошибка валидации заказа: {order.id}:{e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Ошибка создании заказа: {order.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_status(
    order_id: int,
    request: UpdateStatusRequest = None,
    order_service: OrderService = Depends(get_order_service),
):

    try:
        if not request or not request.status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Статус заказа не указан",
            )

        new_status = OrderStatus(request.status.value)

        order = await order_service.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Заказ с ID {order_id} не найден",
            )

        if order.status == OrderStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя изменить статус отменённого заказа",
            )

        updated_order = await order_service.update_order_status(order_id, new_status)

        if not updated_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Заказ с ID {order_id} не найден",
            )

        return order_to_response(updated_order)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка обновления статуса заказа {order_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обновления статуса",
        )



@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    order_service: OrderService = Depends(get_order_service),
) -> None:
    """
    Удалить заказ (только для администрирования)
    """
    success = await order_service.delete_order(order_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден"
        )
    
    
    return None

@router.patch("/{order_id}/cancel",status_code=status.HTTP_200_OK, response_model=CancelOrderResponse)
async def cancel_order(order_id: int, order_service: OrderService = Depends(get_order_service)):

    try:
        cancel = await order_service.cancel_order(order_id)

        if not cancel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Заказ с ID {order_id} не найден"
            )
        
        

        return CancelOrderResponse(
            id=order_id,
            status="cancelled",
            message="Заказ успешно отменен"
        )
    
    except ValueError as e:
        error_message = str(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=error_message)
    except Exception as e:
        logger.error(f"Произошла ошибка отмены заказа: {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутренняя ошибка сервера")