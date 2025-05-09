"""
Utility per la gestione del percorso e dello stato del vector store.
"""
import os
import shutil
import logging
from pathlib import Path

# Assumiamo che init_logging sia disponibile, altrimenti usa logging standard
try:
    from .logging_config import init_logging
    logger = init_logging(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

def ensure_vector_store_path(vector_store_path: str):
    """Assicura che la directory del vector store esista."""
    path = Path(vector_store_path)
    if not path.exists():
        logger.warning(f"Directory vector store non trovata: {vector_store_path}. Creazione in corso...")
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory vector store creata: {vector_store_path}")
        except Exception as e:
            logger.error(f"Errore durante la creazione della directory {vector_store_path}: {e}")
            raise
    else:
        logger.debug(f"Directory vector store trovata: {vector_store_path}")

def clean_vector_store(vector_store_path: str):
    """Elimina e ricrea la directory del vector store."""
    logger.info(f"Pulizia della directory del vector store: {vector_store_path}")
    path = Path(vector_store_path)
    if path.exists():
        try:
            shutil.rmtree(path)
            logger.info("Vecchia directory del vector store eliminata con successo")
        except Exception as e:
            logger.error(f"Errore durante l'eliminazione della directory {vector_store_path}: {e}")
            # Non rilanciare l'eccezione, proviamo comunque a creare la cartella
    
    # Crea la directory (di nuovo)
    ensure_vector_store_path(vector_store_path)
