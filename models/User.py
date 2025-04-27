import hashlib
from typing import List, Optional
import database
from models.Badges import Badge
from models.Roles import Role

class User:
    def __init__(self, id: int, name: str, email: str, password_hash: str, status: str,
                 first_name: str = "", rank: str = ""):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.status = status
        self.first_name = first_name
        self.rank = rank

    def get_available_recipients(self) -> List['User']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            if self.status == 'parent':
                return self.get_children()
            elif self.status == 'administration' or self.has_role('manage_communications'):
                return User.get_all()
            else:
                cur.execute("""
                    SELECT DISTINCT id, name, email, password_hash, status, first_name
                    FROM users
                    WHERE status IN ('administration', 'animateur') OR status = %s
                    ORDER BY name
                """, (self.status,))
                return [User(**row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_email(email: str) -> Optional['User']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, email, password_hash, status, first_name
                FROM users
                WHERE email = %s
            """, (email,))
            if (data := cur.fetchone()) is not None:
                return User(**data)
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(user_id: int) -> Optional['User']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, email, password_hash, status, first_name
                FROM users
                WHERE id = %s
            """, (user_id,))
            if (data := cur.fetchone()) is not None:
                return User(**data)
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all() -> List['User']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, email, password_hash, status, first_name
                FROM users
                ORDER BY name
            """)
            return [User(**row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all_by_status(statuses: List[str]) -> List['User']:
        if not statuses:
            return []
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            placeholders = ', '.join(['%s'] * len(statuses))
            query = f"""
                SELECT id, name, email, password_hash, status, first_name
                FROM users
                WHERE status IN ({placeholders})
                ORDER BY name
            """
            cur.execute(query, statuses)
            return [User(**row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def update(self, name: str, email: str, status: str, roles: List[str],
               first_name: str = "", rank: str = "", password: str = None) -> bool:
        if not name or not email or not status:
            return False

        conn = database.get_connection()
        cur = conn.cursor()
        try:
            update_query = """
                UPDATE users 
                SET name = %s, email = %s, status = %s, 
                    first_name = %s, rank = %s
                WHERE id = %s
            """
            params = [name, email, status, first_name, rank, self.id]

            cur.execute(update_query, params)

            if cur.rowcount == 0:
                conn.rollback()
                return False

            if roles is not None:
                cur.execute("DELETE FROM user_roles WHERE user_id = %s", (self.id,))
                for role_name in roles:
                    cur.execute("""
                        INSERT INTO user_roles (user_id, role_id)
                        SELECT %s, id FROM roles WHERE name = %s
                    """, (self.id, role_name))

            if password:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                cur.execute("""
                    UPDATE users SET password_hash = %s WHERE id = %s
                """, (password_hash, self.id))
                self.password_hash = password_hash

            self.name = name
            self.email = email
            self.status = status
            self.first_name = first_name
            self.rank = rank

            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def verify_password(self, password: str) -> bool:
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return self.password_hash == hashed

    def has_role(self, role_name: str) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT EXISTS(
                    SELECT 1 
                    FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.user_id = %s AND r.name = %s
                )
            """, (self.id, role_name))
            result = cur.fetchone()
            return next(iter(result.values()), False) if result else False
        finally:
            cur.close()
            conn.close()

    def has_permission(self, permission_name: str) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT EXISTS(
                    SELECT 1 
                    FROM user_roles ur
                    JOIN role_permissions rp ON ur.role_id = rp.role_id
                    JOIN permissions p ON rp.permission_id = p.id
                    WHERE ur.user_id = %s AND p.name = %s
                )
            """, (self.id, permission_name))
            result = cur.fetchone()
            return next(iter(result.values()), False) if result else False
        finally:
            cur.close()
            conn.close()

    def get_children(self) -> List['User']:
        if self.status != 'parent':
            return []

        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, email, password_hash, status, first_name
                FROM users
                JOIN parent_child pc ON users.id = pc.child_id
                WHERE pc.parent_id = %s
                ORDER BY users.name
            """, (self.id,))
            return [User(**row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def get_points(self) -> dict:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COALESCE(SUM(rating * 2), 0)
                FROM user_notes
                WHERE user_id = %s
            """, (self.id,))
            note_points = list(cur.fetchone().values())[0]

            cur.execute("""
                SELECT COUNT(*) * 10
                FROM attendance
                WHERE user_id = %s
            """, (self.id,))
            attendance_points = list(cur.fetchone().values())[0]

            total_points = note_points + attendance_points
            level = int((total_points ** 0.5) / 10)

            return {
                "points": int(total_points),
                "level": max(1, level)
            }
        finally:
            cur.close()
            conn.close()

    def get_badges(self) -> List['Badge']:
        points_info = self.get_points()
        total_points = points_info["points"]

        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, description, icon_name, points_required
                FROM badges
                WHERE points_required <= %s
                ORDER BY points_required DESC
            """, (total_points,))
            return [Badge(*row.values()) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def get_notes(self, start_date=None, end_date=None) -> List[dict]:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            query = """
                SELECT n.id, n.user_id, n.note_date, n.note_type, n.rating, n.appreciation, 
                       n.evaluator_id, u.name as evaluator_name
                FROM user_notes n
                JOIN users u ON n.evaluator_id = u.id
                WHERE n.user_id = %s
            """
            params = [self.id]

            if start_date:
                query += " AND n.note_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND n.note_date <= %s"
                params.append(end_date)

            query += " ORDER BY n.note_date DESC"
            cur.execute(query, params)

            notes = []
            for row in cur.fetchall():
                notes.append({
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "date": row["note_date"],
                    "type": row["note_type"],
                    "rating": row["rating"],
                    "appreciation": row["appreciation"],
                    "evaluator_id": row["evaluator_id"],
                    "evaluator_name": row["evaluator_name"]
                })
            return notes
        finally:
            cur.close()
            conn.close()

    def add_note(self, date, note_type, rating, appreciation, evaluator_id):
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO user_notes (user_id, note_date, note_type, rating, appreciation, evaluator_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (self.id, date, note_type, rating, appreciation, evaluator_id))
            conn.commit()
            return cur.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def delete_note(self, note_id):
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                DELETE FROM user_notes
                WHERE id = %s AND user_id = %s
            """, (note_id, self.id))
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def get_permissions(self) -> List[str]:
        permissions = []
        roles = self.get_roles()
        for role_name in roles:
            role = Role.get_by_name(role_name)
            if role:
                permissions.extend(role.get_permissions())
        return permissions

    def get_roles(self) -> List[str]:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT DISTINCT r.name
                FROM users
                JOIN user_roles ur ON users.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                WHERE users.id = %s
            """, (self.id,))
            return [row["name"] for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()
