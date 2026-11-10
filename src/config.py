import os

from dotenv import load_dotenv

load_dotenv() # lee las apis keys y el modelo desde el archivo .env

# "proveedor:modelo". Se cambia en el .env sin tocar el código
# MODELO = os.getenv("MODELO", "openia:gpt-4.1-mini")
# MODELO = os.getenv("MODELO", "anthropic:claude-sonnet-5-5")
MODELO = os.getenv("MODELO", "ollama:llama3.1:8b")