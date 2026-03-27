from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./flight_monitor.db"
    serpapi_api_key: str = ""
    gmail_sender: str = ""
    gmail_app_password: str = ""
    gmail_recipient: str = ""
    app_base_url: str = "http://localhost:8000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
