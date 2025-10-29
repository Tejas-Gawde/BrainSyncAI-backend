from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str
    DATABASE_NAME: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXP_MINUTES: int = 60
    COOKIE_NAME: str = "access_token"
    COOKIE_SECURE: bool = False
    PASSWORD_RESET_EXP_MINUTES: int = 30
    GROQ_API_KEY: str
    GROQ_MODEL_NAME: str = "llama-3.1-8b-instant"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
