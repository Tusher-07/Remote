import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Simple configuration object reading environment variables."""

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model_name: str = os.getenv("MODEL_NAME", "qwen3.5:4b")


config = Config()
