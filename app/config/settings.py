from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = Path(current_dir).parent.parent
os.chdir(current_dir)
dotenv_path = find_dotenv(".env")
load_dotenv(dotenv_path)


class Config(BaseSettings):

    DB_NAME: str
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Config()
