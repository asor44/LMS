.PHONY: build run stop restart logs clean backup restore help

# Variables
IMAGE_NAME=cadets-app
CONTAINER_NAME=cadets-app
BACKUP_FILE=backup-cadets-$(shell date +%Y%m%d-%H%M%S).db

# Construction et lancement
build:
	docker-compose build

run:
	docker-compose up -d

dev:
	docker-compose up

stop:
	docker-compose down

restart: stop run

# Gestion des logs
logs:
	docker-compose logs -f

logs-tail:
	docker-compose logs --tail=100

# Nettoyage
clean:
	docker-compose down -v
	docker system prune -f

clean-all: clean
	docker rmi $(IMAGE_NAME) 2>/dev/null || true

# Sauvegarde et restauration
backup:
	@echo "Création de la sauvegarde..."
	docker cp $(CONTAINER_NAME):/app/data/cadets.db ./$(BACKUP_FILE)
	@echo "Sauvegarde créée: $(BACKUP_FILE)"

restore:
	@read -p "Nom du fichier de sauvegarde: " backup_file; \
	docker cp $$backup_file $(CONTAINER_NAME):/app/data/cadets.db && \
	docker restart $(CONTAINER_NAME)

# État du système
status:
	docker-compose ps

health:
	docker exec $(CONTAINER_NAME) curl -f http://localhost:8501/_stcore/health || echo "Service non accessible"

# Commandes de développement
shell:
	docker exec -it $(CONTAINER_NAME) /bin/bash

inspect:
	docker inspect $(CONTAINER_NAME)

# Aide
help:
	@echo "Commandes disponibles:"
	@echo "  build     - Construire l'image Docker"
	@echo "  run       - Lancer l'application en arrière-plan"
	@echo "  dev       - Lancer l'application avec logs visibles"
	@echo "  stop      - Arrêter l'application"
	@echo "  restart   - Redémarrer l'application"
	@echo "  logs      - Afficher les logs en temps réel"
	@echo "  logs-tail - Afficher les 100 dernières lignes de logs"
	@echo "  status    - Afficher l'état des conteneurs"
	@echo "  health    - Vérifier la santé de l'application"
	@echo "  backup    - Sauvegarder la base de données"
	@echo "  restore   - Restaurer une sauvegarde"
	@echo "  shell     - Ouvrir un shell dans le conteneur"
	@echo "  clean     - Nettoyer les conteneurs et volumes"
	@echo "  clean-all - Nettoyage complet (conteneurs, volumes, images)"