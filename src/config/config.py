from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    sqlalchemy_database_url: str = Field(env="SQLALCHEMY_DATABASE_URL")
    secret_key: str
    algorithm: str
    m_username: str
    m_password: str
    m_from: str
    m_port: int
    m_server: str
    redis_host: str = 'localhost'
    redis_port: int
    cloudinary_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    model_config = SettingsConfigDict(
        env_file="../.env", env_file_encoding="utf-8", extra="ignore"
    )


#settings = Settings()
settings1 = Settings()


