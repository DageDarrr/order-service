from app.config.settings import settings
from app.utils.logger import get_logger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Union

from app.db.models.base import Base

logger = get_logger(__name__)


class DBManager:

    def init_db(self, db_url: str):
        self.engine = create_async_engine(
            url=db_url,
            echo=True,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine, expire_on_commit=False
        )

        self.db_url = db_url

        logger.info("База данных успешно запущена")

    async def create_tables(self):

        if not self.engine:
            raise RuntimeError("Сначала вызови init_db")

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Все таблицы успешно созданы")

    async def drop_tables(self):
        if not self.engine:
            raise RuntimeError("Сначала вызови init_db")

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Все таблицы успешно удалены")

    async def recreate_tables(self):
        await self.drop_tables()
        await self.create_tables()
        logger.info("Таблицы успешно пересозданы")

    async def close(self):
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.db_url = None
            self.session_factory = None
            logger.info("Соединение с DBManager закрыто")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if not self.session_factory:
            raise RuntimeError("Вызови init_db сначала")

        session = self.session_factory()

        try:
            yield session

            await session.commit()

        except Exception as e:
            logger.error(f"Произошла ошибка получения сессии: {e}")
            await session.rollback()
            raise

        finally:
            await session.close()

    @asynccontextmanager
    async def session_context(self) -> AsyncGenerator[AsyncSession, None]:

        async for session in self.get_session():
            yield session


db_manager = DBManager()
