"""
Script per il debug dell'inizializzazione della catena RAG.
"""
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
import sys
sys.path.append(str(Path(__file__).resolve().parent))

from config import VECTOR_STORE_PATH, OPENAI_API_KEY, LLM_MODEL
from utils.vector_store import VectorStoreManager
from utils.rag_chain import RagChain

def main():
    """Funzione principale per il debug dell'inizializzazione della catena RAG."""
    try:
        # Verifica la configurazione
        logger.debug(f"VECTOR_STORE_PATH: {VECTOR_STORE_PATH}")
        logger.debug(f"LLM_MODEL: {LLM_MODEL}")
        logger.debug(f"OPENAI_API_KEY: {'Configurata' if OPENAI_API_KEY else 'Non configurata'}")
        
        # Verifica che la directory vector_store esista
        vector_store_dir = Path(VECTOR_STORE_PATH)
        if not vector_store_dir.exists():
            logger.error(f"Directory vector_store non trovata: {vector_store_dir}")
            return False
        
        # Verifica che ci siano file nella directory vector_store
        files = list(vector_store_dir.glob("*"))
        logger.debug(f"File nella directory vector_store: {[f.name for f in files]}")
        
        # Crea il vector store manager
        logger.debug("Creazione del vector store manager...")
        vector_store_manager = VectorStoreManager(VECTOR_STORE_PATH)
        
        # Carica il vector store
        logger.debug("Caricamento del vector store...")
        if not vector_store_manager.load():
            logger.error("Impossibile caricare il vector store")
            return False
        
        logger.debug("Vector store caricato con successo")
        
        # Crea la catena RAG
        logger.debug("Creazione della catena RAG...")
        rag_chain = RagChain(VECTOR_STORE_PATH)
        
        # Inizializza la catena RAG
        logger.debug("Inizializzazione della catena RAG...")
        if not rag_chain.initialize():
            logger.error("Impossibile inizializzare la catena RAG")
            return False
        
        logger.debug("Catena RAG inizializzata con successo")
        
        # Prova a rispondere a una domanda
        logger.debug("Test della catena RAG con una domanda...")
        result = rag_chain.answer_question("Qual è il fatturato della regione Nord?")
        
        logger.debug(f"Risposta: {result.get('answer', '')}")
        logger.debug(f"Fonti: {len(result.get('sources', []))} trovate")
        
        return True
        
    except Exception as e:
        logger.error(f"Errore durante il debug dell'inizializzazione della catena RAG: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    if success:
        logger.debug("Debug dell'inizializzazione della catena RAG completato con successo")
    else:
        logger.error("Debug dell'inizializzazione della catena RAG fallito")
