"""Exploration method base class and implementations"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from ..models.conversation import Message, MethodDefinition


class ExplorationMethod(ABC):
    """Abstract base class for therapeutic exploration methods"""
    
    def __init__(self, definition: MethodDefinition):
        self.definition = definition
    
    @property
    def id(self) -> str:
        return self.definition.id
    
    @property
    def name(self) -> str:
        return self.definition.name
    
    def get_system_instructions(self) -> str:
        """Get system instructions for this method"""
        return self.definition.system_instructions
    
    @abstractmethod
    def format_prompt(self, context: List[Message], user_input: str) -> str:
        """Format the prompt based on method-specific logic"""
        pass
    
    def validate_response(self, response: str) -> bool:
        """Validate if response adheres to method principles"""
        # Default: check for question marks for inquiry-based methods
        # Override in subclasses for specific validation
        return True
    
    def get_opening_prompt(self) -> str:
        """Get opening prompt for this method"""
        return f"Let's explore this using {self.name}."
    
    def get_transition_prompt(self) -> str:
        """Get prompt for transitioning into this method"""
        return f"I'll use {self.name} to help you explore this."
    
    def get_closing_prompt(self) -> str:
        """Get closing prompt after using this method"""
        return "How did that feel? Would you like to continue with this approach?"


class SocraticQuestioning(ExplorationMethod):
    """Socratic Questioning / Guided Discovery method"""
    
    def format_prompt(self, context: List[Message], user_input: str) -> str:
        """Format prompt for Socratic questioning"""
        # Encourage open-ended questions that uncover assumptions
        return f"""Using Socratic questioning, respond to: "{user_input}"

Remember to:
- Ask ONE open-ended question
- Explore underlying assumptions gently
- Encourage self-discovery rather than providing answers
- Keep tone curious and non-judgmental
- Limit response to 2-3 sentences maximum"""
    
    def validate_response(self, response: str) -> bool:
        """Check if response contains a question"""
        return "?" in response


class ReflectiveListening(ExplorationMethod):
    """Reflective Listening method"""
    
    def format_prompt(self, context: List[Message], user_input: str) -> str:
        """Format prompt for reflective listening"""
        return f"""Using reflective listening, respond to: "{user_input}"

Remember to:
- Mirror the emotion and content you hear
- Use phrases like "It sounds like..." or "You're feeling..."
- Validate without judging or advising
- Keep response short (1-2 sentences)
- Reflect both feeling and meaning"""
    
    def validate_response(self, response: str) -> bool:
        """Check for reflective phrases"""
        reflective_phrases = [
            "it sounds like",
            "you're feeling",
            "it seems like",
            "you feel",
            "what i hear is"
        ]
        return any(phrase in response.lower() for phrase in reflective_phrases)


class ThoughtRecords(ExplorationMethod):
    """Thought Records / Cognitive Restructuring method"""
    
    def format_prompt(self, context: List[Message], user_input: str) -> str:
        """Format prompt for thought records"""
        return f"""Using thought records/cognitive restructuring, respond to: "{user_input}"

Remember to:
- Help identify the automatic thought
- Explore evidence for and against the thought
- Ask about alternative perspectives
- Keep it structured but gentle
- Limit to ONE clarifying question"""


class BehavioralAnalysis(ExplorationMethod):
    """Behavioral Analysis (ABC model) method"""
    
    def format_prompt(self, context: List[Message], user_input: str) -> str:
        """Format prompt for behavioral analysis"""
        return f"""Using behavioral analysis (ABC model), respond to: "{user_input}"

Remember to:
- Explore Antecedent (what happened before)
- Understand Behavior (what they did)
- Examine Consequence (what followed)
- Ask about ONE part of the ABC model
- Keep response conversational"""


class SchemaExploration(ExplorationMethod):
    """Schema Exploration method"""
    
    def format_prompt(self, context: List[Message], user_input: str) -> str:
        """Format prompt for schema exploration"""
        return f"""Using schema exploration, respond to: "{user_input}"

Remember to:
- Look for deeper core beliefs and patterns
- Explore how this connects to earlier experiences
- Ask about recurring themes gently
- Keep it non-threatening and curious
- One question at a time"""


class MindfulnessInquiry(ExplorationMethod):
    """Mindfulness-Based Inquiry method"""
    
    def format_prompt(self, context: List[Message], user_input: str) -> str:
        """Format prompt for mindfulness inquiry"""
        return f"""Using mindfulness-based inquiry, respond to: "{user_input}"

Remember to:
- Invite awareness of present-moment sensations
- Ask about thoughts, feelings, body sensations
- Use curious, non-judgmental tone
- Encourage observation without changing
- Keep it simple and grounding"""
