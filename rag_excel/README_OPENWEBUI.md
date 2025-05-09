# Integrazione RAG Excel con OpenWebUI

Questa guida spiega come integrare il sistema RAG Excel con OpenWebUI utilizzando il meccanismo di Filter Pipeline.

## Prerequisiti

1. Server RAG Excel in esecuzione su `http://localhost:8000`
2. OpenWebUI installato e configurato (versione recente che supporta Filter Pipeline)
3. File Excel indicizzato correttamente nel vector store FAISS

## Configurazione dell'integrazione

### Passo 1: Preparazione del file della funzione

Il file `rag_excel_function.py` contiene l'implementazione del filtro per OpenWebUI. Questo filtro intercetta le domande dell'utente, le invia al server RAG Excel, e arricchisce il messaggio con il contesto recuperato prima di passarlo all'LLM.

### Passo 2: Configurazione in OpenWebUI

1. Accedi a OpenWebUI
2. Vai alla sezione "Functions" (Funzioni)
3. Crea una nuova funzione:
   - Clicca su "New Function" (Nuova Funzione)
   - Assegna un nome descrittivo (es. "RAG Excel Query")
   - Seleziona il tipo "Filter"
   - Copia e incolla il contenuto del file `rag_excel_function.py`
   - Clicca su "Save" (Salva)

### Passo 3: Configurazione del modello

1. Vai alla sezione "Models" (Modelli)
2. Crea un nuovo modello:
   - Clicca su "New Model" (Nuovo Modello)
   - Assegna un nome (es. "Modello RAG Excel")
   - Seleziona un LLM di base potente (idealmente GPT-4 o superiore per ottenere i migliori risultati)
   - Nella sezione "Function" (Funzione), seleziona la funzione "RAG Excel Query" creata nel passo precedente
   - Clicca su "Save" (Salva)
   
   > **Nota**: Il backend RAG utilizza già GPT-4o per generare le risposte iniziali, ma un modello potente come LLM di base in OpenWebUI garantirà una migliore elaborazione del contesto arricchito.

## Come funziona

Quando utilizzi il modello configurato in OpenWebUI:

1. L'utente invia una domanda sui dati Excel
2. Il filtro RAG Excel intercetta la domanda
3. Il filtro invia la domanda al server RAG Excel su `http://localhost:8000`
4. Il server RAG Excel analizza la domanda, cerca nel vector store FAISS i frammenti più rilevanti (8 frammenti), e genera una risposta con le fonti utilizzando GPT-4o
5. Il filtro aggiunge questo contesto al messaggio dell'utente
6. L'LLM di base riceve la domanda arricchita con il contesto e genera la risposta finale
7. La risposta viene mostrata all'utente in OpenWebUI

## Risoluzione dei problemi

### Il server RAG non risponde

Verifica che il server RAG Excel sia in esecuzione su `http://localhost:8000`. Puoi controllare lo stato con:

```bash
curl http://localhost:8000/status
```

La risposta dovrebbe indicare `"status": "ready"`.

### Risposte non pertinenti

Se le risposte non sono pertinenti:

1. Controlla che il file Excel sia stato indicizzato correttamente
2. Verifica i log del server RAG Excel per eventuali errori
3. Se hai modificato il file Excel, esegui `repair_rag_system.py` per reindicizzarlo

### Errori nel filtro

Se il filtro non funziona correttamente:

1. Controlla i log di OpenWebUI per eventuali errori
2. Verifica che il filtro sia configurato correttamente e associato al modello
3. Assicurati che il server RAG Excel sia raggiungibile dall'ambiente in cui è in esecuzione OpenWebUI

## Aggiornamento del vector store

Dopo aver modificato il file Excel, è necessario aggiornare il vector store:

1. Arresta il server RAG Excel (se in esecuzione)
2. Esegui lo script di riparazione:
   ```bash
   python repair_rag_system.py
   ```
3. Riavvia il server RAG Excel:
   ```bash
   python run.py
   ```

## Note tecniche

- Il filtro utilizza il pattern asincrono di OpenWebUI con `async def inlet`
- Il vector store utilizza FAISS con supporto AVX2 per la ricerca efficiente di similarità vettoriale
- Il sistema recupera 8 frammenti rilevanti per ogni query per sfruttare la finestra di contesto ampia di GPT-4o
- Gli embedding vengono generati con il modello `text-embedding-3-small` di OpenAI
- Il backend RAG utilizza GPT-4o per generare risposte di alta qualità
- Il sistema supporta la reindicizzazione senza necessità di riavviare OpenWebUI

### Passo 3: Testa la funzione

1. Seleziona il modello "RAG Excel" nella chat
2. Invia una query come "Qual è il fatturato della regione Nord?"
3. Verifica che la risposta venga generata correttamente

## Risoluzione dei problemi

### Errore di connessione

Se ricevi un errore di connessione come:
```
Connection error: Cannot connect to host localhost:11034 ssl:default [Il computer remoto ha rifiutato la connessione di rete]
```

Verifica che:
1. Il server RAG Excel sia in esecuzione su `http://localhost:8000`
2. La porta configurata nel file `openwebui_function.py` sia corretta (8000)
3. Non ci siano firewall che bloccano la connessione

### Errore di inizializzazione

Se ricevi un errore di inizializzazione come:
```
Mi dispiace, non sono riuscito a inizializzare il sistema RAG. Verifica che il vector store sia stato creato correttamente.
```

Verifica che:
1. Il vector store sia stato creato correttamente eseguendo:
   ```
   Invoke-RestMethod -Uri "http://localhost:8000/index" -Method Post
   ```
2. Lo stato del server sia "ready" eseguendo:
   ```
   Invoke-RestMethod -Uri "http://localhost:8000/status" -Method Get
   ```
