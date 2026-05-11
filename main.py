from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from app.utils.logger import get_logger
from app.db.database import db_manager
from app.api.routes import order_router
from app.config.settings import settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Startup: Connecting to database...")

    db_manager.init_db(settings.DATABASE_URL)

    await db_manager.create_tables()

    yield

    logger.info("Shutdown: Disconnecting from database...")
    await db_manager.close()


app = FastAPI(lifespan=lifespan)

app.include_router(order_router)


@app.get("/")
async def read_root():
    return {"message": "Hello World"}


# Логги в реально времени docker-compose logs -f app
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
