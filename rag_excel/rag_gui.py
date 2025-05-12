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
    EXCEL_FILE_PATH
)
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
        
        faiss_index = vs_manager.vector_store.index
        if not hasattr(faiss_index, "reconstruct"):
            return {"success": False, "error": "L'indice FAISS non supporta la ricostruzione dei vettori"}
        
        # Estrai i vettori e i documenti
        embeddings = []
        documents = []
        
        # Ottieni il numero di vettori nell'indice
        num_vectors = faiss_index.ntotal
        
        for i in range(num_vectors):
            try:
                # Ricostruisci il vettore
                vector = faiss_index.reconstruct(i)
                embeddings.append(vector)
                
                # Ottieni il documento corrispondente
                doc_id = vs_manager.vector_store.docstore._dict.get(f"doc:{i}")
                if doc_id:
                    documents.append(doc_id)
            except Exception as e:
                continue
        
        return {
            "success": True,
            "embeddings": np.array(embeddings),
            "documents": documents,
            "count": len(embeddings)
        }
    except Exception as e:
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
    documents = embeddings_data["documents"]
    
    # Assicurati che il numero di embeddings e documenti sia lo stesso
    min_length = min(len(embeddings), len(documents))
    if min_length < len(embeddings):
        embeddings = embeddings[:min_length]
        st.warning(f"Numero di embeddings ridotto a {min_length} per corrispondere al numero di documenti")
    elif min_length < len(documents):
        documents = documents[:min_length]
        st.warning(f"Numero di documenti ridotto a {min_length} per corrispondere al numero di embeddings")
    
    # Se non ci sono embeddings dopo il controllo, mostra un avviso e termina
    if min_length == 0:
        st.warning("Nessun embedding disponibile per la visualizzazione dopo il controllo di coerenza.")
        return
    
    reduced_embeddings = reduce_dimensions(embeddings, method)
    
    # Se la riduzione dimensionale ha restituito un array vuoto, termina
    if reduced_embeddings.shape[0] == 0:
        st.error("Impossibile visualizzare gli embeddings a causa di un errore nella riduzione dimensionale.")
        return
    
    # Prepara dati per il dataframe assicurandosi che tutte le liste abbiano la stessa lunghezza
    x_values = reduced_embeddings[:, 0]
    y_values = reduced_embeddings[:, 1]
    
    # Crea liste per document_type e content con gestione sicura
    doc_types = []
    contents = []
    
    for doc in documents:
        if hasattr(doc, "metadata"):
            doc_types.append(doc.metadata.get("document_type", "unknown"))
        else:
            doc_types.append("unknown")
            
        if hasattr(doc, "page_content"):
            contents.append(doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content)
        else:
            contents.append("N/A")
    
    # Verifica finale che tutte le liste abbiano la stessa lunghezza
    length = len(x_values)
    if len(y_values) != length or len(doc_types) != length or len(contents) != length:
        st.error(f"Errore: le liste hanno lunghezze diverse: x={len(x_values)}, y={len(y_values)}, types={len(doc_types)}, contents={len(contents)}")
        return
    
    # Crea un dataframe per la visualizzazione
    df = pd.DataFrame({
        "x": x_values,
        "y": y_values,
        "document_type": doc_types,
        "content": contents
    })
    
    # Visualizza con Plotly
    fig = px.scatter(
        df, x="x", y="y", color="document_type", hover_data=["content"],
        title=f"Visualizzazione degli Embeddings ({method.upper()})"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Statistiche
    st.subheader("Statistiche degli Embeddings")
    st.write(f"Numero totale di embeddings: {embeddings_data['count']}")
    
    # Conteggio per tipo di documento
    doc_types = df["document_type"].value_counts().reset_index()
    doc_types.columns = ["Tipo Documento", "Conteggio"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("Distribuzione per tipo di documento:")
        st.dataframe(doc_types)
    
    with col2:
        fig, ax = plt.subplots()
        ax.pie(doc_types["Conteggio"], labels=doc_types["Tipo Documento"], autopct="%1.1f%%")
        ax.set_title("Distribuzione per tipo di documento")
        st.pyplot(fig)

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
    st.title("📊 RAG Document Visualizer")
    
    # Sidebar
    st.sidebar.title("Opzioni")
    
    # Crea una directory temporanea per i file caricati
    temp_dir = tempfile.mkdtemp()
    
    # Opzioni di visualizzazione
    view_option = st.sidebar.radio(
        "Cosa vuoi fare?",
        ["Visualizza Vector Store Esistente", "Carica e Processa Nuovo Documento"]
    )
    
    if view_option == "Visualizza Vector Store Esistente":
        st.header("Visualizzazione Vector Store Esistente")
        
        # Verifica esistenza vector store
        vs_path = Path(VECTOR_STORE_PATH)
        index_file = vs_path / "index.faiss"
        pkl_file = vs_path / "index.pkl"
        
        if not (index_file.exists() and pkl_file.exists()):
            st.warning(f"Vector store non trovato in: {VECTOR_STORE_PATH}")
            st.info("Carica un documento per creare il vector store.")
        else:
            st.success(f"Vector store trovato in: {VECTOR_STORE_PATH}")
            
            # Carica il vector store
            vs_manager = load_vector_store(VECTOR_STORE_PATH)
            
            if vs_manager:
                # Opzioni di visualizzazione
                viz_method = st.radio(
                    "Metodo di visualizzazione:",
                    ["PCA", "t-SNE"]
                )
                
                # Estrai e visualizza gli embeddings
                embeddings_data = extract_embeddings_from_vector_store(vs_manager)
                visualize_embeddings(embeddings_data, viz_method.lower())
                
                # Opzione per pulire il vector store
                if st.sidebar.button("Pulisci Vector Store"):
                    if clean_vector_store(VECTOR_STORE_PATH):
                        st.sidebar.success("Vector store pulito con successo.")
                        st.experimental_rerun()
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
