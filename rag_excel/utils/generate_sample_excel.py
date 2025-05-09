"""
Script per generare un file Excel di esempio per testare il sistema RAG.
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

# Imposta il seed per la riproducibilità
random.seed(42)
np.random.seed(42)

# Directory di output
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "dati_esempio.xlsx"

def generate_sales_data():
    """
    Genera dati di vendita di esempio.
    """
    # Parametri
    num_rows = 100
    start_date = datetime(2024, 1, 1)
    
    # Prodotti
    products = [
        "Laptop Pro", "Smartphone X", "Tablet Y", "Monitor UltraWide",
        "Tastiera Meccanica", "Mouse Wireless", "Cuffie Noise-Cancelling",
        "Stampante Laser", "Scanner Portatile", "Docking Station"
    ]
    
    # Regioni
    regions = ["Nord", "Centro", "Sud", "Isole"]
    
    # Clienti
    customers = [
        "TechCorp", "InnovaSrl", "FutureShop", "DigitalStore", 
        "ElectronicWorld", "SmartBuy", "TechZone", "GadgetHub",
        "ComputerLand", "TechMaster"
    ]
    
    # Venditori
    salespeople = [
        "Mario Rossi", "Giulia Bianchi", "Luca Verdi", "Anna Neri",
        "Paolo Gialli", "Laura Blu", "Marco Viola", "Sofia Arancio"
    ]
    
    # Genera dati
    data = []
    for i in range(num_rows):
        date = start_date + timedelta(days=random.randint(0, 180))
        product = random.choice(products)
        region = random.choice(regions)
        customer = random.choice(customers)
        salesperson = random.choice(salespeople)
        quantity = random.randint(1, 10)
        
        # Prezzo base per prodotto
        base_prices = {
            "Laptop Pro": 1200, "Smartphone X": 800, "Tablet Y": 500,
            "Monitor UltraWide": 350, "Tastiera Meccanica": 120,
            "Mouse Wireless": 50, "Cuffie Noise-Cancelling": 180,
            "Stampante Laser": 250, "Scanner Portatile": 150,
            "Docking Station": 90
        }
        
        unit_price = base_prices[product] * (1 + random.uniform(-0.1, 0.1))
        total_price = unit_price * quantity
        
        data.append({
            "Data": date,
            "Prodotto": product,
            "Regione": region,
            "Cliente": customer,
            "Venditore": salesperson,
            "Quantità": quantity,
            "Prezzo Unitario": round(unit_price, 2),
            "Prezzo Totale": round(total_price, 2)
        })
    
    return pd.DataFrame(data)

def generate_inventory_data():
    """
    Genera dati di inventario di esempio.
    """
    # Prodotti e dettagli
    products = [
        "Laptop Pro", "Smartphone X", "Tablet Y", "Monitor UltraWide",
        "Tastiera Meccanica", "Mouse Wireless", "Cuffie Noise-Cancelling",
        "Stampante Laser", "Scanner Portatile", "Docking Station"
    ]
    
    categories = [
        "Computer", "Mobile", "Mobile", "Periferiche",
        "Periferiche", "Periferiche", "Audio",
        "Stampanti", "Scanner", "Accessori"
    ]
    
    suppliers = [
        "TechSupply", "ElectroVendor", "GadgetWholesale", "ComputerParts",
        "DigitalDistributor"
    ]
    
    warehouses = ["Magazzino A", "Magazzino B", "Magazzino C"]
    
    # Genera dati
    data = []
    for i, product in enumerate(products):
        category = categories[i]
        supplier = random.choice(suppliers)
        warehouse = random.choice(warehouses)
        stock = random.randint(10, 100)
        min_stock = random.randint(5, 15)
        reorder_quantity = random.randint(20, 50)
        last_restock = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 90))
        
        data.append({
            "Prodotto": product,
            "Categoria": category,
            "Fornitore": supplier,
            "Magazzino": warehouse,
            "Quantità in Stock": stock,
            "Scorta Minima": min_stock,
            "Quantità Riordino": reorder_quantity,
            "Ultimo Rifornimento": last_restock
        })
    
    return pd.DataFrame(data)

def generate_customer_data():
    """
    Genera dati dei clienti di esempio.
    """
    # Clienti
    customers = [
        "TechCorp", "InnovaSrl", "FutureShop", "DigitalStore", 
        "ElectronicWorld", "SmartBuy", "TechZone", "GadgetHub",
        "ComputerLand", "TechMaster"
    ]
    
    # Città
    cities = [
        "Milano", "Roma", "Napoli", "Torino", "Bologna",
        "Firenze", "Bari", "Palermo", "Catania", "Venezia"
    ]
    
    # Genera dati
    data = []
    for i, customer in enumerate(customers):
        city = cities[i % len(cities)]
        address = f"Via {random.choice(['Roma', 'Milano', 'Napoli', 'Venezia', 'Firenze'])} {random.randint(1, 100)}"
        postal_code = f"{random.randint(10, 99)}0{random.randint(10, 99)}"
        phone = f"+39 {random.randint(300, 399)} {random.randint(1000000, 9999999)}"
        email = f"info@{customer.lower().replace(' ', '')}.com"
        contact_person = random.choice([
            "Mario Rossi", "Giulia Bianchi", "Luca Verdi", "Anna Neri",
            "Paolo Gialli", "Laura Blu", "Marco Viola", "Sofia Arancio"
        ])
        customer_since = datetime(random.randint(2010, 2023), random.randint(1, 12), random.randint(1, 28))
        credit_limit = random.choice([5000, 10000, 15000, 20000, 25000])
        
        data.append({
            "Cliente": customer,
            "Città": city,
            "Indirizzo": address,
            "CAP": postal_code,
            "Telefono": phone,
            "Email": email,
            "Persona di Contatto": contact_person,
            "Cliente dal": customer_since,
            "Limite di Credito": credit_limit
        })
    
    return pd.DataFrame(data)

def main():
    """
    Funzione principale per generare il file Excel di esempio.
    """
    print("Generazione del file Excel di esempio...")
    
    # Crea la directory di output se non esiste
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Genera i dataframes
    sales_df = generate_sales_data()
    inventory_df = generate_inventory_data()
    customers_df = generate_customer_data()
    
    # Crea un writer Excel
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        sales_df.to_excel(writer, sheet_name='Vendite', index=False)
        inventory_df.to_excel(writer, sheet_name='Inventario', index=False)
        customers_df.to_excel(writer, sheet_name='Clienti', index=False)
    
    print(f"File Excel generato con successo: {OUTPUT_FILE}")
    print(f"Foglio 'Vendite': {len(sales_df)} righe")
    print(f"Foglio 'Inventario': {len(inventory_df)} righe")
    print(f"Foglio 'Clienti': {len(customers_df)} righe")

if __name__ == "__main__":
    main()