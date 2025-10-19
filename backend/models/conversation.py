"""Core data models for the therapeutic chat application"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import json


class ConversationStage(Enum):
    """Conversation flow stages"""
    INTRO = "intro"
    OPENING = "opening"
    METHOD_SELECTION = "method_selection"
    ACTIVE_EXPLORATION = "active_exploration"
    CHECK_IN = "check_in"
    CLOSURE = "closure"
    ENDED = "ended"


# Valid stage transitions
ALLOWED_TRANSITIONS = {
    ConversationStage.INTRO: [ConversationStage.OPENING],
    ConversationStage.OPENING: [ConversationStage.METHOD_SELECTION],
    ConversationStage.METHOD_SELECTION: [
        ConversationStage.ACTIVE_EXPLORATION,
        ConversationStage.CLOSURE
    ],
    ConversationStage.ACTIVE_EXPLORATION: [
        ConversationStage.CHECK_IN,
        ConversationStage.CLOSURE
    ],
    ConversationStage.CHECK_IN: [
        ConversationStage.ACTIVE_EXPLORATION,
        ConversationStage.METHOD_SELECTION,
        ConversationStage.CLOSURE
    ],
    ConversationStage.CLOSURE: [ConversationStage.ENDED],
}


@dataclass
class Message:
    """Individual message in conversation"""
    role: str  # "system" | "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "tokens": self.tokens
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        """Create from dictionary"""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            tokens=data.get("tokens", 0)
        )


@dataclass
class ConversationSession:
    """State for a single conversation session"""
    conn_id: str
    user_id: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    current_stage: ConversationStage = ConversationStage.INTRO
    selected_method: Optional[str] = None  # method ID
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    
    def add_message(self, message: Message) -> None:
        """Add message to conversation"""
        self.messages.append(message)
        self.last_active = datetime.now()
    
    def add_message_from_text(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Convenience method to add message from role and content"""
        message = Message(role=role, content=content, metadata=metadata or {})
        self.add_message(message)
    
    def get_context(self, max_tokens: int = 2000) -> List[Message]:
        """Get recent messages within token budget"""
        context = []
        total_tokens = 0
        
        # Iterate from most recent
        for msg in reversed(self.messages):
            if total_tokens + msg.tokens > max_tokens:
                break
            context.insert(0, msg)
            total_tokens += msg.tokens
        
        return context
    
    def set_exploration_method(self, method_id: str) -> None:
        """Set the selected exploration method"""
        self.selected_method = method_id
        self.metadata["method"] = method_id
    
    def select_method(self, method_id: str) -> None:
        """Alias for set_exploration_method"""
        self.set_exploration_method(method_id)
    
    @property
    def selected_method_id(self) -> Optional[str]:
        """Get the selected method ID"""
        return self.selected_method
    
    def transition_stage(self, new_stage: ConversationStage) -> bool:
        """Transition to new stage if valid"""
        if new_stage in ALLOWED_TRANSITIONS.get(self.current_stage, []):
            self.current_stage = new_stage
            self.metadata["last_stage_change"] = datetime.now().isoformat()
            return True
        return False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "conn_id": self.conn_id,
            "user_id": self.user_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "current_stage": self.current_stage.value,
            "selected_method": self.selected_method,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ConversationSession":
        """Create from dictionary"""
        return cls(
            conn_id=data["conn_id"],
            user_id=data.get("user_id"),
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            current_stage=ConversationStage(data["current_stage"]),
            selected_method=data.get("selected_method"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active=datetime.fromisoformat(data["last_active"])
        )


@dataclass
class MethodDefinition:
    """Definition of an exploration method"""
    id: str
    name: str
    description: str
    icon: str
    reference: str
    key_principles: List[str]
    system_instructions: str
    example_prompts: List[str] = field(default_factory=list)
    response_tone: str = "warm, empathetic"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
