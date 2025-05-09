# Guida all'utilizzo del sistema RAG Excel

Questa guida spiega in dettaglio come configurare e utilizzare il sistema RAG Excel con OpenWebUI.

## Indice
1. [Panoramica del sistema](#panoramica-del-sistema)
2. [Installazione](#installazione)
3. [Configurazione](#configurazione)
4. [Utilizzo](#utilizzo)
5. [Integrazione con OpenWebUI](#integrazione-con-openwebui)
6. [Risoluzione dei problemi](#risoluzione-dei-problemi)
7. [Riferimenti API](#riferimenti-api)

## Panoramica del sistema

Il sistema RAG Excel è una soluzione che permette di:
- Caricare e processare dati da file Excel
- Creare un indice vettoriale dei dati per ricerche semantiche
- Rispondere a domande in linguaggio naturale sui dati Excel
- Integrarsi con OpenWebUI per un'interfaccia chatbot user-friendly

### Componenti principali:
- **ExcelLoader**: Carica e processa i file Excel
- **VectorStoreManager**: Gestisce l'indice vettoriale per le ricerche semantiche
- **RagChain**: Implementa la catena RAG utilizzando LangChain
- **API FastAPI**: Espone le funzionalità del sistema tramite API REST

## Installazione

### Prerequisiti
- Python 3.10 o superiore
- Pip (gestore pacchetti Python)
- File Excel con i dati da interrogare

### Passaggi di installazione

1. Clona o scarica il repository

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

3. Crea un file `.env` nella directory principale copiando `.env.example`:
```bash
cp .env.example .env
```

4. Modifica il file `.env` con le tue impostazioni, in particolare:
   - Inserisci la tua chiave API OpenAI (`OPENAI_API_KEY`)
   - Configura il percorso del file Excel (`EXCEL_FILE_PATH`)

## Configurazione

### Configurazione del file `.env`

Il file `.env` contiene tutte le configurazioni necessarie per il sistema:

```
# Configurazione API
API_HOST=0.0.0.0
API_PORT=8000

# Configurazione OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Modelli
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-3.5-turbo

# Configurazione Excel
EXCEL_FILE_PATH=./data/dati.xlsx

# Configurazione Vector Store
VECTOR_STORE_PATH=./data/vector_store
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Configurazione RAG
MAX_RESULTS=5
SIMILARITY_THRESHOLD=0.7
```

### Generazione di un file Excel di esempio

Se non hai un file Excel da utilizzare, puoi generarne uno di esempio:

```bash
python run.py --generate-sample
```

Questo comando genererà un file Excel di esempio con dati fittizi nella directory `data/`.

## Utilizzo

### Avvio del server

Per avviare il server API:

```bash
python run.py
```

Oppure:

```bash
python app.py
```

Il server sarà disponibile all'indirizzo `http://localhost:8000`.

### Utilizzo delle API

Una volta avviato il server, puoi utilizzare le seguenti API:

1. **Verifica dello stato del sistema**:
   ```
   GET /status
   ```

2. **Caricamento di un file Excel**:
   ```
   POST /upload
   ```
   Con un file Excel allegato.

3. **Indicizzazione dei dati**:
   ```
   POST /index
   ```

4. **Interrogazione dei dati**:
   ```
   POST /query
   ```
   Con un JSON nel formato:
   ```json
   {
     "query": "La tua domanda sui dati Excel"
   }
   ```

5. **Ricerca diretta di similarità**:
   ```
   POST /search
   ```
   Con un JSON nel formato:
   ```json
   {
     "query": "La tua query di ricerca"
   }
   ```

6. **Informazioni sul file Excel**:
   ```
   GET /excel-info
   ```

### Interfaccia Swagger

Puoi accedere all'interfaccia Swagger per testare le API all'indirizzo:
```
http://localhost:8000/docs
```

## Integrazione con OpenWebUI

Per integrare il sistema RAG Excel con OpenWebUI, segui questi passaggi:

### 1. Installazione di OpenWebUI

Segui le istruzioni ufficiali per installare OpenWebUI:
```
https://docs.openwebui.com/
```

Il modo più semplice è utilizzare Docker:
```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main
```

### 2. Configurazione di OpenWebUI

1. Accedi all'interfaccia di OpenWebUI all'indirizzo `http://localhost:3000`
2. Vai su "Admin Panel" > "Settings" > "Functions"
3. Crea una nuova funzione con le seguenti impostazioni:

```json
{
  "name": "query_excel_data",
  "description": "Interroga i dati Excel utilizzando il sistema RAG",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "La domanda sui dati Excel"
      }
    },
    "required": ["query"]
  },
  "url": "http://localhost:8000/query",
  "method": "POST"
}
```

4. Vai su "Admin Panel" > "Settings" > "Models"
5. Crea un nuovo modello o modifica un modello esistente
6. Nella sezione "Functions", abilita la funzione "query_excel_data" che hai creato

### 3. Utilizzo del chatbot

Ora puoi utilizzare il chatbot OpenWebUI per fare domande sui tuoi dati Excel:

1. Seleziona il modello configurato con la funzione RAG Excel
2. Fai una domanda sui tuoi dati, ad esempio:
   - "Quali sono le vendite totali per regione?"
   - "Chi è il cliente con il maggior numero di acquisti?"
   - "Qual è il prodotto più venduto?"

Il sistema RAG recupererà le informazioni pertinenti dal file Excel e fornirà risposte basate sui dati.

## Risoluzione dei problemi

### Problemi comuni e soluzioni

1. **Errore "File Excel non trovato"**
   - Verifica che il percorso del file Excel nel file `.env` sia corretto
   - Utilizza un percorso assoluto invece di un percorso relativo
   - Genera un file di esempio con `python run.py --generate-sample`

2. **Errore "Vector store non trovato"**
   - Esegui l'indicizzazione dei dati con l'endpoint `/index`
   - Verifica che la directory del vector store esista e sia scrivibile

3. **Errore di connessione a OpenAI**
   - Verifica che la chiave API OpenAI nel file `.env` sia valida
   - Controlla la connessione internet

4. **OpenWebUI non riesce a connettersi all'API RAG**
   - Verifica che il server RAG sia in esecuzione
   - Se utilizzi Docker, assicurati di utilizzare l'indirizzo IP corretto invece di localhost
   - Verifica che non ci siano firewall che bloccano la connessione

### Log di debug

Per ottenere log più dettagliati, modifica il livello di logging in `app.py`:

```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
```

## Riferimenti API

### GET /status
Restituisce lo stato attuale del sistema.

**Risposta**:
```json
{
  "status": "ready|not_ready",
  "message": "Messaggio di stato",
  "excel_file": "Percorso del file Excel",
  "vector_store": "Percorso del vector store"
}
```

### POST /upload
Carica un nuovo file Excel.

**Richiesta**: Form data con file Excel

**Risposta**:
```json
{
  "status": "success",
  "message": "File Excel caricato con successo",
  "file_path": "Percorso del file caricato"
}
```

### POST /index
Avvia l'indicizzazione dei dati Excel.

**Risposta**:
```json
{
  "status": "indexing",
  "message": "Indicizzazione dei dati avviata in background",
  "excel_file": "Percorso del file Excel",
  "vector_store": "Percorso del vector store"
}
```

### POST /query
Risponde a una domanda sui dati Excel.

**Richiesta**:
```json
{
  "query": "La tua domanda sui dati Excel"
}
```

**Risposta**:
```json
{
  "answer": "Risposta alla domanda",
  "sources": [
    {
      "content": "Contenuto del documento",
      "metadata": {
        "source": "Percorso del file",
        "sheet": "Nome della scheda",
        "row_index": 0,
        "...": "Altri metadati"
      },
      "similarity": 0.95
    }
  ]
}
```

### POST /search
Esegue una ricerca diretta di similarità.

**Richiesta**:
```json
{
  "query": "La tua query di ricerca"
}
```

**Risposta**:
```json
{
  "results": [
    {
      "content": "Contenuto del documento",
      "metadata": {
        "source": "Percorso del file",
        "sheet": "Nome della scheda",
        "row_index": 0,
        "...": "Altri metadati"
      },
      "similarity": 0.95
    }
  ]
}
```

### GET /excel-info
Restituisce informazioni sul file Excel.

**Risposta**:
```json
{
  "file_path": "Percorso del file Excel",
  "sheets": {
    "Foglio1": {
      "rows": 100,
      "columns": 10,
      "column_names": ["Colonna1", "Colonna2", "..."]
    },
    "Foglio2": {
      "rows": 50,
      "columns": 5,
      "column_names": ["Colonna1", "Colonna2", "..."]
    }
  }
}
```