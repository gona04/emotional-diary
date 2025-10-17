# Low-Level Design: Therapeutic AI Chat Application

## 1. System Overview

### Goal
Provide users with empathetic, structured therapeutic conversations grounded in evidence-based psychological frameworks. The system adapts to user-selected exploration methods while maintaining a warm, human-like conversational tone.

### High-Level Architecture
```
┌─────────────┐     WebSocket/REST      ┌──────────────┐
│   Frontend  │ ◄──────────────────────► │   Backend    │
│  (React)    │                          │  (Python)    │
└─────────────┘                          └──────┬───────┘
                                                 │
                                                 ▼
                                         ┌──────────────┐
                                         │  LLM Service │
                                         │  (GPT-4o)    │
                                         └──────────────┘
                                                 │
                                                 ▼
                                         ┌──────────────┐
                                         │   Memory     │
                                         │   Layer      │
                                         └──────────────┘
```

**Components:**
- **Frontend**: React + TypeScript for UI/UX
- **Backend**: Python WebSocket server with async handlers
- **LLM Service**: OpenAI GPT-4o with CBT agent instructions
- **Memory Layer**: In-memory/Redis for conversation context

---

## 2. Core Components and Classes

### 2.1 Backend Architecture

#### **ConversationManager** (Singleton)
Manages all active user sessions and conversation states.

```python
class ConversationManager:
    """Singleton managing all active conversations"""
    
    # Attributes
    sessions: Dict[str, ConversationSession]
    
    # Methods
    def create_session(conn_id: str, user_id: Optional[str]) -> ConversationSession
    def get_session(conn_id: str) -> Optional[ConversationSession]
    def delete_session(conn_id: str) -> None
    def cleanup_expired_sessions() -> None
```

#### **ConversationSession**
Represents a single user's conversation context.

```python
class ConversationSession:
    """State for a single conversation session"""
    
    # Attributes
    conn_id: str
    user_id: Optional[str]
    messages: List[Message]
    current_stage: ConversationStage
    selected_method: Optional[ExplorationMethod]
    metadata: Dict[str, Any]
    created_at: datetime
    last_active: datetime
    
    # Methods
    def add_message(message: Message) -> None
    def get_context(max_tokens: int) -> List[Message]
    def set_exploration_method(method: ExplorationMethod) -> None
    def transition_stage(new_stage: ConversationStage) -> None
    def to_dict() -> Dict
    def from_dict(data: Dict) -> ConversationSession
```

#### **ExplorationMethod** (Strategy Pattern)
Base class for therapeutic exploration techniques.

```python
class ExplorationMethod(ABC):
    """Abstract base for exploration methods"""
    
    # Attributes
    name: str
    description: str
    key_principles: List[str]
    reference: str
    
    # Methods
    @abstractmethod
    def get_system_instructions() -> str
    
    @abstractmethod
    def format_prompt(context: ConversationContext) -> str
    
    @abstractmethod
    def validate_response(response: str) -> bool
    
    def get_opening_prompt() -> str
    def get_transition_prompt() -> str
    def get_closing_prompt() -> str
```

**Concrete Implementations:**
```python
class SocraticQuestioning(ExplorationMethod):
    """Guided discovery through structured questions"""
    pass

class ReflectiveListening(ExplorationMethod):
    """Mirroring thoughts and feelings"""
    pass

class ThoughtRecords(ExplorationMethod):
    """Cognitive restructuring through evidence tracking"""
    pass

class BehavioralAnalysis(ExplorationMethod):
    """ABC model for behavioral patterns"""
    pass

class SchemaExploration(ExplorationMethod):
    """Deep core beliefs and patterns"""
    pass

# ... 10 more implementations
```

#### **ConversationStage** (State Machine)
Enum representing conversation flow stages.

```python
class ConversationStage(Enum):
    INTRO = "intro"
    OPENING = "opening"
    METHOD_SELECTION = "method_selection"
    ACTIVE_EXPLORATION = "active_exploration"
    CHECK_IN = "check_in"
    CLOSURE = "closure"
    ENDED = "ended"
```

#### **Message**
Individual message in conversation.

```python
@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]
    tokens: int
    
    def to_dict() -> Dict
    def from_dict(data: Dict) -> Message
```

#### **PromptBuilder**
Constructs context-aware prompts for the LLM.

