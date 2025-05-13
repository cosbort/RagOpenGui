"""
Utility per caricare e processare file Excel.
"""
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

# Importa il logger configurato
from config import init_logging
logger = init_logging(__name__)

class ExcelLoader:
    """
    Classe per caricare e processare file Excel per RAG.
    """
    
    def __init__(self, file_path: str):
        """
        Inizializza il loader Excel.
        
        Args:
            file_path: Percorso al file Excel da caricare
        """
        self.file_path = file_path
        self.dataframes: Dict[str, pd.DataFrame] = {}
        
    def load(self) -> Dict[str, pd.DataFrame]:
        """
        Carica tutte le schede del file Excel in dataframes.
        
        Returns:
            Dictionary con i dataframes per ogni scheda
        """
        try:
            logger.info(f"Caricamento del file Excel: {self.file_path}")
            
            # Verifica che il file esista
            if not Path(self.file_path).exists():
                raise FileNotFoundError(f"Il file Excel non esiste: {self.file_path}")
            
            # Carica tutte le schede in un dizionario di dataframes
            excel_file = pd.ExcelFile(self.file_path)
            
            for sheet_name in excel_file.sheet_names:
                logger.info(f"Caricamento della scheda: {sheet_name}")
                self.dataframes[sheet_name] = pd.read_excel(excel_file, sheet_name=sheet_name)
                
            logger.info(f"Caricate {len(self.dataframes)} schede dal file Excel")
            return self.dataframes
            
        except Exception as e:
            logger.error(f"Errore durante il caricamento del file Excel: {str(e)}")
            raise
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """
        Converte i dataframes in documenti per il RAG, 
        utilizzando una rappresentazione Markdown per ogni foglio.

        Returns:
            Lista di documenti (uno per foglio) con metadati.
        """
        documents = []

        # Se i dataframes non sono stati caricati, caricali
        if not self.dataframes:
            self.load()

        for sheet_name, df in self.dataframes.items():
            logger.info(f"Conversione della scheda {sheet_name} in documento Markdown")

            # Gestione DataFrame vuoto
            if df.empty:
                logger.warning(f"La scheda {sheet_name} è vuota. Salto la creazione del documento.")
                continue
                
            try:
                # Converte l'intero DataFrame in una stringa Markdown
                # Includiamo l'indice (index=True) per mostrare i numeri di riga
                # Questo è utile per riferirsi a righe specifiche nei dati
                markdown_content = df.to_markdown(index=True) 
                
                # Aggiungi un titolo per chiarezza
                page_content = f"# Scheda: {sheet_name}\n\n{markdown_content}"

                # Crea il documento con metadati essenziali
                document = {
                    "page_content": page_content,
                    "metadata": {
                        "source": self.file_path,
                        "sheet_name": sheet_name,
                        "num_rows": len(df),
                        "column_headers": list(df.columns) 
                        # Aggiungi altri metadati se utili, es. un riassunto,
                        # ma evita di includere TUTTI i dati qui.
                    }
                }
                documents.append(document)
                
            except Exception as e:
                logger.error(f"Errore durante la conversione della scheda {sheet_name} in Markdown: {str(e)}")
                # Si potrebbe decidere di continuare con altri fogli (continue) 
                # o fermarsi qui (raise e) a seconda della robustezza desiderata.
                # Al momento, logga l'errore e continua.
                continue 
        
        logger.info(f"Creati {len(documents)} documenti (uno per foglio) dal file Excel")
        return documents
    
    def get_sheet_names(self) -> List[str]:
        """
        Restituisce i nomi delle schede nel file Excel.
        
        Returns:
            Lista dei nomi delle schede
        """
        if not self.dataframes:
            self.load()
        
        return list(self.dataframes.keys())
    
    def get_sheet(self, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        Restituisce un dataframe specifico per nome.
        
        Args:
            sheet_name: Nome della scheda da restituire
            
        Returns:
            Dataframe della scheda richiesta o None se non esiste
        """
        if not self.dataframes:
            self.load()
            
        return self.dataframes.get(sheet_name)