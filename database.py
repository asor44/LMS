import os
import sqlite3
import logging
import json
from pathlib import Path

# Emplacement de la base de données SQLite
# Utilise /app/data dans Docker, sinon le répertoire local
if os.path.exists('/app/data'):
    DB_PATH = '/app/data/cadets.db'
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cadets.db')

class DictCursor:
    def __init__(self, cursor):
        self.cursor = cursor
    
    def __iter__(self):
        return self
    
    def __next__(self):
        row = self.cursor.__next__()
        if row is None:
            raise StopIteration
        return {
            description[0]: row[i]
            for i, description in enumerate(self.cursor.description)
        }

class Connection:
    def __init__(self, conn):
        self.conn = conn
    
    def cursor(self):
        return Cursor(self.conn.cursor())
    
    def commit(self):
        return self.conn.commit()
    
    def rollback(self):
        return self.conn.rollback()
    
    def close(self):
        return self.conn.close()

class Cursor:
    def __init__(self, cursor):
        self.cursor = cursor
        self.rows = None
    
    def execute(self, query, params=None):
        # Convertir la requête de type PostgreSQL/MySQL en SQLite
        query = query.replace('%s', '?')
        query = query.replace('RETURNING id', '')
        
        if params is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)
        
        return self
    
    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return {
            description[0]: row[i]
            for i, description in enumerate(self.cursor.description)
        }
    
    def fetchall(self):
        rows = self.cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                description[0]: row[i]
                for i, description in enumerate(self.cursor.description)
            })
        return result
    
    def close(self):
        return self.cursor.close()
    
    @property
    def rowcount(self):
        return self.cursor.rowcount
    
    def __iter__(self):
        self.rows = self.fetchall()
        self.index = 0
        return self
    
    def __next__(self):
        if self.rows is None or self.index >= len(self.rows):
            raise StopIteration
        row = self.rows[self.index]
        self.index += 1
        return row

# Emplacement de la base de données SQLite
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cadets.db')

class DictCursor:
    def __init__(self, cursor):
        self.cursor = cursor
    
    def __iter__(self):
        return self
    
    def __next__(self):
        row = self.cursor.__next__()
        if row is None:
            raise StopIteration
        return {
            description[0]: row[i]
            for i, description in enumerate(self.cursor.description)
        }

class Connection:
    def __init__(self, conn):
        self.conn = conn
    
    def cursor(self):
        return Cursor(self.conn.cursor())
    
    def commit(self):
        return self.conn.commit()
    
    def rollback(self):
        return self.conn.rollback()
    
    def close(self):
        return self.conn.close()

class Cursor:
    def __init__(self, cursor):
        self.cursor = cursor
        self.rows = None
    
    def execute(self, query, params=None):
        # Convertir la requête de type PostgreSQL/MySQL en SQLite
        query = query.replace('%s', '?')
        query = query.replace('RETURNING id', '')
        
        if params is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)
        
        return self
    
    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return {
            description[0]: row[i]
            for i, description in enumerate(self.cursor.description)
        }
    
    def fetchall(self):
        rows = self.cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                description[0]: row[i]
                for i, description in enumerate(self.cursor.description)
            })
        return result
    
    def close(self):
        return self.cursor.close()
    
    @property
    def rowcount(self):
        return self.cursor.rowcount
    
    def __iter__(self):
        self.rows = self.fetchall()
        self.index = 0
        return self
    
    def __next__(self):
        if self.rows is None or self.index >= len(self.rows):
            raise StopIteration
        row = self.rows[self.index]
        self.index += 1
        return row

