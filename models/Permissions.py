from typing import List, Optional

import database


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