```python
class PromptBuilder:
    """Builds dynamic prompts based on context and method"""
    
    # Attributes
    base_instructions: str
    method_instructions: Dict[str, str]
    
    # Methods
    def build_system_prompt(
        stage: ConversationStage,
        method: Optional[ExplorationMethod]
    ) -> str
    
    def build_user_prompt(
        user_message: str,
        context: List[Message]
    ) -> str
    
    def inject_memory(
        prompt: str,
        relevant_memories: List[str]
    ) -> str
```

#### **LLMService**
Handles all LLM interactions.

```python
class LLMService:
    """Manages OpenAI API calls and response streaming"""
    
    # Attributes
    api_key: str
    model: str
    base_url: str
    client: AsyncOpenAI
    
    # Methods
    async def generate_response(
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str
    
    async def stream_response(
        messages: List[Message],
        callback: Callable[[str], Awaitable[None]]
    ) -> str
    
    def count_tokens(text: str) -> int
    
    def validate_response(response: str) -> Tuple[bool, Optional[str]]
```

#### **MemoryManager**
Manages conversation memory and retrieval.

```python
class MemoryManager:
    """Handles short-term and long-term memory"""
    
    # Attributes
    short_term_cache: Dict[str, List[Message]]
    vector_store: Optional[VectorStore]
    
    # Methods
    def store_message(conn_id: str, message: Message) -> None
    
    def get_recent_context(
        conn_id: str,
        max_messages: int = 10
    ) -> List[Message]
    
    async def search_relevant_memories(
        conn_id: str,
        query: str,
        top_k: int = 3
    ) -> List[str]
    
    def summarize_session(conn_id: str) -> str
    
    def persist_session(conn_id: str, summary: str) -> None
```

#### **SafetyValidator**
Validates inputs and outputs for safety.

```python
class SafetyValidator:
    """Content moderation and safety checks"""
    
    # Methods
    def validate_user_input(text: str) -> Tuple[bool, Optional[str]]
    
    def validate_assistant_output(text: str) -> Tuple[bool, Optional[str]]
    
    def check_crisis_keywords(text: str) -> bool
    
    def get_crisis_resources() -> List[Dict[str, str]]
```

---

## 3. Flow Description

### 3.1 Full Conversation Flow

```
User Connects
     │
     ▼
[INTRO Stage]
  └─► Deliver quirky intro joke
     │
     ▼
[OPENING Stage]
  └─► Warm greeting: "Hey there, how's your day been?"
     │
     ▼
  User responds
     │
     ▼
  Validate and empathize
     │
     ▼
[METHOD_SELECTION Stage]
  └─► Present 15 exploration methods
     │
     ▼
  User selects method
     │
     ▼
[ACTIVE_EXPLORATION Stage]
  └─► Apply selected method's logic
  │   - Use method-specific prompts
  │   - Keep responses short (2-3 sentences)
  │   - Ask one question at a time
  │   - Validate user understanding
  │
  └─► After 3-5 exchanges
     │
     ▼
[CHECK_IN Stage]
  └─► "Is this helping? Want to shift approaches?"
     │
     ▼
  If YES: Continue exploration
  If NO:  Return to METHOD_SELECTION
     │
     ▼
[CLOSURE Stage]
  └─► Affirm progress
  └─► Summarize session
  └─► Offer next steps
     │
     ▼
[ENDED Stage]
  └─► Save session summary
  └─► Clean up memory
```

### 3.2 State Transitions

```python
# State Machine Transitions
ALLOWED_TRANSITIONS = {
    ConversationStage.INTRO: [ConversationStage.OPENING],
    ConversationStage.OPENING: [ConversationStage.METHOD_SELECTION],
    ConversationStage.METHOD_SELECTION: [
        ConversationStage.ACTIVE_EXPLORATION,
        ConversationStage.CLOSURE  # User wants to end
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
```

---

## 4. Data Structures

### 4.1 Message Schema

```json
{
  "role": "user|assistant|system",
  "content": "Message text",
  "timestamp": "2025-10-17T10:30:00Z",
  "metadata": {
    "stage": "active_exploration",
    "method": "socratic_questioning",
    "tokens": 45,
    "sentiment": "neutral",
    "crisis_detected": false
  }
}
```

### 4.2 Conversation State

