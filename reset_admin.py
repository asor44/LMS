import os
import hashlib
import psycopg2
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connexion à la base de données
def get_connection():
    try:
        # Utilisation directe des variables d'environnement de Replit
        conn = psycopg2.connect(
            host=os.environ.get('PGHOST', 'localhost'),
            port=os.environ.get('PGPORT', '5432'),
            user=os.environ.get('PGUSER', 'postgres'),
            password=os.environ.get('PGPASSWORD', ''),
            database=os.environ.get('PGDATABASE', 'cadets_db')
        )
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Erreur de connexion à la base de données: {e}")
        raise

def reset_admin():
    # Nouvelles informations d'identification pour l'administrateur
    admin_email = "admin@example.com"
    admin_password = "admin123"
    admin_name = "Administrateur"
    
    # Hachage du mot de passe (même méthode que dans le modèle User)
    hashed_password = hashlib.sha256(admin_password.encode()).hexdigest()
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Vérifier si l'utilisateur existe déjà
        cur.execute("SELECT id FROM users WHERE email = %s", (admin_email,))
        user_data = cur.fetchone()
        
        if user_data:
            # Mise à jour de l'utilisateur existant
            user_id = user_data[0]
            cur.execute("""
                UPDATE users 
                SET password_hash = %s, name = %s, status = 'administration'
                WHERE id = %s
                RETURNING id
            """, (hashed_password, admin_name, user_id))
            logger.info(f"Utilisateur administrateur mis à jour avec l'ID: {user_id}")
        else:
            # Création d'un nouvel utilisateur administrateur
            cur.execute("""
                INSERT INTO users (email, password_hash, name, status)
                VALUES (%s, %s, %s, 'administration')
                RETURNING id
            """, (admin_email, hashed_password, admin_name))
            user_id = cur.fetchone()[0]
            logger.info(f"Nouvel utilisateur administrateur créé avec l'ID: {user_id}")
        
        # Vérifier si le rôle admin existe
        cur.execute("SELECT id FROM roles WHERE name = 'admin'")
        role_data = cur.fetchone()
        
        if not role_data:
            # Créer le rôle admin s'il n'existe pas
            cur.execute("""
                INSERT INTO roles (name, description)
                VALUES ('admin', 'Rôle administrateur avec tous les droits')
                RETURNING id
            """)
            role_id = cur.fetchone()[0]
            logger.info(f"Rôle admin créé avec l'ID: {role_id}")
        else:
            role_id = role_data[0]
        
        # Attribuer le rôle admin à l'utilisateur (en supprimant d'abord toute association existante)
        cur.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
        cur.execute("""
            INSERT INTO user_roles (user_id, role_id)
            VALUES (%s, %s)
            ON CONFLICT (user_id, role_id) DO NOTHING
        """, (user_id, role_id))
        
        # Valider les modifications
        conn.commit()
        
        logger.info(f"Compte administrateur configuré avec succès:")
        logger.info(f"Email: {admin_email}")
        logger.info(f"Mot de passe: {admin_password}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur lors de la réinitialisation du compte admin: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    reset_admin()
    print("==============================================")
    print("    RÉINITIALISATION DU COMPTE ADMIN")
    print("==============================================")
    print("Nouvelles informations de connexion:")
    print("Email: admin@example.com")
    print("Mot de passe: admin123")
    print("==============================================")
    print("Vous pouvez maintenant vous connecter avec ces identifiants.")