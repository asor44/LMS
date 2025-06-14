# Dockerisation de l'Application Cadets de la défense de Nantes

## Prérequis

- Docker installé sur votre machine
- Docker Compose installé (généralement inclus avec Docker Desktop)

## Construction et lancement rapide

### Option 1 : Avec Docker Compose (recommandé)

```bash
# Construire et lancer l'application
docker-compose up --build

# Ou en arrière-plan
docker-compose up --build -d

# Arrêter l'application
docker-compose down
```

### Option 2 : Avec Docker directement

```bash
# Construire l'image
docker build -t cadets-app .

# Créer un volume pour persister les données
docker volume create cadets-data

# Lancer le conteneur
docker run -d \
  --name cadets-app \
  -p 8501:8501 \
  -v cadets-data:/app/data \
  cadets-app

# Arrêter le conteneur
docker stop cadets-app
docker rm cadets-app
```

## Accès à l'application

Une fois lancée, l'application sera accessible à l'adresse :
- **URL locale** : http://localhost:8501
- **Identifiants par défaut** :
  - Email : admin@admin.com
  - Mot de passe : admin123

## Gestion des données

### Persistence des données
- La base de données SQLite est stockée dans le volume Docker `cadets-data`
- Les données sont conservées même après redémarrage du conteneur

### Sauvegarde des données
```bash
# Copier la base de données depuis le conteneur
docker cp cadets-app:/app/data/cadets.db ./backup-cadets.db
```

### Restauration des données
```bash
# Copier une sauvegarde vers le conteneur
docker cp ./backup-cadets.db cadets-app:/app/data/cadets.db
docker restart cadets-app
```

## Variables d'environnement disponibles

Vous pouvez personnaliser l'application en modifiant le fichier `docker-compose.yml` :

```yaml
environment:
  - STREAMLIT_SERVER_PORT=8501
  - STREAMLIT_SERVER_ADDRESS=0.0.0.0
  - STREAMLIT_SERVER_HEADLESS=true
  - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

## Surveillance et logs

```bash
# Voir les logs en temps réel
docker-compose logs -f

# Voir les logs d'un conteneur spécifique
docker logs cadets-app

# Vérifier l'état de santé
docker-compose ps
```

## Mise à jour de l'application

```bash
# Arrêter l'application
docker-compose down

# Reconstruire avec les dernières modifications
docker-compose up --build

# Ou forcer la reconstruction complète
docker-compose build --no-cache
docker-compose up
```

## Dépannage

### Port déjà utilisé
Si le port 8501 est déjà utilisé, modifiez le mapping dans `docker-compose.yml` :
```yaml
ports:
  - "8502:8501"  # Utilise le port 8502 au lieu de 8501
```

### Problèmes de permissions
```bash
# Donner les permissions au script de démarrage
chmod +x docker-start.sh
```

### Réinitialiser complètement
```bash
# Supprimer tous les conteneurs et volumes
docker-compose down -v
docker system prune -f
```

## Structure des fichiers Docker

- `Dockerfile` : Configuration de l'image Docker
- `docker-compose.yml` : Orchestration des services
- `docker-requirements.txt` : Dépendances Python spécifiques à Docker
- `.dockerignore` : Fichiers à exclure de l'image
- `docker-start.sh` : Script de démarrage personnalisé