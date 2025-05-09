"""
Implementazione della catena RAG utilizzando LangChain.
"""
import logging
import os
from typing import Dict, Any, List
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import configurazione e utility centralizzate
from config import (
    init_logging,
    OPENAI_API_KEY, 
    LLM_MODEL, 
    MAX_RESULTS, 
    SIMILARITY_THRESHOLD,
    EXCEL_FILE_PATH # Necessario per fallback creazione
)
from .vector_store import VectorStoreManager
from .prompts import RAG_TEMPLATE # Importa il template
from .excel_loader import ExcelLoader # Importa ExcelLoader per fallback creazione

# Inizializza logger
logger = init_logging(__name__)

class RagChain:
    """
    Classe per gestire la catena RAG utilizzando LangChain.
    """
    
    def __init__(self, vector_store_path: str):
        """
        Inizializza la catena RAG.
        
        Args:
            vector_store_path: Percorso al vector store
        """
        self.vector_store_manager = VectorStoreManager(vector_store_path) # Usa il path passato
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=OPENAI_API_KEY,
            temperature=0.1
        )
        self.qa_chain = None
        
    def initialize(self) -> bool:
        """
        Inizializza la catena RAG caricando il vector store.
        Non tenta più la creazione automatica se fallisce.
        
        Returns:
            True se l'inizializzazione è avvenuta con successo, False altrimenti
        """
        logger.info("Tentativo di inizializzazione della catena RAG...")
        self.qa_chain = None # Resetta la catena prima di provare a inizializzare
        try:
            # Tenta di caricare il vector store
            if not self.vector_store_manager.load():
                logger.error("Inizializzazione fallita: Vector store non trovato o non caricabile.")
                return False
            
            # Crea il retriever
            logger.info("Creazione del retriever...")
            retriever = self.vector_store_manager.vector_store.as_retriever(
                # Usa costanti da config
                search_kwargs={"k": MAX_RESULTS} 
            )
            
            # Crea il prompt template
            logger.info("Creazione del prompt template...")
            prompt = PromptTemplate(
                template=RAG_TEMPLATE, # Usa template importato
                input_variables=["context", "question"]
            )
            
            # Crea la catena QA
            logger.info(f"Creazione della catena QA con LLM: {LLM_MODEL}...")
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                chain_type_kwargs={"prompt": prompt},
                return_source_documents=True
            )
            logger.info("Catena QA creata e inizializzazione completata con successo.")
            return True

        except Exception as e:
            logger.error(f"Errore generale durante l'inizializzazione della catena RAG: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.qa_chain = None # Assicura che la catena sia None in caso di errore
            return False

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Risponde a una domanda utilizzando la catena RAG.
        Assicura che la catena sia inizializzata prima di rispondere.
        
        Args:
            question: Domanda da rispondere
            
        Returns:
            Dizionario con la risposta e le fonti
        """
        # Verifica che la catena sia inizializzata
        if not self.qa_chain:
            logger.error("Impossibile rispondere: la catena RAG non è inizializzata.")
            # Tentativo di ri-inizializzazione (opzionale, potrebbe essere meglio gestirlo esternamente)
            # logger.info("Tentativo di ri-inizializzazione automatica...")
            # if not self.initialize():
            #     return {
            #         "answer": "Errore: Il sistema RAG non è pronto e non è stato possibile inizializzarlo.",
            #         "sources": []
            #     }
            # else:
            #    logger.info("Ri-inizializzazione riuscita, procedo con la query.")
            # Per ora, restituisce errore se non inizializzato
            return {
                 "answer": "Errore: Il sistema RAG non è pronto.",
                 "sources": []
             }
            
        try:
            logger.info(f"Elaborazione della domanda tramite catena QA: '{question}'")
            
            # Esegui la query
            result = self.qa_chain({"query": question})
            
            # Estrai la risposta e i documenti sorgente
            answer = result.get("result", "")
            source_documents = result.get("source_documents", [])
            
            # Formatta le fonti
            sources = []
            for doc in source_documents:
                sources.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            logger.info(f"Risposta generata con {len(sources)} fonti")
            
            return {
                "answer": answer,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Errore durante la risposta alla domanda: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "answer": f"Mi dispiace, si è verificato un errore durante l'elaborazione della tua domanda: {str(e)}",
                "sources": []
            }
    
    def direct_similarity_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Esegue direttamente una ricerca di similarità nel vector store.
        
        Args:
            query: Query di ricerca
            
        Returns:
            Lista di documenti simili con score
        """
        return self.vector_store_manager.similarity_search(
            query,
            k=MAX_RESULTS, # Usa costante da config
            threshold=SIMILARITY_THRESHOLD # Usa costante da config
        )