"""
Script per avviare facilmente il sistema RAG Excel.
"""
import os
import argparse
import logging
import uvicorn
from pathlib import Path

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Funzione principale per avviare il sistema RAG Excel.
    """
    parser = argparse.ArgumentParser(description="Avvia il sistema RAG Excel")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host su cui avviare il server")
    parser.add_argument("--port", type=int, default=8000, help="Porta su cui avviare il server")
    parser.add_argument("--generate-sample", action="store_true", help="Genera un file Excel di esempio")
    parser.add_argument("--reload", action="store_true", help="Abilita il reload automatico")
    
    args = parser.parse_args()
    
    # Genera il file Excel di esempio se richiesto
    if args.generate_sample:
        try:
            from utils.generate_sample_excel import main as generate_sample
            generate_sample()
        except Exception as e:
            logger.error(f"Errore durante la generazione del file Excel di esempio: {str(e)}")
            return
    
    # Avvia il server
    logger.info(f"Avvio del server su {args.host}:{args.port}")
    uvicorn.run(
        "app:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()