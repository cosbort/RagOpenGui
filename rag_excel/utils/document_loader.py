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

# Importa il loader Excel esistente
from .excel_loader import ExcelLoader

# Importa il logger configurato
from config import init_logging
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
                # Usa il loader Excel esistente
                excel_loader = ExcelLoader(self.file_path)
                self.content = excel_loader.load()
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
        
        if self.file_type == 'excel':
            # Usa il loader Excel esistente per i documenti
            excel_loader = ExcelLoader(self.file_path)
            return excel_loader.get_documents()
            
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