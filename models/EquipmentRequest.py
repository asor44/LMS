from datetime import datetime
from typing import Optional, List

import database
from models.EquipmentAssignement import EquipmentAssignment


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
