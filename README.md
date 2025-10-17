# 🧠 Emotional Diary - Therapeutic AI Chat Application

Emotional Diary is a production-grade therapeutic AI chat application that provides users with empathetic, structured conversations grounded in evidence-based psychological frameworks. The system offers 15 different exploration methods (6 currently implemented) and maintains a warm, human-like conversational tone.

This project blends psychology, cognitive behavioral therapy (CBT), and modern AI to help users explore their thoughts and feelings through interactive, compassionate dialogue.

---

## 📚 Documentation Index

**Start Here**: 
- **[COMPLETE_SUMMARY.md](COMPLETE_SUMMARY.md)** - Quick overview and implementation metrics
- **[docs/LOW_LEVEL_DESIGN.md](docs/LOW_LEVEL_DESIGN.md)** - Complete architectural blueprint (14 sections)
- **[docs/ARCHITECTURE_DIAGRAMS.md](docs/ARCHITECTURE_DIAGRAMS.md)** - Visual architecture and flow diagrams

**Implementation Guides**:
- **[backend/IMPLEMENTATION_SUMMARY.md](backend/IMPLEMENTATION_SUMMARY.md)** - Detailed component breakdown
- **[backend/MIGRATION_GUIDE.py](backend/MIGRATION_GUIDE.py)** - Step-by-step integration instructions
- **[backend/CBT_AGENT_CHANGES.md](backend/CBT_AGENT_CHANGES.md)** - Change history

---

## 🏗️ Architecture Highlights

### Design Patterns
- **Strategy Pattern**: Exploration methods with runtime selection
- **State Machine**: 7-stage conversation flow with enforced transitions
- **Singleton**: Global session management
- **Builder**: Dynamic context-aware prompt construction

### Key Components
```
├── Models (Data Layer)
│   └── ConversationSession, Message, MethodDefinition
│
├── Core Services
│   ├── ConversationManager (Session lifecycle)
│   └── PromptBuilder (Context-aware prompts)
│
├── Exploration Methods (Strategy Pattern)
│   ├── Socratic Questioning
│   ├── Reflective Listening
│   ├── Thought Records
│   ├── Behavioral Analysis
│   ├── Schema Exploration
│   └── Mindfulness Inquiry
│   ... (9 more planned)
│
└── LLM Integration
    └── OpenAI GPT-4o with CBT agent instructions
```

---

## 🧩 Exploration Methods

### Currently Implemented (6 of 15)
1. **1️⃣ Socratic Questioning** - Gentle questions to uncover assumptions
2. **2️⃣ Reflective Listening** - Mirroring thoughts and feelings
3. **3️⃣ Thought Records** - Cognitive restructuring through evidence
4. **4️⃣ Behavioral Analysis** - ABC model pattern exploration
5. **5️⃣ Schema Exploration** - Core belief investigation
6. **🔟 Mindfulness Inquiry** - Present-moment awareness

### Planned (9 more)
- Narrative Techniques, Psychodynamic Exploration, Motivational Interviewing, Gestalt/Empty Chair Work, Behavioral Experiments, Reflective Writing/Journaling, Scaling & Rating Techniques, Parts Work/IFS, Life Review & Meaning-Making

---

## 💬 Conversation Flow

```
1. INTRO → Quirky self-deprecating joke (from JSON pool)
2. OPENING → Warm greeting: "How's your day been?"
3. METHOD_SELECTION → Offer 15 exploration styles
4. ACTIVE_EXPLORATION → Apply selected method
5. CHECK_IN → "Is this helping?" (every 3-5 exchanges)
6. CLOSURE → Affirm progress, summarize session
7. ENDED → Clean up, save summary
```

---

## 🚀 Getting Started

This project includes two main components:

1. **React frontend** - User interface with chat, speech-to-text, background sounds
2. **Python backend** - WebSocket server with OpenAI GPT-4o, conversation management, exploration methods

### Requirements

- Node 18+
- Python 3.9+
- OpenAI API key (replaced Mistral)
- (Optional) Vosk model for offline transcription (`backend/vosk-model-small-en-us-0.15`)

### Environment Variables

**Frontend** (create `.env` in project root):
```bash
REACT_APP_STREAMING_WS_URL=ws://localhost:8765
```

**Backend** (set in terminal or `backend/.env`):
```bash
OPENAI_API_KEY=sk-your-key-here
GPT_MODEL=gpt-4o
USE_LOCAL_JOKES=True
DEBUG_MODE=False
```

### Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# Start the WebSocket server
python streaming_server.py
```

### Frontend Setup

```bash
cd ..  # Back to project root
npm install
npm start
```

The app will open at `http://localhost:3000` and connect to the WebSocket server at `ws://localhost:8765`.

