from datetime import datetime, time
from typing import Optional, List

import database

class Activity:
    def __init__(self, id: int, name: str, description: str, date: datetime, start_time: time,
                 end_time: time, max_participants: int, location: str = None,
                 lunch_included: bool = False, dinner_included: bool = False):
        self.id = id
        self.name = name
        self.description = description
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.max_participants = max_participants
        self.location = location
        self.lunch_included = lunch_included
        self.dinner_included = dinner_included

    @staticmethod
    def create(name: str, description: str, date: datetime, start_time: time,
               end_time: time, max_participants: int, location: str = None,
               lunch_included: bool = False, dinner_included: bool = False) -> Optional['Activity']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO activities (
                    name, description, date, start_time, end_time,
                    max_participants, location, lunch_included, dinner_included
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name, description, date, start_time, end_time,
                          max_participants, location, lunch_included, dinner_included
            """, (name, description, date, start_time, end_time,
                  max_participants, location, lunch_included, dinner_included))
            conn.commit()
            if (data := cur.fetchone()) is not None:
                return Activity(*data)
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all() -> List['Activity']:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, description, date, start_time, end_time,
                       max_participants, location, lunch_included, dinner_included
                FROM activities
                ORDER BY date DESC, start_time ASC
            """)
            return [Activity(*row) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def update(self, name: str, description: str, date: datetime, start_time: time,
               end_time: time, max_participants: int, location: str = None,
               lunch_included: bool = False, dinner_included: bool = False) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE activities
                SET name = %s, description = %s, date = %s, start_time = %s,
                    end_time = %s, max_participants = %s, location = %s,
                    lunch_included = %s, dinner_included = %s
                WHERE id = %s
                RETURNING id
            """, (name, description, date, start_time, end_time,
                  max_participants, location, lunch_included, dinner_included, self.id))
            conn.commit()
            success = cur.fetchone() is not None
            if success:
                self.name = name
                self.description = description
                self.date = date
                self.start_time = start_time
                self.end_time = end_time
                self.max_participants = max_participants
                self.location = location
                self.lunch_included = lunch_included
                self.dinner_included = dinner_included
            return success
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(activity_id: int) -> bool:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM activities WHERE id = %s RETURNING id", (activity_id,))
            conn.commit()
            return cur.fetchone() is not None
        except Exception as e:
            conn.rollback()
            print(f"Error deleting activity: {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()

    def get_attendance_list(self) -> List[int]:
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT user_id
                FROM activity_attendance
                WHERE activity_id = %s
            """, (self.id,))
            return [row[0] for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def get_required_equipment(self) -> List[tuple]:
        """Returns list of tuples (equipment_id, item_name, unit, quantity)"""
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT ae.inventory_id, i.item_name, i.unit, ae.quantity_required,
                       i.quantity as available_quantity
                FROM activity_equipment ae
                JOIN inventory i ON i.id = ae.inventory_id
                WHERE ae.activity_id = %s
            """, (self.id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def update_equipment(self, equipment_list: List[tuple]) -> bool:
        """Update required equipment for activity
        equipment_list: list of tuples (equipment_id, quantity_required)
        """
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            # Remove existing equipment assignments
            cur.execute("DELETE FROM activity_equipment WHERE activity_id = %s", (self.id,))

            # Add new equipment assignments
            for equipment_id, quantity in equipment_list:
                cur.execute("""
                    INSERT INTO activity_equipment (activity_id, equipment_id, quantity_required)
                    VALUES (%s, %s, %s)
                """, (self.id, equipment_id, quantity))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating equipment: {str(e)}")
            return False
        finally:
            cur.close()
            conn.close()
