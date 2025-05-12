"""
Interfaccia grafica per il sistema RAG con supporto per diversi tipi di documenti.
Permette di visualizzare i documenti indicizzati e vettorizzati.
"""
import os
import sys
import time
import json
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile
import shutil
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

# Aggiungi il percorso base del progetto
sys.path.append(str(Path(__file__).resolve().parent))

# Importa configurazione e utility
from config import (
    init_logging,
    VECTOR_STORE_PATH,
    EXCEL_FILE_PATH,
    OPENAI_API_KEY,
    EMBEDDING_MODEL
)
from langchain_openai import OpenAIEmbeddings
from utils.document_loader import DocumentLoader
from utils.vector_store import VectorStoreManager
from utils.excel_loader import ExcelLoader
from utils.vector_utils import ensure_vector_store_path, clean_vector_store

# Inizializza il logger
logger = init_logging(__name__)

# Configurazione pagina Streamlit
st.set_page_config(
    page_title="RAG Document Visualizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Funzioni di utilità
def load_vector_store(vector_store_path: str) -> Optional[VectorStoreManager]:
    """Carica il vector store esistente."""
    try:
        vs_manager = VectorStoreManager(vector_store_path)
        if vs_manager.load():
            return vs_manager
        return None
    except Exception as e:
        st.error(f"Errore durante il caricamento del vector store: {str(e)}")
        return None

def process_document(file_path: str, temp_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Processa un documento e restituisce i documenti generati."""
    try:
        # Se è un file temporaneo, copia in una posizione accessibile
        if temp_dir and not os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            new_path = os.path.join(temp_dir, file_name)
            shutil.copy2(file_path, new_path)
            file_path = new_path
            
        loader = DocumentLoader(file_path)
        documents = loader.get_documents()
        return documents
    except Exception as e:
        st.error(f"Errore durante il processamento del documento: {str(e)}")
        return []

def create_or_update_vector_store(documents: List[Dict[str, Any]], vector_store_path: str) -> bool:
    """Crea o aggiorna il vector store con i documenti forniti."""
    try:
        vs_manager = VectorStoreManager(vector_store_path)
        vs_manager.create_or_update(documents)
        return True
    except Exception as e:
        st.error(f"Errore durante la creazione/aggiornamento del vector store: {str(e)}")
        return False

def extract_embeddings_from_vector_store(vs_manager: VectorStoreManager) -> Dict[str, Any]:
    """Estrae gli embeddings dal vector store per la visualizzazione."""
    try:
        # Accedi direttamente al vector store FAISS
        if vs_manager.vector_store is None:
            return {"success": False, "error": "Vector store non inizializzato"}
        
        # Ottieni i documenti dal docstore
        documents = list(vs_manager.vector_store.docstore._dict.values())
        if not documents:
            return {"success": False, "error": "Nessun documento trovato nel vector store"}
        
        st.info(f"Trovati {len(documents)} documenti nel vector store")
        
        # Crea gli embeddings per ogni documento
        embeddings = []
        document_contents = []
        document_metadata = []
        
        # Usa l'embedding model per generare gli embeddings
        embedder = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY
        )
        
        # Limita il numero di documenti per evitare troppe chiamate API
        max_docs = min(len(documents), 100)  # Limita a 100 documenti
        
        with st.spinner(f"Generazione embeddings per {max_docs} documenti..."):
            for i, doc in enumerate(documents[:max_docs]):
                try:
                    # Genera l'embedding per questo documento
                    embedding = embedder.embed_query(doc.page_content[:8000])  # Limita a 8000 caratteri
                    embeddings.append(embedding)
                    document_contents.append(doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content)
                    document_metadata.append(doc.metadata)
                except Exception as e:
                    st.warning(f"Errore durante la generazione dell'embedding per il documento {i}: {str(e)}")
        
        if not embeddings:
            return {"success": False, "error": "Nessun embedding generato"}
        
        return {
            "success": True,
            "embeddings": np.array(embeddings),
            "document_contents": document_contents,
            "document_metadata": document_metadata,
            "count": len(embeddings)
        }
    except Exception as e:
        st.error(f"Errore durante l'estrazione degli embeddings: {str(e)}")
        return {"success": False, "error": str(e)}

def reduce_dimensions(embeddings: np.ndarray, method: str = "pca") -> np.ndarray:
    """Riduce le dimensioni degli embeddings per la visualizzazione."""
    # Verifica se l'array è vuoto o non ha abbastanza campioni
    if embeddings.shape[0] == 0:
        st.error("Nessun embedding trovato per la riduzione dimensionale.")
        # Restituisci un array vuoto con 2 dimensioni
        return np.array([]).reshape(0, 2)
    
    # Se c'è un solo campione, non possiamo applicare PCA o t-SNE
    # quindi restituiamo il punto con coordinate arbitrarie
    if embeddings.shape[0] == 1:
        st.warning("Un solo embedding trovato. La visualizzazione potrebbe non essere significativa.")
        return np.array([[0.0, 0.0]])
    
    try:
        if method == "pca":
            reducer = PCA(n_components=2)
        else:  # t-SNE
            reducer = TSNE(n_components=2, random_state=42)
        
        return reducer.fit_transform(embeddings)
    except Exception as e:
        st.error(f"Errore durante la riduzione dimensionale: {str(e)}")
        # In caso di errore, restituisci un array vuoto
        return np.array([]).reshape(0, 2)

def visualize_embeddings(embeddings_data: Dict[str, Any], method: str = "pca") -> None:
    """Visualizza gli embeddings in 2D."""
    if not embeddings_data or "success" in embeddings_data and not embeddings_data["success"]:
        if "error" in embeddings_data:
            st.error(f"Errore nell'estrazione degli embeddings: {embeddings_data['error']}")
        else:
            st.warning("Nessun embedding trovato nel vector store.")
        return
    
    if embeddings_data["count"] == 0:
        st.warning("Nessun embedding trovato nel vector store.")
        return
    
    # Riduci le dimensioni per la visualizzazione
    embeddings = embeddings_data["embeddings"]
    document_contents = embeddings_data.get("document_contents", [])
    document_metadata = embeddings_data.get("document_metadata", [])
    
    # Riduci le dimensioni degli embeddings
    reduced_data = reduce_dimensions(embeddings, method)
    
    if reduced_data is None:
        st.error(f"Errore durante la riduzione delle dimensioni con {method.upper()}.")
        return
    
    # Crea un dataframe per la visualizzazione
    df = pd.DataFrame({
        "x": reduced_data[:, 0],
        "y": reduced_data[:, 1],
    })
    
    # Aggiungi informazioni sui documenti
    if document_contents and len(document_contents) == len(df):
        df["content"] = document_contents
    
    # Aggiungi metadati se disponibili
    if document_metadata and len(document_metadata) == len(df):
        # Estrai informazioni comuni dai metadati
        doc_types = []
        sources = []
        sheet_names = []
        
        for meta in document_metadata:
            doc_type = meta.get("document_type", meta.get("file_type", "unknown"))
            source = meta.get("source", "unknown")
            sheet = meta.get("sheet_name", "")
            
            doc_types.append(doc_type)
            sources.append(Path(source).name if source != "unknown" else source)
            sheet_names.append(sheet)
        
        df["tipo"] = doc_types
        df["fonte"] = sources
        if any(sheet_names):
            df["scheda"] = sheet_names
        
        # Usa il tipo di documento come colore
        color_column = "tipo"
    else:
        # Senza informazioni sui documenti, usa un colore unico
        color_column = None
    
    # Crea il grafico con Plotly
    hover_data = [col for col in df.columns if col not in ["x", "y", color_column]]
    
    fig = px.scatter(
        df,
        x="x",
        y="y",
        color=color_column,
        hover_data=hover_data,
        title=f"Visualizzazione {method.upper()} degli Embeddings"
    )
    
    # Personalizza il grafico
    fig.update_layout(
        width=800,
        height=600,
        xaxis_title=f"{method.upper()} Componente 1",
        yaxis_title=f"{method.upper()} Componente 2"
    )
    
    # Mostra il grafico
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostra statistiche sui documenti
    if "tipo" in df.columns:
        st.subheader("Distribuzione dei Tipi di Documenti")
        type_counts = df["tipo"].value_counts()
        
        # Crea un grafico a torta
        fig_pie = px.pie(
            values=type_counts.values,
            names=type_counts.index,
            title="Tipi di Documenti"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Mostra anche una tabella con i documenti
        st.subheader("Documenti nel Vector Store")
        st.dataframe(df[[col for col in df.columns if col not in ["x", "y"]]])

def display_document_preview(documents: List[Dict[str, Any]]) -> None:
    """Mostra un'anteprima dei documenti processati."""
    if not documents:
        st.warning("Nessun documento da visualizzare.")
        return
    
    st.subheader("Anteprima dei Documenti Processati")
    st.write(f"Numero totale di documenti: {len(documents)}")
    
    # Raggruppa per tipo di documento
    doc_types = {}
    for doc in documents:
        doc_type = doc["metadata"].get("document_type", "unknown")
        if doc_type not in doc_types:
            doc_types[doc_type] = []
        doc_types[doc_type].append(doc)
    
    # Mostra statistiche per tipo
    for doc_type, docs in doc_types.items():
        with st.expander(f"{doc_type.upper()} ({len(docs)} documenti)"):
            # Mostra i primi 5 documenti
            for i, doc in enumerate(docs[:5]):
                st.markdown(f"**Documento {i+1}**")
                st.markdown(f"**Contenuto:**\n```\n{doc['page_content'][:500]}{'...' if len(doc['page_content']) > 500 else ''}\n```")
                st.markdown("**Metadati:**")
                st.json(doc["metadata"])
                st.markdown("---")
            
            if len(docs) > 5:
                st.info(f"Altri {len(docs) - 5} documenti non mostrati.")

# Interfaccia principale
def main():
    """Funzione principale dell'applicazione."""
    st.title("RAG Document Visualizer")
    st.write("Visualizza e gestisci i documenti nel sistema RAG.")
    
    # Crea una directory temporanea per i file caricati
    temp_dir = tempfile.mkdtemp()
    
    # Sidebar con opzioni
    st.sidebar.title("Opzioni")
    page = st.sidebar.radio(
        "Seleziona Pagina:",
        ["Visualizza Vector Store Esistente", "Carica e Processa Nuovo Documento"]
    )
    
    if page == "Visualizza Vector Store Esistente":
        st.header("Vector Store Esistente")
        
        # Verifica se il vector store esiste
        vs_path = Path(VECTOR_STORE_PATH)
        index_file = vs_path / "index.faiss"
        pkl_file = vs_path / "index.pkl"
        
        if not (index_file.exists() and pkl_file.exists()):
            st.warning(f"Vector store non trovato in: {VECTOR_STORE_PATH}")
            st.info("Carica un documento per creare il vector store.")
        else:
            st.success(f"Vector store trovato in: {VECTOR_STORE_PATH}")
            st.info(f"Percorso: {VECTOR_STORE_PATH}")
            
            # Mostra informazioni sul file Excel di origine
            if Path(EXCEL_FILE_PATH).exists():
                st.success(f"File Excel trovato: {EXCEL_FILE_PATH}")
                st.info(f"Dimensione: {Path(EXCEL_FILE_PATH).stat().st_size / 1024:.1f} KB")
            else:
                st.warning(f"File Excel non trovato: {EXCEL_FILE_PATH}")
            
            # Carica il vector store
            vs_manager = load_vector_store(VECTOR_STORE_PATH)
            
            if vs_manager:
                # Mostra informazioni sul vector store
                st.subheader("Informazioni Vector Store")
                
                # Estrai documenti dal vector store
                documents = list(vs_manager.vector_store.docstore._dict.values())
                st.success(f"Trovati {len(documents)} documenti nel vector store")
                
                # Mostra un campione di documenti
                st.subheader("Campione di Documenti")
                sample_size = min(5, len(documents))
                for i, doc in enumerate(documents[:sample_size]):
                    st.markdown(f"**Documento {i+1}:**")
                    st.markdown(f"**Contenuto:** {doc.page_content[:200]}..." if len(doc.page_content) > 200 else doc.page_content)
                    st.markdown(f"**Metadati:** {doc.metadata}")
                    st.markdown("---")
                
                # Opzioni di visualizzazione
                st.subheader("Visualizzazione Embeddings")
                viz_method = st.radio(
                    "Metodo di visualizzazione:",
                    ["PCA", "t-SNE"]
                )
                
                # Pulsante per generare la visualizzazione
                if st.button("Genera Visualizzazione Embeddings"):
                    # Estrai e visualizza gli embeddings
                    embeddings_data = extract_embeddings_from_vector_store(vs_manager)
                    visualize_embeddings(embeddings_data, viz_method.lower())
                
                # Opzione per pulire il vector store
                if st.sidebar.button("Pulisci Vector Store"):
                    if clean_vector_store(VECTOR_STORE_PATH):
                        st.sidebar.success("Vector store pulito con successo.")
                    else:
                        st.sidebar.error("Errore durante la pulizia del vector store.")
    
    else:  # Carica e Processa Nuovo Documento
        st.header("Carica e Processa Nuovo Documento")
        
        # Opzioni di caricamento file
        upload_option = st.radio(
            "Scegli come caricare il documento:",
            ["Carica File", "Usa Percorso File"]
        )
        
        documents = []
        file_path = None
        
        if upload_option == "Carica File":
            uploaded_file = st.file_uploader(
                "Carica un documento (Excel, Word, PDF, CSV, JSON, XML)",
                type=["xlsx", "xls", "docx", "doc", "pdf", "csv", "json", "xml", "html"]
            )
            
            if uploaded_file:
                # Salva il file in una posizione temporanea
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.success(f"File caricato: {uploaded_file.name}")
        else:
            file_path = st.text_input("Inserisci il percorso completo del file:")
            
            if file_path and not os.path.exists(file_path):
                st.error(f"File non trovato: {file_path}")
                file_path = None
        
        if file_path:
            # Processa il documento
            if st.button("Processa Documento"):
                with st.spinner("Processamento del documento in corso..."):
                    documents = process_document(file_path, temp_dir)
                    
                if documents:
                    st.success(f"Documento processato con successo. Generati {len(documents)} documenti.")
                    
                    # Mostra anteprima dei documenti
                    display_document_preview(documents)
                    
                    # Opzione per creare/aggiornare il vector store
                    if st.button("Crea/Aggiorna Vector Store"):
                        with st.spinner("Creazione/aggiornamento del vector store in corso..."):
                            if create_or_update_vector_store(documents, VECTOR_STORE_PATH):
                                st.success("Vector store creato/aggiornato con successo.")
                                st.info("Vai a 'Visualizza Vector Store Esistente' per vedere i risultati.")
                            else:
                                st.error("Errore durante la creazione/aggiornamento del vector store.")
                else:
                    st.error("Errore durante il processamento del documento.")
    
    # Pulisci la directory temporanea alla chiusura
    try:
        shutil.rmtree(temp_dir)
    except:
        pass

if __name__ == "__main__":
    main()
