import os
import shutil
import subprocess
import time

def delete_pycache_folders(path="."):
    """Supprimer tous les dossiers __pycache__ récursivement"""
    for root, dirs, files in os.walk(path):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                full_path = os.path.join(root, dir_name)
                print(f"Suppression du cache : {full_path}")
                shutil.rmtree(full_path)

def run_streamlit(file_name):
    """Lancer Streamlit proprement"""
    print(f"Lancement de Streamlit avec {file_name}...")
    subprocess.run(["streamlit", "run", file_name])

if __name__ == "__main__":
    print("Nettoyage des fichiers __pycache__...")
    delete_pycache_folders(".")
    time.sleep(1)  # Petite pause pour être propre
    run_streamlit("main.py")  # Remplacez ici par votre fichier principal si besoin
