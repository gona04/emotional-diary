"""Prompt Builder - constructs context-aware prompts"""

import logging
from typing import List, Optional
from ..models.conversation import Message, ConversationStage, ConversationSession
from ..exploration_methods import get_method

LOG = logging.getLogger("prompt_builder")


class PromptBuilder:
    """Builds dynamic prompts based on context and method"""
    
    BASE_INSTRUCTIONS = """Goal: Create a calm, supportive space where the person feels genuinely heard and understood — guiding them gently based on how they prefer to explore their thoughts or emotions.

Key principles:
- Start light and personable — not heavy or clinical
- Keep responses SHORT (1-3 sentences maximum)
- Ask ONE question at a time
- Be curious, validating, and empathetic
- Match the user's emotional tone
- Never give direct advice unless asked
- Check in periodically"""
    
    STAGE_PROMPTS = {
        ConversationStage.OPENING: """The user just finished the intro joke. 
Greet them warmly and ask how their day has been. Keep it light and personable.
Example: "Hey there, it's good to see you. How's your day been so far?\"""",
        
        ConversationStage.METHOD_SELECTION: """After the user shares a bit, invite them to choose an exploration approach.
Say something like: "Before we go deeper, would you like to pick a way we explore this? I have several different approaches we could try.\"""",
        
        ConversationStage.ACTIVE_EXPLORATION: """You are actively exploring using the selected method.
Follow the method's specific instructions. Keep responses short and focused.
Ask ONE question at a time. Be curious and validating.""",
        
        ConversationStage.CHECK_IN: """Pause and check in with the user.
Ask: "Is this helping you see things a bit more clearly, or would you like to shift our approach?\"""",
        
        ConversationStage.CLOSURE: """Wrap up the conversation warmly.
Affirm their effort and offer encouragement. Keep it brief and supportive.
Example: "You've done really well reflecting on this today.\""""
    }
    
    def build_system_prompt(
        self,
        session: ConversationSession,
        method_id: Optional[str] = None
    ) -> str:
        """Build complete system prompt based on stage and method"""
        
        # Start with base instructions
        prompt = self.BASE_INSTRUCTIONS
        
        # Add stage-specific guidance
        stage_guidance = self.STAGE_PROMPTS.get(session.current_stage, "")
        if stage_guidance:
            prompt += f"\n\nCurrent Stage: {session.current_stage.value.upper()}\n{stage_guidance}"
        
        # Add method-specific instructions if in active exploration
        if method_id and session.current_stage == ConversationStage.ACTIVE_EXPLORATION:
            method = get_method(method_id)
            if method:
                prompt += f"\n\nExploration Method: {method.name}\n{method.get_system_instructions()}"
        
        return prompt
    
    def build_user_prompt(
        self,
        user_message: str,
        session: ConversationSession
    ) -> str:
        """Build user prompt with context"""
        
        # If using a specific method, format the prompt according to that method
        if session.selected_method and session.current_stage == ConversationStage.ACTIVE_EXPLORATION:
            method = get_method(session.selected_method)
            if method:
                recent_context = session.get_context(max_tokens=500)
                return method.format_prompt(recent_context, user_message)
        
        # Default: just return the user message
        return user_message
    
    def inject_memory(
        self,
        prompt: str,
        relevant_memories: List[str]
    ) -> str:
        """Inject relevant memories into prompt"""
        if not relevant_memories:
            return prompt
        
        memory_context = "\n".join([f"- {mem}" for mem in relevant_memories])
        return f"{prompt}\n\nRelevant context from earlier:\n{memory_context}"
    
    def build_messages_for_llm(
        self,
        session: ConversationSession,
        user_input: str,
        relevant_memories: Optional[List[str]] = None
    ) -> List[dict]:
        """Build complete message array for LLM"""
        
        # Build system prompt
        system_prompt = self.build_system_prompt(session, session.selected_method)
        
        # Inject memories if provided
        if relevant_memories:
            system_prompt = self.inject_memory(system_prompt, relevant_memories)
        
        # Get recent conversation context
        recent_messages = session.get_context(max_tokens=2000)
        
        # Build messages array
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history
        for msg in recent_messages:
            if msg.role != "system":  # Don't duplicate system messages
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add current user input
        user_prompt = self.build_user_prompt(user_input, session)
        messages.append({
            "role": "user",
            "content": user_prompt
        })
        
        return messages
