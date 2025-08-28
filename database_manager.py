import uuid
from datetime import datetime
from typing import List, Tuple, Optional
from database import conn


conn.autocommit = True

class DatabaseManager:
    
    @staticmethod
    def insert_message(session_id: str, sender: str, message_text: str) -> None:
        """Insert a message into the database"""
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages (message_id, session_id, sender, message_text, created_at) 
                VALUES (%s, %s, %s, %s, %s)
                """,
                (str(uuid.uuid4()), session_id, sender, message_text, datetime.now())
            )
            if sender == "user":
                cur.execute(
                    "SELECT COUNT(*) FROM messages WHERE session_id = %s",
                    (session_id,)
                )
                msg_count = cur.fetchone()[0]
                if msg_count == 1:
                    session_name = message_text[:30]
                    cur.execute(
                        "UPDATE sessions SET session_name = %s WHERE session_id = %s",
                        (session_name,session_id)
                    )
   
    @staticmethod
    def create_session(user_id: str) -> str:
        """Create a new session without name (name set after first message)"""
        session_id = str(uuid.uuid4())
        
        
            
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessions (session_id, user_id,  start_time)
                VALUES (%s, %s,  %s)
                """,
                (session_id, user_id,  datetime.now())
            )
        return session_id
    
    @staticmethod
    def create_user(username: str) -> str:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users(user_id, username, created_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, username, datetime.now())
            )
        return user_id
    
    @staticmethod
    def get_or_create_user(username: str) -> str:
        """Get existing user or create new one"""
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            result = cur.fetchone()
            if result:
                return result[0]
            else:
                return DatabaseManager.create_user(username)
   
    @staticmethod
    def get_session_messages(session_id: str) -> List[Tuple[str, str]]:
        """Get all messages from a session"""
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sender, message_text FROM messages 
                WHERE session_id = %s 
                ORDER BY created_at ASC
                """, 
                (session_id,)
            )
            return cur.fetchall()
   
    @staticmethod
    def get_user_sessions(user_id: str) -> List[Tuple[str, str, datetime, int]]:
        """Get all sessions for a user with session names"""
        with conn.cursor() as cur:
            cur.execute(
                 """
            SELECT session_id, COALESCE(session_name, '[unnamed]') as session_name,
                   start_time,
                   (SELECT COUNT(*) FROM messages WHERE session_id = s.session_id) as msg_count
            FROM sessions s 
            WHERE user_id = %s 
            ORDER BY start_time DESC 
            LIMIT 20
            """, 
                (user_id,)
            )
            return cur.fetchall()
   
    @staticmethod
    def update_session_name(session_id: str, new_name: str) -> None:
        """Update session name"""
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sessions SET session_name = %s WHERE session_id = %s",
                (new_name, session_id)
            )
    
    @staticmethod
    def get_session_info(session_id: str) -> Optional[Tuple[str, str, datetime]]:
        """Get session info by ID"""
        with conn.cursor() as cur:
            cur.execute(
                "SELECT session_id, session_name, start_time FROM sessions WHERE session_id = %s",
                (session_id,)
            )
            return cur.fetchone()
   
    @staticmethod
    def delete_session(session_id: str) -> None:
        """Delete a session and all its messages"""
        with conn.cursor() as cur:
            cur.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
            cur.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))