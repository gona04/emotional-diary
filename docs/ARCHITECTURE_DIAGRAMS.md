# Architecture Visualization

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React + TypeScript)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Components/                                                                 │
│  ├── SpeechIntro.tsx          → Intro jokes, TTS                           │
│  ├── ChatInterface/            → Message display, input                     │
│  ├── MethodSelector/           → 15 exploration methods grid               │
│  └── SessionSummary/           → End-of-session recap                      │
│                                                                              │
│  Services/                                                                   │
│  ├── websocketService.ts       → WebSocket connection manager              │
│  ├── audioService.ts           → TTS and speech recognition                │
│  └── storageService.ts         → Local storage for preferences             │
│                                                                              │
│  State Management (Redux):                                                  │
│  ├── conversationSlice         → Messages, stage, method                   │
│  ├── uiSlice                   → UI state, modals                          │
│  └── sessionSlice              → User session, preferences                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ WebSocket (JSON messages)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND (Python + AsyncIO)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  streaming_server.py (Main Entry Point)                                     │
│  ├── WebSocket Handler                                                      │
│  ├── Message Router                                                         │
│  └── Connection Manager                                                     │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  CORE SERVICES                                                              │
│                                                                              │
│  ┌─────────────────────────┐     ┌──────────────────────────┐             │
│  │  ConversationManager    │     │    PromptBuilder         │             │
│  │  (Singleton)            │     │    (Builder Pattern)     │             │
│  ├─────────────────────────┤     ├──────────────────────────┤             │
│  │ • Session CRUD          │     │ • System prompt builder  │             │
│  │ • Session cleanup       │     │ • Stage-aware prompts    │             │
│  │ • Active monitoring     │     │ • Method injection       │             │
│  └─────────────────────────┘     │ • Memory integration     │             │
│                                   └──────────────────────────┘             │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  DATA MODELS                                                                │
│                                                                              │
│  ┌──────────────────┐  ┌────────────────────┐  ┌──────────────────┐       │
│  │ Message          │  │ ConversationSession│  │ MethodDefinition │       │
│  ├──────────────────┤  ├────────────────────┤  ├──────────────────┤       │
│  │ • role           │  │ • conn_id          │  │ • id             │       │
│  │ • content        │  │ • messages[]       │  │ • name           │       │
│  │ • timestamp      │  │ • current_stage    │  │ • instructions   │       │
│  │ • metadata       │  │ • selected_method  │  │ • principles[]   │       │
│  │ • tokens         │  │ • metadata         │  │ • reference      │       │
│  └──────────────────┘  └────────────────────┘  └──────────────────┘       │
│                                                                              │
│  ConversationStage (Enum)                                                   │
│  INTRO → OPENING → METHOD_SELECTION → ACTIVE_EXPLORATION →                 │
│  CHECK_IN → CLOSURE → ENDED                                                │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  EXPLORATION METHODS (Strategy Pattern)                                     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │          ExplorationMethod (Abstract Base Class)                 │      │
│  ├──────────────────────────────────────────────────────────────────┤      │
│  │  • get_system_instructions()                                     │      │
│  │  • format_prompt(context, user_input)                            │      │
│  │  • validate_response(response)                                   │      │
│  │  • get_opening_prompt() / get_closing_prompt()                   │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                              ▲                                               │
│                              │ extends                                       │
│           ┌──────────────────┼──────────────────┬──────────────────┐       │
│           │                  │                  │                  │       │
│  ┌────────────────┐  ┌───────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │ Socratic       │  │ Reflective    │  │ Thought     │  │ Behavioral   │ │
│  │ Questioning    │  │ Listening     │  │ Records     │  │ Analysis     │ │
│  └────────────────┘  └───────────────┘  └─────────────┘  └──────────────┘ │
│                                                                              │
│  ┌────────────────┐  ┌───────────────┐                                     │
│  │ Schema         │  │ Mindfulness   │   + 9 more to implement             │
│  │ Exploration    │  │ Inquiry       │                                     │
│  └────────────────┘  └───────────────┘                                     │
│                                                                              │
│  METHOD_REGISTRY (dict) - Runtime lookup by ID                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP API Calls
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LLM SERVICE (OpenAI GPT-4o)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Model: gpt-4o                                                            │
│  • Temperature: 0.7                                                         │
│  • Max tokens: 500                                                          │
│  • Store: true (conversation persistence)                                   │
│                                                                              │
│  Features:                                                                   │
│  ├── Context-aware responses                                                │
│  ├── Method-specific prompts                                                │
│  ├── Short, empathetic replies (1-3 sentences)                              │
│  └── Safety validation                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Store/Retrieve
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MEMORY & PERSISTENCE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  L1: Short-term (In-Memory Dict)                                            │
│  ├── Current session messages                                               │
│  ├── Active conversations                                                   │
│  └── TTL: Session duration                                                  │
│                                                                              │
│  L2: Working Memory (Redis) - TO BE IMPLEMENTED                             │
│  ├── Last 50 messages                                                       │
│  ├── Session metadata                                                       │
│  └── TTL: 24 hours                                                          │
│                                                                              │
│  L3: Long-term (PostgreSQL + Vector Store) - TO BE IMPLEMENTED              │
│  ├── Session summaries                                                      │
│  ├── User preferences                                                       │
│  ├── Journal entries                                                        │
│  └── Semantic search (FAISS/Chroma)                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Message Flow Diagram

