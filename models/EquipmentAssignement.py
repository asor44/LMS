from datetime import datetime
from typing import List

import database


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
