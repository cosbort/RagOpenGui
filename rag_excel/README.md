# RAG Excel per OpenWebUI

Sistema di Retrieval Augmented Generation (RAG) per dati Excel con integrazione OpenWebUI.

## Descrizione

Questo progetto implementa un sistema RAG per l'interrogazione di dati Excel utilizzando LLM e tecniche di embedding. Il sistema consente di porre domande in linguaggio naturale sui dati contenuti in un file Excel e ricevere risposte pertinenti basate sul contenuto del file. Include anche l'integrazione con OpenWebUI per un'interfaccia utente avanzata.

## Prerequisiti

- Python 3.9+
- UV o Pip per l'installazione delle dipendenze
- Una API key di OpenAI
- OpenWebUI (per l'integrazione con l'interfaccia utente)

## Installazione

1. Clona il repository
2. Crea un ambiente virtuale:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate  # Windows
   ```
3. Installa le dipendenze con UV (consigliato) o Pip:
   ```bash
   # Con UV
   uv pip install -r requirements.txt
   
   # Con Pip
   pip install -r requirements.txt
   ```
4. Installa le dipendenze aggiuntive necessarie per il caricamento dei file Excel:
   ```bash
   uv pip install unstructured networkx python-multipart
   ```

## Configurazione

1. Crea un file `.env` nella directory principale del progetto con le seguenti variabili:
   ```
   OPENAI_API_KEY=your_openai_api_key
   EXCEL_FILE_PATH=./data/dati.xlsx
   VECTOR_STORE_PATH=./data/vector_store
   LLM_MODEL=gpt-4o
   EMBEDDING_MODEL=text-embedding-3-small
   MAX_RESULTS=8
   ```

2. Sostituisci `your_openai_api_key` con la tua API key di OpenAI.
3. Modifica `EXCEL_FILE_PATH` per puntare al tuo file Excel se necessario.

## Utilizzo

1. Avvia il server RAG:
   ```bash
   # Nell'ambiente virtuale attivato
   python run.py
   
   # Oppure con UV
   uv run python run.py
   ```

2. Il server sarà disponibile all'indirizzo `http://localhost:8000`.

3. Puoi interrogare il sistema utilizzando l'endpoint `/query`:
   ```bash
   curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"query": "Qual è il fatturato totale?"}'
   ```

4. Per verificare lo stato del sistema:
   ```bash
   curl http://localhost:8000/status
   ```

## Reindicizzazione dopo modifiche al file Excel

Se modifichi il file Excel di origine o vuoi cambiare la configurazione del sistema (come il modello LLM), devi reindicizzare i dati per aggiornare il vector store:

```bash
# Nell'ambiente virtuale attivato
python repair_rag_system.py

# Oppure con UV (consigliato)
uv run python repair_rag_system.py
```

Il processo di reindicizzazione:
1. Pulisce la directory del vector store
2. Carica il file Excel e crea i chunk di testo
3. Genera gli embedding utilizzando il modello configurato (text-embedding-3-small)
4. Crea un nuovo indice FAISS ottimizzato con supporto AVX2
5. Salva l'indice nella directory del vector store

Dopo la reindicizzazione, riavvia il server RAG per rendere effettive le modifiche.

## Integrazione con OpenWebUI

Per l'integrazione con OpenWebUI, consulta il file [README_OPENWEBUI.md](README_OPENWEBUI.md).

## Struttura del progetto

- `app.py`: Applicazione FastAPI principale
- `run.py`: Script per avviare il server
- `config.py`: Configurazioni del sistema (modello GPT-4o, embedding, parametri RAG)
- `repair_rag_system.py`: Script per riparare/ricostruire il vector store
- `rag_excel_function.py`: Implementazione del filtro per OpenWebUI
- `utils/`: Directory contenente moduli di utilità
  - `excel_loader.py`: Caricatore per file Excel
  - `rag_chain.py`: Implementazione della catena RAG
  - `vector_store.py`: Gestione del vector store FAISS (Facebook AI Similarity Search)
- `data/`: Directory per i dati
  - `dati.xlsx`: File Excel di esempio
  - `vector_store/`: Directory per il vector store FAISS (indici vettoriali)

## Tecnologie utilizzate

- **LangChain**: Framework per la creazione di applicazioni basate su LLM
- **OpenAI API**: Per l'accesso ai modelli LLM (GPT-4o) e di embedding (text-embedding-3-small)
- **FAISS**: Per l'archiviazione e la ricerca efficiente di vettori di embedding con supporto AVX2
- **FastAPI**: Per l'API REST
- **Uvicorn**: Server ASGI per FastAPI
- **OpenWebUI**: Per l'interfaccia utente web (integrazione opzionale)

## Licenza

MIT