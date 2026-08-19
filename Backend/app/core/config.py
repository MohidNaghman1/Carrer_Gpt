# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- Database Settings ---
    DATABASE_URL: str
    
    # --- AI Provider API Keys ---
    GOOGLE_API_KEY: str
    GROQ_API_KEY: str
    TAVILY_API_KEY: str
    FRONTEND_ORIGIN: str
    # --- JWT / Security Settings ---
    # It's better to load these from .env as well
    SECRET_KEY: str
    ALGORITHM: str = "HS256" # You can provide a default value
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # And a default value here

    # This tells Pydantic to load the variables from a file named .env
    model_config = SettingsConfigDict(env_file=".env")


# Create a single, global instance of the Settings class
# This object will be imported by other parts of the application
settings = Settings()