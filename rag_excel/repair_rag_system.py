"""
Script per riparare completamente il sistema RAG Excel.
"""

import os
import logging
import argparse
from pathlib import Path
import time
import shutil

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Import configurazione e utility
from config import (
    init_logging,
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    LLM_MODEL,
    EXCEL_FILE_PATH,
    VECTOR_STORE_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MAX_RESULTS,
    SIMILARITY_THRESHOLD
)
from utils.excel_loader import ExcelLoader
from utils.vector_store import VectorStoreManager
from utils.vector_utils import clean_vector_store, ensure_vector_store_path
from utils.prompts import REPAIR_RAG_TEMPLATE # Usa il template specifico per il repair

# Inizializza il logger
logger = init_logging(__name__)

def check_environment() -> bool:
    """
    Verifica che l'ambiente sia configurato correttamente.
    """
    logger.info("Verifica delle variabili d'ambiente...")
    
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY non trovata nelle variabili d'ambiente")
        return False
    
    logger.info(f"EXCEL_FILE_PATH: {EXCEL_FILE_PATH}")
    logger.info(f"VECTOR_STORE_PATH: {VECTOR_STORE_PATH}")
    logger.info(f"LLM_MODEL: {LLM_MODEL}")
    
    # Verifica percorso file Excel
    logger.info(f"Verifica percorso file Excel: {EXCEL_FILE_PATH}")
    if not Path(EXCEL_FILE_PATH).exists():
        logger.error(f"File Excel non trovato: {EXCEL_FILE_PATH}")
        return False
    
    # Verifica esistenza directory Vector Store (usa utility)
    ensure_vector_store_path(VECTOR_STORE_PATH)
    logger.info(f"Verifica completata. Vector Store Path assicurato: {VECTOR_STORE_PATH}")
    
    return True

def create_vector_store() -> bool:
    """
    Carica i dati dal file Excel, crea gli embeddings e salva il vector store FAISS.
    """
    logger.info("Avvio creazione Vector Store...")
    start_time = time.time()
    try:
        # Carica i documenti dal file Excel
        logger.info(f"Caricamento documenti da: {EXCEL_FILE_PATH}")
        excel_loader = ExcelLoader(EXCEL_FILE_PATH)
        documents = excel_loader.get_documents()
        if not documents:
            logger.error("Nessun documento caricato dal file Excel.")
            return False
        logger.info(f"Caricati {len(documents)} documenti.")
        
        # Crea il vector store manager e crea/aggiorna il vector store
        vector_store_manager = VectorStoreManager(VECTOR_STORE_PATH)
        vector_store_manager.create_or_update(documents)
        
        end_time = time.time()
        logger.info(f"Vector Store creato con successo in {end_time - start_time:.2f} secondi.")
        return True
        
    except Exception as e:
        logger.error(f"Errore durante la creazione del Vector Store: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_rag_system(query: str = "Qual è lo stipendio medio?") -> bool:
    """
    Carica il vector store esistente e testa il sistema RAG con una query.
    """
    logger.info("Avvio test del sistema RAG...")
    try:
        # Crea il vector store manager e carica il vector store
        vector_store_manager = VectorStoreManager(VECTOR_STORE_PATH)
        if not vector_store_manager.load():
            logger.error("Impossibile caricare il Vector Store per il test.")
            return False
        
        # Crea il retriever
        retriever = vector_store_manager.vector_store.as_retriever(
            search_kwargs={"k": MAX_RESULTS}
        )
        
        # Crea l'LLM
        llm = ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=OPENAI_API_KEY,
            temperature=0.0
        )
        
        # Crea il prompt template (usando quello specifico del repair)
        prompt = PromptTemplate(
            template=REPAIR_RAG_TEMPLATE, 
            input_variables=["context", "question"]
        )
        
        # Crea la catena QA
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        
        logger.info(f"Esecuzione query di test: '{query}'")
        result = qa_chain({"query": query})
        
        logger.info("Risposta dal sistema RAG:")
        logger.info(f"  Risposta: {result['result']}")
        
        if result.get('source_documents'):
            logger.info("  Documenti sorgente trovati:")
            for i, doc in enumerate(result['source_documents']):
                logger.info(f"    - Documento {i+1}: (Punteggio: {doc.metadata.get('score', 'N/A')})")
                logger.info(f"      Contenuto: {doc.page_content[:150]}...") # Mostra solo i primi 150 caratteri
                logger.info(f"      Metadati: {doc.metadata}")
        else:
            logger.info("  Nessun documento sorgente trovato.")
            
        logger.info("Test del sistema RAG completato con successo.")
        return True

    except Exception as e:
        logger.error(f"Errore durante il test del sistema RAG: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script di riparazione e test per il sistema RAG Excel.")
    parser.add_argument("--clean", action="store_true", help="Pulisce il vector store prima di ricrearlo.")
    parser.add_argument("--create", action="store_true", help="Ricrea il vector store dai dati Excel.")
    parser.add_argument("--test", action="store_true", help="Testa il sistema RAG con una query di default.")
    parser.add_argument("--query", type=str, default="Qual è lo stipendio medio?", help="Query specifica da usare per il test.")
    
    args = parser.parse_args()
    
    logger.info("Avvio script di riparazione/test RAG...")
    
    if not check_environment():
        logger.error("Controllo ambiente fallito. Impossibile procedere.")
    else:
        logger.info("Controllo ambiente superato.")
        
        if args.clean:
            logger.info("Pulizia del Vector Store richiesta...")
            # Usa la funzione centralizzata
            if clean_vector_store(VECTOR_STORE_PATH):
                logger.info("Pulizia del Vector Store completata.")
            else:
                logger.warning("Pulizia del Vector Store fallita o non necessaria.")
        
        if args.create:
            logger.info("Creazione del Vector Store richiesta...")
            if create_vector_store():
                logger.info("Creazione del Vector Store completata con successo.")
            else:
                logger.error("Creazione del Vector Store fallita.")
        
        if args.test:
            logger.info("Test del sistema RAG richiesto...")
            if test_rag_system(args.query):
                logger.info("Test del sistema RAG completato.")
            else:
                logger.error("Test del sistema RAG fallito.")

    logger.info("Script di riparazione/test RAG terminato.")
