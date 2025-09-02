from pydantic import BaseModel
import os

from dotenv import load_dotenv

load_dotenv(override=True)

class Settings(BaseModel):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    gen_temperature: float = float(os.getenv("GEN_TEMPERATURE", "0.1"))
    gen_max_tokens: int = int(os.getenv("GEN_MAX_TOKENS", "512"))
    request_timeout_s: int = int(os.getenv("REQUEST_TIMEOUT_S", "45"))

settings = Settings()
