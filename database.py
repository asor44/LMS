import os
import pymysql
import logging
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    try:
        required_vars = ['MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing_vars)}. "
                             "Créez un fichier .env avec ces variables.")
        conn = pymysql.connect(
            host=os.getenv('MYSQL_HOST'),
            port=int(os.getenv('MYSQL_PORT')),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE'),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
        return conn
    except pymysql.MySQLError as e:
        raise RuntimeError("Impossible de se connecter à MySQL : " + str(e)) from e

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SET sql_mode = ''")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                status ENUM('parent', 'cadet', 'AMC', 'animateur', 'administration') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS parent_child (
                parent_id INT,
                child_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (parent_id, child_id),
                FOREIGN KEY (parent_id) REFERENCES users(id),
                FOREIGN KEY (child_id) REFERENCES users(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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

        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                activity_id INT,
                user_id INT,
                check_in_time TIMESTAMP,
                qr_code_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (activity_id, user_id),
                FOREIGN KEY (activity_id) REFERENCES activities(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INT AUTO_INCREMENT PRIMARY KEY
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_equipment (
                id INT AUTO_INCREMENT PRIMARY KEY,
                activity_id INT,
                inventory_id INT,
                quantity_required INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (activity_id, inventory_id),
                FOREIGN KEY (activity_id) REFERENCES activities(id),
                FOREIGN KEY (inventory_id) REFERENCES inventory(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_notes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                evaluator_id INT,
                note_date DATE NOT NULL,
                note_type VARCHAR(50) NOT NULL,
                rating INT,
                appreciation TEXT,
                evaluation_type_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (evaluator_id) REFERENCES users(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_types (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                min_rating INT NOT NULL DEFAULT 1,
                max_rating INT NOT NULL DEFAULT 5,
                description TEXT,
                active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("SELECT COUNT(*) AS count FROM evaluation_types")
        if cur.fetchone()["count"] == 0:
            default_types = [
                ('Comportement', 1, 5, 'Évaluation du comportement général'),
                ('Participation', 1, 5, 'Niveau de participation aux activités'),
                ('Leadership', 1, 5, 'Capacités de leadership'),
                ('Technique', 1, 5, 'Compétences techniques'),
                ("Esprit d'équipe", 1, 5, 'Capacité à travailler en équipe')
            ]
            for name, min_rating, max_rating, description in default_types:
                cur.execute("""
                    INSERT IGNORE INTO evaluation_types 
                    (name, min_rating, max_rating, description)
                    VALUES (%s, %s, %s, %s)
                """, (name, min_rating, max_rating, description))

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

        default_roles = [
            ('admin', 'Administrateur système', ['manage_users', 'manage_roles', 'manage_inventory', 'manage_activities', 'view_reports', 'manage_communications', 'manage_attendance']),
            ('animateur', 'Animateur standard', ['manage_activities', 'view_reports', 'manage_attendance']),
            ('parent', 'Parent', ['view_child_attendance', 'view_child_equipment', 'view_child_progression', 'view_activities', 'manage_communications']),
            ('cadet', 'Cadet', ['scan_qr_codes', 'view_activities']),
            ('AMC', 'Aide-Moniteur Cadet', ['scan_qr_codes', 'view_activities'])
        ]

        for role_name, description, permissions in default_roles:
            cur.execute("""
                INSERT IGNORE INTO roles (name, description)
                VALUES (%s, %s)
            """, (role_name, description))
            cur.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
            role_id = cur.fetchone()["id"]
            for perm in permissions:
                cur.execute("""
                    INSERT IGNORE INTO role_permissions (role_id, permission_id)
                    SELECT %s, id FROM permissions WHERE name = %s
                """, (role_id, perm))

        cur.execute("SELECT * FROM users WHERE email = 'admin@admin.com'")
        if not cur.fetchone():
            import hashlib
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            cur.execute("""
                INSERT INTO users (email, password_hash, name, status)
                VALUES (%s, %s, %s, %s)
            """, ('admin@admin.com', password_hash, 'Administrateur', 'administration'))
            cur.execute("SELECT id FROM users WHERE email = 'admin@admin.com'")
            admin_id = cur.fetchone()["id"]
            cur.execute("""
                INSERT INTO user_roles (user_id, role_id)
                SELECT %s, id FROM roles WHERE name = 'admin'
            """, (admin_id,))

        conn.commit()

    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation de la base de données : {str(e)}")
        raise RuntimeError("Une erreur est survenue lors de l'initialisation de la base de données.") from e
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals() and conn:
            conn.close()
