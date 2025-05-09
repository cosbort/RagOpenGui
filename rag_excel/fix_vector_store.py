"""
Script per risolvere i problemi con il vector store del sistema RAG Excel.
"""

import os
import shutil
import logging
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders.excel import UnstructuredExcelLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configura il logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carica le variabili d'ambiente
load_dotenv()

# Configurazione
EXCEL_FILE_PATH = os.getenv("EXCEL_FILE_PATH", "./data/dati.xlsx")
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./data/vector_store")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def check_environment():
    """Verifica che l'ambiente sia configurato correttamente."""
    logger.info("Verifica delle variabili d'ambiente...")
    
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY non trovata nelle variabili d'ambiente")
        return False
    
    logger.info(f"EXCEL_FILE_PATH: {EXCEL_FILE_PATH}")
    logger.info(f"VECTOR_STORE_PATH: {VECTOR_STORE_PATH}")
    
    if not os.path.exists(EXCEL_FILE_PATH):
        logger.error(f"File Excel non trovato: {EXCEL_FILE_PATH}")
        return False
    
    return True

def clean_vector_store():
    """Pulisce la directory del vector store."""
    logger.info(f"Pulizia della directory del vector store: {VECTOR_STORE_PATH}")
    
    if os.path.exists(VECTOR_STORE_PATH):
        try:
            shutil.rmtree(VECTOR_STORE_PATH)
            logger.info("Directory del vector store eliminata con successo")
        except Exception as e:
            logger.error(f"Errore durante l'eliminazione della directory: {str(e)}")
            return False
    
    # Crea la directory vuota
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    logger.info("Directory del vector store creata")
    
    return True

def create_vector_store():
    """Crea un nuovo vector store dai dati Excel."""
    logger.info(f"Creazione del vector store da: {EXCEL_FILE_PATH}")
    
    try:
        # Carica i dati Excel
        loader = UnstructuredExcelLoader(EXCEL_FILE_PATH)
        documents = loader.load()
        logger.info(f"Caricati {len(documents)} documenti dal file Excel")
        
        # Dividi i documenti in chunk più piccoli
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Creati {len(chunks)} chunks dai documenti")
        
        # Crea gli embeddings
        embeddings = OpenAIEmbeddings()
        logger.info("Embeddings inizializzati")
        
        # Crea il vector store
        vector_store = FAISS.from_documents(chunks, embeddings)
        logger.info("Vector store creato")
        
        # Salva il vector store
        vector_store.save_local(VECTOR_STORE_PATH)
        logger.info(f"Vector store salvato in: {VECTOR_STORE_PATH}")
        
        return True
    except Exception as e:
        logger.error(f"Errore durante la creazione del vector store: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def verify_vector_store():
    """Verifica che il vector store sia stato creato correttamente."""
    logger.info(f"Verifica del vector store in: {VECTOR_STORE_PATH}")
    
    if not os.path.exists(VECTOR_STORE_PATH):
        logger.error("Directory del vector store non trovata")
        return False
    
    files = list(Path(VECTOR_STORE_PATH).glob("*"))
    if not files:
        logger.error("Nessun file trovato nella directory del vector store")
        return False
    
    logger.info(f"File trovati nella directory del vector store: {[f.name for f in files]}")
    
    try:
        # Prova a caricare il vector store
        embeddings = OpenAIEmbeddings()
        vector_store = FAISS.load_local(
            VECTOR_STORE_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        logger.info("Vector store caricato con successo")
        
        # Prova a fare una query di test
        docs = vector_store.similarity_search("test", k=1)
        logger.info(f"Query di test eseguita con successo, trovati {len(docs)} documenti")
        
        return True
    except Exception as e:
        logger.error(f"Errore durante la verifica del vector store: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Funzione principale."""
    logger.info("Avvio dello script di riparazione del vector store")
    
    # Verifica l'ambiente
    if not check_environment():
        logger.error("Verifica dell'ambiente fallita")
        return False
    
    # Pulisci il vector store
    if not clean_vector_store():
        logger.error("Pulizia del vector store fallita")
        return False
    
    # Crea il vector store
    if not create_vector_store():
        logger.error("Creazione del vector store fallita")
        return False
    
    # Verifica il vector store
    if not verify_vector_store():
        logger.error("Verifica del vector store fallita")
        return False
    
    logger.info("Vector store riparato con successo")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("Vector store riparato con successo!")
    else:
        print("Riparazione del vector store fallita. Controlla i log per maggiori dettagli.")