```json
{
  "conn_id": "a1b2c3d4",
  "user_id": "user_12345",
  "current_stage": "active_exploration",
  "selected_method": "reflective_listening",
  "messages": [...],
  "metadata": {
    "session_start": "2025-10-17T10:00:00Z",
    "last_active": "2025-10-17T10:30:00Z",
    "exchange_count": 7,
    "method_switches": 0,
    "sentiment_trend": ["neutral", "positive", "positive"]
  },
  "context_summary": "User discussing work stress and anxiety..."
}
```

### 4.3 Exploration Method Definition

```json
{
  "id": "socratic_questioning",
  "name": "Socratic Questioning / Guided Discovery",
  "description": "Gentle, structured questions to uncover assumptions",
  "icon": "1️⃣",
  "reference": "Cognitive Therapy: Basics and Beyond (Beck, 2011)",
  "key_principles": [
    "Ask open-ended questions",
    "Guide without telling",
    "Uncover implicit beliefs",
    "Encourage self-discovery"
  ],
  "system_instructions": "You are using Socratic questioning...",
  "example_prompts": [
    "What makes you think that?",
    "Have you always believed this?",
    "What evidence supports this view?"
  ],
  "response_tone": "curious, gentle, non-judgmental"
}
```

### 4.4 User Session

```json
{
  "user_id": "user_12345",
  "sessions": [
    {
      "session_id": "sess_001",
      "date": "2025-10-17",
      "duration_minutes": 25,
      "method_used": "reflective_listening",
      "summary": "User explored work-related anxiety...",
      "key_insights": [
        "Perfectionism triggers stress",
        "Need for validation from manager"
      ],
      "sentiment_arc": ["neutral", "sad", "hopeful"],
      "follow_up_recommended": true
    }
  ],
  "preferences": {
    "preferred_methods": ["reflective_listening", "mindfulness"],
    "voice_speed": 1.0,
    "text_display": true
  }
}
```

---

## 5. Model Integration

### 5.1 Prompt Construction Pipeline

```python
def build_llm_request(session: ConversationSession, user_input: str) -> Dict:
    """Constructs complete LLM request"""
    
    # 1. Get base system instructions
    base_system = CBT_AGENT_INSTRUCTIONS
    
    # 2. Add method-specific instructions
    if session.selected_method:
        method_instructions = session.selected_method.get_system_instructions()
        system_prompt = f"{base_system}\n\n{method_instructions}"
    else:
        system_prompt = base_system
    
    # 3. Inject relevant memories
    relevant_memories = memory_manager.search_relevant_memories(
        session.conn_id, user_input
    )
    if relevant_memories:
        memory_context = "\n".join([f"- {mem}" for mem in relevant_memories])
        system_prompt += f"\n\nRelevant context:\n{memory_context}"
    
    # 4. Build message history
    recent_messages = session.get_context(max_tokens=2000)
    messages = [
        {"role": "system", "content": system_prompt},
        *[msg.to_dict() for msg in recent_messages],
        {"role": "user", "content": user_input}
    ]
    
    return {
        "model": "gpt-4o",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500,
        "presence_penalty": 0.6,
        "frequency_penalty": 0.3
    }
```

### 5.2 Response Validation

```python
async def validate_and_send_response(
    response: str,
    session: ConversationSession,
    send_callback: Callable
) -> None:
    """Validates and sends LLM response"""
    
    # 1. Safety check
    is_safe, warning = safety_validator.validate_assistant_output(response)
    if not is_safe:
        LOG.warning(f"Unsafe response detected: {warning}")
        response = "I want to make sure I'm being helpful. Could you share more?"
    
    # 2. Length check (keep responses short)
    if len(response.split()) > 50:
        # Truncate or request shorter response
        response = await llm_service.generate_response(
            session.messages,
            instructions="Keep response under 30 words"
        )
    
    # 3. Method adherence check
    if session.selected_method:
        adheres = session.selected_method.validate_response(response)
        if not adheres:
            LOG.warning("Response doesn't match method principles")
    
    # 4. Send response
    await send_callback({
        "type": "ai_reply",
        "text": response,
        "stage": session.current_stage.value,
        "method": session.selected_method.name if session.selected_method else None
    })
```

### 5.3 Model Switching Strategy

```python
class ModelSelector:
    """Selects optimal model based on context"""
    
    def select_model(stage: ConversationStage, complexity: str) -> str:
        if stage == ConversationStage.INTRO:
            return "gpt-4o-mini"  # Simple joke generation
        elif complexity == "high":
            return "o1-preview"  # Deep reasoning
        else:
            return "gpt-4o"  # Default balanced model
```

