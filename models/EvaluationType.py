from typing import Optional, List

import database


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
