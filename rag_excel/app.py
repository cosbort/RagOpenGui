"""
Applicazione principale per il sistema RAG Excel.
"""
import os
import logging
import uvicorn
import json
import math
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from pathlib import Path
import shutil
import time
from typing import Any, Dict, List

# Import configurazione e utility centralizzate
from config import (
    init_logging,
    API_HOST,
    API_PORT,
    VECTOR_STORE_PATH,
    EXCEL_FILE_PATH # Necessario per la logica di riparazione potenziale
)
from utils.rag_chain import RagChain
from utils.vector_utils import ensure_vector_store_path, clean_vector_store
# Importa anche ExcelLoader e VectorStoreManager se decidi di 
# implementare la logica di creazione automatica qui invece che 
# affidarti solo allo script repair_rag_system.py
# from utils.excel_loader import ExcelLoader
# from utils.vector_store import VectorStoreManager 

# Inizializza il logger
logger = init_logging(__name__)

# Rimosso: Configurazione logger locale

# Variabile globale per la catena RAG
rag_chain_instance: RagChain = None

# Definisci il modello Pydantic per la richiesta
class QueryRequest(BaseModel):
    query: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestisce l'inizializzazione e la pulizia all'avvio e allo spegnimento."""
    global rag_chain_instance
    logger.info("Avvio dell'applicazione RAG Excel...")
    
    # Assicura che la directory del vector store esista (usando l'utility)
    ensure_vector_store_path(VECTOR_STORE_PATH)
    logger.info(f"Directory Vector Store assicurata: {VECTOR_STORE_PATH}")

    # Inizializza la catena RAG
    logger.info("Inizializzazione dell'istanza RagChain...")
    rag_chain_instance = RagChain(vector_store_path=VECTOR_STORE_PATH)
    
    # Tenta l'inizializzazione (caricamento del vector store)
    if not rag_chain_instance.initialize():
        logger.error("Inizializzazione di RagChain fallita all'avvio.")
        logger.warning("Il server partirà, ma le query falliranno finché il vector store non sarà disponibile.")
        logger.warning(f"Esegui lo script 'repair_rag_system.py --create' per creare il vector store da '{EXCEL_FILE_PATH}'.")
        # Decisione: non bloccare l'avvio, ma loggare l'errore. Le richieste falliranno con un messaggio appropriato.
        # Potresti aggiungere una logica di fallback qui se lo desideri, 
        # ma è più pulito gestirlo separatamente con lo script di riparazione.
        # Esempio di logica di fallback (commentata):
        # logger.warning("Tentativo di creazione automatica del vector store...")
        # try:
        #     excel_loader = ExcelLoader(EXCEL_FILE_PATH)
        #     docs = excel_loader.load_documents()
        #     if docs:
        #         vs_manager = VectorStoreManager(VECTOR_STORE_PATH)
        #         vs_manager.create_or_update(docs)
        #         logger.info("Vector store creato automaticamente. Tentativo di ri-inizializzazione...")
        #         if not rag_chain_instance.initialize():
        #             logger.error("Ri-inizializzazione fallita anche dopo la creazione automatica.")
        #     else:
        #         logger.error("Impossibile caricare documenti per la creazione automatica.")
        # except Exception as e:
        #     logger.error(f"Errore durante la creazione automatica: {e}")
    else:
        logger.info("RagChain inizializzata con successo.")
        
    yield
    
    # Logica di pulizia allo spegnimento (se necessaria)
    logger.info("Spegnimento dell'applicazione RAG Excel...")

# Crea l'applicazione FastAPI con il lifespan manager
app = FastAPI(lifespan=lifespan)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/query")
async def query_rag(request: Request, data: QueryRequest):
    """Endpoint per interrogare il sistema RAG."""
    global rag_chain_instance
    query = data.query
    logger.info(f"Ricevuta richiesta query dall'IP: {request.client.host} - Query: '{query}'")
    
    if rag_chain_instance is None or rag_chain_instance.qa_chain is None:
        logger.error("Tentativo di query su RagChain non inizializzata.")
        raise HTTPException(
            status_code=503, # Service Unavailable
            detail="Il sistema RAG non è pronto. Potrebbe essere necessario creare il vector store."
        )
        
    try:
        start_time = time.time()
        result = rag_chain_instance.answer_question(query)
        end_time = time.time()
        processing_time = end_time - start_time
        logger.info(f"Query elaborata in {processing_time:.2f} secondi.")
        
        # Verifica se la risposta indica un errore interno di RAG (es. non inizializzato)
        if "Errore:" in result.get("answer", ""):
             logger.error(f"Errore restituito da answer_question: {result['answer']}")
             # Potresti voler mappare questo a un errore HTTP specifico
             raise HTTPException(
                 status_code=500, 
                 detail=f"Errore interno del sistema RAG: {result['answer']}"
             )

        # Pulisci i valori NaN, infiniti o non serializzabili in JSON
        clean_result = clean_for_json(result)
        
        logger.info(f"Risposta inviata: {clean_result['answer'][:100]}... (Fonti: {len(clean_result['sources'])})")        
        return clean_result
        
    except HTTPException as http_exc:
        # Ri-lancia le eccezioni HTTP per mantenere lo status code corretto
        raise http_exc
    except Exception as e:
        logger.error(f"Errore imprevisto durante l'elaborazione della query '{query}': {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Errore interno del server durante l'elaborazione della richiesta: {str(e)}"
        )

@app.get("/status")
async def get_status():
    """Endpoint per verificare lo stato del server e del sistema RAG."""
    global rag_chain_instance
    status = {
        "server_status": "online",
        "rag_status": "non_inizializzato",
        "vector_store_path": str(VECTOR_STORE_PATH), 
        "vector_store_exists": False,
        "excel_file_path": str(EXCEL_FILE_PATH),
        "excel_file_exists": Path(EXCEL_FILE_PATH).exists()
    }
    
    # Verifica esistenza vector store
    vs_path = Path(VECTOR_STORE_PATH)
    index_file = vs_path / "index.faiss"
    pkl_file = vs_path / "index.pkl"
    status["vector_store_exists"] = index_file.exists() and pkl_file.exists()
    
    if rag_chain_instance and rag_chain_instance.qa_chain:
        status["rag_status"] = "inizializzato_e_pronto"
    elif status["vector_store_exists"]:
         status["rag_status"] = "vector_store_presente_ma_rag_non_inizializzato"
    else:
        status["rag_status"] = "vector_store_non_trovato"
        
    # Aggiungi un campo di compatibilità per OpenWebUI
    # "status" sarà "ready" solo quando il sistema è effettivamente inizializzato e pronto.
    status["status"] = "ready" if status["rag_status"] == "inizializzato_e_pronto" else "not_ready"
    
    logger.info(f"Richiesta stato: {status}")
    return status

def clean_for_json(obj: Any) -> Any:
    """Pulisce un oggetto per renderlo serializzabile in JSON.
    Sostituisce NaN, infiniti e altri valori problematici."""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, (np.ndarray, np.generic)):
        # Converti array numpy in liste
        return clean_for_json(obj.tolist())
    elif isinstance(obj, (int, str, bool)) or obj is None:
        return obj
    elif isinstance(obj, float):
        # Sostituisci NaN e infiniti con None
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        # Tenta di convertire altri tipi in stringhe
        try:
            return str(obj)
        except:
            return None

# Aggiungi qui eventuali altri endpoint, come /clean o /create se vuoi 
# esporre queste funzionalità via API (sconsigliato per operazioni lunghe/distruttive)
# Esempio:
# @app.post("/admin/clean-vector-store")
# async def clean_vs():
#     logger.warning("Richiesta API per pulire il vector store...")
#     if clean_vector_store(VECTOR_STORE_PATH):
#         # Potrebbe essere necessario ri-inizializzare RagChain qui o riavviare
#         global rag_chain_instance
#         rag_chain_instance = None # Forza reinizializzazione al prossimo avvio/richiesta?
#         logger.info("Pulizia del vector store completata via API.")
#         return {"message": "Vector store pulito con successo. Riavviare l'applicazione per reinizializzare."}
#     else:
#         raise HTTPException(status_code=500, detail="Errore durante la pulizia del vector store.")

if __name__ == "__main__":
    logger.info(f"Avvio del server FastAPI su {API_HOST}:{API_PORT}")
    # Usa le costanti importate da config
    uvicorn.run(app, host=API_HOST, port=API_PORT)