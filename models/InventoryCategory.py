from typing import Optional, List

import database
from models.CategoryField import CategoryField


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