---

## 6. Persistence and Memory

### 6.1 Memory Architecture

```
┌─────────────────────────────────────────┐
│         Memory Layers                    │
├─────────────────────────────────────────┤
│  L1: Short-term (Current Session)       │
│      - In-memory dict                   │
│      - Last 10 messages                 │
│      - TTL: Session duration            │
├─────────────────────────────────────────┤
│  L2: Working Memory (Redis)             │
│      - Last 50 messages                 │
│      - Session metadata                 │
│      - TTL: 24 hours                    │
├─────────────────────────────────────────┤
│  L3: Long-term (Vector Store + DB)      │
│      - Session summaries                │
│      - Key insights                     │
│      - User preferences                 │
│      - TTL: Indefinite                  │
└─────────────────────────────────────────┘
```

### 6.2 Storage Models

#### Redis Schema
```python
# Session cache
REDIS_KEY_PATTERN = "session:{conn_id}"

session_data = {
    "messages": [...],  # JSON serialized
    "stage": "active_exploration",
    "method": "socratic_questioning",
    "created_at": "2025-10-17T10:00:00Z",
    "ttl": 86400  # 24 hours
}
```

#### PostgreSQL Schema
```sql
-- Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    preferences JSONB,
    total_sessions INTEGER DEFAULT 0
);

-- Sessions table
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    conn_id VARCHAR(50),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    method_used VARCHAR(100),
    stage_reached VARCHAR(50),
    summary TEXT,
    insights JSONB,
    sentiment_arc JSONB
);

-- Messages table (for long-term storage)
CREATE TABLE messages (
    message_id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(session_id),
    role VARCHAR(20),
    content TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    embedding VECTOR(1536)  -- For semantic search
);

-- Journal entries
CREATE TABLE journal_entries (
    entry_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    title VARCHAR(255),
    content TEXT,
    mood VARCHAR(50),
    tags TEXT[],
    related_sessions UUID[]
);
```

### 6.3 Vector Store Integration

```python
class VectorMemoryStore:
    """Semantic memory using embeddings"""
    
    def __init__(self, dimension: int = 1536):
        self.index = faiss.IndexFlatL2(dimension)
        self.id_to_text: Dict[int, str] = {}
        self.embedding_model = "text-embedding-3-small"
    
    async def add_memory(self, text: str, metadata: Dict) -> None:
        embedding = await self.get_embedding(text)
        idx = self.index.ntotal
        self.index.add(np.array([embedding]))
        self.id_to_text[idx] = text
    
    async def search(self, query: str, top_k: int = 3) -> List[str]:
        query_embedding = await self.get_embedding(query)
        distances, indices = self.index.search(
            np.array([query_embedding]), top_k
        )
        return [self.id_to_text[idx] for idx in indices[0]]
```

---

## 7. API Layer

### 7.1 WebSocket API

```python
# Main WebSocket handler
@websocket_route("/ws")
async def websocket_handler(websocket: WebSocket):
    """Primary real-time communication channel"""
    await websocket.accept()
    conn_id = generate_conn_id()
    
    # Create session
    session = conversation_manager.create_session(conn_id)
    
    try:
        async for message in websocket.iter_json():
            await handle_message(websocket, session, message)
    finally:
        conversation_manager.delete_session(conn_id)
```

### 7.2 Message Types (Client → Server)

```typescript
// Handshake
{
  "type": "handshake",
  "user_id": "optional_user_id",
  "simulate": false,
  "sampleRate": 16000
}

// Request intro jokes
{
  "type": "get_intro_jokes"
}

// User message
{
  "type": "user_text",
  "text": "I've been feeling anxious lately..."
}

// Method selection
{
  "type": "select_method",
  "method_id": "reflective_listening"
}

// Stage transition request
{
  "type": "transition_stage",
  "target_stage": "closure"
}

// Get session summary
{
  "type": "get_summary"
}
```

### 7.3 Message Types (Server → Client)