def get_connection():
    try:
        # Créer le répertoire parent si nécessaire
        Path(os.path.dirname(DB_PATH)).mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        return Connection(conn)
    except Exception as e:
        error_msg = (
            f"Impossible de se connecter à la base de données SQLite: {str(e)}\n"
            f"Emplacement de la base de données: {DB_PATH}"
        )
        logging.error(error_msg)
        raise RuntimeError(error_msg) from e

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Permissions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Users table with additional fields
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('parent', 'cadet', 'AMC', 'animateur', 'administration')),
                first_name TEXT,
                rank TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Parent-Child relationship table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS parent_child (
                parent_id INTEGER,
                child_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (parent_id, child_id),
                FOREIGN KEY (parent_id) REFERENCES users(id),
                FOREIGN KEY (child_id) REFERENCES users(id),
                CHECK (parent_id != child_id)
            )
        """)

        # Roles table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Role permissions mapping
        cur.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER,
                permission_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (role_id, permission_id),
                FOREIGN KEY (role_id) REFERENCES roles(id),
                FOREIGN KEY (permission_id) REFERENCES permissions(id)
            )
        """)

        # User roles mapping
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER,
                role_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (role_id) REFERENCES roles(id)
            )
        """)

        # Activities table with QR codes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
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

        # Inventory categories table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory_categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Inventory table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY,
                item_name TEXT NOT NULL,
                category_id INTEGER,
                quantity INTEGER NOT NULL DEFAULT 0,
                unit TEXT NOT NULL,
                min_quantity INTEGER NOT NULL DEFAULT 0,
                photo_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES inventory_categories(id)
            )
        """)
        
        # Add default inventory category if none exists
        cur.execute("SELECT COUNT(*) as count FROM inventory_categories")
        result = cur.fetchone()
        if result and result['count'] == 0:
            cur.execute("""
                INSERT INTO inventory_categories (name, description)
                VALUES (?, ?)
            """, ('Général', 'Catégorie par défaut pour tous les articles'))
        
        # Attendance records
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY,
                activity_id INTEGER,
                user_id INTEGER,
                check_in_time TIMESTAMP,
                qr_code_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (activity_id, user_id),
                FOREIGN KEY (activity_id) REFERENCES activities(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Activity equipment table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_equipment (
                id INTEGER PRIMARY KEY,
                activity_id INTEGER,
                inventory_id INTEGER,
                quantity_required INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (activity_id, inventory_id),
                FOREIGN KEY (activity_id) REFERENCES activities(id),
                FOREIGN KEY (inventory_id) REFERENCES inventory(id),
                CHECK (quantity_required > 0)
            )
        """)

        # Evaluation types table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_types (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                min_rating INTEGER NOT NULL DEFAULT 1,
                max_rating INTEGER NOT NULL DEFAULT 5,
                description TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (min_rating <= max_rating)
            )
        """)

        # User notes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_notes (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                evaluator_id INTEGER,
                note_date DATE NOT NULL,
                note_type TEXT NOT NULL,
                rating INTEGER CHECK (rating BETWEEN 1 AND 5),
                appreciation TEXT,
                evaluation_type_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (evaluator_id) REFERENCES users(id),
                FOREIGN KEY (evaluation_type_id) REFERENCES evaluation_types(id)
            )
        """)

        # Insert default evaluation types if none exist
        cur.execute("SELECT COUNT(*) as count FROM evaluation_types")
        result = cur.fetchone()
        if result and result['count'] == 0:
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
                    VALUES (?, ?, ?, ?)
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
            # Use OR IGNORE for SQLite instead of INSERT IGNORE
            cur.execute("""
                INSERT OR IGNORE INTO permissions (name, description)
                VALUES (?, ?)
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
            cur.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
            role_result = cur.fetchone()
            
            if not role_result:
                cur.execute("""
                    INSERT INTO roles (name, description)
                    VALUES (?, ?)
                """, (role_name, description))
                
                # En SQLite, utiliser sqlite_last_insert_rowid() ou juste SELECT last_insert_rowid()
                cur.execute("SELECT last_insert_rowid() as id")
                role_result = cur.fetchone()
            
            if role_result:
                role_id = role_result['id']
                
                # Ajouter les permissions
                for perm in permissions:
                    cur.execute("SELECT id FROM permissions WHERE name = ?", (perm,))
                    perm_result = cur.fetchone()
                    if perm_result:
                        try:
                            cur.execute("""
                                INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                                VALUES (?, ?)
                            """, (role_id, perm_result['id']))
                        except Exception as e:
                            logging.warning(f"Erreur lors de l'ajout de la permission {perm} au rôle {role_name}: {str(e)}")

        # Create default admin user if it doesn't exist
        cur.execute("SELECT * FROM users WHERE email = 'admin@admin.com'")
        admin_exists = cur.fetchone()

        if not admin_exists:
            import hashlib
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            cur.execute("""
                INSERT INTO users (email, password_hash, name, status)
                VALUES (?, ?, ?, ?)
            """, ('admin@admin.com', password_hash, 'Administrateur', 'administration'))
            
            # Get the last inserted id
            cur.execute("SELECT last_insert_rowid() as id")
            admin_id_row = cur.fetchone()
            if admin_id_row:
                admin_id = admin_id_row['id']

                # Assign admin role
                cur.execute("SELECT id FROM roles WHERE name = 'admin'")
                admin_role = cur.fetchone()
                if admin_role:
                    try:
                        cur.execute("""
                            INSERT OR IGNORE INTO user_roles (user_id, role_id)
                            VALUES (?, ?)
                        """, (admin_id, admin_role['id']))
                    except Exception as e:
                        logging.warning(f"Erreur lors de l'ajout du rôle admin à l'utilisateur admin: {str(e)}")

        conn.commit()
        logging.info("Base de données SQLite initialisée avec succès!")

    except (RuntimeError, ValueError) as e:
        # Ces erreurs ont déjà des messages détaillés
        raise
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation de la base de données : {str(e)}")
        raise RuntimeError(
            f"Une erreur est survenue lors de l'initialisation de la base de données SQLite: {str(e)}"
        ) from e
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals() and conn:
            conn.close()