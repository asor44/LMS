from typing import List

import database


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