```typescript
// Intro jokes
{
  "type": "intro_jokes",
  "jokes": ["...", "...", "..."]
}

// AI response
{
  "type": "ai_reply",
  "text": "That sounds really challenging...",
  "stage": "active_exploration",
  "method": "reflective_listening"
}

// Streaming response chunk
{
  "type": "ai_reply_chunk",
  "chunk": "That sounds",
  "done": false
}

// Method options
{
  "type": "method_options",
  "methods": [
    {
      "id": "socratic_questioning",
      "name": "Socratic Questioning",
      "icon": "1️⃣",
      "description": "..."
    },
    ...
  ]
}

// Stage update
{
  "type": "stage_update",
  "stage": "check_in",
  "message": "Let's pause and reflect..."
}

// Session summary
{
  "type": "session_summary",
  "duration": 1500,
  "exchange_count": 12,
  "method": "reflective_listening",
  "insights": ["...", "..."],
  "follow_up": "Consider journaling about..."
}

// Error
{
  "type": "error",
  "error": "rate_limit",
  "message": "Please wait a moment..."
}
```

### 7.4 REST API (Optional)

```python
# Session management
GET    /api/sessions              # List user sessions
GET    /api/sessions/{session_id} # Get session details
POST   /api/sessions              # Create new session
DELETE /api/sessions/{session_id} # End session

# User preferences
GET    /api/users/{user_id}/preferences
PUT    /api/users/{user_id}/preferences

# Journal
GET    /api/journal/entries
POST   /api/journal/entries
GET    /api/journal/entries/{entry_id}

# Analytics
GET    /api/analytics/mood-trends
GET    /api/analytics/method-usage
```

---

## 8. Extensibility Plan

### 8.1 Adding New Exploration Methods

```python
# 1. Create new method class
class NewTherapyMethod(ExplorationMethod):
    def __init__(self):
        super().__init__(
            name="New Therapy Method",
            description="...",
            key_principles=["...", "..."],
            reference="..."
        )
    
    def get_system_instructions(self) -> str:
        return """
        You are applying [New Method]...
        Key principles: ...
        """
    
    def format_prompt(self, context: ConversationContext) -> str:
        # Custom prompt logic
        pass
    
    def validate_response(self, response: str) -> bool:
        # Method-specific validation
        pass

# 2. Register in method registry
METHOD_REGISTRY = {
    "socratic_questioning": SocraticQuestioning(),
    "reflective_listening": ReflectiveListening(),
    # ...
    "new_therapy_method": NewTherapyMethod(),  # Add here
}

# 3. Add to frontend options (automatic from registry)
```

### 8.2 Plugin Architecture

```python
class TherapyPlugin(ABC):
    """Base class for extensible plugins"""
    
    @abstractmethod
    def on_session_start(self, session: ConversationSession) -> None:
        pass
    
    @abstractmethod
    def on_message(self, message: Message, session: ConversationSession) -> None:
        pass
    
    @abstractmethod
    def on_session_end(self, session: ConversationSession) -> None:
        pass

# Example: Mood tracking plugin
class MoodTrackerPlugin(TherapyPlugin):
    def on_message(self, message: Message, session: ConversationSession):
        if message.role == "user":
            sentiment = analyze_sentiment(message.content)
            session.metadata.setdefault("moods", []).append(sentiment)
```

### 8.3 Configuration-Driven Behavior

```yaml
# config/exploration_methods.yaml
methods:
  - id: socratic_questioning
    enabled: true
    name: "Socratic Questioning"
    icon: "1️⃣"
    class: "SocraticQuestioning"
    config:
      max_questions_per_exchange: 2
      tone: "curious"
      avoid_statements: true
  
  - id: custom_method
    enabled: false
    name: "Custom Method"
    icon: "🔧"
    class: "CustomMethod"
    config:
      custom_param: "value"
```

---

## 9. Frontend Interaction

### 9.1 Frontend Architecture

```
src/
├── components/
│   ├── ChatInterface/
│   │   ├── MessageList.tsx
│   │   ├── InputArea.tsx
│   │   └── StreamingMessage.tsx
│   ├── MethodSelector/
│   │   ├── MethodCard.tsx
│   │   └── MethodGrid.tsx
│   ├── SpeechIntro/
│   │   └── SpeechIntro.tsx
│   └── SessionSummary/
│       └── SummaryCard.tsx
├── hooks/
│   ├── useWebSocket.ts
│   ├── useConversation.ts
│   └── useSpeechSynthesis.ts
├── services/
│   ├── websocketService.ts
│   ├── audioService.ts
│   └── storageService.ts
└── store/
    ├── conversationSlice.ts
    ├── uiSlice.ts
    └── sessionSlice.ts
```