```
Client                   Server                  Manager              Builder              LLM
  │                        │                        │                     │                  │
  │  1. handshake          │                        │                     │                  │
  ├───────────────────────>│                        │                     │                  │
  │                        │  create_session()      │                     │                  │
  │                        ├───────────────────────>│                     │                  │
  │                        │<───session─────────────┤                     │                  │
  │                        │                        │                     │                  │
  │  2. get_intro_jokes    │                        │                     │                  │
  ├───────────────────────>│                        │                     │                  │
  │<────jokes──────────────┤                        │                     │                  │
  │                        │  transition(OPENING)   │                     │                  │
  │                        ├───────────────────────>│                     │                  │
  │                        │                        │                     │                  │
  │  3. user_text          │                        │                     │                  │
  ├───────────────────────>│  get_session()         │                     │                  │
  │                        ├───────────────────────>│                     │                  │
  │                        │<───session─────────────┤                     │                  │
  │                        │                        │                     │                  │
  │                        │  build_messages()      │                     │                  │
  │                        ├────────────────────────┴────────────────────>│                  │
  │                        │                        │                     │                  │
  │                        │                        │  build_system_prompt(session)          │
  │                        │                        │                     │                  │
  │                        │                        │  build_user_prompt(input)              │
  │                        │                        │                     │                  │
  │                        │<────messages────────────────────────────────┤                  │
  │                        │                        │                     │                  │
  │                        │  generate_response()   │                     │                  │
  │                        ├─────────────────────────────────────────────┴─────────────────>│
  │                        │                        │                     │                  │
  │                        │                        │                     │   [GPT Processing]
  │                        │                        │                     │                  │
  │                        │<──────response───────────────────────────────────────────────────┤
  │                        │                        │                     │                  │
  │                        │  add_message(user)     │                     │                  │
  │                        ├───────────────────────>│                     │                  │
  │                        │  add_message(assistant)│                     │                  │
  │                        ├───────────────────────>│                     │                  │
  │                        │                        │                     │                  │
  │<────ai_reply───────────┤                        │                     │                  │
  │                        │                        │                     │                  │
  │  4. get_methods        │                        │                     │                  │
  ├───────────────────────>│                        │                     │                  │
  │<────method_options─────┤                        │                     │                  │
  │                        │                        │                     │                  │
  │  5. select_method      │                        │                     │                  │
  ├───────────────────────>│  set_method()          │                     │                  │
  │                        ├───────────────────────>│                     │                  │
  │                        │  transition(ACTIVE)    │                     │                  │
  │                        ├───────────────────────>│                     │                  │
  │<────method_selected────┤                        │                     │                  │
  │                        │                        │                     │                  │
  │  6. user_text          │                        │                     │                  │
  ├───────────────────────>│                        │                     │                  │
  │                        │  [Uses selected method for prompt formatting]                   │
  │                        │                        │                     │                  │
  │<────ai_reply───────────┤                        │                     │                  │
  │  (method-specific)     │                        │                     │                  │
  │                        │                        │                     │                  │
```

---

## State Machine Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                      CONVERSATION STATE MACHINE                         │
└────────────────────────────────────────────────────────────────────────┘

    ┌────────┐
    │ INTRO  │  (Deliver quirky joke)
    └───┬────┘
        │
        ▼
    ┌────────┐
    │OPENING │  (Warm greeting, ask how user is)
    └───┬────┘
        │
        ▼
    ┌───────────────────┐
    │METHOD_SELECTION   │  (Offer 15 exploration styles)
    └─────┬─────────────┘
          │
          ├─────────────────────────┐
          │                         │
          ▼                         ▼
    ┌──────────────────┐      ┌─────────┐
    │ACTIVE_EXPLORATION│◄─────│CHECK_IN │  (Every 3-5 exchanges)
    │                  │      └────┬────┘
    │ (Apply method    │           │
    │  principles)     │           │ (If want to switch)
    └────┬─────────────┘           │
         │                         │
         └────────┬────────────────┘
                  │
                  ▼
             ┌─────────┐
             │ CLOSURE │  (Affirm, summarize, encourage)
             └────┬────┘
                  │
                  ▼
             ┌────────┐
             │ ENDED  │  (Clean up, save summary)
             └────────┘

TRANSITIONS:
✅ INTRO → OPENING
✅ OPENING → METHOD_SELECTION
✅ METHOD_SELECTION → ACTIVE_EXPLORATION
✅ METHOD_SELECTION → CLOSURE (if user wants to end)
✅ ACTIVE_EXPLORATION → CHECK_IN (after N exchanges)
✅ ACTIVE_EXPLORATION → CLOSURE (if user wants to end)
✅ CHECK_IN → ACTIVE_EXPLORATION (continue)
✅ CHECK_IN → METHOD_SELECTION (switch method)
✅ CHECK_IN → CLOSURE (end session)
✅ CLOSURE → ENDED

