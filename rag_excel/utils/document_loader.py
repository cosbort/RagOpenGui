"""
Utility per caricare e processare diversi tipi di documenti.
Supporta: EXCEL, WORD, PDF, CSV, JSON, XML
"""
import os
import pandas as pd
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# Importazioni specifiche per tipo di file
import docx  # python-docx per file Word
import PyPDF2  # PyPDF2 per file PDF

# Importa il loader Excel esistente (lo useremo ancora come fallback o per altri scopi se necessario)
from .excel_loader import ExcelLoader

# Importa LlamaParse e la configurazione
from llama_parse import LlamaParse
from config import LLAMA_CLOUD_API_KEY, init_logging # Assicurati che LLAMA_CLOUD_API_KEY sia in config

# Importa il logger configurato
logger = init_logging(__name__)

class DocumentLoader:
    """
    Classe per caricare e processare diversi tipi di documenti per RAG.
    Supporta: EXCEL, WORD, PDF, CSV, JSON, XML
    """
    
    def __init__(self, file_path: str):
        """
        Inizializza il loader di documenti.
        
        Args:
            file_path: Percorso al file da caricare
        """
        self.file_path = file_path
        self.file_type = self._detect_file_type()
        self.content = None
        self.documents = []
        self.parsing_instructions_excel = "Questa è una tabella di dati. Estrai il contenuto in formato markdown, preservando la struttura della tabella."
        
    def _detect_file_type(self) -> str:
        """
        Rileva il tipo di file in base all'estensione.
        
        Returns:
            Tipo di file (excel, word, pdf, csv, json, xml)
        """
        ext = Path(self.file_path).suffix.lower()
        if ext in ['.xlsx', '.xls']:
            return 'excel'
        elif ext in ['.docx', '.doc']:
            return 'word'
        elif ext == '.pdf':
            return 'pdf'
        elif ext == '.csv':
            return 'csv'
        elif ext == '.json':
            return 'json'
        elif ext in ['.xml', '.html']:
            return 'xml'
        else:
            raise ValueError(f"Tipo di file non supportato: {ext}")
    
    def load(self) -> Any:
        """
        Carica il documento in base al tipo di file.
        
        Returns:
            Contenuto del documento nel formato appropriato
        """
        logger.info(f"Caricamento del file {self.file_type}: {self.file_path}")
        
        # Verifica che il file esista
        if not Path(self.file_path).exists():
            raise FileNotFoundError(f"Il file non esiste: {self.file_path}")
        
        try:
            if self.file_type == 'excel':
                if LLAMA_CLOUD_API_KEY:
                    logger.info(f"Utilizzo di LlamaParse per il file Excel: {self.file_path}")
                    # Inizializza LlamaParse
                    try:
                        # Importa la regione dalla configurazione
                        from config import LLAMA_CLOUD_REGION
                        
                        logger.info(f"Inizializzazione LlamaParse con regione: {LLAMA_CLOUD_REGION}...")
                        parser = LlamaParse(
                            api_key=LLAMA_CLOUD_API_KEY,
                            result_type="markdown",  # Richiede l'output in formato Markdown
                            verbose=True,
                            region=LLAMA_CLOUD_REGION,  # Specifica la regione (us, eu, ap)
                            base_url=f"https://api.cloud.{LLAMA_CLOUD_REGION}.llamaindex.ai",  # URL base specifico per la regione
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
                        
                        # Carica e parsa il file
                        logger.info(f"Parsing del file Excel con LlamaParse: {self.file_path}")
                        llama_documents = parser.load_data(self.file_path)
                        
                        # Verifica che llama_documents non sia None e contenga effettivamente documenti
                        if llama_documents and len(llama_documents) > 0:
                            self.content = llama_documents # Salviamo i documenti parsati
                            logger.info(f"File Excel parsato con successo usando LlamaParse: {len(llama_documents)} documenti generati")
                        else:
                            # Se non ci sono documenti, considera questo come un errore
                            raise ValueError("Nessun documento generato da LlamaParse")
                            
                    except Exception as e:
                        logger.error(f"Errore durante il parsing con LlamaParse: {str(e)}")
                        logger.warning("Fallback al loader Excel tradizionale dopo errore di parsing.")
                        excel_loader = ExcelLoader(self.file_path)
                        self.content = excel_loader.load()
                else:
                    logger.warning("LLAMA_CLOUD_API_KEY non configurata. Fallback al loader Excel tradizionale.")
                    excel_loader = ExcelLoader(self.file_path)
                    self.content = excel_loader.load() # self.content sarà un dict di DataFrame
            elif self.file_type == 'word':
                self.content = self._load_word()
            elif self.file_type == 'pdf':
                self.content = self._load_pdf()
            elif self.file_type == 'csv':
                self.content = self._load_csv()
            elif self.file_type == 'json':
                self.content = self._load_json()
            elif self.file_type == 'xml':
                self.content = self._load_xml()
            
            logger.info(f"File {self.file_type} caricato con successo")
            return self.content
            
        except Exception as e:
            logger.error(f"Errore durante il caricamento del file {self.file_type}: {str(e)}")
            raise
    
    def _load_word(self) -> Dict[str, str]:
        """
        Carica un documento Word.
        
        Returns:
            Dizionario con il testo del documento
        """
        doc = docx.Document(self.file_path)
        content = {"text": "\n".join([para.text for para in doc.paragraphs if para.text])}
        return content
    
    def _load_pdf(self) -> Dict[str, List[str]]:
        """
        Carica un documento PDF.
        
        Returns:
            Dizionario con il testo di ogni pagina
        """
        content = {"pages": []}
        with open(self.file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                content["pages"].append(page.extract_text())
        return content
    
    def _load_csv(self) -> Dict[str, pd.DataFrame]:
        """
        Carica un file CSV.
        
        Returns:
            Dizionario con il dataframe
        """
        df = pd.read_csv(self.file_path)
        return {"main": df}
    
    def _load_json(self) -> Dict[str, Any]:
        """
        Carica un file JSON.
        
        Returns:
            Dizionario con il contenuto JSON
        """
        with open(self.file_path, 'r', encoding='utf-8') as file:
            content = json.load(file)
        return {"content": content}
    
    def _load_xml(self) -> Dict[str, str]:
        """
        Carica un file XML/HTML.
        
        Returns:
            Dizionario con il contenuto XML/HTML come testo
        """
        with open(self.file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Usa BeautifulSoup per una migliore gestione di XML/HTML
        soup = BeautifulSoup(content, 'lxml')
        return {"text": soup.get_text()}
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """
        Converte il contenuto caricato in documenti per il RAG.
        
        Returns:
            Lista di documenti con metadati
        """
        # Se il contenuto non è stato caricato, caricalo
        if self.content is None:
            self.load()
        
        documents = []
        
        logger.info(f"Conversione del file {self.file_type} in documenti RAG...")

        if self.file_type == 'excel':
            if isinstance(self.content, list) and len(self.content) > 0 and hasattr(self.content[0], 'get_content'): # Verifica se è output di LlamaParse
                logger.info("Conversione dei documenti LlamaParse in formato RAG.")
                for llama_doc in self.content: # self.content qui è la lista di LlamaIndex Documents
                    # Estrai metadati rilevanti da llama_doc.metadata se necessario
                    # e aggiungili ai tuoi metadati standard
                    doc_metadata = {
                        "source": self.file_path,
                        "document_type": "excel_llamaparse",
                        # Aggiungi altri metadati da llama_doc.metadata se utili
                        **(llama_doc.metadata or {}) 
                    }
                    documents.append({
                        "page_content": llama_doc.get_content(), # Il contenuto Markdown della tabella/sezione
                        "metadata": doc_metadata
                    })
            else: # Fallback al vecchio metodo se LlamaParse non è stato usato
                logger.info("Conversione dei DataFrame Excel (metodo tradizionale) in formato RAG.")
                # Crea un nuovo ExcelLoader e carica il file da zero
                excel_loader = ExcelLoader(self.file_path)
                # Non assegnare self.content a dataframes, ma lascia che ExcelLoader carichi il file
                try:
                    documents.extend(excel_loader.get_documents())
                except Exception as e:
                    logger.error(f"Errore durante la conversione del file Excel: {str(e)}")
                    # Aggiungi un documento di errore per informare l'utente
                    documents.append({
                        "page_content": f"Errore durante il caricamento del file Excel: {str(e)}",
                        "metadata": {
                            "source": self.file_path,
                            "document_type": "error",
                            "error": str(e)
                        }
                    })
            
        elif self.file_type == 'word':
            text = self.content.get("text", "")
            # Dividi il testo in paragrafi
            paragraphs = [p for p in text.split("\n") if p.strip()]
            
            for idx, paragraph in enumerate(paragraphs):
                document = {
                    "page_content": paragraph,
                    "metadata": {
                        "source": self.file_path,
                        "document_type": "word",
                        "paragraph_number": idx+1
                    }
                }
                documents.append(document)
                
        elif self.file_type == 'pdf':
            pages = self.content.get("pages", [])
            
            for idx, page_text in enumerate(pages):
                document = {
                    "page_content": page_text,
                    "metadata": {
                        "source": self.file_path,
                        "document_type": "pdf",
                        "page_number": idx+1
                    }
                }
                documents.append(document)
                
        elif self.file_type == 'csv':
            df = self.content.get("main")
            
            # Converti le colonne non stringa in stringhe
            for col in df.columns:
                if df[col].dtype != 'object':
                    df[col] = df[col].astype(str)
            
            # Crea un documento per ogni riga
            for idx, row in df.iterrows():
                # Crea un testo rappresentativo della riga
                row_text = f"Riga: {idx+1}\n"
                
                # Aggiungi ogni colonna e valore
                for col, value in row.items():
                    row_text += f"{col}: {value}\n"
                
                # Crea il documento con metadati
                document = {
                    "page_content": row_text,
                    "metadata": {
                        "source": self.file_path,
                        "document_type": "csv",
                        "row_number": idx+1,
                        **{col: value for col, value in row.items()}
                    }
                }
                documents.append(document)
                
        elif self.file_type == 'json':
            content = self.content.get("content")
            
            # Converti il JSON in testo
            json_text = json.dumps(content, indent=2)
            
            # Crea un documento per il JSON completo
            document = {
                "page_content": json_text,
                "metadata": {
                    "source": self.file_path,
                    "document_type": "json"
                }
            }
            documents.append(document)
            
            # Se il JSON è una lista di oggetti, crea un documento per ogni oggetto
            if isinstance(content, list):
                for idx, item in enumerate(content):
                    item_text = json.dumps(item, indent=2)
                    document = {
                        "page_content": item_text,
                        "metadata": {
                            "source": self.file_path,
                            "document_type": "json",
                            "item_number": idx+1
                        }
                    }
                    documents.append(document)
                    
        elif self.file_type == 'xml':
            text = self.content.get("text", "")
            
            # Crea un documento per il testo completo
            document = {
                "page_content": text,
                "metadata": {
                    "source": self.file_path,
                    "document_type": "xml"
                }
            }
            documents.append(document)
            
        logger.info(f"Creati {len(documents)} documenti dal file {self.file_type}")
        return documents