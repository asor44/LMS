# Utiliser Python 3.11 slim comme base
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY docker-requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r docker-requirements.txt

# Copier le code de l'application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p attached_assets static pages data

# Rendre le script de démarrage exécutable
RUN chmod +x docker-start.sh

# Exposer le port 8501 (port par défaut de Streamlit)
EXPOSE 8501

# Variables d'environnement pour Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Commande de démarrage
CMD ["./docker-start.sh"]