### Testing the New Architecture

Test the modular components in isolation:

```python
cd backend
python3 -c "
from core.conversation_manager import ConversationManager
from exploration_methods import get_all_methods, get_method

# Test session management
manager = ConversationManager()
session = manager.create_session('test123')
print(f'✅ Session created: {session.conn_id}')
print(f'   Stage: {session.current_stage.value}')

# Test exploration methods
methods = get_all_methods()
print(f'\n✅ Available methods: {len(methods)}')
for m_id, m_def in methods.items():
    print(f\"   {m_def['icon']} {m_def['name']}\")

# Test method lookup
method = get_method('socratic_questioning')
print(f\"\n✅ Retrieved method: {method.name}\")
"
```

---

## 📋 Project Structure

```
emotional-diary/
├── docs/
│   ├── LOW_LEVEL_DESIGN.md           # Complete system design (14 sections)
│   └── ARCHITECTURE_DIAGRAMS.md      # Visual architecture diagrams
│
├── backend/
│   ├── streaming_server.py           # Main WebSocket server
│   ├── intro_jokes.json              # Prewritten intro jokes pool
│   │
│   ├── models/
│   │   └── conversation.py           # Data models (Session, Message, Stage, etc.)
│   │
│   ├── core/
│   │   ├── conversation_manager.py   # Session management (Singleton)
│   │   └── prompt_builder.py         # Dynamic prompt construction (Builder)
│   │
│   ├── exploration_methods/
│   │   ├── __init__.py
│   │   ├── base.py                   # Abstract base + 6 implementations
│   │   └── registry.py               # Method registry and lookup
│   │
│   ├── services/                     # Future: LLM, Memory, Safety
│   │
│   ├── helpfuldiary/                 # Django app (existing)
│   │   └── ...
│   │
│   ├── IMPLEMENTATION_SUMMARY.md     # What's been built
│   ├── MIGRATION_GUIDE.py            # Integration instructions
│   └── CBT_AGENT_CHANGES.md          # Change history
│
├── src/                              # React frontend
│   ├── components/
│   │   ├── Chatbot.tsx               # Main chat interface
│   │   ├── SpeechIntro/              # Intro jokes + TTS
│   │   └── BackgroundSoundPicker/    # Ambient sounds
│   │
│   ├── hooks/
│   │   └── useStreamingASR.ts        # WebSocket integration
│   │
│   └── store/                        # Redux state management
│
├── COMPLETE_SUMMARY.md               # Overall summary
└── README.md                         # This file
```

---

## 🎯 Implementation Status

### ✅ Phase 1 Complete
- [x] Complete Low-Level Design (14 sections, 20,000+ words)
- [x] Data models with serialization and state machine
- [x] ConversationManager (Singleton pattern)
- [x] PromptBuilder (Builder pattern)  
- [x] 6 exploration methods (Strategy pattern)
- [x] Method registry system
- [x] CBT agent integration with OpenAI GPT-4o
- [x] Intro joke system (local JSON pool)
- [x] WebSocket communication
- [x] Conversation history management

### ⏳ Phase 2 In Progress
- [ ] Integration with streaming_server.py (migration guide ready)
- [ ] Method selection UI in React
- [ ] Stage-based flow control
- [ ] Remaining 9 exploration methods

### 📅 Phase 3 Planned
- [ ] LLMService wrapper class
- [ ] MemoryManager with vector store
- [ ] SafetyValidator for content filtering
- [ ] Database persistence (PostgreSQL)
- [ ] Redis caching layer
- [ ] REST API endpoints

---

## 📡 WebSocket API

### Client → Server Messages

```javascript
// Handshake
{ type: "handshake", simulate: false }

// Request intro jokes
{ type: "get_intro_jokes" }

// User message
{ type: "user_text", text: "I'm feeling anxious about work..." }

// Get available exploration methods
{ type: "get_methods" }

// Select exploration method
{ type: "select_method", method_id: "reflective_listening" }

// Manual stage transition
{ type: "transition_stage", target_stage: "closure" }
```

### Server → Client Messages

```javascript
// Intro jokes
{ type: "intro_jokes", jokes: ["joke1", "joke2", "joke3"] }

// AI response
{ type: "ai_reply", text: "...", stage: "opening", method: "socratic_questioning" }

// Available methods
{ type: "method_options", methods: [{id: "...", name: "...", icon: "...", description: "..."}] }

// Method confirmation
{ type: "method_selected", method_id: "...", method_name: "...", message: "..." }

// Stage update
{ type: "stage_updated", stage: "active_exploration", message: "..." }
```

