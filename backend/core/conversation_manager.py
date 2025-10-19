"""Conversation Manager - manages all active sessions"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from models.conversation import ConversationSession

LOG = logging.getLogger("conversation_manager")


class ConversationManager:
    """Singleton managing all active conversation sessions"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.sessions: Dict[str, ConversationSession] = {}
        self._initialized = True
        LOG.info("ConversationManager initialized")
    
    def create_session(
        self,
        conn_id: str,
        user_id: Optional[str] = None
    ) -> ConversationSession:
        """Create a new conversation session"""
        session = ConversationSession(
            conn_id=conn_id,
            user_id=user_id
        )
        self.sessions[conn_id] = session
        LOG.info(f"Created session for conn_id: {conn_id}, user_id: {user_id}")
        return session
    
    def get_session(self, conn_id: str) -> Optional[ConversationSession]:
        """Get existing session by connection ID"""
        return self.sessions.get(conn_id)
    
    def delete_session(self, conn_id: str) -> None:
        """Delete a session"""
        if conn_id in self.sessions:
            del self.sessions[conn_id]
            LOG.info(f"Deleted session for conn_id: {conn_id}")
    
    def cleanup_expired_sessions(self, timeout_minutes: int = 60) -> int:
        """Clean up sessions inactive for longer than timeout"""
        now = datetime.now()
        expired = []
        
        for conn_id, session in self.sessions.items():
            if now - session.last_active > timedelta(minutes=timeout_minutes):
                expired.append(conn_id)
        
        for conn_id in expired:
            self.delete_session(conn_id)
        
        if expired:
            LOG.info(f"Cleaned up {len(expired)} expired sessions")
        
        return len(expired)
    
    def get_active_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)
