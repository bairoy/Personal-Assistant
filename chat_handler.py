from langchain_core.messages import HumanMessage
from bot2 import chatbot
from database_manager import DatabaseManager
from typing import List, Tuple, Optional


class ChatHandler:
    def __init__(self):
        self.db = DatabaseManager()
        self.current_user_id: Optional[str] = None
        self.current_session_id: Optional[str] = None
   
    def set_user(self, username: str) -> None:
        """Set the current user"""
        self.current_user_id = self.db.get_or_create_user(username)
   
    def create_new_session(self, username: str) -> str:
        """Create a new chat session"""
        self.set_user(username)
        self.current_session_id = self.db.create_session(self.current_user_id)
        return self.current_session_id
    
    def set_session(self, session_id: str) -> None:
        """Set the current session"""
        self.current_session_id = session_id
    
    def process_message(self, message: str, username: str) -> str:
        """Process user message and return AI response"""
        if not self.current_user_id:
            self.set_user(username)
        
        if not self.current_session_id:
            self.create_new_session(username)
        
        # Insert user message
        self.db.insert_message(self.current_session_id, "user", message)
        
        # Get AI response
        config = {"configurable": {"thread_id": self.current_session_id}}
        response = chatbot.invoke({'messages': [HumanMessage(content=message)]}, config=config)
        ai_reply = response['messages'][-1].content
        
        # Insert AI response
        self.db.insert_message(self.current_session_id, "ai", ai_reply)
        
        return ai_reply
    
    def get_session_history(self, session_id: str = None) -> List[List[str]]:
        """Get formatted chat history for Gradio"""
        if not session_id:
            session_id = self.current_session_id
        
        if not session_id:
            return []
        
        messages = self.db.get_session_messages(session_id)
        history = []
        
        for sender, text in messages:
            if sender == "user":
                history.append([text, None])
            elif sender == "ai":
                if history and history[-1][1] is None:
                    history[-1][1] = text
                else:
                    history.append([None, text])
        
        return history
    
    def get_user_sessions_formatted(self, username: str) -> List[Tuple[str, str]]:
        """Get formatted session list for dropdown"""
        self.set_user(username)
        sessions = self.db.get_user_sessions(self.current_user_id)
        
        choices = []
        for session_id, session_name, start_time, msg_count in sessions:
            display_text = f"{session_name} ({msg_count} messages)"
            choices.append((display_text, session_id))
        
        return choices
   
    def rename_session(self, session_id: str, new_name: str) -> None:
        """Rename a session"""
        self.db.update_session_name(session_id, new_name)
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session"""
        self.db.delete_session(session_id)
        if self.current_session_id == session_id:
            self.current_session_id = None