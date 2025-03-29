import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

def get_connection():
    try:
        # Vérifier si les variables d'environnement sont définies
        required_vars = ['PGHOST', 'PGPORT', 'PGUSER', 'PGPASSWORD', 'PGDATABASE']
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing_vars)}. "
                           "Créez un fichier .env avec ces variables.")

        conn = psycopg2.connect(
            host=os.getenv('PGHOST'),
            port=os.getenv('PGPORT'),
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD'),
            database=os.getenv('PGDATABASE')
        )
        return conn
    except psycopg2.OperationalError as e:
        if "Connection refused" in str(e):
            error_msg = (
                "Impossible de se connecter à PostgreSQL. Assurez-vous que :\n"
                "1. PostgreSQL est installé sur votre machine\n"
                "2. Le service PostgreSQL est démarré\n"
                "3. Les informations de connexion dans le fichier .env sont correctes\n"
                "\nPour installer PostgreSQL :\n"
                "1. Téléchargez-le depuis https://www.postgresql.org/download/\n"
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
        # Create sequences
        cur.execute("""
            DO $$
            BEGIN
                CREATE SEQUENCE IF NOT EXISTS permissions_id_seq;
            EXCEPTION WHEN duplicate_table THEN
                NULL;
            END $$;
        """)

        # Permissions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY DEFAULT nextval('permissions_id_seq'),
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Users table with additional fields
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
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
                parent_id INTEGER REFERENCES users(id),
                child_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (parent_id, child_id),
                CHECK (parent_id != child_id)
            )
        """)

        # Roles table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Role permissions mapping
        cur.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER REFERENCES roles(id),
                permission_id INTEGER REFERENCES permissions(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (role_id, permission_id)
            )
        """)

        # User roles mapping
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER REFERENCES users(id),
                role_id INTEGER REFERENCES roles(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, role_id)
            )
        """)

        # Activities table with QR codes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                max_participants INTEGER NOT NULL,
                entry_qr_code TEXT NOT NULL,
                exit_qr_code TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Attendance records
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                activity_id INTEGER REFERENCES activities(id),
                user_id INTEGER REFERENCES users(id),
                check_in_time TIMESTAMP,
                qr_code_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (activity_id, user_id)
            )
        """)

        # Activity equipment table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_equipment (
                id SERIAL PRIMARY KEY,
                activity_id INTEGER REFERENCES activities(id),
                inventory_id INTEGER REFERENCES inventory(id),
                quantity_required INTEGER NOT NULL CHECK (quantity_required > 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (activity_id, inventory_id)
            )
        """)

        # User notes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_notes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                evaluator_id INTEGER REFERENCES users(id),
                note_date DATE NOT NULL,
                note_type VARCHAR(50) NOT NULL,
                rating INTEGER CHECK (rating BETWEEN 1 AND 5),
                appreciation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Evaluation types table
        cur.execute("""
            DO $$
            BEGIN
                CREATE SEQUENCE IF NOT EXISTS evaluation_types_id_seq;
            EXCEPTION WHEN duplicate_table THEN
                NULL;
            END $$;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_types (
                id INTEGER PRIMARY KEY DEFAULT nextval('evaluation_types_id_seq'),
                name VARCHAR(100) NOT NULL UNIQUE,
                min_rating INTEGER NOT NULL DEFAULT 1,
                max_rating INTEGER NOT NULL DEFAULT 5,
                description TEXT,
                active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (min_rating <= max_rating)
            )
        """)

        # Modify user_notes table to reference evaluation_types
        cur.execute("""
            ALTER TABLE user_notes 
            ADD COLUMN IF NOT EXISTS evaluation_type_id INTEGER 
            REFERENCES evaluation_types(id)
        """)

        # Insert default evaluation types if none exist
        cur.execute("SELECT COUNT(*) FROM evaluation_types")
        if cur.fetchone()[0] == 0:
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
                    ON CONFLICT (name) DO NOTHING
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
                INSERT INTO permissions (name, description)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING
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
            cur.execute("""
                INSERT INTO roles (name, description)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING
                RETURNING id
            """, (role_name, description))

            role_result = cur.fetchone()
            if role_result:
                role_id = role_result[0]
                for perm in permissions:
                    cur.execute("""
                        INSERT INTO role_permissions (role_id, permission_id)
                        SELECT %s, id FROM permissions WHERE name = %s
                        ON CONFLICT DO NOTHING
                    """, (role_id, perm))

        # Create default admin user if it doesn't exist
        cur.execute("SELECT * FROM users WHERE email = 'admin@admin.com'")
        admin_exists = cur.fetchone()

        if not admin_exists:
            import hashlib
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            cur.execute("""
                INSERT INTO users (email, password_hash, name, status)
                VALUES ('admin@admin.com', %s, 'Administrateur', 'administration')
                RETURNING id
            """, (password_hash,))
            admin_id = cur.fetchone()[0]

            # Assign admin role
            cur.execute("""
                INSERT INTO user_roles (user_id, role_id)
                SELECT %s, id FROM roles WHERE name = 'admin'
            """, (admin_id,))

        conn.commit()

    except (RuntimeError, ValueError) as e:
        # Ces erreurs ont déjà des messages détaillés
        raise
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation de la base de données : {str(e)}")
        raise RuntimeError(
            "Une erreur est survenue lors de l'initialisation de la base de données. "
            "Vérifiez que PostgreSQL est correctement installé et configuré."
        ) from e
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals() and conn:
            conn.close()