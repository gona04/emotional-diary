"""
Migration Guide: Integrating Modular Architecture into streaming_server.py

This file demonstrates how to refactor streaming_server.py to use the new modular components.
Copy the relevant sections into streaming_server.py to enable the new architecture.
"""

# ==================== IMPORTS TO ADD ====================
# Add these imports at the top of streaming_server.py

from models.conversation import Message, ConversationSession, ConversationStage
from core.conversation_manager import ConversationManager
from core.prompt_builder import PromptBuilder
from exploration_methods import get_method, get_all_methods

# ==================== INITIALIZATION ====================
# Replace conversation_histories dict with ConversationManager

# OLD CODE (remove):
# conversation_histories = {}

# NEW CODE (add):
conversation_manager = ConversationManager()
prompt_builder = PromptBuilder()

# ==================== REFACTORED send_assistant_reply ====================
# Replace the existing send_assistant_reply function with this:

async def send_assistant_reply(send_json, text, mode, conn_id=None):
    """Send assistant reply using CBT Agent with conversation history"""
    
    # Get or create session
    session = conversation_manager.get_session(conn_id)
    if not session:
        LOG.warning(f"No session found for conn_id: {conn_id}")
        # Create emergency session
        session = conversation_manager.create_session(conn_id)
    
    # Build context-aware prompt using PromptBuilder
    messages_for_llm = prompt_builder.build_messages_for_llm(
        session=session,
        user_input=text,
        relevant_memories=None  # TODO: Add memory retrieval later
    )
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": GPT_MODEL,
        "messages": messages_for_llm,
        "temperature": 0.7,
        "max_tokens": 500,
        "presence_penalty": 0.6,
        "frequency_penalty": 0.3
    }
    
    try:
        async with aiohttp.ClientSession() as session_http:
            async with session_http.post(OPENAI_API_URL, headers=headers, json=data, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    ai_text = result["choices"][0]["message"]["content"]
                    
                    # Store user message
                    user_msg = Message(
                        role="user",
                        content=text,
                        metadata={"stage": session.current_stage.value},
                        tokens=len(text.split()) * 1.3  # Rough estimate
                    )
                    session.add_message(user_msg)
                    
                    # Store assistant response
                    assistant_msg = Message(
                        role="assistant",
                        content=ai_text,
                        metadata={"stage": session.current_stage.value},
                        tokens=len(ai_text.split()) * 1.3
                    )
                    session.add_message(assistant_msg)
                    
                else:
                    ai_text = f"[AI error: {resp.status}]"
    except Exception as e:
        ai_text = f"[AI error: {e}]"
        LOG.exception(f"Error in send_assistant_reply: {e}")
    
    LOG.info(f"Sending AI reply (stage={session.current_stage.value}): {ai_text}")
    await send_json({
        "type": "ai_reply",
        "text": ai_text,
        "mode": mode,
        "stage": session.current_stage.value
    })


# ==================== NEW MESSAGE HANDLER ====================
# Add this new handler for method selection

async def handle_method_selection(send_json, method_id: str, conn_id: str):
    """Handle user selecting an exploration method"""
    session = conversation_manager.get_session(conn_id)
    if not session:
        LOG.error(f"No session found for method selection: {conn_id}")
        return
    
    # Set the method
    session.set_exploration_method(method_id)
    
    # Transition to active exploration stage
    if session.transition_stage(ConversationStage.ACTIVE_EXPLORATION):
        method = get_method(method_id)
        if method:
            response = method.get_opening_prompt()
            await send_json({
                "type": "method_selected",
                "method_id": method_id,
                "method_name": method.name,
                "message": response
            })
            LOG.info(f"Method selected for {conn_id}: {method_id}")
    else:
        LOG.error(f"Invalid stage transition for method selection: {conn_id}")


async def handle_get_methods(send_json):
    """Send list of available exploration methods"""
    methods = get_all_methods()
    await send_json({
        "type": "method_options",
        "methods": list(methods.values())
    })


async def handle_stage_transition(send_json, target_stage: str, conn_id: str):
    """Handle manual stage transition request"""
    session = conversation_manager.get_session(conn_id)
    if not session:
        LOG.error(f"No session found for stage transition: {conn_id}")
        return
    
    try:
        new_stage = ConversationStage(target_stage)
        if session.transition_stage(new_stage):
            await send_json({
                "type": "stage_updated",
                "stage": new_stage.value,
                "message": f"Transitioned to {new_stage.value}"
            })
            LOG.info(f"Stage transition for {conn_id}: {session.current_stage.value} -> {new_stage.value}")
        else:
            await send_json({
                "type": "error",
                "error": "invalid_transition",
                "message": f"Cannot transition from {session.current_stage.value} to {new_stage.value}"
            })
    except ValueError:
        await send_json({
            "type": "error",
            "error": "invalid_stage",
            "message": f"Unknown stage: {target_stage}"
        })


# ==================== HANDLER FUNCTION UPDATES ====================
# Update the handler function to use ConversationManager

async def handler(ws, path=None):
    conn_id = str(uuid.uuid4())[:8]
    LOG.info("New connection %s path=%s", conn_id, path)
    
    # All state variables must be in the enclosing scope for nonlocal
    bytes_received = 0
    chunks = 0
    sim_task: Optional[asyncio.Task] = None
    recognizer = None
    pcm_path = None
    handshake_mode = "unknown"
    sample_rate = DEFAULT_SAMPLE_RATE
    last_partial = ""
    last_partial_ts = 0.0
    pending_text = ""
    last_ai_request = ""
    ai_processing = False
    last_ai_response_time = 0.0
    AI_COOLDOWN_SECONDS = 2.0
    
    # CREATE SESSION using ConversationManager
    session = conversation_manager.create_session(conn_id=conn_id, user_id=None)
    
    # [Rest of handler code stays the same until message handling...]
    
    # In the message handling section, ADD these new cases:
    
    # Inside the `async for data in ws:` loop, after `msg_type = obj.get("type")`:
    
    if msg_type == "get_intro_jokes":
        LOG.info("Generating intro jokes for %s", conn_id)
        await generate_intro_jokes(send_json)
        # Transition to opening stage after intro
        session.transition_stage(ConversationStage.OPENING)
    
    elif msg_type == "get_methods":
        LOG.info("Sending method options to %s", conn_id)
        await handle_get_methods(send_json)
    
    elif msg_type == "select_method":
        method_id = obj.get("method_id")
        if method_id:
            LOG.info(f"Method selection for {conn_id}: {method_id}")
            await handle_method_selection(send_json, method_id, conn_id)
        else:
            LOG.warning(f"No method_id provided in select_method: {conn_id}")
    
    elif msg_type == "transition_stage":
        target_stage = obj.get("target_stage")
        if target_stage:
            await handle_stage_transition(send_json, target_stage, conn_id)
    
    elif msg_type in {"user_text", "chat"}:
        user_text = (obj.get("text") or "").strip()
        current_time = time.monotonic()
        time_since_last_ai = current_time - last_ai_response_time
        
        if (not user_text or user_text == last_ai_request or ai_processing or time_since_last_ai < AI_COOLDOWN_SECONDS):
            if time_since_last_ai < AI_COOLDOWN_SECONDS:
                LOG.info("Chat message (%s): Skipping due to cooldown (%.1fs remaining): %s", conn_id, AI_COOLDOWN_SECONDS - time_since_last_ai, user_text)
            continue
        
        LOG.info("Chat message (%s): %s", conn_id, user_text)
        
        # Auto-transition from opening to method selection after first exchange
        if session.current_stage == ConversationStage.OPENING:
            # User has responded to opening, now offer methods
            session.transition_stage(ConversationStage.METHOD_SELECTION)
        
        last_ai_request = user_text
        ai_processing = True
        await send_assistant_reply(send_json, user_text, handshake_mode or "chat", conn_id)
        ai_processing = False
        last_ai_response_time = time.monotonic()
    
    # In the finally block, REPLACE cleanup:
    
    # Clean up conversation session
    conversation_manager.delete_session(conn_id)
    LOG.info("Cleaned up session for %s", conn_id)


# ==================== PERIODIC CLEANUP ====================
# Add this background task to main() or _run_server()

async def periodic_cleanup():
    """Background task to clean up expired sessions"""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        expired = conversation_manager.cleanup_expired_sessions(timeout_minutes=60)
        if expired > 0:
            LOG.info(f"Periodic cleanup removed {expired} expired sessions")


# Update _run_server() to include cleanup task:

async def _run_server():
    LOG.info(f"Starting streaming server on ws://{HOST}:{PORT}{WS_PATH}")
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    try:
        async with websockets.serve(handler, HOST, PORT):
            while True:
                await asyncio.sleep(1)
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass


# ==================== FRONTEND MESSAGE EXAMPLES ====================
# Update frontend to send these new message types:

"""
// Request available methods
ws.send(JSON.stringify({
    type: "get_methods"
}));

// Select a method
ws.send(JSON.stringify({
    type: "select_method",
    method_id: "reflective_listening"
}));

// Manual stage transition (admin/debug)
ws.send(JSON.stringify({
    type: "transition_stage",
    target_stage: "closure"
}));

// Receive responses:
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch (data.type) {
        case "method_options":
            // data.methods = array of method definitions
            showMethodSelector(data.methods);
            break;
        
        case "method_selected":
            // data.method_id, data.method_name, data.message
            displayMethodConfirmation(data);
            break;
        
        case "stage_updated":
            // data.stage, data.message
            updateUIStage(data.stage);
            break;
        
        case "ai_reply":
            // data.text, data.stage, data.mode
            displayMessage(data.text, data.stage);
            break;
    }
};
"""

# ==================== TESTING THE INTEGRATION ====================
"""
To test the new architecture:

1. Start the server:
   cd backend
   python streaming_server.py

2. Connect via WebSocket:
   ws = new WebSocket("ws://localhost:8765/ws")

3. Send handshake:
   ws.send(JSON.stringify({type: "handshake", simulate: true}))

4. Request intro jokes:
   ws.send(JSON.stringify({type: "get_intro_jokes"}))

5. Send first message (triggers opening stage):
   ws.send(JSON.stringify({type: "user_text", text: "I've been feeling stressed"}))

6. Get available methods:
   ws.send(JSON.stringify({type: "get_methods"}))

7. Select a method:
   ws.send(JSON.stringify({type: "select_method", method_id: "reflective_listening"}))

8. Continue conversation:
   ws.send(JSON.stringify({type: "user_text", text: "Work has been overwhelming"}))

9. Check session state in logs:
   - Watch for stage transitions
   - Verify method application
   - Confirm message storage
"""

# ==================== ROLLBACK PLAN ====================
"""
If issues occur, you can rollback by:

1. Keep the old code in a backup file (streaming_server_old.py)
2. The new modular components don't break existing functionality
3. ConversationManager is backward-compatible with dict-based storage
4. PromptBuilder can run alongside old inline prompts
5. Exploration methods are additive, not replacing existing logic

To gradually migrate:
- Week 1: Add imports and initialization (no behavior change)
- Week 2: Switch to ConversationManager (replace dict)
- Week 3: Integrate PromptBuilder (verify prompts match)
- Week 4: Enable method selection messages
- Week 5: Full stage-based flow with transitions
"""
