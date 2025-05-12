"""
Script di avvio per l'interfaccia grafica RAG Document Visualizer.
Utilizza l'ambiente virtuale gestito da uv.
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Avvia l'interfaccia grafica Streamlit nell'ambiente virtuale."""
    # Ottieni il percorso assoluto dello script rag_gui.py
    base_dir = Path(__file__).resolve().parent
    gui_path = base_dir / "rag_gui.py"
    
    print("Avvio dell'interfaccia grafica RAG Document Visualizer...")
    print(f"Percorso GUI: {gui_path}")
    
    # Determina il percorso dell'ambiente virtuale
    venv_path = base_dir / ".venv"
    if not venv_path.exists():
        print(f"Ambiente virtuale non trovato in {venv_path}")
        print("Creazione di un nuovo ambiente virtuale con uv...")
        
        try:
            # Crea un nuovo ambiente virtuale con uv
            subprocess.run(["uv", "venv", ".venv"], cwd=str(base_dir), check=True)
            
            # Installa le dipendenze
            print("Installazione delle dipendenze...")
            subprocess.run(["uv", "pip", "install", "-r", "requirements.txt"], cwd=str(base_dir), check=True)
            subprocess.run(["uv", "pip", "install", "-r", "requirements_gui.txt"], cwd=str(base_dir), check=True)
        except Exception as e:
            print(f"Errore durante la creazione dell'ambiente virtuale: {str(e)}")
            sys.exit(1)
    
    # Determina il percorso dell'eseguibile Python nell'ambiente virtuale
    if os.name == 'nt':  # Windows
        python_exe = venv_path / "Scripts" / "python.exe"
    else:  # Linux/Mac
        python_exe = venv_path / "bin" / "python"
    
    if not python_exe.exists():
        print(f"Eseguibile Python non trovato in {python_exe}")
        sys.exit(1)
    
    # Comando per avviare Streamlit usando l'ambiente virtuale
    cmd = [str(python_exe), "-m", "streamlit", "run", str(gui_path), "--server.port=8501"]
    
    try:
        print(f"Avvio dell'applicazione con: {' '.join(cmd)}")
        # Esegui il comando
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nChiusura dell'interfaccia grafica...")
    except Exception as e:
        print(f"Errore durante l'avvio dell'interfaccia grafica: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
