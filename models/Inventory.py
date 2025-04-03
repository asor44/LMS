from typing import Optional, List

import database


class Inventory:
    def __init__(self, id: int, item_name: str, category: str, quantity: int, unit: str, min_quantity: int = 0,
                 photo_url: str = None):
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
    def create(item_name: str, category: str, quantity: int, unit: str, min_quantity: int = 0, photo_data=None) -> \
    Optional['Inventory']:
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
