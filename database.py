import hashlib
import mysql.connector
from mysql.connector import Error

class DatabaseEngine:
    def __init__(self):
        self.host     = "localhost"
        self.user     = "root"
        self.password = ""       
        self.database = "dormitory_db"

    def connect(self):
        try:
            return mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
        except Error as e:
            print(f"[DB Connection Error] {e}")
            return None

class AdminModule(DatabaseEngine):
    def validate_login(self, username, password):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                hashed = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute(
                    "SELECT * FROM admins WHERE username = %s AND password = %s",
                    (username, hashed)
                )
                result = cursor.fetchone()
                if result:
                    self.add_log(result['admin_id'], 'LOGIN',
                                 f"{result['full_name']} logged in.")
                return result
            except Exception as e:
                print(f"[AdminModule.validate_login] {e}")
            finally:
                conn.close()
        return None
    def get_all_admins(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT admin_id, username, full_name, role, created_at "
                    "FROM admins ORDER BY admin_id"
                )
                return cursor.fetchall()
            except Exception as e:
                print(f"[AdminModule.get_all_admins] {e}")
            finally:
                conn.close()
        return []

    def hash_existing_admin_passwords(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT admin_id, password FROM admins")
                rows = cursor.fetchall()
                count = 0
                for row in rows:
                    raw = row.get('password')
                    if not raw:
                        continue
                    if len(raw) == 64 and all(c in '0123456789abcdef' for c in raw.lower()):
                        continue
                    hashed = hashlib.sha256(raw.encode()).hexdigest()
                    cursor.execute("UPDATE admins SET password=%s WHERE admin_id=%s", (hashed, row['admin_id']))
                    count += 1
                conn.commit()
                return count
            except Exception as e:
                print(f"[AdminModule.hash_existing_admin_passwords] {e}")
            finally:
                conn.close()
        return 0

    def add_admin(self, username, password, full_name, role="Admin"):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                hashed = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO admins (username, password, full_name, role) "
                    "VALUES (%s, %s, %s, %s)",
                    (username, hashed, full_name, role)
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"[AdminModule.add_admin] {e}")
            finally:
                conn.close()
        return False

    def update_admin(self, admin_id, username, full_name, role, password=None):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                if password:
                    hashed = hashlib.sha256(password.encode()).hexdigest()
                    cursor.execute(
                        "UPDATE admins SET username=%s, full_name=%s, role=%s, password=%s "
                        "WHERE admin_id=%s",
                        (username, full_name, role, hashed, admin_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE admins SET username=%s, full_name=%s, role=%s "
                        "WHERE admin_id=%s",
                        (username, full_name, role, admin_id)
                    )
                conn.commit()
                return True
            except Exception as e:
                print(f"[AdminModule.update_admin] {e}")
            finally:
                conn.close()
        return False

    def delete_admin(self, admin_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM admins WHERE admin_id=%s", (admin_id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"[AdminModule.delete_admin] {e}")
            finally:
                conn.close()
        return False
    def add_log(self, admin_id, action_type, action_text):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO activity_logs (admin_id, action_type, action_text) "
                    "VALUES (%s, %s, %s)",
                    (admin_id, action_type, action_text)
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"[AdminModule.add_log] {e}")
            finally:
                conn.close()
        return False

    def get_activity_logs(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT l.log_id, a.full_name AS admin_name,
                           l.action_type, l.action_text, l.log_timestamp
                    FROM activity_logs l
                    JOIN admins a ON l.admin_id = a.admin_id
                    ORDER BY l.log_timestamp DESC
                """)
                return cursor.fetchall()
            except Exception as e:
                print(f"[AdminModule.get_activity_logs] {e}")
            finally:
                conn.close()
        return []

    def get_event_scheduler_status(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SHOW VARIABLES LIKE 'event_scheduler'")
                row = cursor.fetchone()
                conn.close()
                return row[1] if row else None
            except Exception as e:
                print(f"[AdminModule.get_event_scheduler_status] {e}")
                conn.close()
        return None

    def enable_event_scheduler(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SET GLOBAL event_scheduler = ON")
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[AdminModule.enable_event_scheduler] {e}")
                conn.close()
        return False

    def get_scheduler_events(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT EVENT_NAME, STATUS, LAST_ALTERED FROM information_schema.EVENTS WHERE EVENT_SCHEMA = DATABASE()")
                events = cursor.fetchall()
                conn.close()
                return events
            except Exception as e:
                print(f"[AdminModule.get_scheduler_events] {e}")
                conn.close()
        return []

    def create_overdue_payments_event(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE EVENT IF NOT EXISTS ev_mark_overdue_payments
                    ON SCHEDULE EVERY 1 DAY
                    STARTS CURRENT_TIMESTAMP + INTERVAL 1 DAY
                    DO
                      UPDATE payments
                      SET status = 'Overdue'
                      WHERE status = 'Pending'
                        AND due_date < CURRENT_DATE();
                """)
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[AdminModule.create_overdue_payments_event] {e}")
                conn.close()
        return False

    def create_expire_assignments_event(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE EVENT IF NOT EXISTS ev_expire_assignments
                    ON SCHEDULE EVERY 1 DAY
                    DO
                      UPDATE assignments
                      SET status = 'Expired'
                      WHERE status = 'Active'
                        AND end_date < CURRENT_DATE();
                """)
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[AdminModule.create_expire_assignments_event] {e}")
                conn.close()
        return False

    def create_cleanup_visitors_event(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE EVENT IF NOT EXISTS ev_cleanup_old_visitors
                    ON SCHEDULE EVERY 30 DAY
                    DO
                      DELETE FROM visitor_logs
                      WHERE time_out < CURRENT_DATE() - INTERVAL 90 DAY;
                """)
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[AdminModule.create_cleanup_visitors_event] {e}")
                conn.close()
        return False

    def create_scheduler_events(self):
        results = []
        results.append(self.create_overdue_payments_event())
        results.append(self.create_expire_assignments_event())
        results.append(self.create_cleanup_visitors_event())
        return sum(1 for success in results if success)

class RenterModule(DatabaseEngine):
    def hash_existing_renter_passwords(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT renter_id, password FROM renter_accounts")
                rows = cursor.fetchall()
                count = 0
                for row in rows:
                    raw = row.get('password')
                    if not raw:
                        continue
                    if len(raw) == 64 and all(c in '0123456789abcdef' for c in raw.lower()):
                        continue
                    hashed = hashlib.sha256(raw.encode()).hexdigest()
                    cursor.execute("UPDATE renter_accounts SET password=%s WHERE renter_id=%s", (hashed, row['renter_id']))
                    count += 1
                conn.commit()
                return count
            except Exception as e:
                print(f"[RenterModule.hash_existing_renter_passwords] {e}")
            finally:
                conn.close()
        return 0

    def get_all_renters(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM renters ORDER BY last_name, first_name")
                return cursor.fetchall()
            except Exception as e:
                print(f"[RenterModule.get_all_renters] {e}")
            finally:
                conn.close()
        return []

    def get_renter_by_id(self, renter_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM renters WHERE renter_id=%s", (renter_id,))
                return cursor.fetchone()
            except Exception as e:
                print(f"[RenterModule.get_renter_by_id] {e}")
            finally:
                conn.close()
        return None

    def add_renter(self, first_name, middle_name, last_name, occupation_type,
                   institution_employer, gender, contact_number, email,
                   id_type, id_number, address,
                   emergency_contact_name, emergency_contact_number,
                   renter_status="Active"):
        conn = self.connect()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO renters (
                        first_name, middle_name, last_name, occupation_type,
                        institution_employer, gender, contact_number, email,
                        id_type, id_number, address,
                        emergency_contact_name, emergency_contact_number, renter_status
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (first_name, middle_name, last_name, occupation_type,
                      institution_employer, gender, contact_number, email,
                      id_type, id_number, address,
                      emergency_contact_name, emergency_contact_number, renter_status))
                renter_id = cursor.lastrowid
                username = f"renter{renter_id}"
                default_password = "dorm123"
                hashed_password = hashlib.sha256(default_password.encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO renter_accounts (renter_id, username, password) "
                    "VALUES (%s, %s, %s)",
                    (renter_id, username, hashed_password)
                )
                conn.commit()
                return renter_id
            except Exception as e:
                conn.rollback() 
                print(f"[RenterModule.add_renter] {e}")
            finally:
                conn.close()
        return None

    def update_renter(self, renter_id, **fields):
        if not fields:
            return False
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                set_clause = ", ".join(f"{k}=%s" for k in fields)
                values = list(fields.values()) + [renter_id]
                cursor.execute(f"UPDATE renters SET {set_clause} WHERE renter_id=%s", values)
                conn.commit()
                return True
            except Exception as e:
                print(f"[RenterModule.update_renter] {e}")
            finally:
                conn.close()
        return False

    def delete_renter(self, renter_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM renters WHERE renter_id=%s", (renter_id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"[RenterModule.delete_renter] {e}")
            finally:
                conn.close()
        return False

    def get_stats(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT COUNT(*) AS total FROM assignments WHERE status='Active'")
                total_active = cursor.fetchone()['total']
                cursor.execute("SELECT COUNT(*) AS total FROM rooms WHERE status='Available'")
                vacant_rooms = cursor.fetchone()['total']
                return {"renters": total_active, "vacant": vacant_rooms}
            except Exception as e:
                print(f"[RenterModule.get_stats] {e}")
            finally:
                conn.close()
        return None

    def search_renters(self, keyword):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                like = f"%{keyword}%"
                cursor.execute("""
                    SELECT * FROM renters
                    WHERE first_name LIKE %s OR last_name LIKE %s
                       OR contact_number LIKE %s OR email LIKE %s
                    ORDER BY last_name
                """, (like, like, like, like))
                return cursor.fetchall()
            except Exception as e:
                print(f"[RenterModule.search_renters] {e}")
            finally:
                conn.close()
        return []

class RoomModule(DatabaseEngine):
    def get_all_rooms(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM rooms ORDER BY room_number")
                return cursor.fetchall()
            except Exception as e:
                print(f"[RoomModule.get_all_rooms] {e}")
            finally:
                conn.close()
        return []

    def get_room_by_id(self, room_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM rooms WHERE room_id=%s", (room_id,))
                return cursor.fetchone()
            except Exception as e:
                print(f"[RoomModule.get_room_by_id] {e}")
            finally:
                conn.close()
        return None

    def add_room(self, room_number, floor_level, monthly_rate, capacity,
                 status="Available", description=""):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO rooms (room_number, floor_level, monthly_rate,
                                      capacity, status, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (room_number, floor_level, monthly_rate,
                      capacity, status, description))
                conn.commit()
                return True
            except Exception as e:
                print(f"[RoomModule.add_room] {e}")
            finally:
                conn.close()
        return False

    def update_room(self, room_id, room_number, floor_level, monthly_rate,
                    capacity, status, description):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE rooms SET room_number=%s, floor_level=%s,
                        monthly_rate=%s, capacity=%s, status=%s, description=%s
                    WHERE room_id=%s
                """, (room_number, floor_level, monthly_rate,
                      capacity, status, description, room_id))
                conn.commit()
                return True
            except Exception as e:
                print(f"[RoomModule.update_room] {e}")
            finally:
                conn.close()
        return False

    def delete_room(self, room_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM rooms WHERE room_id=%s", (room_id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"[RoomModule.delete_room] {e}")
            finally:
                conn.close()
        return False

    def get_amenities(self, room_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM room_amenities WHERE room_id=%s", (room_id,))
                return cursor.fetchall()
            except Exception as e:
                print(f"[RoomModule.get_amenities] {e}")
            finally:
                conn.close()
        return []

    def add_amenity(self, room_id, amenity_name, quantity=1, item_condition="Good"):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO room_amenities (room_id, amenity_name, quantity, item_condition)
                    VALUES (%s, %s, %s, %s)
                """, (room_id, amenity_name, quantity, item_condition))
                conn.commit()
                return True
            except Exception as e:
                print(f"[RoomModule.add_amenity] {e}")
            finally:
                conn.close()
        return False

    def delete_amenity(self, amenity_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM room_amenities WHERE amenity_id=%s", (amenity_id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"[RoomModule.delete_amenity] {e}")
            finally:
                conn.close()
        return False

class AssignmentModule(DatabaseEngine):
    def get_all_assignments(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT a.assignment_id,
                           CONCAT(r.first_name,' ',r.last_name) AS renter_name,
                           rm.room_number, a.bed_assignment,
                           a.check_in_date, a.check_out_date,
                           a.status, a.agreed_rate, a.security_deposit,
                           a.contract_term, a.notes
                    FROM assignments a
                    JOIN renters r  ON a.renter_id = r.renter_id
                    JOIN rooms   rm ON a.room_id   = rm.room_id
                    ORDER BY a.assignment_id
                """)
                return cursor.fetchall()
            except Exception as e:
                print(f"[AssignmentModule.get_all_assignments] {e}")
            finally:
                conn.close()
        return []

    def add_assignment(self, renter_id, room_id, bed_assignment, check_in_date,
                       agreed_rate=1800.00, security_deposit=0.00,
                       contract_term=None, assigned_by=None, notes=None):
        conn = self.connect()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO assignments
                        (renter_id, room_id, bed_assignment, check_in_date,
                         agreed_rate, security_deposit, contract_term,
                         assigned_by, notes)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (renter_id, room_id, bed_assignment, check_in_date,
                      agreed_rate, security_deposit, contract_term,
                      assigned_by, notes))
                cursor.execute(
                    "UPDATE rooms SET occupied = occupied + 1 WHERE room_id=%s",
                    (room_id,)
                )
                conn.commit()
                return True
            except Exception as e:
                conn.rollback() 
                print(f"[AssignmentModule.add_assignment] {e}")
            finally:
                conn.close()
        return False

    def check_out(self, assignment_id, check_out_date):
        conn = self.connect()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT room_id FROM assignments WHERE assignment_id=%s",
                    (assignment_id,)
                )
                row = cursor.fetchone()
                
                cursor.execute("""
                    UPDATE assignments SET status='Inactive', check_out_date=%s
                    WHERE assignment_id=%s
                """, (check_out_date, assignment_id))
                
                if row:
                    cursor.execute(
                        "UPDATE rooms SET occupied = GREATEST(occupied-1,0) WHERE room_id=%s",
                        (row[0],)
                    )
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                print(f"[AssignmentModule.check_out] {e}")
            finally:
                conn.close()
        return False

    def delete_assignment(self, assignment_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM assignments WHERE assignment_id=%s", (assignment_id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"[AssignmentModule.delete_assignment] {e}")
            finally:
                conn.close()
        return False

class PaymentModule(DatabaseEngine):
    def get_all_payments(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT p.payment_id, p.invoice_number,
                           CONCAT(r.first_name,' ',r.last_name) AS renter_name,
                           p.amount, p.balance_amount, p.payment_method,
                           p.billing_month, p.payment_date, p.status, p.remarks
                    FROM payments p
                    JOIN renters r ON p.renter_id = r.renter_id
                    ORDER BY p.payment_date DESC
                """)
                return cursor.fetchall()
            except Exception as e:
                print(f"[PaymentModule.get_all_payments] {e}")
            finally:
                conn.close()
        return []

    def add_payment(self, invoice_number, renter_id, amount, balance_amount,
                    payment_method, billing_month, payment_date,
                    status="Pending", processed_by=None,
                    reference_number=None, remarks=None):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO payments
                        (invoice_number, renter_id, amount, balance_amount,
                         payment_method, reference_number, billing_month,
                         payment_date, status, processed_by, remarks)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (invoice_number, renter_id, amount, balance_amount,
                      payment_method, reference_number, billing_month,
                      payment_date, status, processed_by, remarks))
                conn.commit()
                return True
            except Exception as e:
                print(f"[PaymentModule.add_payment] {e}")
            finally:
                conn.close()
        return False

    def update_payment_status(self, payment_id, status):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE payments SET status=%s WHERE payment_id=%s", (status, payment_id))
                conn.commit()
                return True
            except Exception as e:
                print(f"[PaymentModule.update_payment_status] {e}")
            finally:
                conn.close()
        return False

    def delete_payment(self, payment_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM payments WHERE payment_id=%s", (payment_id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"[PaymentModule.delete_payment] {e}")
            finally:
                conn.close()
        return False

    def get_payments_by_renter(self, renter_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM payments WHERE renter_id=%s ORDER BY payment_date DESC", (renter_id,))
                return cursor.fetchall()
            except Exception as e:
                print(f"[PaymentModule.get_payments_by_renter] {e}")
            finally:
                conn.close()
        return []

class MaintenanceModule(DatabaseEngine):
    def get_all_requests(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT mr.request_id, rm.room_number,
                           CONCAT(r.first_name,' ',r.last_name) AS renter_name,
                           mr.description, mr.priority, mr.status,
                           mr.request_date, mr.resolution_notes, mr.completion_date
                    FROM maintenance_requests mr
                    JOIN rooms   rm ON mr.room_id   = rm.room_id
                    JOIN renters r  ON mr.renter_id = r.renter_id
                    ORDER BY mr.request_date DESC
                """)
                return cursor.fetchall()
            except Exception as e:
                print(f"[MaintenanceModule.get_all_requests] {e}")
            finally:
                conn.close()
        return []

    def add_request(self, room_id, renter_id, description, priority="Medium"):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO maintenance_requests (room_id, renter_id, description, priority)
                    VALUES (%s, %s, %s, %s)
                """, (room_id, renter_id, description, priority))
                conn.commit()
                return True
            except Exception as e:
                print(f"[MaintenanceModule.add_request] {e}")
            finally:
                conn.close()
        return False

    def update_status(self, request_id, status, resolution_notes=None, completion_date=None):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE maintenance_requests SET status=%s, resolution_notes=%s, completion_date=%s
                    WHERE request_id=%s
                """, (status, resolution_notes, completion_date, request_id))
                conn.commit()
                return True
            except Exception as e:
                print(f"[MaintenanceModule.update_status] {e}")
            finally:
                conn.close()
        return False

    def delete_request(self, request_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM maintenance_requests WHERE request_id=%s", (request_id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"[MaintenanceModule.delete_request] {e}")
            finally:
                conn.close()
        return False

class UtilityModule(DatabaseEngine):
    def get_all_bills(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT ub.*, rm.room_number
                    FROM utility_bills ub
                    JOIN rooms rm ON ub.room_id = rm.room_id
                    ORDER BY ub.billing_date DESC
                """)
                return cursor.fetchall()
            except Exception as e:
                print(f"[UtilityModule.get_all_bills] {e}")
            finally:
                conn.close()
        return []

    def add_bill(self, room_id, bill_type, previous_reading, current_reading,
                 consumption, amount, amount_per_person,
                 billing_month, billing_date, due_date):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO utility_bills
                        (room_id, bill_type, previous_reading, current_reading,
                         consumption, amount, amount_per_person,
                         billing_month, billing_date, due_date)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (room_id, bill_type, previous_reading, current_reading,
                      consumption, amount, amount_per_person,
                      billing_month, billing_date, due_date))
                conn.commit()
                return True
            except Exception as e:
                print(f"[UtilityModule.add_bill] {e}")
            finally:
                conn.close()
        return False

    def mark_paid(self, bill_id, payment_date, reference_no=None):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE utility_bills SET status='Paid', payment_date=%s, reference_no=%s
                    WHERE bill_id=%s
                """, (payment_date, reference_no, bill_id))
                conn.commit()
                return True
            except Exception as e:
                print(f"[UtilityModule.mark_paid] {e}")
            finally:
                conn.close()
        return False

    def delete_bill(self, bill_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM utility_bills WHERE bill_id=%s", (bill_id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"[UtilityModule.delete_bill] {e}")
            finally:
                conn.close()
        return False

class VisitorModule(DatabaseEngine):
    def get_all_visitors(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT vl.visitor_id, vl.visitor_name, vl.relationship,
                           CONCAT(r.first_name,' ',r.last_name) AS renter_name,
                           vl.time_in, vl.time_out
                    FROM visitor_logs vl
                    JOIN renters r ON vl.renter_id = r.renter_id
                    ORDER BY vl.time_in DESC
                """)
                return cursor.fetchall()
            except Exception as e:
                print(f"[VisitorModule.get_all_visitors] {e}")
            finally:
                conn.close()
        return []

    def log_visitor_in(self, renter_id, visitor_name, relationship):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO visitor_logs (renter_id, visitor_name, relationship)
                    VALUES (%s, %s, %s)
                """, (renter_id, visitor_name, relationship))
                conn.commit()
                return True
            except Exception as e:
                print(f"[VisitorModule.log_visitor_in] {e}")
            finally:
                conn.close()
        return False

    def log_visitor_out(self, visitor_id, time_out):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE visitor_logs SET time_out=%s WHERE visitor_id=%s", (time_out, visitor_id))
                conn.commit()
                return True
            except Exception as e:
                print(f"[VisitorModule.log_visitor_out] {e}")
            finally:
                conn.close()
        return False

    def delete_visitor_log(self, visitor_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM visitor_logs WHERE visitor_id=%s", (visitor_id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"[VisitorModule.delete_visitor_log] {e}")
            finally:
                conn.close()
        return False

class FacilityModule(DatabaseEngine):
    def get_all_facilities(self):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM facility_overview ORDER BY floor_level, facility_type")
                return cursor.fetchall()
            except Exception as e:
                print(f"[FacilityModule.get_all_facilities] {e}")
            finally:
                conn.close()
        return []

    def add_facility(self, floor_level, facility_type, count):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO facility_overview (floor_level, facility_type, count)
                    VALUES (%s, %s, %s)
                """, (floor_level, facility_type, count))
                conn.commit()
                return True
            except Exception as e:
                print(f"[FacilityModule.add_facility] {e}")
            finally:
                conn.close()
        return False

    def update_facility(self, facility_id, floor_level, facility_type, count):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE facility_overview SET floor_level=%s, facility_type=%s, count=%s
                    WHERE facility_id=%s
                """, (floor_level, facility_type, count, facility_id))
                conn.commit()
                return True
            except Exception as e:
                print(f"[FacilityModule.update_facility] {e}")
            finally:
                conn.close()
        return False

    def delete_facility(self, facility_id):
        conn = self.connect()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM facility_overview WHERE facility_id=%s", (facility_id,))
                conn.commit()
                return True
            except Exception as e:
                print(f"[FacilityModule.delete_facility] {e}")
            finally:
                conn.close()
        return False
    
if __name__ == "__main__":
    print("--- Database Connection Test ---")
    
    admin_mod = AdminModule()
    hashed_admins = admin_mod.hash_existing_admin_passwords()
    print(f"[MIGRATION] Hashed {hashed_admins} admin password rows.")
    
    renter_mod = RenterModule()
    hashed_renters = renter_mod.hash_existing_renter_passwords()
    print(f"[MIGRATION] Hashed {hashed_renters} renter account password rows.")
    
    login_test = admin_mod.validate_login("gel_admin", "gel123") 
    
    if login_test:
        print(f"[SUCCESS] Connected! Welcome, {login_test['full_name']}")
    else:
        print("[FAILED] Login failed. Check your username/password or DB connection.")

    stats = renter_mod.get_stats()
    if stats:
        print(f"[SUCCESS] Stats found: {stats['renters']} Active Renters, {stats['vacant']} Vacant Rooms")

    room_mod = RoomModule()
    rooms = room_mod.get_all_rooms()
    print(f"[SUCCESS] Found {len(rooms)} rooms in the database.")