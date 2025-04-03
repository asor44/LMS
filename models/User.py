import hashlib
from typing import List, Optional
import database
from models.Badges import Badge
from models.Roles import Role


class User:
    def __init__(self, id: int, name: str, email: str, password_hash: str, status: str,
                 first_name: str = None, rank: str = None):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.status = status
        self.first_name = first_name or ""  # Default to empty string if None
        self.rank = rank or ""  # Default to empty string if None

    def get_available_recipients(self) -> List['User']:
        """Retourne la liste des utilisateurs disponibles comme destinataires de messages"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            if self.status == 'parent':
                # Les parents peuvent envoyer des messages à leurs enfants
                return self.get_children()
            elif self.status == 'administration' or self.has_role('manage_communications'):
                # Les administrateurs peuvent envoyer des messages à tout le monde
                return User.get_all()
            else:
                # Les autres utilisateurs peuvent envoyer des messages aux utilisateurs
                # de même statut et aux animateurs/administrateurs
                cur.execute("""
                    SELECT DISTINCT u.id, u.name, u.email, u.password_hash, u.status
                    FROM users u
                    WHERE u.status IN ('administration', 'animateur')
                    OR u.status = %s
                    ORDER BY u.name
                """, (self.status,))
                return [User(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_email(email: str) -> Optional['User']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, email, password_hash, status, first_name, rank
                FROM users
                WHERE email = %s
            """, (email,))
            if (data := cur.fetchone()) is not None:
                return User(*data)
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
                SELECT id, name, email, password_hash, status, first_name, rank
                FROM users
                WHERE id = %s
            """, (user_id,))
            if (data := cur.fetchone()) is not None:
                return User(*data)
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
                SELECT id, name, email, password_hash, status, first_name, rank
                FROM users
                ORDER BY name
            """)
            return [User(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all_by_status(statuses: List[str]) -> List['User']:
        """Récupère tous les utilisateurs ayant un statut dans la liste fournie"""
        if not statuses:
            return []

        conn = database.get_connection()
        cur = conn.cursor()
        try:
            # Construire la requête avec des paramètres pour tous les statuts
            placeholders = ', '.join(['%s'] * len(statuses))
            query = f"""
                SELECT id, name, email, password_hash, status, first_name, rank
                FROM users
                WHERE status IN ({placeholders})
                ORDER BY name
            """
            cur.execute(query, statuses)
            return [User(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def update(self, name: str, email: str, status: str, roles: List[str],
               first_name: str = None, rank: str = None, password: str = None) -> bool:
        """Update user information and roles"""
        if not name or not email or not status:
            return False

        conn = database.get_connection()
        cur = conn.cursor()
        try:
            # Start with basic user info update
            update_query = """
                UPDATE users 
                SET name = %s, email = %s, status = %s, 
                    first_name = %s, rank = %s
            """
            params = [name, email, status, first_name, rank]

            # Add password update if provided
            if password:
                update_query += ", password_hash = %s"
                params.append(hashlib.sha256(password.encode()).hexdigest())

            update_query += " WHERE id = %s RETURNING id"
            params.append(self.id)

            cur.execute(update_query, params)

            if cur.fetchone() is None:
                conn.rollback()
                return False

            # Update roles if provided
            if roles is not None:
                # Remove existing roles
                cur.execute("DELETE FROM user_roles WHERE user_id = %s", (self.id,))

                # Add new roles
                for role_name in roles:
                    cur.execute("""
                        INSERT INTO user_roles (user_id, role_id)
                        SELECT %s, id FROM roles WHERE name = %s
                    """, (self.id, role_name))

            # Update object attributes
            self.name = name
            self.email = email
            self.status = status
            self.first_name = first_name
            self.rank = rank
            if password:
                self.password_hash = hashlib.sha256(password.encode()).hexdigest()

            conn.commit()
            return True

        except Exception as e:
            print(f"Error updating user: {str(e)}")
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
            return cur.fetchone()[0]
        finally:
            cur.close()
            conn.close()

    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission through any of their roles"""
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
            return cur.fetchone()[0]
        finally:
            cur.close()
            conn.close()

    def get_children(self) -> List['User']:
        """Récupérer les enfants d'un parent."""
        if self.status != 'parent':
            return []

        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT u.id, u.name, u.email, u.password_hash, u.status
                FROM users u
                JOIN parent_child pc ON u.id = pc.child_id
                WHERE pc.parent_id = %s
                ORDER BY u.name
            """, (self.id,))
            return [User(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def get_points(self) -> dict:
        """Calculate user points and level based on their activities and notes."""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            # Get points from notes (rating 1-5 = 2-10 points)
            cur.execute("""
                SELECT COALESCE(SUM(rating * 2), 0)
                FROM user_notes
                WHERE user_id = %s
            """, (self.id,))
            note_points = cur.fetchone()[0]

            # Get points from attendance (10 points per attendance)
            cur.execute("""
                SELECT COUNT(*) * 10
                FROM attendance
                WHERE user_id = %s
            """, (self.id,))
            attendance_points = cur.fetchone()[0]

            total_points = note_points + attendance_points

            # Calculate level: level N requires (N*10)^2 points
            # So if you have 100 points, you're level 1 (requires 100 points)
            # Level 2 requires 400 points, level 3 requires 900 points, etc.
            level = int((total_points ** 0.5) / 10)  # Integer division to get current level

            return {
                "points": int(total_points),
                "level": max(1, level)  # Minimum level is 1
            }
        finally:
            cur.close()
            conn.close()

    def get_badges(self) -> List['Badge']:
        """Get all badges earned by the user based on points."""
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
            return [Badge(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def get_notes(self, start_date=None, end_date=None) -> List[dict]:
        """Get notes for this user with optional date filtering"""
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
                    "id": row[0],
                    "user_id": row[1],
                    "date": row[2],
                    "type": row[3],
                    "rating": row[4],
                    "appreciation": row[5],
                    "evaluator_id": row[6],
                    "evaluator_name": row[7]
                })
            return notes
        finally:
            cur.close()
            conn.close()

    def add_note(self, date, note_type, rating, appreciation, evaluator_id):
        """Add a note for this user"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO user_notes (user_id, note_date, note_type, rating, appreciation, evaluator_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (self.id, date, note_type, rating, appreciation, evaluator_id))
            conn.commit()
            return cur.fetchone()[0]
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def delete_note(self, note_id):
        """Delete a note for this user"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                DELETE FROM user_notes 
                WHERE id = %s AND user_id = %s
                RETURNING id
            """, (note_id, self.id))
            conn.commit()
            return cur.fetchone() is not None
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def get_permissions(self) -> List[str]:
        """Get all permissions for this user through their roles"""
        permissions = []
        roles = self.get_roles()
        for role_name in roles:
            role = Role.get_by_name(role_name)
            if role:
                permissions.extend(role.get_permissions())
        return permissions

    def get_roles(self) -> List[str]:
        """Get all roles for this user"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT DISTINCT r.name
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                WHERE u.id = %s
            """, (self.id,))
            return [row[0] for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()
