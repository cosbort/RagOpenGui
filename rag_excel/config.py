"""
Configurazione dell'applicazione RAG Excel.
"""
import os
import logging
import sys
from dotenv import load_dotenv
from pathlib import Path

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Directory base del progetto
BASE_DIR = Path(__file__).resolve().parent

# Configurazione API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Configurazione OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")  # Utilizzo di GPT-4o, il modello più recente

# Configurazione Excel
EXCEL_FILE_PATH = os.getenv("EXCEL_FILE_PATH", str(BASE_DIR / "data" / "dati.xlsx"))

# Configurazione Vector Store
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", str(BASE_DIR / "data" / "vector_store"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "256"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))

# Configurazione RAG
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "15"))  # Aumentato a 15 per più contesto
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.4"))

# Configurazione Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def init_logging(name: str) -> logging.Logger:
    """Inizializza e restituisce un logger configurato."""
    log_level_numeric = getattr(logging, LOG_LEVEL, logging.INFO)
    
    # Evita configurazioni multiple se già fatta
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=log_level_numeric,
            format=LOG_FORMAT,
            handlers=[
                # Aggiungi qui eventuali handler specifici se necessario, es. FileHandler
                # logging.FileHandler("app.log"), 
                logging.StreamHandler(sys.stdout) # Output sulla console
            ]
        )
    logger = logging.getLogger(name)
    logger.setLevel(log_level_numeric) # Assicura che il logger specifico abbia il livello corretto
    return logger

# Configurazione HTTP Client (per rag_excel_function.py)
HTTPX_TIMEOUT = float(os.getenv("HTTPX_TIMEOUT", "60.0"))
HTTPX_RETRIES = int(os.getenv("HTTPX_RETRIES", "5"))

# URL Server RAG (per rag_excel_function.py)
RAG_EXCEL_URL = f"http://{API_HOST}:{API_PORT}"