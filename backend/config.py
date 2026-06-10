import os
from pathlib import Path


def load_env_file(override=False):
    for key, value in read_env_file().items():
        if override or key not in os.environ:
            os.environ[key] = value


def read_env_file():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return {}

    values = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value

    return values


def env_file_path():
    return Path(__file__).resolve().parents[1] / ".env"


load_env_file()


DB_URL = "sqlite:///./ojs_scanner.db"
SECRET_KEY = "secret123"

# Optional LLM reasoning.
# Kosongkan agar scanner tetap memakai fallback lokal tanpa LLM.
# Contoh OpenAI-compatible:
#   $env:LLM_PROVIDER = "openai"
#   $env:LLM_API_KEY = "sk-..."
#   $env:LLM_MODEL = "gpt-4o-mini"
#
# Contoh Ollama lokal:
#   $env:LLM_PROVIDER = "ollama"
#   $env:LLM_MODEL = "llama3.1"
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")
LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "20"))
