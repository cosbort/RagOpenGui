import httpx
import json
from typing import Dict, Any, Optional

class QueryExcelData:
    """
    Funzione per interrogare i dati Excel utilizzando il sistema RAG.
    """
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """
        Inizializza la funzione con l'URL dell'API RAG Excel.
        
        Args:
            api_url: URL dell'API RAG Excel
        """
        self.api_url = api_url
    
    def inlet(self, query: str) -> Dict[str, Any]:
        """
        Metodo di ingresso per la funzione.
        
        Args:
            query: Query da inviare al sistema RAG
            
        Returns:
            Risposta dal sistema RAG
        """
        try:
            # Verifica lo stato del server
            with httpx.Client(timeout=10.0) as client:
                status_response = client.get(f"{self.api_url}/status")
                status_data = status_response.json()
                
                if status_data.get("status") != "ready":
                    # Se non c'è il nuovo campo, fallback a rag_status
                    rag_state = status_data.get("rag_status", "unknown")
                    if rag_state != "inizializzato_e_pronto":
                        return {
                            "result": f"Il sistema RAG non è pronto. Stato attuale: {rag_state}",
                            "sources": []
                        }
                
                # Invia la query al server
                query_response = client.post(
                    f"{self.api_url}/query",
                    json={"query": query}
                )
                
                if query_response.status_code != 200:
                    return {
                        "result": f"Errore durante l'invio della query: {query_response.text}",
                        "sources": []
                    }
                
                # Estrai la risposta
                response_data = query_response.json()
                answer = response_data.get("answer", "")
                sources = response_data.get("sources", [])
                
                # Formatta le fonti
                formatted_sources = []
                for source in sources:
                    content = source.get("content", "")
                    metadata = source.get("metadata", {})
                    formatted_source = f"Foglio: {metadata.get('sheet_name', 'N/A')}, "
                    formatted_source += f"Riga: {metadata.get('row', 'N/A')}, "
                    formatted_source += f"Colonna: {metadata.get('column', 'N/A')}\n"
                    formatted_source += f"Contenuto: {content}"
                    formatted_sources.append(formatted_source)
                
                return {
                    "result": answer,
                    "sources": formatted_sources
                }
                
        except Exception as e:
            return {
                "result": f"Si è verificato un errore durante l'elaborazione della query: {str(e)}",
                "sources": []
            }

# Istanza della funzione per OpenWebUI
query_excel_data = QueryExcelData()

# Metodo di ingresso per OpenWebUI
def inlet(query: str) -> Dict[str, Any]:
    """
    Metodo di ingresso per OpenWebUI.
    
    Args:
        query: Query da inviare al sistema RAG
        
    Returns:
        Risposta dal sistema RAG
    """
    return query_excel_data.inlet(query)
