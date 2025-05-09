"""
Utility per gestire il vector store per il RAG.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
# Importa configurazione centralizzata
from config import (
    init_logging,
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    VECTOR_STORE_PATH # Importa anche il percorso di default se necessario
)
# Importa utility per il vector store
from .vector_utils import ensure_vector_store_path

# Inizializza il logger
logger = init_logging(__name__)

class VectorStoreManager:
    """
    Classe per gestire il vector store per il RAG.
    """
    
    def __init__(self, vector_store_path: str):
        """
        Inizializza il manager del vector store.
        
        Args:
            vector_store_path: Percorso dove salvare/caricare il vector store
        """
        # Usa il percorso fornito o quello di default da config
        self.vector_store_path = vector_store_path or VECTOR_STORE_PATH 
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY
        )
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", ", ", " ", ""]
        )
        self.allow_dangerous_deserialization = True # Mantenuto per compatibilità con memoria

    def _convert_to_langchain_documents(self, documents: List[Dict[str, Any]]) -> List[Document]:
        """
        Converte i documenti nel formato richiesto da LangChain.
        
        Args:
            documents: Lista di documenti con page_content e metadata
            
        Returns:
            Lista di Document di LangChain
        """
        return [
            Document(
                page_content=doc["page_content"],
                metadata=doc["metadata"]
            )
            for doc in documents
        ]
    
    def create_or_update(self, documents: List[Dict[str, Any]]) -> None:
        """
        Crea o aggiorna il vector store con i documenti forniti.
        
        Args:
            documents: Lista di documenti da aggiungere al vector store
        """
        try:
            logger.info(f"Creazione/aggiornamento del vector store in: {self.vector_store_path}")
            
            # Converti i documenti nel formato LangChain
            langchain_docs = self._convert_to_langchain_documents(documents)
            
            # Dividi i documenti in chunks
            logger.info(f"Divisione di {len(langchain_docs)} documenti in chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
            chunks = self.text_splitter.split_documents(langchain_docs)
            logger.info(f"Creati {len(chunks)} chunks dai documenti")
            
            # Assicura che la directory esista
            ensure_vector_store_path(self.vector_store_path)
            
            # Crea o aggiorna il vector store
            # Verifica se la directory contiene già un indice FAISS valido
            index_file = Path(self.vector_store_path) / "index.faiss"
            pkl_file = Path(self.vector_store_path) / "index.pkl"
            
            # Modificato: controlla esistenza file specifici invece che listdir
            if index_file.exists() and pkl_file.exists():
                # Carica il vector store esistente
                logger.info("Vector store esistente trovato, caricamento per aggiornamento...")
                # Usa il metodo load interno che gestisce l'opzione
                if self.load(): 
                    # Aggiungi i nuovi documenti
                    logger.info(f"Aggiunta di {len(chunks)} chunks al vector store esistente")
                    self.vector_store.add_documents(chunks)
                    
                    # Salva il vector store aggiornato
                    self.vector_store.save_local(self.vector_store_path)
                    logger.info("Vector store aggiornato e salvato")
                else:
                    logger.error("Impossibile caricare il vector store esistente per l'aggiornamento.")
                    # Potrebbe essere corrotto, ricreiamolo da zero
                    self._create_new_vector_store(chunks)
            else:
                # Crea un nuovo vector store
                self._create_new_vector_store(chunks)
                
        except Exception as e:
            logger.error(f"Errore durante la creazione/aggiornamento del vector store: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _create_new_vector_store(self, chunks: List[Document]):
        """Helper interno per creare un nuovo vector store."""
        logger.info(f"Creazione di un nuovo vector store con {len(chunks)} chunks")
        self.vector_store = FAISS.from_documents(
            chunks,
            self.embeddings
        )
        # Salva il nuovo vector store
        self.vector_store.save_local(self.vector_store_path)
        logger.info("Nuovo vector store creato e salvato")

    def load(self) -> bool:
        """
        Carica il vector store se esiste.
        
        Returns:
            True se il vector store è stato caricato, False altrimenti
        """
        try:
            # Assicura che il path esista prima di verificare i file interni
            ensure_vector_store_path(self.vector_store_path)
            index_file = Path(self.vector_store_path) / "index.faiss"
            pkl_file = Path(self.vector_store_path) / "index.pkl"
            
            if index_file.exists() and pkl_file.exists():
                logger.info(f"Caricamento del vector store da: {self.vector_store_path}")
                self.vector_store = FAISS.load_local(
                    self.vector_store_path,
                    self.embeddings,
                    # Opzione centralizzata nell'init ma usata qui
                    allow_dangerous_deserialization=self.allow_dangerous_deserialization 
                )
                logger.info("Vector store caricato con successo")
                return True
            else:
                logger.warning(f"Nessun file indice FAISS valido (index.faiss, index.pkl) trovato in: {self.vector_store_path}")
                self.vector_store = None
                return False
        except Exception as e:
            logger.error(f"Errore durante il caricamento del vector store: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.vector_store = None # Resetta in caso di errore
            return False

    def similarity_search(self, query: str, k: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Esegue una ricerca di similarità nel vector store.
        
        Args:
            query: Query di ricerca
            k: Numero massimo di risultati da restituire
            threshold: Soglia di similarità minima
            
        Returns:
            Lista di documenti simili con score
        """
        try:
            # Carica il vector store se non è già caricato
            if not self.vector_store:
                if not self.load():
                    logger.error("Impossibile eseguire la ricerca: vector store non caricato")
                    return []
            
            logger.info(f"Esecuzione della ricerca di similarità per: '{query}'")
            
            # Esegui la ricerca con score
            docs_with_scores = self.vector_store.similarity_search_with_score(
                query,
                k=k
            )
            
            # Filtra i risultati in base alla soglia di similarità
            filtered_results = []
            for doc, score in docs_with_scores:
                # Converti lo score in similarità (più alto è meglio)
                # FAISS restituisce la distanza, quindi convertiamo in similarità
                similarity = 1.0 / (1.0 + score)
                
                if similarity >= threshold:
                    filtered_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": similarity
                    })
            
            logger.info(f"Trovati {len(filtered_results)} risultati rilevanti")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Errore durante la ricerca di similarità: {str(e)}")
            return []