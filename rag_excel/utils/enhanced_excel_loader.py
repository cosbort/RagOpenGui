"""
Loader avanzato per file Excel complessi con supporto per strutture tabellari e semantiche.
Combina le migliori caratteristiche di pandas, unstructured e LlamaParse per un'analisi ottimale.
"""
import os
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import pandas as pd

from langchain.schema import Document
from langchain_community.document_loaders.excel import UnstructuredExcelLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Importa il logger configurato
from config import init_logging, CHUNK_SIZE, CHUNK_OVERLAP
logger = init_logging(__name__)

class EnhancedExcelLoader:
    """
    Loader avanzato per file Excel che combina più approcci per ottimizzare
    l'estrazione di informazioni da fogli Excel complessi.
    
    Caratteristiche:
    - Supporto per strutture tabellari complesse
    - Rilevamento di subtabelle e relazioni
    - Estrazione di metadati ricchi
    - Preservazione del contesto e della struttura
    - Supporto per formule e riferimenti incrociati
    """
    
    def __init__(self, file_path: str, use_unstructured: bool = True, chunk_size: int = None, chunk_overlap: int = None):
        """
        Inizializza il loader Excel avanzato.
        
        Args:
            file_path: Percorso al file Excel da caricare
            use_unstructured: Se True, utilizza la libreria unstructured per l'analisi avanzata
            chunk_size: Dimensione dei chunk per il text splitter (default da config)
            chunk_overlap: Sovrapposizione dei chunk (default da config)
        """
        self.file_path = file_path
        self.use_unstructured = use_unstructured
        self.chunk_size = chunk_size or CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or CHUNK_OVERLAP
        self.dataframes: Dict[str, pd.DataFrame] = {}
        
    def load_with_pandas(self) -> Dict[str, pd.DataFrame]:
        """
        Carica tutte le schede del file Excel in dataframes usando pandas.
        Utile per analisi strutturata e accesso programmatico ai dati.
        
        Returns:
            Dictionary con i dataframes per ogni scheda
        """
        try:
            logger.info(f"Caricamento del file Excel con pandas: {self.file_path}")
            
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
            logger.error(f"Errore durante il caricamento del file Excel con pandas: {str(e)}")
            raise
    
    def load_with_unstructured(self) -> List[Document]:
        """
        Carica il file Excel usando la libreria unstructured che offre
        un'analisi più sofisticata delle strutture tabellari.
        
        Returns:
            Lista di documenti LangChain
        """
        try:
            logger.info(f"Caricamento del file Excel con unstructured: {self.file_path}")
            
            # Utilizza UnstructuredExcelLoader in modalità "elements" per ottenere
            # una rappresentazione più granulare delle tabelle
            loader = UnstructuredExcelLoader(
                self.file_path,
                mode="elements",  # Estrae ogni foglio come elemento Table separato
                # Parametri avanzati per unstructured
                find_subtable=True,  # Rileva subtabelle all'interno dei fogli
                include_header=True,  # Includi le intestazioni delle tabelle
                infer_table_structure=True  # Preserva la struttura delle tabelle
            )
            
            documents = loader.load()
            logger.info(f"Caricati {len(documents)} elementi dal file Excel con unstructured")
            
            # Arricchisci i metadati
            enhanced_docs = []
            for doc in documents:
                # Estrai informazioni aggiuntive dai metadati esistenti
                sheet_name = doc.metadata.get("page_name", "Unknown")
                
                # Arricchisci i metadati con informazioni utili per il retrieval
                enhanced_metadata = {
                    **doc.metadata,
                    "source": self.file_path,
                    "document_type": "excel",
                    "sheet_name": sheet_name,
                    "content_type": "table" if "text_as_html" in doc.metadata else "text",
                    "parser": "unstructured"
                }
                
                # Crea un nuovo documento con metadati arricchiti
                enhanced_doc = Document(
                    page_content=doc.page_content,
                    metadata=enhanced_metadata
                )
                enhanced_docs.append(enhanced_doc)
            
            return enhanced_docs
            
        except Exception as e:
            logger.error(f"Errore durante il caricamento del file Excel con unstructured: {str(e)}")
            # Fallback a pandas in caso di errore
            logger.info("Fallback al caricamento con pandas")
            return self.get_documents_from_pandas()
    
    def get_documents_from_pandas(self) -> List[Document]:
        """
        Converte i dataframes pandas in documenti LangChain.
        Utilizzato come fallback o quando use_unstructured=False.
        
        Returns:
            Lista di documenti LangChain
        """
        documents = []
        
        # Se i dataframes non sono stati caricati, caricali
        if not self.dataframes:
            self.load_with_pandas()
        
        for sheet_name, df in self.dataframes.items():
            logger.info(f"Conversione della scheda {sheet_name} in documento")
            
            # Gestione DataFrame vuoto
            if df.empty:
                logger.warning(f"La scheda {sheet_name} è vuota. Salto la creazione del documento.")
                continue
                
            try:
                # Estrai statistiche utili dal DataFrame
                num_rows, num_cols = df.shape
                has_numeric = any(pd.api.types.is_numeric_dtype(df[col]) for col in df.columns)
                has_dates = any(pd.api.types.is_datetime64_dtype(df[col]) for col in df.columns)
                
                # Identifica possibili colonne chiave (prime colonne o colonne con valori unici)
                key_columns = []
                for col in df.columns[:3]:  # Prime 3 colonne come potenziali chiavi
                    if df[col].nunique() > 0.5 * len(df):  # Più del 50% di valori unici
                        key_columns.append(col)
                
                # Converti l'intero DataFrame in una stringa Markdown
                markdown_content = df.to_markdown(index=True)
                
                # Aggiungi un titolo per chiarezza
                page_content = f"# Scheda: {sheet_name}\n\n{markdown_content}"
                
                # Crea il documento con metadati arricchiti
                document = Document(
                    page_content=page_content,
                    metadata={
                        "source": self.file_path,
                        "sheet_name": sheet_name,
                        "num_rows": num_rows,
                        "num_columns": num_cols,
                        "column_headers": list(df.columns),
                        "key_columns": key_columns,
                        "has_numeric_data": has_numeric,
                        "has_date_data": has_dates,
                        "document_type": "excel",
                        "content_type": "table",
                        "parser": "pandas"
                    }
                )
                documents.append(document)
                
            except Exception as e:
                logger.error(f"Errore durante la conversione della scheda {sheet_name}: {str(e)}")
                continue
        
        logger.info(f"Creati {len(documents)} documenti dal file Excel con pandas")
        return documents
    
    def get_documents(self) -> List[Document]:
        """
        Ottiene i documenti dal file Excel utilizzando il metodo più appropriato
        in base alla configurazione.
        
        Returns:
            Lista di documenti LangChain
        """
        if self.use_unstructured:
            try:
                return self.load_with_unstructured()
            except Exception as e:
                logger.error(f"Errore con unstructured, fallback a pandas: {str(e)}")
                return self.get_documents_from_pandas()
        else:
            return self.get_documents_from_pandas()
    
    def get_chunked_documents(self) -> List[Document]:
        """
        Ottiene i documenti dal file Excel e li suddivide in chunk ottimizzati
        per la vettorizzazione, preservando il contesto e la struttura.
        
        Returns:
            Lista di documenti LangChain suddivisi in chunk
        """
        # Ottieni i documenti
        documents = self.get_documents()
        
        # Configura il text splitter ottimizzato per Excel
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["# ", "##", "###", "\n\n", "\n", "\t", "|", ",", ";", " ", ""],
            keep_separator=True,
            add_start_index=True
        )
        
        # Applica il chunking solo ai documenti più grandi della dimensione del chunk
        chunked_documents = []
        for doc in documents:
            # Se il documento è piccolo, mantienilo intatto
            if len(doc.page_content) <= self.chunk_size * 2:
                chunked_documents.append(doc)
                continue
                
            # Altrimenti, dividi in chunk preservando i metadati
            chunks = text_splitter.split_text(doc.page_content)
            for i, chunk_text in enumerate(chunks):
                # Crea un nuovo documento per ogni chunk con metadati arricchiti
                chunk_doc = Document(
                    page_content=chunk_text,
                    metadata={
                        **doc.metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "is_chunked": True
                    }
                )
                chunked_documents.append(chunk_doc)
        
        logger.info(f"Creati {len(chunked_documents)} chunk dai {len(documents)} documenti originali")
        return chunked_documents