"""
Script per riparare il sistema RAG e avviare il server.
"""

import os
import sys
import subprocess
import logging

# Configura il logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Funzione principale."""
    logger.info("Avvio dello script di riparazione e avvio del server")
    
    # Esegui lo script di riparazione
    logger.info("Esecuzione dello script di riparazione...")
    repair_result = subprocess.run([sys.executable, "repair_rag_system.py"], capture_output=True, text=True)
    
    if repair_result.returncode != 0:
        logger.error(f"Errore durante l'esecuzione dello script di riparazione: {repair_result.stderr}")
        print("Errore durante la riparazione del sistema RAG. Controlla i log per maggiori dettagli.")
        return False
    
    logger.info("Script di riparazione eseguito con successo")
    print(repair_result.stdout)
    
    # Avvia il server
    logger.info("Avvio del server...")
    server_process = subprocess.Popen([sys.executable, "app.py"])
    
    logger.info(f"Server avviato con PID: {server_process.pid}")
    print(f"Server avviato con PID: {server_process.pid}")
    print("Il server è in esecuzione su http://localhost:8000")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