### 9.2 WebSocket Integration

```typescript
// services/websocketService.ts
class WebSocketService {
  private ws: WebSocket | null = null;
  private messageHandlers: Map<string, (data: any) => void> = new Map();
  
  connect(url: string): void {
    this.ws = new WebSocket(url);
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      const handler = this.messageHandlers.get(message.type);
      if (handler) handler(message);
    };
  }
  
  on(messageType: string, handler: (data: any) => void): void {
    this.messageHandlers.set(messageType, handler);
  }
  
  send(message: object): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
  
  disconnect(): void {
    this.ws?.close();
  }
}

// Usage in component
const wsService = new WebSocketService();
wsService.connect("ws://localhost:8765/ws");

wsService.on("ai_reply", (data) => {
  dispatch(addMessage({
    role: "assistant",
    content: data.text,
    stage: data.stage
  }));
});

wsService.on("method_options", (data) => {
  setAvailableMethods(data.methods);
});
```

### 9.3 Streaming Response Handling

```typescript
// hooks/useStreamingMessage.ts
const useStreamingMessage = () => {
  const [streamingText, setStreamingText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  
  useEffect(() => {
    wsService.on("ai_reply_chunk", (data) => {
      if (data.done) {
        setIsStreaming(false);
        // Add complete message to history
      } else {
        setStreamingText((prev) => prev + data.chunk);
        setIsStreaming(true);
      }
    });
  }, []);
  
  return { streamingText, isStreaming };
};
```

### 9.4 State Management

```typescript
// store/conversationSlice.ts
interface ConversationState {
  messages: Message[];
  currentStage: ConversationStage;
  selectedMethod: ExplorationMethod | null;
  isLoading: boolean;
  error: string | null;
}

const conversationSlice = createSlice({
  name: "conversation",
  initialState: {
    messages: [],
    currentStage: "intro",
    selectedMethod: null,
    isLoading: false,
    error: null
  },
  reducers: {
    addMessage: (state, action: PayloadAction<Message>) => {
      state.messages.push(action.payload);
    },
    setStage: (state, action: PayloadAction<ConversationStage>) => {
      state.currentStage = action.payload;
    },
    selectMethod: (state, action: PayloadAction<ExplorationMethod>) => {
      state.selectedMethod = action.payload;
    }
  }
});
```

---

## 10. Sequence Diagram

### Single Message Exchange Flow

```
┌──────┐          ┌──────────┐        ┌─────────────┐       ┌──────────┐      ┌──────────┐
│Client│          │WebSocket │        │Conversation │       │  LLM     │      │  Memory  │
│      │          │ Handler  │        │  Manager    │       │ Service  │      │ Manager  │
└──┬───┘          └────┬─────┘        └──────┬──────┘       └────┬─────┘      └────┬─────┘
   │                   │                     │                    │                 │
   │ user_text msg     │                     │                    │                 │
   ├──────────────────>│                     │                    │                 │
   │                   │                     │                    │                 │
   │                   │ get_session(conn_id)│                    │                 │
   │                   ├────────────────────>│                    │                 │
   │                   │                     │                    │                 │
   │                   │<────session─────────┤                    │                 │
   │                   │                     │                    │                 │
   │                   │                     │  search_memories(query)              │
   │                   │                     ├──────────────────────────────────────>│
   │                   │                     │                    │                 │
   │                   │                     │<─────memories──────────────────────────┤
   │                   │                     │                    │                 │
   │                   │  build_prompt(session, user_input, memories)               │
   │                   ├─────────────────────────────────────────>│                 │
   │                   │                     │                    │                 │
   │                   │                     │    OpenAI API      │                 │
   │                   │                     │   generate_response│                 │
   │                   │                     │                    ├─────────────┐   │
   │                   │                     │                    │ LLM Call    │   │
   │                   │                     │                    │<────────────┘   │
   │                   │                     │                    │                 │
   │                   │<─────response───────────────────────────┤                 │
   │                   │                     │                    │                 │
   │                   │ validate_response() │                    │                 │
   │                   ├────────────────┐    │                    │                 │
   │                   │  Safety check  │    │                    │                 │
   │                   │<───────────────┘    │                    │                 │
   │                   │                     │                    │                 │
   │                   │ store_message()     │                    │                 │
   │                   ├────────────────────>│                    │                 │
   │                   │                     │                    │                 │
   │                   │                     │ store_message()    │                 │
   │                   │                     ├──────────────────────────────────────>│
   │                   │                     │                    │                 │
   │  ai_reply msg     │                     │                    │                 │
   │<──────────────────┤                     │                    │                 │
   │                   │                     │                    │                 │
```

