import database
from typing import Optional, List
from datetime import datetime, time
import hashlib

class Inventory:
    def __init__(self, id: int, item_name: str, category: str, quantity: int, unit: str, min_quantity: int = 0, photo_url: str = None):
        self.id = id
        self.item_name = item_name
        self.category = category
        self.quantity = quantity
        self.unit = unit
        self.min_quantity = min_quantity
        self.photo_url = photo_url

    @staticmethod
    def update_quantity(item_id: int, new_quantity: int) -> bool:
        """Update the quantity of an inventory item."""
        if new_quantity < 0:
            return False

        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE inventory 
                SET quantity = %s 
                WHERE id = %s
                RETURNING id
            """, (new_quantity, item_id))

            result = cur.fetchone() is not None
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            print(f"Error updating quantity: {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()
            
    @staticmethod
    def update_photo_url(item_id: int, photo_data) -> bool:
        """
        Met à jour la photo d'un article d'inventaire.
        photo_data peut être:
        - une URL (str)
        - des données binaires d'image (bytes)
        - None pour supprimer la photo
        """
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE inventory 
                SET photo_url = %s 
                WHERE id = %s
                RETURNING id
            """, (photo_data, item_id))

            result = cur.fetchone() is not None
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            print(f"Error updating photo: {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()
            
    @staticmethod
    def remove_photo(item_id: int) -> bool:
        """
        Supprime la photo d'un article d'inventaire.
        """
        return Inventory.update_photo_url(item_id, None)

    @staticmethod
    def create(item_name: str, category: str, quantity: int, unit: str, min_quantity: int = 0, photo_data = None) -> Optional['Inventory']:
        """
        Crée un nouvel article dans l'inventaire
        photo_data peut être soit une URL (str) soit des données binaires d'image (bytes)
        """
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO inventory (item_name, category, quantity, unit, min_quantity, photo_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, item_name, category, quantity, unit, min_quantity, photo_url
            """, (item_name, category, quantity, unit, min_quantity, photo_data))
            conn.commit()
            if (data := cur.fetchone()) is not None:
                return Inventory(*data)
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all() -> List['Inventory']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, item_name, category, quantity, unit, min_quantity, photo_url
                FROM inventory
                ORDER BY category, item_name
            """)
            return [Inventory(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()
            
    @staticmethod
    def get_by_parent(parent_id: int) -> List['Inventory']:
        """Get inventory items assigned to children of a parent user"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT i.id, i.item_name, i.category, ea.quantity, i.unit, i.min_quantity, i.photo_url
                FROM inventory i
                JOIN equipment_assignments ea ON i.id = ea.inventory_id
                JOIN parent_child pc ON ea.user_id = pc.child_id
                WHERE pc.parent_id = %s AND ea.returned_at IS NULL
                ORDER BY i.category, i.item_name
            """, (parent_id,))
            return [Inventory(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(item_id: int) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM inventory WHERE id = %s RETURNING id", (item_id,))
            conn.commit()
            return cur.fetchone() is not None
        except Exception as e:
            conn.rollback()
            print(f"Error deleting item: {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()

class InventoryCategory:
    def __init__(self, id: int, name: str, description: str):
        self.id = id
        self.name = name
        self.description = description
        self.fields = []  # Will be populated with CategoryField objects

    @staticmethod
    def create(name: str, description: str) -> Optional['InventoryCategory']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO inventory_categories (name, description)
                VALUES (%s, %s)
                RETURNING id, name, description
            """, (name, description))
            conn.commit()
            if (data := cur.fetchone()) is not None:
                category = InventoryCategory(*data)
                category.fields = CategoryField.get_for_category(category.id)
                return category
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all() -> List['InventoryCategory']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, description
                FROM inventory_categories
                ORDER BY name
            """)
            categories = [InventoryCategory(*row) for row in cur.fetchall()]
            for category in categories:
                category.fields = CategoryField.get_for_category(category.id)
            return categories
        finally:
            cur.close()
            conn.close()

    def update(self, new_name: str, new_description: str) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE inventory_categories
                SET name = %s, description = %s
                WHERE id = %s
                RETURNING id
            """, (new_name, new_description, self.id))
            conn.commit()
            success = cur.fetchone() is not None
            if success:
                self.name = new_name
                self.description = new_description
            return success
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(category_id: int) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM inventory_categories WHERE id = %s RETURNING id", (category_id,))
            conn.commit()
            return cur.fetchone() is not None
        except Exception as e:
            conn.rollback()
            print(f"Error deleting category: {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()

class CategoryField:
    def __init__(self, id: int, category_id: int, field_name: str, field_type: str, required: bool):
        self.id = id
        self.category_id = category_id
        self.field_name = field_name
        self.field_type = field_type
        self.required = required

    @staticmethod
    def create(category_id: int, field_name: str, field_type: str, required: bool) -> Optional['CategoryField']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO category_fields (category_id, field_name, field_type, required)
                VALUES (%s, %s, %s, %s)
                RETURNING id, category_id, field_name, field_type, required
            """, (category_id, field_name, field_type, required))
            conn.commit()
            if (data := cur.fetchone()) is not None:
                return CategoryField(*data)
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_for_category(category_id: int) -> List['CategoryField']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, category_id, field_name, field_type, required
                FROM category_fields
                WHERE category_id = %s
                ORDER BY field_name
            """, (category_id,))
            return [CategoryField(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def update(self, field_name: str, field_type: str, required: bool) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE category_fields
                SET field_name = %s, field_type = %s, required = %s
                WHERE id = %s
                RETURNING id
            """, (field_name, field_type, required, self.id))
            conn.commit()
            success = cur.fetchone() is not None
            if success:
                self.field_name = field_name
                self.field_type = field_type
                self.required = required
            return success
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(field_id: int) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM category_fields WHERE id = %s RETURNING id", (field_id,))
            conn.commit()
            return cur.fetchone() is not None
        except Exception as e:
            conn.rollback()
            print(f"Error deleting field: {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()

class EquipmentAssignment:
    def __init__(self, id: int, inventory_id: int, user_id: int, quantity: int, assigned_at: datetime):
        self.id = id
        self.inventory_id = inventory_id
        self.user_id = user_id
        self.quantity = quantity
        self.assigned_at = assigned_at

    @staticmethod
    def assign_to_user(inventory_id: int, user_id: int, quantity: int) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            # Vérifier si l'équipement est disponible en quantité suffisante
            cur.execute("SELECT quantity FROM inventory WHERE id = %s", (inventory_id,))
            current_stock = cur.fetchone()
            if not current_stock or current_stock[0] < quantity:
                raise ValueError("Stock insuffisant")

            # Créer l'assignation
            cur.execute("""
                INSERT INTO equipment_assignments (inventory_id, user_id, quantity, assigned_at)
                VALUES (%s, %s, %s, NOW())
                RETURNING id, inventory_id, user_id, quantity, assigned_at
            """, (inventory_id, user_id, quantity))

            # Mettre à jour le stock
            new_quantity = current_stock[0] - quantity
            cur.execute("""
                UPDATE inventory
                SET quantity = %s
                WHERE id = %s
            """, (new_quantity, inventory_id))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_user_assignments(user_id: int) -> List['EquipmentAssignment']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, inventory_id, user_id, quantity, assigned_at
                FROM equipment_assignments
                WHERE user_id = %s AND returned_at IS NULL
                ORDER BY assigned_at DESC
            """, (user_id,))
            return [EquipmentAssignment(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def return_equipment(self) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            # Marquer l'équipement comme retourné
            cur.execute("""
                UPDATE equipment_assignments
                SET returned_at = NOW()
                WHERE id = %s AND returned_at IS NULL
                RETURNING id
            """, (self.id,))

            if cur.fetchone() is None:
                return False

            # Remettre la quantité en stock
            cur.execute("""
                UPDATE inventory
                SET quantity = quantity + %s
                WHERE id = %s
            """, (self.quantity, self.inventory_id))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error returning equipment: {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()

class EquipmentRequest:
    def __init__(self, id: int, user_id: int, equipment_id: int, request_type: str, quantity: int, 
                 reason: str, status: str, created_at: datetime, processed_at: Optional[datetime] = None,
                 processed_by: Optional[int] = None, rejection_reason: Optional[str] = None):
        self.id = id
        self.user_id = user_id
        self.equipment_id = equipment_id
        self.request_type = request_type
        self.quantity = quantity
        self.reason = reason
        self.status = status
        self.created_at = created_at
        self.processed_at = processed_at
        self.processed_by = processed_by
        self.rejection_reason = rejection_reason

    @staticmethod
    def create(user_id: int, equipment_id: int, request_type: str, quantity: int, 
               reason: str, status: str = 'pending') -> Optional['EquipmentRequest']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO equipment_requests 
                (user_id, equipment_id, request_type, quantity, reason, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                RETURNING id, user_id, equipment_id, request_type, quantity, reason, status, created_at,
                          processed_at, processed_by, rejection_reason
            """, (user_id, equipment_id, request_type, quantity, reason, status))
            conn.commit()
            if (data := cur.fetchone()) is not None:
                return EquipmentRequest(*data)
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_pending_requests() -> List['EquipmentRequest']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, user_id, equipment_id, request_type, quantity, reason,
                       status, created_at, processed_at, processed_by, rejection_reason
                FROM equipment_requests
                WHERE status = 'pending'
                ORDER BY created_at DESC
            """)
            return [EquipmentRequest(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def approve(self) -> tuple[bool, str]:
        try:
            # Assigner l'équipement à l'utilisateur
            EquipmentAssignment.assign_to_user(self.equipment_id, self.user_id, self.quantity)

            # Mettre à jour le statut de la demande
            conn = database.get_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE equipment_requests
                    SET status = 'approved', processed_at = NOW()
                    WHERE id = %s
                    RETURNING id
                """, (self.id,))
                conn.commit()
                return True, "Demande approuvée et équipement assigné avec succès"
            finally:
                cur.close()
                conn.close()
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Erreur lors de l'approbation: {str(e)}"

    def reject(self, reason: str) -> tuple[bool, str]:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE equipment_requests
                SET status = 'rejected', processed_at = NOW(), rejection_reason = %s
                WHERE id = %s
                RETURNING id
            """, (reason, self.id))
            conn.commit()
            return True, "Demande rejetée avec succès"
        except Exception as e:
            conn.rollback()
            return False, f"Erreur lors du rejet: {str(e)}"
        finally:
            cur.close()
            conn.close()

class User:
    def __init__(self, id: int, name: str, email: str, password_hash: str, status: str, 
                 first_name: str = None, rank: str = None):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.status = status
        self.first_name = first_name or ""  # Default to empty string if None
        self.rank = rank or ""  # Default to empty string if None

    def get_available_recipients(self) -> List['User']:
        """Retourne la liste des utilisateurs disponibles comme destinataires de messages"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            if self.status == 'parent':
                # Les parents peuvent envoyer des messages à leurs enfants
                return self.get_children()
            elif self.status == 'administration' or self.has_role('manage_communications'):
                # Les administrateurs peuvent envoyer des messages à tout le monde
                return User.get_all()
            else:
                # Les autres utilisateurs peuvent envoyer des messages aux utilisateurs 
                # de même statut et aux animateurs/administrateurs
                cur.execute("""
                    SELECT DISTINCT u.id, u.name, u.email, u.password_hash, u.status
                    FROM users u
                    WHERE u.status IN ('administration', 'animateur')
                    OR u.status = %s
                    ORDER BY u.name
                """, (self.status,))
                return [User(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_email(email: str) -> Optional['User']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, email, password_hash, status, first_name, rank
                FROM users
                WHERE email = %s
            """, (email,))
            if (data := cur.fetchone()) is not None:
                return User(*data)
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(user_id: int) -> Optional['User']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, email, password_hash, status, first_name, rank
                FROM users
                WHERE id = %s
            """, (user_id,))
            if (data := cur.fetchone()) is not None:
                return User(*data)
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all() -> List['User']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, email, password_hash, status, first_name, rank
                FROM users
                ORDER BY name
            """)
            return [User(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()
            
    @staticmethod
    def get_all_by_status(statuses: List[str]) -> List['User']:
        """Récupère tous les utilisateurs ayant un statut dans la liste fournie"""
        if not statuses:
            return []
            
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            # Construire la requête avec des paramètres pour tous les statuts
            placeholders = ', '.join(['%s'] * len(statuses))
            query = f"""
                SELECT id, name, email, password_hash, status, first_name, rank
                FROM users
                WHERE status IN ({placeholders})
                ORDER BY name
            """
            cur.execute(query, statuses)
            return [User(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def update(self, name: str, email: str, status: str, roles: List[str], 
              first_name: str = None, rank: str = None, password: str = None) -> bool:
        """Update user information and roles"""
        if not name or not email or not status:
            return False

        conn = database.get_connection()
        cur = conn.cursor()
        try:
            # Start with basic user info update
            update_query = """
                UPDATE users 
                SET name = %s, email = %s, status = %s, 
                    first_name = %s, rank = %s
            """
            params = [name, email, status, first_name, rank]

            # Add password update if provided
            if password:
                update_query += ", password_hash = %s"
                params.append(hashlib.sha256(password.encode()).hexdigest())

            update_query += " WHERE id = %s RETURNING id"
            params.append(self.id)

            cur.execute(update_query, params)

            if cur.fetchone() is None:
                conn.rollback()
                return False

            # Update roles if provided
            if roles is not None:
                # Remove existing roles
                cur.execute("DELETE FROM user_roles WHERE user_id = %s", (self.id,))

                # Add new roles
                for role_name in roles:
                    cur.execute("""
                        INSERT INTO user_roles (user_id, role_id)
                        SELECT %s, id FROM roles WHERE name = %s
                    """, (self.id, role_name))

            # Update object attributes
            self.name = name
            self.email = email
            self.status = status
            self.first_name = first_name
            self.rank = rank
            if password:
                self.password_hash = hashlib.sha256(password.encode()).hexdigest()

            conn.commit()
            return True

        except Exception as e:
            print(f"Error updating user: {str(e)}")
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def verify_password(self, password: str) -> bool:
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return self.password_hash == hashed

    def has_role(self, role_name: str) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT EXISTS(
                    SELECT 1 
                    FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.user_id = %s AND r.name = %s
                )
            """, (self.id, role_name))
            return cur.fetchone()[0]
        finally:
            cur.close()
            conn.close()
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission through any of their roles"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT EXISTS(
                    SELECT 1 
                    FROM user_roles ur
                    JOIN role_permissions rp ON ur.role_id = rp.role_id
                    JOIN permissions p ON rp.permission_id = p.id
                    WHERE ur.user_id = %s AND p.name = %s
                )
            """, (self.id, permission_name))
            return cur.fetchone()[0]
        finally:
            cur.close()
            conn.close()

    def get_children(self) -> List['User']:
        """Récupérer les enfants d'un parent."""
        if self.status != 'parent':
            return []

        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT u.id, u.name, u.email, u.password_hash, u.status
                FROM users u
                JOIN parent_child pc ON u.id = pc.child_id
                WHERE pc.parent_id = %s
                ORDER BY u.name
            """, (self.id,))
            return [User(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def get_points(self) -> dict:
        """Calculate user points and level based on their activities and notes."""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            # Get points from notes (rating 1-5 = 2-10 points)
            cur.execute("""
                SELECT COALESCE(SUM(rating * 2), 0)
                FROM user_notes
                WHERE user_id = %s
            """, (self.id,))
            note_points = cur.fetchone()[0]

            # Get points from attendance (10 points per attendance)
            cur.execute("""
                SELECT COUNT(*) * 10
                FROM attendance
                WHERE user_id = %s
            """, (self.id,))
            attendance_points = cur.fetchone()[0]

            total_points = note_points + attendance_points

            # Calculate level: level N requires (N*10)^2 points
            # So if you have 100 points, you're level 1 (requires 100 points)
            # Level 2 requires 400 points, level 3 requires 900 points, etc.
            level = int((total_points ** 0.5) / 10)  # Integer division to get current level

            return {
                "points": int(total_points),
                "level": max(1, level)  # Minimum level is 1
            }
        finally:
            cur.close()
            conn.close()

    def get_badges(self) -> List['Badge']:
        """Get all badges earned by the user based on points."""
        points_info = self.get_points()
        total_points = points_info["points"]

        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, description, icon_name, points_required
                FROM badges
                WHERE points_required <= %s
                ORDER BY points_required DESC
            """, (total_points,))
            return [Badge(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()
            
    def get_notes(self, start_date=None, end_date=None) -> List[dict]:
        """Get notes for this user with optional date filtering"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            query = """
                SELECT n.id, n.user_id, n.note_date, n.note_type, n.rating, n.appreciation, 
                       n.evaluator_id, u.name as evaluator_name
                FROM user_notes n
                JOIN users u ON n.evaluator_id = u.id
                WHERE n.user_id = %s
            """
            
            params = [self.id]
            
            if start_date:
                query += " AND n.note_date >= %s"
                params.append(start_date)
                
            if end_date:
                query += " AND n.note_date <= %s"
                params.append(end_date)
                
            query += " ORDER BY n.note_date DESC"
            
            cur.execute(query, params)
            
            notes = []
            for row in cur.fetchall():
                notes.append({
                    "id": row[0],
                    "user_id": row[1],
                    "date": row[2],
                    "type": row[3],
                    "rating": row[4],
                    "appreciation": row[5],
                    "evaluator_id": row[6],
                    "evaluator_name": row[7]
                })
            return notes
        finally:
            cur.close()
            conn.close()
            
    def add_note(self, date, note_type, rating, appreciation, evaluator_id):
        """Add a note for this user"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO user_notes (user_id, note_date, note_type, rating, appreciation, evaluator_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (self.id, date, note_type, rating, appreciation, evaluator_id))
            conn.commit()
            return cur.fetchone()[0]
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
            
    def delete_note(self, note_id):
        """Delete a note for this user"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                DELETE FROM user_notes 
                WHERE id = %s AND user_id = %s
                RETURNING id
            """, (note_id, self.id))
            conn.commit()
            return cur.fetchone() is not None
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def get_permissions(self) -> List[str]:
        """Get all permissions for this user through their roles"""
        permissions = []
        roles = self.get_roles()
        for role_name in roles:
            role = Role.get_by_name(role_name) 
            if role:
                permissions.extend(role.get_permissions())
        return permissions

    def get_roles(self) -> List[str]:
        """Get all roles for this user"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT DISTINCT r.name
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                WHERE u.id = %s
            """, (self.id,))
            return [row[0] for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

class Activity:
    def __init__(self, id: int, name: str, description: str, date: datetime, start_time: time,
                 end_time: time, max_participants: int, location: str = None,
                 lunch_included: bool = False, dinner_included: bool = False):
        self.id = id
        self.name = name
        self.description = description
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.max_participants = max_participants
        self.location = location
        self.lunch_included = lunch_included
        self.dinner_included = dinner_included

    @staticmethod
    def create(name: str, description: str, date: datetime, start_time: time,
               end_time: time, max_participants: int, location: str = None,
               lunch_included: bool = False, dinner_included: bool = False) -> Optional['Activity']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO activities (
                    name, description, date, start_time, end_time,
                    max_participants, location, lunch_included, dinner_included
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name, description, date, start_time, end_time,
                          max_participants, location, lunch_included, dinner_included
            """, (name, description, date, start_time, end_time,
                  max_participants, location, lunch_included, dinner_included))
            conn.commit()
            if (data := cur.fetchone()) is not None:
                return Activity(*data)
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all() -> List['Activity']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, description, date, start_time, end_time,
                       max_participants, location, lunch_included, dinner_included
                FROM activities
                ORDER BY date DESC, start_time ASC
            """)
            return [Activity(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def update(self, name: str, description: str, date: datetime, start_time: time,
               end_time: time, max_participants: int, location: str = None,
               lunch_included: bool = False, dinner_included: bool = False) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE activities
                SET name = %s, description = %s, date = %s, start_time = %s,
                    end_time = %s, max_participants = %s, location = %s,
                    lunch_included = %s, dinner_included = %s
                WHERE id = %s
                RETURNING id
            """, (name, description, date, start_time, end_time,
                  max_participants, location, lunch_included, dinner_included, self.id))
            conn.commit()
            success = cur.fetchone() is not None
            if success:
                self.name = name
                self.description = description
                self.date = date
                self.start_time = start_time
                self.end_time = end_time
                self.max_participants = max_participants
                self.location = location
                self.lunch_included = lunch_included
                self.dinner_included = dinner_included
            return success
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(activity_id: int) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM activities WHERE id = %s RETURNING id", (activity_id,))
            conn.commit()
            return cur.fetchone() is not None
        except Exception as e:
            conn.rollback()
            print(f"Error deleting activity: {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()

    def get_attendance_list(self) -> List[int]:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT user_id
                FROM activity_attendance
                WHERE activity_id = %s
            """, (self.id,))
            return [row[0] for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def get_required_equipment(self) -> List[tuple]:
        """Returns list of tuples (equipment_id, item_name, unit, quantity)"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT ae.inventory_id, i.item_name, i.unit, ae.quantity_required,
                       i.quantity as available_quantity
                FROM activity_equipment ae
                JOIN inventory i ON i.id = ae.inventory_id
                WHERE ae.activity_id = %s
            """, (self.id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def update_equipment(self, equipment_list: List[tuple]) -> bool:
        """Update required equipment for activity
        equipment_list: list of tuples (equipment_id, quantity_required)
        """
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            # Remove existing equipment assignments
            cur.execute("DELETE FROM activity_equipment WHERE activity_id = %s", (self.id,))

            # Add new equipment assignments
            for equipment_id, quantity in equipment_list:
                cur.execute("""
                    INSERT INTO activity_equipment (activity_id, equipment_id, quantity_required)
                    VALUES (%s, %s, %s)
                """, (self.id, equipment_id, quantity))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating equipment: {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()

class Badge:
    def __init__(self, id: int, name: str, description: str, icon_name: str, points_required: int):
        self.id = id
        self.name = name
        self.description = description
        self.icon_name = icon_name
        self.points_required = points_required

    @staticmethod
    def get_all() -> List['Badge']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, description, icon_name, points_required
                FROM badges
                ORDER BY points_required
            """)
            return [Badge(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def create(name: str, description: str, icon_name: str, points_required: int) -> Optional['Badge']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO badges (name, description, icon_name, points_required)
                VALUES (%s, %s, %s, %s)
                RETURNING id, name, description, icon_name, points_required
            """, (name, description, icon_name, points_required))
            conn.commit()
            if (data := cur.fetchone()) is not None:
                return Badge(*data)
            return None
        finally:
            cur.close()
            conn.close()

class EvaluationType:
    def __init__(self, id: int, name: str, min_rating: int, max_rating: int, 
                 description: str, active: bool = True):
        self.id = id
        self.name = name
        self.min_rating = min_rating
        self.max_rating = max_rating
        self.description = description
        self.active = active

    @staticmethod
    def create(name: str, min_rating: int, max_rating: int, 
              description: str = None, active: bool = True) -> Optional['EvaluationType']:
        if min_rating > max_rating:
            raise ValueError("min_rating cannot be greater than max_rating")

        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO evaluation_types (name, min_rating, max_rating, description, active)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, name, min_rating, max_rating, description, active
            """, (name, min_rating, max_rating, description, active))
            conn.commit()
            if (data := cur.fetchone()) is not None:
                return EvaluationType(*data)
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all(active_only: bool = True) -> List['EvaluationType']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            if active_only:
                cur.execute("""
                    SELECT id, name, min_rating, max_rating, description, active
                    FROM evaluation_types
                    WHERE active = true
                    ORDER BY name
                """)
            else:
                cur.execute("""
                    SELECT id, name, min_rating, max_rating, description, active
                    FROM evaluation_types                    ORDER BY name
                """)
            return [EvaluationType(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def update(self, name: str = None, min_rating: int = None, 
               max_rating: int = None, description: str = None, 
               active: bool = None) -> bool:
        """Update evaluation type fields"""
        update_fields = []
        values = []

        if name is not None:
            update_fields.append("name = %s")
            values.append(name)
        if min_rating is not None:
            update_fields.append("min_rating = %s")
            values.append(min_rating)
        if max_rating is not None:
            update_fields.append("max_rating = %s")
            values.append(max_rating)
        if description is not None:
            update_fields.append("description = %s")
            values.append(description)
        if active is not None:
            update_fields.append("active = %s")
            values.append(active)

        if not update_fields:
            return True

        query = """
            UPDATE evaluation_types
            SET {}
            WHERE id = %s
            RETURNING id
        """.format(", ".join(update_fields))
        values.append(self.id)

        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query, values)
            conn.commit()
            success = cur.fetchone() is not None
            if success:
                if name is not None:
                    self.name = name
                if min_rating is not None:
                    self.min_rating = min_rating
                if max_rating is not None:
                    self.max_rating = max_rating
                if description is not None:
                    self.description = description
                if active is not None:
                    self.active = active
            return success
        except Exception as e:
            conn.rollback()
            print(f"Error updating evaluation type: {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(eval_type_id: int) -> Optional['EvaluationType']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, min_rating, max_rating, description, active
                FROM evaluation_types
                WHERE id = %s
            """, (eval_type_id,))
            if (data := cur.fetchone()) is not None:
                return EvaluationType(*data)
            return None
        finally:
            cur.close()
            conn.close()

class Permission:
    def __init__(self, id: int, name: str, description: str = None):
        self.id = id
        self.name = name
        self.description = description

    @staticmethod
    def get_all() -> List['Permission']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, description
                FROM permissions
                ORDER BY name
            """)
            return [Permission(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(permission_id: int) -> Optional['Permission']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, description
                FROM permissions
                WHERE id = %s
            """, (permission_id,))
            if (data := cur.fetchone()) is not None:
                return Permission(*data)
            return None
        finally:
            cur.close()
            conn.close()

class Role:
    def __init__(self, id: int, name: str, description: str = None):
        self.id = id
        self.name = name
        self.description = description

    @staticmethod
    def get_all() -> List['Role']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, description
                FROM roles
                ORDER BY name
            """)
            return [Role(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def get_permissions(self) -> List[str]:
        """Get all permissions for this role"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT DISTINCT p.name
                FROM roles r
                JOIN role_permissions rp ON r.id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE r.id = %s
            """, (self.id,))
            return [row[0] for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def update_permissions(self, new_permissions: List[str]) -> bool:
        """Update role permissions"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            # First remove all existing permissions
            cur.execute("""
                DELETE FROM role_permissions
                WHERE role_id = %s
            """, (self.id,))

            # Then add new permissions
            for perm_name in new_permissions:
                cur.execute("""
                    INSERT INTO role_permissions (role_id, permission_id)
                    SELECT %s, id FROM permissions WHERE name = %s
                """, (self.id, perm_name))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating permissions: {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def create(name: str, description: str) -> Optional['Role']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO roles (name, description)
                VALUES (%s, %s)
                RETURNING id, name, description
            """, (name, description))
            conn.commit()
            if (data := cur.fetchone()) is not None:
                return Role(*data)
            return None
        finally:
            cur.close()
            conn.close()
    @staticmethod
    def get_by_name(role_name: str) -> Optional['Role']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, description
                FROM roles
                WHERE name = %s
            """, (role_name,))
            if (data := cur.fetchone()) is not None:
                return Role(*data)
            return None
        finally:
            cur.close()
            conn.close()
    def delete(self) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM roles WHERE id = %s RETURNING id", (self.id,))
            conn.commit()
            return cur.fetchone() is not None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(role_id: int) -> Optional['Role']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, description
                FROM roles
                WHERE id = %s
            """, (role_id,))
            if (data := cur.fetchone()) is not None:
                return Role(*data)
            return None
        finally:
            cur.close()
            conn.close()

    def add_permission(self, permission_id: int) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO role_permissions (role_id, permission_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                RETURNING role_id
            """, (self.id, permission_id))
            conn.commit()
            return cur.fetchone() is not None
        finally:
            cur.close()
            conn.close()

    def remove_permission(self, permission_id: int) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                DELETE FROM role_permissions
                WHERE role_id = %s AND permission_id = %s
                RETURNING role_id
            """, (self.id, permission_id))
            conn.commit()
            return cur.fetchone() is not None
        finally:
            cur.close()
            conn.close()