---

## 🤝 Contributing

### Adding a New Exploration Method

1. **Create method class** in `backend/exploration_methods/base.py`:

```python
class NewMethod(ExplorationMethod):
    def format_prompt(self, context: str, user_input: str) -> str:
        return f"Using {self.name}, respond to: {user_input}"
    
    def validate_response(self, response: str) -> bool:
        return True  # Add validation logic
```

2. **Add definition** in `backend/exploration_methods/registry.py`:

```python
METHOD_DEFINITIONS["new_method"] = MethodDefinition(
    id="new_method",
    name="New Therapeutic Method",
    description="Brief description for UI",
    icon="🔧",
    reference="Research reference (Author, Year)",
    key_principles=["Principle 1", "Principle 2"],
    system_instructions="Detailed LLM instructions..."
)
```

3. **Register** in `METHOD_REGISTRY`:

```python
METHOD_REGISTRY["new_method"] = NewMethod(METHOD_DEFINITIONS["new_method"])
```

That's it! The method is now available automatically through the registry.

---

## 📊 Metrics & Performance

### Implementation Statistics
- **Total Lines of Code**: 1,500+
- **Documentation**: 20,000+ words
- **Design Patterns**: 4 (Strategy, State Machine, Singleton, Builder)
- **Exploration Methods**: 6 implemented, 9 planned
- **Conversation Stages**: 7
- **Data Models**: 4

### Performance Targets (from LLD)
- Message Response Time: < 2 seconds (p95)
- WebSocket Connection: < 500ms
- Memory Retrieval: < 100ms
- Token Usage: < 1000 per exchange
- Concurrent Users: 1000+

---

## 🐛 Known Limitations

### Current Limitations
- Session storage is in-memory only (no persistence)
- No user authentication
- No long-term memory (vector store not implemented)
- No safety validation layer
- Only 6 of 15 methods implemented
- Integration with streaming_server.py pending

### Planned Fixes
- Add database persistence (Phase 3)
- Implement MemoryManager with vector store
- Add SafetyValidator class
- Complete remaining 9 methods
- Add user authentication
- Complete migration following MIGRATION_GUIDE.py

---

## 📖 Documentation

### Deep Dives
1. **[Low-Level Design](docs/LOW_LEVEL_DESIGN.md)** - Complete system architecture, components, flows, decisions
2. **[Architecture Diagrams](docs/ARCHITECTURE_DIAGRAMS.md)** - Visual flows and relationships
3. **[Implementation Summary](backend/IMPLEMENTATION_SUMMARY.md)** - What's been built, checklists, next steps
4. **[Migration Guide](backend/MIGRATION_GUIDE.py)** - How to integrate new components into streaming_server.py
5. **[Complete Summary](COMPLETE_SUMMARY.md)** - High-level overview and metrics

### Key Concepts
- **Strategy Pattern**: How exploration methods work independently
- **State Machine**: Conversation flow control with enforced transitions
- **Prompt Engineering**: Context-aware LLM prompts with method injection
- **WebSocket Protocol**: Real-time bidirectional communication

---

## 🎉 Acknowledgments

This project implements evidence-based therapeutic techniques from:
- *Cognitive Therapy: Basics and Beyond* (Beck, 2011)
- *Motivational Interviewing* (Miller & Rollnick, 2012)
- *Mind Over Mood* (Greenberger & Padesky)
- *Schema Therapy* (Young et al., 2003)
- *The Mindful Way Through Depression* (Segal et al., 2007)
- And many more (see method references in code)

---

## 🚀 Project Status

**Phase 1 Complete**: Foundation built, ready for integration  
**Current Version**: 0.1.0-alpha  
**Production Ready**: Foundation only (needs Phases 2-3)  

**Next Steps**: 
1. Review documentation (LLD, diagrams, summaries)
2. Test modular components in isolation
3. Begin streaming_server.py migration following MIGRATION_GUIDE.py
4. Implement remaining 9 exploration methods
5. Add persistence and memory layers

---

---

*Built with ❤️ using Python, React, OpenAI GPT-4o, and evidence-based psychology*


You should see logs like `server listening on 0.0.0.0:8765`. The frontend microphone button connects to this server and streams audio patches for transcription. Final transcripts are dispatched to the chat and forwarded to the Mistral backend.

### Frontend setup

```bash
cd frontend
npm install
npm start
```

The UI opens at http://localhost:3000. The chat panel and microphone now exchange both transcripts and assistant replies directly with the streaming WebSocket server, which relays prompts to Mistral and streams the responses back to the browser.
