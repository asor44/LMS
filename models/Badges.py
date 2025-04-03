from typing import List, Optional

import database


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
