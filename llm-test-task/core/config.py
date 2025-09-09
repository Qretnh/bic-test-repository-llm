import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY")
    openrouter_api_url: str = "https://openrouter.ai/api/v1/completions"

    class Config:
        env_file = ".env"


settings = Settings()