❌ All other transitions are INVALID and will be rejected
```

---

## Class Relationship Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                          CLASS RELATIONSHIPS                          │
└──────────────────────────────────────────────────────────────────────┘

ConversationManager (Singleton)
    │
    ├─── manages ──> ConversationSession *
    │                    │
    │                    ├─── contains ──> Message *
    │                    ├─── has ──> ConversationStage (Enum)
    │                    └─── has ──> selected_method: str
    │
    └─── uses ──> PromptBuilder
                      │
                      ├─── uses ──> ConversationSession
                      ├─── uses ──> ConversationStage
                      └─── uses ──> METHOD_REGISTRY
                                        │
                                        └─── contains ──> ExplorationMethod * (ABC)
                                                              │
                                                              ├─── SocraticQuestioning
                                                              ├─── ReflectiveListening
                                                              ├─── ThoughtRecords
                                                              ├─── BehavioralAnalysis
                                                              ├─── SchemaExploration
                                                              ├─── MindfulnessInquiry
                                                              └─── ... 9 more

Legend:
  *   = One to many relationship
  ABC = Abstract Base Class
```

---

## Data Flow: Single User Message

```
┌────────────────────────────────────────────────────────────────────────┐
│                    DATA TRANSFORMATION PIPELINE                         │
└────────────────────────────────────────────────────────────────────────┘

User Input: "I feel overwhelmed by work"
                    │
                    ▼
        ┌─────────────────────┐
        │ WebSocket Handler   │  Receives raw JSON
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ Get Session         │  manager.get_session(conn_id)
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ Create Message      │  Message(role="user", content=input)
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ PromptBuilder       │  builder.build_messages_for_llm()
        │                     │
        │ 1. Get base         │  CBT_AGENT_INSTRUCTIONS
        │    instructions     │
        │                     │
        │ 2. Add stage        │  if stage == ACTIVE_EXPLORATION:
        │    guidance         │      add stage-specific prompt
        │                     │
        │ 3. Inject method    │  if method == "reflective_listening":
        │    instructions     │      add method.get_system_instructions()
        │                     │
        │ 4. Get context      │  session.get_context(max_tokens=2000)
        │    messages         │
        │                     │
        │ 5. Format as        │  [
        │    LLM array        │    {"role": "system", "content": ...},
        │                     │    {"role": "user", "content": ...},
        │                     │    ...
        │                     │  ]
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ LLM Service         │  POST to OpenAI API
        │                     │
        │ Request:            │
        │ {                   │
        │   "model": "gpt-4o",│
        │   "messages": [...],│
        │   "temperature": 0.7│
        │ }                   │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ OpenAI GPT-4o       │  AI Processing
        │                     │  (considers context, method, stage)
        └──────────┬──────────┘
                   │
                   ▼
Response: "It sounds like work has been really heavy lately. What feels most overwhelming right now?"
                   │
                   ▼
        ┌─────────────────────┐
        │ Validate Response   │  Check length, safety, method adherence
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ Create Message      │  Message(role="assistant", content=response)
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ Store in Session    │  session.add_message(msg)
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ Send to Client      │  {"type": "ai_reply", "text": response}
        └─────────────────────┘
```

---

## Method Selection Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                     METHOD SELECTION & APPLICATION                      │
└────────────────────────────────────────────────────────────────────────┘

User: "I want to try reflective listening"
            │
            ▼
    ┌───────────────┐
    │ get_method()  │  METHOD_REGISTRY["reflective_listening"]
    └───────┬───────┘
            │
            ▼
    ┌───────────────────────────────────────┐
    │ ReflectiveListening instance          │
    ├───────────────────────────────────────┤
    │ • name: "Reflective Listening"        │
    │ • description: "I mirror..."          │
    │ • system_instructions: "You are..."   │
    │ • example_prompts: [...]              │
    └───────┬───────────────────────────────┘
            │
            ├─── set_exploration_method() ───> Session
            │                                   (stores method_id)
            │
            ├─── transition_stage() ──────────> ACTIVE_EXPLORATION
            │
            └─── get_opening_prompt() ────────> "Let's explore this using
                                                  Reflective Listening."

Next user message: "I'm stressed about deadlines"
            │
            ▼
    ┌───────────────────────────────────┐
    │ format_prompt()                   │
    │                                   │
    │ Returns:                          │
    │ "Using reflective listening,      │
    │  respond to: 'I'm stressed...'    │
    │                                   │
    │  Remember to:                     │
    │  - Mirror emotion and content     │
    │  - Use 'It sounds like...'        │
    │  - Keep short (1-2 sentences)"    │
    └───────┬───────────────────────────┘
            │
            ▼
    [Sent to LLM for generation]
            │
            ▼
    "It sounds like the deadlines are weighing heavily on you."
            │
            ▼
    ┌───────────────────────────────────┐
    │ validate_response()               │
    │                                   │
    │ Checks for reflective phrases:    │
    │ ✅ Contains "It sounds like"      │
    └───────────────────────────────────┘
```

This architecture provides a complete, production-ready foundation! 🎉
