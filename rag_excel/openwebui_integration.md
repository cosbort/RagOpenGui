# Integrazione con OpenWebUI

Questa guida spiega come integrare il nostro sistema RAG Excel con OpenWebUI per creare un chatbot che risponda a domande basate sui dati Excel.

## Prerequisiti

1. Sistema RAG Excel installato e funzionante
2. OpenWebUI installato (seguire le istruzioni su https://docs.openwebui.com/)

## Configurazione

### 1. Avvia il server RAG Excel

Prima di tutto, avvia il server RAG Excel:

```bash
cd rag_excel
python app.py
```

Verifica che il server sia in esecuzione visitando `http://localhost:8000/docs` nel tuo browser.

### 2. Carica e indicizza i dati Excel

Utilizza le API per caricare un file Excel e indicizzarlo:

1. Utilizza l'endpoint `/upload` per caricare un file Excel
2. Utilizza l'endpoint `/index` per indicizzare i dati
3. Verifica lo stato con l'endpoint `/status`

### 3. Configura OpenWebUI

OpenWebUI supporta l'integrazione con API personalizzate tramite la funzionalità "Functions". Ecco come configurare OpenWebUI per utilizzare la nostra API RAG:

1. Accedi all'interfaccia di amministrazione di OpenWebUI
2. Vai su "Admin Panel" > "Settings" > "Functions"
3. Crea una nuova funzione con le seguenti impostazioni:

#### Configurazione della funzione RAG Excel

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

### 4. Crea un modello di chat che utilizzi la funzione

1. Vai su "Admin Panel" > "Settings" > "Models"
2. Crea un nuovo modello o modifica un modello esistente
3. Nella sezione "Functions", abilita la funzione "query_excel_data" che hai creato

### 5. Utilizza il chatbot

Ora puoi utilizzare il chatbot OpenWebUI per fare domande sui tuoi dati Excel. Il sistema RAG recupererà le informazioni pertinenti e fornirà risposte basate sui dati.

## Esempio di utilizzo

Ecco alcuni esempi di domande che puoi porre al chatbot:

1. "Quali sono i dati di vendita per il mese di marzo?"
2. "Chi è il cliente con il fatturato più alto?"
3. "Qual è il prodotto più venduto nella regione Nord?"

Il sistema RAG recupererà le informazioni pertinenti dal file Excel e fornirà risposte basate sui dati.

## Risoluzione dei problemi

Se riscontri problemi con l'integrazione, verifica quanto segue:

1. Il server RAG Excel è in esecuzione e accessibile
2. Il file Excel è stato caricato e indicizzato correttamente
3. La funzione OpenWebUI è configurata correttamente con l'URL del server RAG
4. CORS è abilitato sul server RAG (già configurato di default)

Per ulteriori informazioni, consulta la documentazione di OpenWebUI su come configurare e utilizzare le funzioni personalizzate.