from typing import Optional, List

import database

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
