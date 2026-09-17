from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:0.5b"
    database_path: str = "./data/workflow.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()