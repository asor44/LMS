import os
import pymysql
import pymysql.cursors
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

def get_connection():
    try:
        # Vérifier si les variables d'environnement sont définies
        required_vars = ['MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DB']
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        # Essayons aussi avec les variables PG au cas où
        if missing_vars:
            pg_vars = ['PGHOST', 'PGPORT', 'PGUSER', 'PGPASSWORD', 'PGDATABASE']
            mysql_vars = {}
            has_pg_vars = True
            for i, var in enumerate(pg_vars):
                if not os.getenv(var):
                    has_pg_vars = False
                    break
                mysql_vars[required_vars[i]] = os.getenv(var)
            
            if has_pg_vars:
                # Utiliser les variables PG à la place
                logging.info("Utilisation des variables PostgreSQL pour la connexion MySQL")
                conn = pymysql.connect(
                    host=os.getenv('PGHOST'),
                    port=int(os.getenv('PGPORT', 3306)),
                    user=os.getenv('PGUSER'),
                    password=os.getenv('PGPASSWORD'),
                    database=os.getenv('PGDATABASE'),
                    cursorclass=pymysql.cursors.DictCursor
                )
                return conn
            else:
                raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing_vars)}. "
                               "Créez un fichier .env avec ces variables.")

        conn = pymysql.connect(
            host=os.getenv('MYSQL_HOST'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DB'),
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.OperationalError as e:
        if "Can't connect to MySQL server" in str(e):
            error_msg = (
                "Impossible de se connecter à MySQL. Assurez-vous que :\n"
                "1. MySQL est installé sur votre machine\n"
                "2. Le service MySQL est démarré\n"
                "3. Les informations de connexion dans le fichier .env sont correctes\n"
                "\nPour installer MySQL :\n"
                "1. Téléchargez-le depuis https://dev.mysql.com/downloads/\n"
                "2. Suivez les instructions d'installation\n"
                "3. Créez un fichier .env avec les informations de connexion"
            )
            logging.error(error_msg)
            raise RuntimeError(error_msg) from e
        raise

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Permissions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Users table with additional fields
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL CHECK (status IN ('parent', 'cadet', 'AMC', 'animateur', 'administration')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Parent-Child relationship table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS parent_child (
                parent_id INT,
                child_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (parent_id, child_id),
                FOREIGN KEY (parent_id) REFERENCES users(id),
                FOREIGN KEY (child_id) REFERENCES users(id),
                CONSTRAINT check_different_ids CHECK (parent_id != child_id)
            )
        """)

        # Roles table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Role permissions mapping
        cur.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INT,
                permission_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (role_id, permission_id),
                FOREIGN KEY (role_id) REFERENCES roles(id),
                FOREIGN KEY (permission_id) REFERENCES permissions(id)
            )
        """)

        # User roles mapping
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INT,
                role_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (role_id) REFERENCES roles(id)
            )
        """)

        # Activities table with QR codes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                max_participants INT NOT NULL,
                entry_qr_code TEXT NOT NULL,
                exit_qr_code TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Inventory categories table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory_categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Inventory table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_name VARCHAR(255) NOT NULL,
                category_id INT,
                quantity INT NOT NULL DEFAULT 0,
                unit VARCHAR(50) NOT NULL,
                min_quantity INT NOT NULL DEFAULT 0,
                photo_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES inventory_categories(id)
            )
        """)
        
        # Add default inventory category if none exists
        cur.execute("SELECT COUNT(*) as count FROM inventory_categories")
        result = cur.fetchone()
        if result['count'] == 0:
            cur.execute("""
                INSERT INTO inventory_categories (name, description)
                VALUES ('Général', 'Catégorie par défaut pour tous les articles')
            """)
        
        # Attendance records
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                activity_id INT,
                user_id INT,
                check_in_time TIMESTAMP,
                qr_code_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY (activity_id, user_id),
                FOREIGN KEY (activity_id) REFERENCES activities(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Activity equipment table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_equipment (
                id INT AUTO_INCREMENT PRIMARY KEY,
                activity_id INT,
                inventory_id INT,
                quantity_required INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY (activity_id, inventory_id),
                FOREIGN KEY (activity_id) REFERENCES activities(id),
                FOREIGN KEY (inventory_id) REFERENCES inventory(id),
                CONSTRAINT check_quantity_positive CHECK (quantity_required > 0)
            )
        """)

        # User notes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_notes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                evaluator_id INT,
                note_date DATE NOT NULL,
                note_type VARCHAR(50) NOT NULL,
                rating INT,
                appreciation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (evaluator_id) REFERENCES users(id),
                CONSTRAINT check_rating_range CHECK (rating BETWEEN 1 AND 5)
            )
        """)

        # Evaluation types table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_types (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                min_rating INT NOT NULL DEFAULT 1,
                max_rating INT NOT NULL DEFAULT 5,
                description TEXT,
                active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT check_min_max_rating CHECK (min_rating <= max_rating)
            )
        """)

        # Modify user_notes table to reference evaluation_types
        # MySQL doesn't support ADD COLUMN IF NOT EXISTS directly, so we need to check first
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.COLUMNS 
            WHERE TABLE_NAME = 'user_notes' 
            AND COLUMN_NAME = 'evaluation_type_id'
        """)
        result = cur.fetchone()
        if result['count'] == 0:
            cur.execute("""
                ALTER TABLE user_notes 
                ADD COLUMN evaluation_type_id INT,
                ADD FOREIGN KEY (evaluation_type_id) REFERENCES evaluation_types(id)
            """)

        # Insert default evaluation types if none exist
        cur.execute("SELECT COUNT(*) as count FROM evaluation_types")
        result = cur.fetchone()
        if result['count'] == 0:
            default_types = [
                ('Comportement', 1, 5, 'Évaluation du comportement général'),
                ('Participation', 1, 5, 'Niveau de participation aux activités'),
                ('Leadership', 1, 5, 'Capacités de leadership'),
                ('Technique', 1, 5, 'Compétences techniques'),
                ('Esprit d\'équipe', 1, 5, 'Capacité à travailler en équipe')
            ]
            for name, min_rating, max_rating, description in default_types:
                cur.execute("""
                    INSERT INTO evaluation_types 
                    (name, min_rating, max_rating, description)
                    VALUES (%s, %s, %s, %s)
                """, (name, min_rating, max_rating, description))

        # Insert default permissions
        default_permissions = [
            ('manage_users', 'Gérer les utilisateurs'),
            ('manage_roles', 'Gérer les rôles et permissions'),
            ('manage_inventory', 'Gérer les stocks'),
            ('manage_activities', 'Gérer les activités'),
            ('view_reports', 'Voir les rapports'),
            ('manage_communications', 'Gérer les communications'),
            ('manage_attendance', 'Gérer les présences'),
            ('scan_qr_codes', 'Scanner les QR codes de présence'),
            ('view_child_attendance', 'Voir les présences des enfants'),
            ('view_child_equipment', 'Voir les équipements des enfants'),
            ('view_child_progression', 'Voir la progression des enfants'),
            ('view_activities', 'Voir les activités')
        ]

        for perm_name, description in default_permissions:
            cur.execute("""
                INSERT IGNORE INTO permissions (name, description)
                VALUES (%s, %s)
            """, (perm_name, description))

        # Insert default roles with their permissions
        default_roles = [
            ('admin', 'Administrateur système', ['manage_users', 'manage_roles', 'manage_inventory', 'manage_activities', 'view_reports', 'manage_communications', 'manage_attendance']),
            ('animateur', 'Animateur standard', ['manage_activities', 'view_reports', 'manage_attendance']),
            ('parent', 'Parent', ['view_child_attendance', 'view_child_equipment', 'view_child_progression', 'view_activities', 'manage_communications']),
            ('cadet', 'Cadet', ['scan_qr_codes', 'view_activities']),
            ('AMC', 'Aide-Moniteur Cadet', ['scan_qr_codes', 'view_activities'])
        ]

        for role_name, description, permissions in default_roles:
            # Insérer le rôle s'il n'existe pas déjà
            cur.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
            role_result = cur.fetchone()
            
            if not role_result:
                cur.execute("""
                    INSERT INTO roles (name, description)
                    VALUES (%s, %s)
                """, (role_name, description))
                cur.execute("SELECT LAST_INSERT_ID() as id")
                role_result = cur.fetchone()
            
            role_id = role_result['id']
            
            # Ajouter les permissions
            for perm in permissions:
                cur.execute("SELECT id FROM permissions WHERE name = %s", (perm,))
                perm_result = cur.fetchone()
                if perm_result:
                    try:
                        cur.execute("""
                            INSERT IGNORE INTO role_permissions (role_id, permission_id)
                            VALUES (%s, %s)
                        """, (role_id, perm_result['id']))
                    except:
                        pass  # Ignorer si la relation existe déjà

        # Create default admin user if it doesn't exist
        cur.execute("SELECT * FROM users WHERE email = 'admin@admin.com'")
        admin_exists = cur.fetchone()

        if not admin_exists:
            import hashlib
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            cur.execute("""
                INSERT INTO users (email, password_hash, name, status)
                VALUES ('admin@admin.com', %s, 'Administrateur', 'administration')
            """, (password_hash,))
            
            cur.execute("SELECT LAST_INSERT_ID() as id")
            admin_id = cur.fetchone()['id']

            # Assign admin role
            cur.execute("SELECT id FROM roles WHERE name = 'admin'")
            admin_role = cur.fetchone()
            if admin_role:
                try:
                    cur.execute("""
                        INSERT INTO user_roles (user_id, role_id)
                        VALUES (%s, %s)
                    """, (admin_id, admin_role['id']))
                except:
                    pass  # Ignorer si la relation existe déjà

        conn.commit()

    except (RuntimeError, ValueError) as e:
        # Ces erreurs ont déjà des messages détaillés
        raise
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation de la base de données : {str(e)}")
        raise RuntimeError(
            "Une erreur est survenue lors de l'initialisation de la base de données. "
            "Vérifiez que MySQL est correctement installé et configuré."
        ) from e
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals() and conn:
            conn.close()