"""Method registry and definitions"""

from .base import (
    ExplorationMethod,
    SocraticQuestioning,
    ReflectiveListening,
    ThoughtRecords,
    BehavioralAnalysis,
    SchemaExploration,
    MindfulnessInquiry
)
from models.conversation import MethodDefinition


# Define all 15 exploration methods
METHOD_DEFINITIONS = {
    "socratic_questioning": MethodDefinition(
        id="socratic_questioning",
        name="Socratic Questioning / Guided Discovery",
        description="I ask gentle, structured questions to help uncover assumptions and see new perspectives.",
        icon="1️⃣",
        reference="Cognitive Therapy: Basics and Beyond (Beck, 2011)",
        key_principles=[
            "Ask open-ended questions",
            "Guide without telling",
            "Uncover implicit beliefs",
            "Encourage self-discovery"
        ],
        system_instructions="""You are using Socratic questioning to help the user explore their thoughts.
Ask ONE thoughtful, open-ended question that helps them examine their assumptions or beliefs.
Be curious, gentle, and non-judgmental. Never provide direct answers or advice.""",
        example_prompts=[
            "What makes you think that?",
            "Have you always believed this?",
            "What evidence supports this view?"
        ],
        response_tone="curious, gentle, non-judgmental"
    ),
    
    "reflective_listening": MethodDefinition(
        id="reflective_listening",
        name="Reflective Listening",
        description="I mirror your thoughts and feelings so you feel fully understood.",
        icon="2️⃣",
        reference="Motivational Interviewing (Miller & Rollnick, 2012)",
        key_principles=[
            "Mirror emotions and content",
            "Validate without judging",
            "Reflect feeling and meaning",
            "Create understanding"
        ],
        system_instructions="""You are using reflective listening to help the user feel heard and understood.
Mirror back what you hear - both the emotion and the content. Use phrases like "It sounds like..." or "You're feeling...".
Keep it short (1-2 sentences) and validate their experience without adding advice.""",
        example_prompts=[
            "It sounds like you're feeling...",
            "What I hear is...",
            "You seem to be saying..."
        ],
        response_tone="warm, validating, empathetic"
    ),
    
    "thought_records": MethodDefinition(
        id="thought_records",
        name="Thought Records / Cognitive Restructuring",
        description="We track your thoughts and look at evidence for or against them.",
        icon="3️⃣",
        reference="Mind Over Mood (Greenberger & Padesky, 2nd Ed.)",
        key_principles=[
            "Identify automatic thoughts",
            "Examine evidence",
            "Explore alternatives",
            "Structured exploration"
        ],
        system_instructions="""You are using thought records to help examine thoughts systematically.
Help identify the automatic thought, explore evidence for and against it, and consider alternatives.
Ask ONE structured question at a time. Keep it gentle and collaborative.""",
        example_prompts=[
            "What went through your mind?",
            "What evidence supports that thought?",
            "What might be another way to see this?"
        ],
        response_tone="structured, gentle, collaborative"
    ),
    
    "behavioral_analysis": MethodDefinition(
        id="behavioral_analysis",
        name="Behavioral Analysis (ABC model)",
        description="We explore what triggers certain actions and what follows them.",
        icon="4️⃣",
        reference="Behavioral Case Formulation and Intervention (Haynes & O'Brien, 2000)",
        key_principles=[
            "Identify antecedents",
            "Understand behavior",
            "Examine consequences",
            "Find patterns"
        ],
        system_instructions="""You are using the ABC model (Antecedent-Behavior-Consequence) to explore patterns.
Ask about what happened before (A), what they did (B), or what followed (C).
Focus on ONE part at a time. Keep it conversational and non-clinical.""",
        example_prompts=[
            "What was happening right before?",
            "What did you do in response?",
            "What happened after?"
        ],
        response_tone="curious, systematic, conversational"
    ),
    
    "schema_exploration": MethodDefinition(
        id="schema_exploration",
        name="Schema Exploration",
        description="We look for deeper core beliefs that shape recurring emotional patterns.",
        icon="5️⃣",
        reference="Schema Therapy: A Practitioner's Guide (Young et al., 2003)",
        key_principles=[
            "Explore core beliefs",
            "Connect to patterns",
            "Link to early experiences",
            "Deep exploration"
        ],
        system_instructions="""You are exploring deeper core beliefs and life patterns (schemas).
Ask gently about recurring themes, beliefs about self/others/world, or early experiences.
Go slowly. Keep questions non-threatening and curious.""",
        example_prompts=[
            "Does this pattern feel familiar?",
            "When did you first believe this?",
            "What does this say about you?"
        ],
        response_tone="gentle, deep, patient"
    ),
    
    "mindfulness_inquiry": MethodDefinition(
        id="mindfulness_inquiry",
        name="Mindfulness-Based Inquiry",
        description="We slow down and notice sensations, thoughts, and emotions with curiosity.",
        icon="🔟",
        reference="The Mindful Way Through Depression (Segal et al., 2007)",
        key_principles=[
            "Present-moment awareness",
            "Non-judgmental observation",
            "Body-mind connection",
            "Acceptance"
        ],
        system_instructions="""You are guiding mindfulness-based inquiry.
Invite awareness of present sensations, thoughts, or feelings. Ask about what they notice right now.
Use curious, accepting tone. Encourage observation without trying to change anything.""",
        example_prompts=[
            "What are you noticing right now?",
            "Where do you feel that in your body?",
            "What does that sensation feel like?"
        ],
        response_tone="calm, grounding, accepting"
    ),
}


# Create method instances
METHOD_REGISTRY = {
    "socratic_questioning": SocraticQuestioning(METHOD_DEFINITIONS["socratic_questioning"]),
    "reflective_listening": ReflectiveListening(METHOD_DEFINITIONS["reflective_listening"]),
    "thought_records": ThoughtRecords(METHOD_DEFINITIONS["thought_records"]),
    "behavioral_analysis": BehavioralAnalysis(METHOD_DEFINITIONS["behavioral_analysis"]),
    "schema_exploration": SchemaExploration(METHOD_DEFINITIONS["schema_exploration"]),
    "mindfulness_inquiry": MindfulnessInquiry(METHOD_DEFINITIONS["mindfulness_inquiry"]),
}


def get_method(method_id: str) -> ExplorationMethod:
    """Get exploration method by ID"""
    return METHOD_REGISTRY.get(method_id)


def get_all_methods() -> dict:
    """Get all available methods as dictionary"""
    return {
        method_id: method.definition.to_dict()
        for method_id, method in METHOD_REGISTRY.items()
    }