---

## 11. Implementation Roadmap

### Phase 1: Core Architecture (Week 1-2)
- [ ] Implement ConversationManager and ConversationSession
- [ ] Create ExplorationMethod base class and 3 concrete methods
- [ ] Set up PromptBuilder with dynamic instructions
- [ ] Implement basic LLMService with OpenAI integration

### Phase 2: Memory & Persistence (Week 3)
- [ ] Implement MemoryManager with Redis cache
- [ ] Set up PostgreSQL schema
- [ ] Add vector store integration (FAISS)
- [ ] Implement session summarization

### Phase 3: Safety & Validation (Week 4)
- [ ] Create SafetyValidator class
- [ ] Add crisis keyword detection
- [ ] Implement content moderation
- [ ] Add rate limiting

### Phase 4: API & WebSocket (Week 5)
- [ ] Refactor WebSocket handler with new architecture
- [ ] Implement all message types
- [ ] Add streaming response support
- [ ] Create REST endpoints

### Phase 5: Frontend Integration (Week 6)
- [ ] Update frontend state management
- [ ] Implement method selector UI
- [ ] Add streaming message display
- [ ] Create session summary component

### Phase 6: Remaining Methods (Week 7)
- [ ] Implement remaining 12 exploration methods
- [ ] Add method-specific validation
- [ ] Create method configuration system

### Phase 7: Testing & Polish (Week 8)
- [ ] Unit tests for all components
- [ ] Integration tests for flow
- [ ] Load testing for WebSocket
- [ ] UI/UX refinements

---

## 12. Technical Decisions & Rationale

| Decision | Rationale |
|----------|-----------|
| **Strategy Pattern for Methods** | Each therapeutic approach has unique logic; Strategy allows clean separation and easy extension |
| **State Machine for Stages** | Conversation flow is sequential with defined transitions; State Machine enforces valid paths |
| **Redis for Short-term Memory** | Fast in-memory cache for active sessions; TTL auto-cleanup |
| **PostgreSQL for Long-term** | Structured data with JSONB for flexibility; Proven reliability |
| **FAISS for Vector Search** | Fast similarity search for semantic memory retrieval |
| **WebSocket over REST** | Real-time bidirectional communication; Better for conversational UX |
| **Async Python** | Non-blocking I/O for concurrent connections; Scalable |
| **Modular Prompt Builder** | Centralizes prompt logic; Easier to maintain and test |
| **Message-based Protocol** | Clear contract between frontend/backend; Easy to extend |

---

## 13. Security Considerations

1. **API Key Protection**: Store in environment variables, never commit
2. **Rate Limiting**: Per-user and per-IP limits to prevent abuse
3. **Input Validation**: Sanitize all user inputs before LLM processing
4. **Output Filtering**: Validate LLM responses for harmful content
5. **Session Authentication**: JWT tokens for user identification
6. **Data Encryption**: TLS for WebSocket, encryption at rest for DB
7. **Crisis Detection**: Immediate escalation for self-harm keywords
8. **GDPR Compliance**: User data deletion, export capabilities

---

## 14. Performance Targets

| Metric | Target |
|--------|--------|
| **Message Response Time** | < 2 seconds (p95) |
| **WebSocket Connection** | < 500ms handshake |
| **Memory Retrieval** | < 100ms for top-3 |
| **Token Usage** | < 1000 tokens per exchange |
| **Concurrent Users** | 1000+ simultaneous |
| **Session Storage** | < 50MB per active session |
| **Database Query** | < 50ms (p95) |

---

## Conclusion

This LLD provides a production-ready, modular architecture for a therapeutic AI chat system. The design prioritizes:
- **Extensibility**: Easy to add new methods, plugins, features
- **Scalability**: Async design, caching, efficient memory management
- **Maintainability**: Clear separation of concerns, well-defined interfaces
- **User Experience**: Warm, adaptive, responsive conversations
- **Safety**: Multi-layered validation and crisis detection

The architecture supports the current 15 therapeutic methods while allowing unlimited future expansion through the Strategy pattern and plugin system.
