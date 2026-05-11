from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.api.dependencies.db_session import get_db
from app.db.database import db_manager
from app.services.order_service import OrderService


async def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    """Dependency для получения сервиса заказов"""
    return OrderService(db)
