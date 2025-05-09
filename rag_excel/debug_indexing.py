"""
Script per il debug del processo di indicizzazione.
"""
import os
import sys
import logging
import traceback
from pathlib import Path

# Configurazione del logger per mostrare informazioni dettagliate
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Aggiungi la directory principale al path
sys.path.append(str(Path(__file__).resolve().parent))

from config import VECTOR_STORE_PATH, EXCEL_FILE_PATH, OPENAI_API_KEY, EMBEDDING_MODEL
from utils.excel_loader import ExcelLoader
from utils.vector_store import VectorStoreManager

def main():
    """Funzione principale per il debug del processo di indicizzazione."""
    try:
        # Verifica la configurazione
        logger.debug(f"EXCEL_FILE_PATH: {EXCEL_FILE_PATH}")
        logger.debug(f"VECTOR_STORE_PATH: {VECTOR_STORE_PATH}")
        logger.debug(f"EMBEDDING_MODEL: {EMBEDDING_MODEL}")
        logger.debug(f"OPENAI_API_KEY: {'Configurata' if OPENAI_API_KEY else 'Non configurata'}")
        
        # Verifica che il file Excel esista
        if not os.path.exists(EXCEL_FILE_PATH):
            logger.error(f"File Excel non trovato: {EXCEL_FILE_PATH}")
            return False
        
        logger.debug(f"File Excel trovato: {EXCEL_FILE_PATH}")
        
        # Verifica che la directory vector_store esista
        vector_store_dir = Path(VECTOR_STORE_PATH)
        if not vector_store_dir.exists():
            logger.debug(f"Creazione della directory vector_store: {vector_store_dir}")
            vector_store_dir.mkdir(parents=True, exist_ok=True)
        
        # Carica i dati Excel
        logger.debug("Caricamento dei dati Excel...")
        excel_loader = ExcelLoader(EXCEL_FILE_PATH)
        documents = excel_loader.get_documents()
        
        if not documents:
            logger.error("Nessun dato trovato nel file Excel")
            return False
        
        logger.debug(f"Caricati {len(documents)} documenti dal file Excel")
        logger.debug(f"Esempio di documento: {documents[0] if documents else 'Nessun documento'}")
        
        # Crea il vector store manager
        logger.debug(f"Inizializzazione del vector store manager in: {VECTOR_STORE_PATH}")
        vector_store_manager = VectorStoreManager(VECTOR_STORE_PATH)
        
        # Crea o aggiorna il vector store
        logger.debug("Creazione/aggiornamento del vector store...")
        try:
            vector_store_manager.create_or_update(documents)
            logger.debug("Creazione/aggiornamento del vector store completato")
        except Exception as e:
            logger.error(f"Errore durante la creazione/aggiornamento del vector store: {str(e)}")
            logger.error(traceback.format_exc())
            return False
        
        # Verifica che il vector store sia stato creato correttamente
        logger.debug("Verifica del vector store...")
        if vector_store_manager.load():
            logger.debug("Vector store caricato con successo")
            
            # Esegui una ricerca di test
            logger.debug("Esecuzione di una ricerca di test...")
            results = vector_store_manager.similarity_search("test", k=1)
            logger.debug(f"Risultati della ricerca di test: {results}")
            
            return True
        else:
            logger.error("Impossibile caricare il vector store dopo la creazione")
            return False
        
    except Exception as e:
        logger.error(f"Errore durante il debug del processo di indicizzazione: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    if success:
        logger.debug("Debug del processo di indicizzazione completato con successo")
    else:
        logger.error("Debug del processo di indicizzazione fallito")
