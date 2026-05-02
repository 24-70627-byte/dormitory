import hashlib
from database import DatabaseEngine

class AdminModule(DatabaseEngine):
    def validate_login(self, username, password):
        conn = self.connect()
        if conn:
            cursor = conn.cursor(dictionary=True)
            hashed = hashlib.sha256(password.encode()).hexdigest()
            query = "SELECT * FROM admins WHERE username = %s AND password = %s"
            cursor.execute(query, (username, hashed))
            result = cursor.fetchone() 
            
            if result:
                # Automatic log upon login
                self.add_log(result['admin_id'], 'LOGIN', f"{result['full_name']} logged in.")
                
            conn.close()
            return result 
        return None
    
    def add_log(self, admin_id, action_type, action_text):
        conn = self.connect()
        if conn:
            cursor = conn.cursor()
            try:
                query = """
                    INSERT INTO activity_logs (admin_id, action_type, action_text)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(query, (admin_id, action_type, action_text))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"Logging Error: {e}")
                return False
        return False

    def get_activity_logs(self):
        conn = self.connect()
        if conn:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT 
                    l.log_id, 
                    a.full_name as admin_name, 
                    l.action_type, 
                    l.action_text, 
                    l.log_timestamp 
                FROM activity_logs l
                JOIN admins a ON l.admin_id = a.admin_id
                ORDER BY l.log_timestamp DESC
            """
            cursor.execute(query)
            result = cursor.fetchall()
            conn.close()
            return result
        return None
