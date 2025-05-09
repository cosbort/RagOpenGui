"""
title: RAG Excel Query
author: open-webui
github: https://github.com/open-webui
funding_url: https://github.com/open-webui
version: 0.2
"""

import httpx
import json
import os
import sys
import traceback
import asyncio
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

# Configura il logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rag_excel_function.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("rag_excel_function")

# Configurazioni per il server RAG Excel
API_HOST = "localhost"  # Il tuo IP Wi-Fi
API_PORT = 8000         # Modifica se necessario
RAG_EXCEL_URL = f"http://{API_HOST}:{API_PORT}"

# Configurazione del client HTTP
HTTPX_TIMEOUT = 60.0
HTTPX_RETRIES = 5

# Aggiunto import helper (assumendo che sia nel path corretto di OpenWebUI)
try:
    from utils.pipelines.main import get_last_user_message
except (ImportError, ModuleNotFoundError):
    # Fallback o log se l'import non funziona nell'ambiente di test locale
    logger.warning("Could not import OpenWebUI utils.pipelines.main. Define dummy function.")
    def get_last_user_message(messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for message in reversed(messages):
            if message.get("role") == "user":
                return message
        return None

# Configurazioni definite localmente per evitare dipendenze esterne

class Filter:
    class QueryParams(BaseModel):
        query: str = Field(default="", description="La domanda sui dati Excel")
        pass

    def __init__(self):
        # Inizializzazione della classe
        self.name = "query_excel_data"
        self.description = "Interroga i dati Excel utilizzando il sistema RAG"
        logger.info(f"Inizializzazione del filtro RAG Excel con URL: {RAG_EXCEL_URL}")
        pass

    async def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        try:
            logger.info(f"Ricevuta richiesta: {body}")
            
            messages = body.get("messages", [])
            user_message = get_last_user_message(messages)
            
            if not user_message or not user_message.get("content"): 
                logger.warning("Nessun messaggio utente trovato o messaggio vuoto.")
                return body # Restituisce il body originale se non c'è query

            query = user_message["content"]
            logger.info(f"Query estratta per RAG: {query}")
            
            rag_context = ""
            try:
                # Crea un client HTTP con configurazione adeguata
                # Evita l'uso diretto di HTTPTransport con retries che può causare problemi
                limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
                async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT, limits=limits) as client:
                    # 1. Verifica stato server RAG
                    try:
                        status_response = await client.get(f"{RAG_EXCEL_URL}/status")
                        status_response.raise_for_status() # Solleva eccezione per status >= 400
                        status_data = status_response.json()
                    except Exception as e:
                        error_msg = f"Errore durante la verifica dello stato del server RAG: {str(e)}"
                        logger.error(error_msg)
                        # Potremmo aggiungere questo errore al body? Per ora logghiamo e continuiamo senza RAG.
                        return body 

                    # Verifica lo stato del server RAG (supporta sia il vecchio che il nuovo formato)
                    rag_ready = False
                    if "rag_status" in status_data:
                        # Nuovo formato dopo il refactoring
                        rag_ready = status_data.get("rag_status") == "inizializzato_e_pronto"
                    elif "status" in status_data:
                        # Vecchio formato prima del refactoring
                        rag_ready = status_data.get("status") == "ready"
                    
                    if not rag_ready:
                        logger.warning(f"Il server RAG Excel non è pronto. Stato: {status_data}. Salto RAG.")
                        return body

                    # 2. Invia query al server RAG
                    logger.info(f"Invio query '{query}' al server RAG: {RAG_EXCEL_URL}/query")
                    rag_response = await client.post(f"{RAG_EXCEL_URL}/query", json={"query": query})
                    
                    # 3. Elabora risposta RAG
                    if rag_response.status_code == 200:
                        try:
                            result = rag_response.json()
                            answer = result.get("answer", "Nessuna risposta dal RAG.")
                            sources = result.get("sources", [])
                            
                            formatted_sources = "Nessuna fonte specifica."
                            if sources:
                                formatted_sources = "\nFonti:\n" + "\n".join([
                                    f"- Foglio: {s.get('sheet_name', 'N/D')}, Riga: {s.get('row_number', 'N/D')}" 
                                    for s in sources
                                ])
                            
                            # Costruisci il contesto da aggiungere
                            rag_context = f"\n\n--- Contesto dai dati Excel (fornito dal sistema RAG) ---\nRisposta preliminare: {answer}{formatted_sources}\n--------------------------------------------------------\n\nDomanda originale: "
                            logger.info("Contesto RAG generato con successo.")

                        except Exception as e:
                            logger.error(f"Errore durante l'elaborazione della risposta RAG: {str(e)}")
                            # Continua senza contesto RAG
                            rag_context = "\n\n[Errore interno nell'elaborazione del contesto RAG]\n\nDomanda originale: "
                    else:
                        error_detail = "N/D"
                        try:
                            error_detail = rag_response.json().get("detail", "N/D")
                        except:
                            pass
                        logger.error(f"Errore dal server RAG ({rag_response.status_code}): {error_detail}. Salto RAG.")
                        # Continua senza contesto RAG
                        rag_context = "\n\n[Errore nella comunicazione con il sistema RAG]\n\nDomanda originale: "

            except Exception as e:
                logger.error(f"Errore generale durante il recupero del contesto RAG: {str(e)}")
                logger.error(traceback.format_exc())
                # Continua senza contesto RAG
                rag_context = "\n\n[Errore generale nel sistema RAG]\n\nDomanda originale: "
                
            # --- Fine Logica RAG ---

            # Modifica l'ultimo messaggio utente aggiungendo il contesto RAG
            if rag_context: # Solo se abbiamo generato un contesto (anche se è un errore)
                logger.info(f"Aggiungo contesto RAG al messaggio utente.")
                updated = False
                for message in reversed(messages):
                    if message.get("role") == "user":
                        original_content = message.get("content", "")
                        message["content"] = f"{rag_context}{original_content}" # Anteponi il contesto
                        updated = True
                        logger.debug(f"Messaggio utente aggiornato: {message['content']}")
                        break
                if not updated:
                     logger.warning("Non è stato possibile aggiornare il messaggio utente con il contesto RAG.")
            else:
                logger.info("Nessun contesto RAG da aggiungere.")
                
            # Aggiorna i messaggi nel body
            body["messages"] = messages
            
            logger.info("Restituisco il body modificato.")
            # Restituisce l'intero body modificato
            return body
        except Exception as e:
            logger.error(f"Errore imprevisto nel filtro inlet: {str(e)}")
            logger.error(traceback.format_exc())
            # Restituisci il body originale per non bloccare il flusso
            return body
        
    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        # Questo filtro viene applicato DOPO la risposta dell'LLM
        return body
