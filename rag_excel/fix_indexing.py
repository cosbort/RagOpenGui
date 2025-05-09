"""
Script per verificare e risolvere i problemi di indicizzazione del vector store.
"""
import os
import sys
import logging
from pathlib import Path

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Aggiungi la directory principale al path
sys.path.append(str(Path(__file__).resolve().parent))

from config import VECTOR_STORE_PATH, EXCEL_FILE_PATH
from utils.excel_loader import ExcelLoader
from utils.vector_store import VectorStoreManager

def main():
    """Funzione principale per verificare e risolvere i problemi di indicizzazione."""
    try:
        # Verifica che il file Excel esista
        if not os.path.exists(EXCEL_FILE_PATH):
            logger.error(f"File Excel non trovato: {EXCEL_FILE_PATH}")
            return False
        
        logger.info(f"File Excel trovato: {EXCEL_FILE_PATH}")
        
        # Verifica che la directory vector_store esista
        vector_store_dir = Path(VECTOR_STORE_PATH)
        if not vector_store_dir.exists():
            logger.info(f"Creazione della directory vector_store: {vector_store_dir}")
            vector_store_dir.mkdir(parents=True, exist_ok=True)
        
        # Carica i dati Excel
        logger.info("Caricamento dei dati Excel...")
        excel_loader = ExcelLoader(EXCEL_FILE_PATH)
        documents = excel_loader.get_documents()
        
        if not documents:
            logger.error("Nessun dato trovato nel file Excel")
            return False
        
        logger.info(f"Caricati {len(documents)} documenti dal file Excel")
        
        # Crea il vector store manager
        logger.info(f"Inizializzazione del vector store manager in: {VECTOR_STORE_PATH}")
        vector_store_manager = VectorStoreManager(VECTOR_STORE_PATH)
        
        # Crea o aggiorna il vector store
        logger.info("Creazione/aggiornamento del vector store...")
        vector_store_manager.create_or_update(documents)
        
        # Verifica che il vector store sia stato creato correttamente
        if vector_store_manager.load():
            logger.info("Vector store creato e caricato con successo")
            return True
        else:
            logger.error("Impossibile caricare il vector store dopo la creazione")
            return False
        
    except Exception as e:
        logger.error(f"Errore durante la verifica/risoluzione dei problemi di indicizzazione: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Indicizzazione completata con successo")
    else:
        logger.error("Indicizzazione fallita")
