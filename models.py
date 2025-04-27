import database
import hashlib
from typing import List, Optional, Dict, Tuple
import logging

class User:
    def __init__(self, id: int, name: str, email: str, password_hash: str, status: str,
                 first_name: str = None, rank: str = None):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.status = status
        self.first_name = first_name
        self.rank = rank

    @staticmethod
    def get_by_email(email: str) -> Optional['User']:
        """Récupère un utilisateur par son email"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            result = cur.fetchone()
            if result:
                return User(
                    id=result['id'],
                    name=result['name'],
                    email=result['email'],
                    password_hash=result['password_hash'],
                    status=result['status'],
                    first_name=result.get('first_name'),
                    rank=result.get('rank')
                )
            return None
        except Exception as e:
            logging.error(f"Erreur lors de la récupération de l'utilisateur par email : {str(e)}")
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(user_id: int) -> Optional['User']:
        """Récupère un utilisateur par son ID"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            result = cur.fetchone()
            if result:
                return User(
                    id=result['id'],
                    name=result['name'],
                    email=result['email'],
                    password_hash=result['password_hash'],
                    status=result['status'],
                    first_name=result.get('first_name'),
                    rank=result.get('rank')
                )
            return None
        except Exception as e:
            logging.error(f"Erreur lors de la récupération de l'utilisateur par ID : {str(e)}")
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all() -> List['User']:
        """Récupère tous les utilisateurs"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM users ORDER BY name")
            results = cur.fetchall()
            users = []
            for result in results:
                users.append(User(
                    id=result['id'],
                    name=result['name'],
                    email=result['email'],
                    password_hash=result['password_hash'],
                    status=result['status'],
                    first_name=result.get('first_name'),
                    rank=result.get('rank')
                ))
            return users
        except Exception as e:
            logging.error(f"Erreur lors de la récupération de tous les utilisateurs : {str(e)}")
            return []
        finally:
            cur.close()
            conn.close()

    def verify_password(self, password: str) -> bool:
        """Vérifie si le mot de passe fourni correspond au hash stocké"""
        try:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            return hashed_password == self.password_hash
        except Exception as e:
            logging.error(f"Erreur lors de la vérification du mot de passe : {str(e)}")
            return False

class InventoryCategory:
    def __init__(self, id: int, name: str, description: str):
        self.id = id
        self.name = name
        self.description = description

    @staticmethod
    def get_all() -> List['InventoryCategory']:
        """Récupère toutes les catégories d'inventaire"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM inventory_categories ORDER BY name")
            results = cur.fetchall()
            categories = []
            for result in results:
                categories.append(InventoryCategory(
                    id=result['id'],
                    name=result['name'],
                    description=result['description']
                ))
            return categories
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des catégories d'inventaire : {str(e)}")
            return []
        finally:
            cur.close()
            conn.close()

class Inventory:
    def __init__(self, id: int, item_name: str, category_id: int, quantity: int, unit: str, 
                 min_quantity: int = 0, photo_url: str = None):
        self.id = id
        self.item_name = item_name
        self.category_id = category_id
        self.quantity = quantity
        self.unit = unit
        self.min_quantity = min_quantity
        self.photo_url = photo_url

    @staticmethod
    def get_all() -> List['Inventory']:
        """Récupère tous les articles d'inventaire"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT i.*, c.name as category_name 
                FROM inventory i 
                LEFT JOIN inventory_categories c ON i.category_id = c.id 
                ORDER BY i.item_name
            """)
            results = cur.fetchall()
            items = []
            for result in results:
                item = Inventory(
                    id=result['id'],
                    item_name=result['item_name'],
                    category_id=result['category_id'],
                    quantity=result['quantity'],
                    unit=result['unit'],
                    min_quantity=result['min_quantity'],
                    photo_url=result['photo_url']
                )
                item.category_name = result['category_name']
                items.append(item)
            return items
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des articles d'inventaire : {str(e)}")
            return []
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def create(item_name: str, category_id: int, quantity: int, unit: str, 
               min_quantity: int = 0, photo_url: str = None) -> Optional['Inventory']:
        """Crée un nouvel article dans l'inventaire"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO inventory (item_name, category_id, quantity, unit, min_quantity, photo_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (item_name, category_id, quantity, unit, min_quantity, photo_url))
            
            conn.commit()
            result = cur.fetchone()
            if result:
                return Inventory(
                    id=result['id'],
                    item_name=item_name,
                    category_id=category_id,
                    quantity=quantity,
                    unit=unit,
                    min_quantity=min_quantity,
                    photo_url=photo_url
                )
            return None
        except Exception as e:
            conn.rollback()
            logging.error(f"Erreur lors de la création d'un article d'inventaire : {str(e)}")
            return None
        finally:
            cur.close()
            conn.close()

    def update(self, item_name: str = None, category_id: int = None, quantity: int = None, 
               unit: str = None, min_quantity: int = None, photo_url: str = None) -> bool:
        """Met à jour un article d'inventaire"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            # Construire la requête de mise à jour dynamiquement
            update_fields = []
            params = []
            
            if item_name is not None:
                update_fields.append("item_name = %s")
                params.append(item_name)
                self.item_name = item_name
                
            if category_id is not None:
                update_fields.append("category_id = %s")
                params.append(category_id)
                self.category_id = category_id
                
            if quantity is not None:
                update_fields.append("quantity = %s")
                params.append(quantity)
                self.quantity = quantity
                
            if unit is not None:
                update_fields.append("unit = %s")
                params.append(unit)
                self.unit = unit
                
            if min_quantity is not None:
                update_fields.append("min_quantity = %s")
                params.append(min_quantity)
                self.min_quantity = min_quantity
                
            if photo_url is not None:
                update_fields.append("photo_url = %s")
                params.append(photo_url)
                self.photo_url = photo_url
                
            if not update_fields:
                return True  # Rien à mettre à jour
                
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            params.append(self.id)  # Pour la clause WHERE
            
            query = f"""
                UPDATE inventory 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            
            cur.execute(query, params)
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            conn.rollback()
            logging.error(f"Erreur lors de la mise à jour d'un article d'inventaire : {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(item_id: int) -> bool:
        """Supprime un article d'inventaire"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            conn.rollback()
            logging.error(f"Erreur lors de la suppression d'un article d'inventaire : {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()