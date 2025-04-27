from typing import Optional, List
import database

class Inventory:
    def __init__(self, id: int, item_name: str, category_id: int, quantity: int, unit: str, min_quantity: int = 0,
                 photo_url: Optional[str] = None):
        self.id = id
        self.item_name = item_name
        self.category_id = category_id
        self.quantity = quantity
        self.unit = unit
        self.min_quantity = min_quantity
        self.photo_url = photo_url

    @staticmethod
    def update_quantity(item_id: int, new_quantity: int) -> bool:
        """Met à jour la quantité d'un item."""
        if new_quantity < 0:
            return False

        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE inventory
                SET quantity = %s
                WHERE id = %s
            """, (new_quantity, item_id))
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            conn.rollback()
            print(f"Erreur lors de la mise à jour de la quantité : {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def update_photo_url(item_id: int, photo_data: Optional[str]) -> bool:
        """Met à jour la photo associée à un item."""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE inventory
                SET photo_url = %s
                WHERE id = %s
            """, (photo_data, item_id))
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            conn.rollback()
            print(f"Erreur lors de la mise à jour de la photo : {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def remove_photo(item_id: int) -> bool:
        """Supprime la photo d'un item."""
        return Inventory.update_photo_url(item_id, None)

    @staticmethod
    def create(item_name: str, category_id: int, quantity: int, unit: str,
               min_quantity: int = 0, photo_data: Optional[str] = None) -> Optional['Inventory']:
        """Crée un nouvel article d'inventaire."""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO inventory (item_name, category_id, quantity, unit, min_quantity, photo_url)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (item_name, category_id, quantity, unit, min_quantity, photo_data))
            conn.commit()

            new_id = cur.lastrowid
            if new_id:
                cur.execute("""
                    SELECT id, item_name, category_id, quantity, unit, min_quantity, photo_url
                    FROM inventory
                    WHERE id = %s
                """, (new_id,))
                if (data := cur.fetchone()) is not None:
                    return Inventory(**data)
            return None
        except Exception as e:
            conn.rollback()
            print(f"Erreur lors de la création de l'item : {str(e)}")
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all() -> List['Inventory']:
        """Récupère tous les articles d'inventaire."""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, item_name, category_id, quantity, unit, min_quantity, photo_url
                FROM inventory
                ORDER BY category_id, item_name
            """)
            return [Inventory(**row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_parent(parent_id: int) -> List['Inventory']:
        """Récupère les articles d'inventaire affectés aux enfants d'un parent."""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT i.id, i.item_name, i.category_id, ea.quantity, i.unit, i.min_quantity, i.photo_url
                FROM inventory i
                JOIN equipment_assignments ea ON i.id = ea.inventory_id
                JOIN parent_child pc ON ea.user_id = pc.child_id
                WHERE pc.parent_id = %s AND ea.returned_at IS NULL
                ORDER BY i.category_id, i.item_name
            """, (parent_id,))
            return [Inventory(**row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(item_id: int) -> bool:
        """Supprime un article d'inventaire."""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                DELETE FROM inventory
                WHERE id = %s
            """, (item_id,))
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            conn.rollback()
            print(f"Erreur lors de la suppression de l'item : {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()
