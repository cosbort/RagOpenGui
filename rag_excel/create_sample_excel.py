"""
Script per creare un file Excel di esempio con dati di vendita.
"""
import os
import pandas as pd
from pathlib import Path

# Crea la directory data se non esiste
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Dati di esempio: vendite per regione
vendite_regione = {
    "Regione": ["Nord", "Centro", "Sud", "Isole"],
    "Fatturato_2023": [1250000, 980000, 750000, 420000],
    "Fatturato_2024": [1380000, 1050000, 820000, 480000],
    "Crescita_Percentuale": [10.4, 7.1, 9.3, 14.3]
}

# Dati di esempio: vendite per prodotto
vendite_prodotto = {
    "Prodotto": ["Laptop", "Smartphone", "Tablet", "Monitor", "Accessori"],
    "Quantità_Venduta": [1200, 3500, 950, 780, 4200],
    "Prezzo_Medio": [1200, 800, 450, 350, 120],
    "Fatturato_Totale": [1440000, 2800000, 427500, 273000, 504000]
}

# Dati di esempio: clienti principali
clienti = {
    "Cliente": ["TechCorp", "MediaGroup", "EduSystems", "HealthCare", "RetailOne"],
    "Settore": ["Tecnologia", "Media", "Istruzione", "Sanità", "Retail"],
    "Fatturato": [980000, 750000, 620000, 580000, 490000],
    "Anni_Cliente": [5, 3, 7, 2, 4]
}

# Crea il file Excel con più fogli
excel_path = data_dir / "dati.xlsx"
with pd.ExcelWriter(excel_path) as writer:
    pd.DataFrame(vendite_regione).to_excel(writer, sheet_name="Vendite_Regione", index=False)
    pd.DataFrame(vendite_prodotto).to_excel(writer, sheet_name="Vendite_Prodotto", index=False)
    pd.DataFrame(clienti).to_excel(writer, sheet_name="Clienti", index=False)

print(f"File Excel creato con successo: {excel_path}")
