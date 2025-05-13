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
    SIMILARITY_THRESHOLD,
    LLAMA_CLOUD_API_KEY
)
from utils.excel_loader import ExcelLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
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

def create_vector_store_optimized() -> bool:
    """
    Carica i dati dal file Excel con ottimizzazioni avanzate per il chunking e l'indicizzazione.
    """
    logger.info("Avvio creazione Vector Store ottimizzato...")
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
        
        # Applica il chunking avanzato per Excel complessi
        logger.info("Applicazione chunking avanzato per Excel complessi...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["# ", "##", "###", "\n\n", "\n", "\t", "|", ",", ";", " ", ""],  # Priorità ai separatori semantici
            keep_separator=True,  # Mantiene i separatori per preservare il contesto
            add_start_index=True  # Aggiunge l'indice di inizio per tracciare meglio la posizione nel documento
        )
        
        # Converti i documenti nel formato Document di LangChain
        langchain_docs = []
        for doc in documents:
            langchain_docs.append(
                Document(
                    page_content=doc["page_content"],
                    metadata=doc["metadata"]
                )
            )
        
        # Applica il chunking
        chunked_docs = text_splitter.split_documents(langchain_docs)
        logger.info(f"Creati {len(chunked_docs)} chunk dopo l'ottimizzazione.")
        
        # Converti i documenti nel formato richiesto da VectorStoreManager
        optimized_documents = []
        for doc in chunked_docs:
            optimized_documents.append({
                "page_content": doc.page_content,
                "metadata": doc.metadata
            })
        
        # Crea il vector store manager e crea/aggiorna il vector store
        vector_store_manager = VectorStoreManager(VECTOR_STORE_PATH)
        vector_store_manager.create_or_update(optimized_documents)
        
        end_time = time.time()
        logger.info(f"Vector Store ottimizzato creato con successo in {end_time - start_time:.2f} secondi.")
        return True
        
    except Exception as e:
        logger.error(f"Errore durante la creazione del Vector Store ottimizzato: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

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

def create_vector_store_with_llamaparse() -> bool:
    """
    Carica i dati dal file Excel usando LlamaParse, crea gli embeddings e salva il vector store FAISS.
    """
    logger.info("Avvio creazione Vector Store con LlamaParse...")
    start_time = time.time()
    try:
        # Inizializza LlamaParse
        from llama_parse import LlamaParse
        from config import LLAMA_CLOUD_REGION
        
        if not LLAMA_CLOUD_API_KEY:
            logger.error("LLAMA_CLOUD_API_KEY non configurata. Impossibile usare LlamaParse.")
            return False
            
        logger.info(f"Inizializzazione LlamaParse con regione: {LLAMA_CLOUD_REGION}...")
        parser = LlamaParse(
            api_key=LLAMA_CLOUD_API_KEY,
            result_type="markdown",  # Formato ottimale per la vettorizzazione
            verbose=True,
            region=LLAMA_CLOUD_REGION,  # Specifica la regione (us, eu, ap)
            base_url=f"https://api.cloud.{LLAMA_CLOUD_REGION}.llamaindex.ai",  # URL base specifico per la regione
            # Istruzioni avanzate per fogli Excel complessi
            parsing_instructions="""Analizza approfonditamente questo file Excel complesso seguendo queste linee guida:
1. Estrai tutte le tabelle preservando la struttura originale, gli indici delle righe e le intestazioni delle colonne
2. Identifica e preserva le relazioni tra celle, formule e riferimenti incrociati tra fogli
3. Riconosci e mantieni la gerarchia dei dati (gruppi, sottogruppi, totali, subtotali)
4. Estrai e interpreta eventuali grafici, evidenziando i trend e le correlazioni rappresentate
5. Identifica e descrivi le celle con formattazione condizionale o speciale
6. Preserva i nomi delle persone, organizzazioni, date e valori numerici significativi
7. Riconosci e mantieni la struttura di eventuali tabelle pivot
8. Formatta il contenuto in modo ottimale per la ricerca semantica e l'estrazione di informazioni specifiche
9. Mantieni il contesto di ogni dato, specificando a quale foglio, sezione o categoria appartiene
10. Evidenzia eventuali anomalie o incongruenze nei dati
"""
        )
        
        # Carica e parsa il file Excel
        logger.info(f"Parsing del file Excel con LlamaParse: {EXCEL_FILE_PATH}")
        llama_documents = parser.load_data(EXCEL_FILE_PATH)
        
        if not llama_documents:
            logger.error("Nessun documento generato da LlamaParse.")
            return False
            
        logger.info(f"Generati {len(llama_documents)} documenti con LlamaParse.")
        
        # Converti i documenti LlamaParse nel formato richiesto da VectorStoreManager
        documents = []
        for llama_doc in llama_documents:
            # Estrai metadati avanzati dal documento
            metadata = {
                "source": EXCEL_FILE_PATH,
                "sheet": llama_doc.metadata.get("sheet", "Unknown"),
                "title": llama_doc.metadata.get("title", "Excel Document"),
                "document_type": "excel",
                "parser": "llamaparse",
                "parse_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "content_type": llama_doc.metadata.get("content_type", "table"),
                "row_count": llama_doc.metadata.get("row_count", 0),
                "column_count": llama_doc.metadata.get("column_count", 0),
                "has_formulas": llama_doc.metadata.get("has_formulas", False),
                "has_charts": llama_doc.metadata.get("has_charts", False),
                "has_pivots": llama_doc.metadata.get("has_pivots", False),
                "sheet_index": llama_doc.metadata.get("sheet_index", 0),
                "content_structure": llama_doc.metadata.get("content_structure", "unknown")
            }
            
            # Aggiungi metadati specifici se disponibili
            if "table_headers" in llama_doc.metadata:
                metadata["table_headers"] = llama_doc.metadata["table_headers"]
            
            if "data_ranges" in llama_doc.metadata:
                metadata["data_ranges"] = llama_doc.metadata["data_ranges"]
                
            if "summary" in llama_doc.metadata:
                metadata["summary"] = llama_doc.metadata["summary"]
                
            documents.append({
                "page_content": llama_doc.get_content(),
                "metadata": metadata
            })
        
        # Applica il chunking avanzato per Excel complessi
        logger.info("Applicazione chunking avanzato per Excel complessi...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["# ", "##", "###", "\n\n", "\n", "\t", "|", ",", ";", " ", ""],  # Priorità ai separatori semantici
            keep_separator=True,  # Mantiene i separatori per preservare il contesto
            add_start_index=True  # Aggiunge l'indice di inizio per tracciare meglio la posizione nel documento
        )
        
        chunked_documents = []
        for doc in documents:
            if len(doc["page_content"]) > CHUNK_SIZE * 2:  # Solo per documenti molto grandi
                chunks = text_splitter.split_text(doc["page_content"])
                for i, chunk in enumerate(chunks):
                    chunked_documents.append({
                        "page_content": chunk,
                        "metadata": {
                            **doc["metadata"],
                            "chunk": i,
                            "total_chunks": len(chunks)
                        }
                    })
            else:
                chunked_documents.append(doc)
        
        logger.info(f"Creati {len(chunked_documents)} chunk dopo l'ottimizzazione.")
        
        # Crea il vector store manager e crea/aggiorna il vector store
        vector_store_manager = VectorStoreManager(VECTOR_STORE_PATH)
        vector_store_manager.create_or_update(chunked_documents)
        
        end_time = time.time()
        logger.info(f"Vector Store creato con successo in {end_time - start_time:.2f} secondi.")
        return True
        
    except Exception as e:
        logger.error(f"Errore durante la creazione del Vector Store con LlamaParse: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_rag_system(query: str = "Chi è il riferimento di Gallina Alessandro?") -> bool:
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
        
        # Crea il retriever con parametri ottimizzati per Excel complessi usando MMR
        retriever = vector_store_manager.vector_store.as_retriever(
            search_kwargs={
                "k": MAX_RESULTS * 3,  # Triplica il numero di risultati per aumentare la copertura
                "fetch_k": MAX_RESULTS * 6,  # Recupera più documenti prima del filtraggio finale
                "lambda_mult": 0.7  # Bilancia tra rilevanza (1.0) e diversità (0.0)
            },
            search_type="mmr"  # Maximum Marginal Relevance: bilancia rilevanza e diversità
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
    parser.add_argument("--query", type=str, default="Chi è il riferimento di Alessandro Gallina?", help="Query specifica da usare per il test.")
    parser.add_argument("--no-llamaparse", action="store_true", help="Disabilita l'uso di LlamaParse anche se configurato.")
    
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
            # Usa LlamaParse se la chiave API è configurata e non è disabilitato
            if LLAMA_CLOUD_API_KEY and not args.no_llamaparse:
                logger.info("Utilizzo di LlamaParse per la creazione del Vector Store...")
                if create_vector_store_with_llamaparse():
                    logger.info("Creazione del Vector Store con LlamaParse completata con successo.")
                else:
                    logger.error("Creazione del Vector Store con LlamaParse fallita. Tentativo con metodo ottimizzato...")
                    if create_vector_store_optimized():
                        logger.info("Creazione del Vector Store ottimizzato completata con successo.")
                    else:
                        logger.error("Creazione del Vector Store ottimizzato fallita. Tentativo con metodo tradizionale...")
                        if create_vector_store():
                            logger.info("Creazione del Vector Store completata con successo.")
                        else:
                            logger.error("Creazione del Vector Store fallita.")
            else:
                logger.info("Utilizzo del metodo ottimizzato per la creazione del Vector Store...")
                if create_vector_store_optimized():
                    logger.info("Creazione del Vector Store ottimizzato completata con successo.")
                else:
                    logger.error("Creazione del Vector Store ottimizzato fallita. Tentativo con metodo tradizionale...")
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
