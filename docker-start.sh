#!/bin/bash

# Script de démarrage pour l'application Cadets de la défense de Nantes

echo "🚀 Démarrage de l'application Cadets de la défense de Nantes..."

# Créer le répertoire data s'il n'existe pas
mkdir -p /app/data

# Démarrer l'application Streamlit
streamlit run main.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false