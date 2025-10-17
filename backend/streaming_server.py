#!/usr/bin/env python3
"""Simple WebSocket streaming server for ASR patches (simulate mode supported).

Protocol:
- Client sends a JSON handshake text frame: { type: 'handshake', sampleRate: 16000, channels:1, format:'s16le', simulate: true }
- Then client streams binary frames containing raw s16le PCM. The server can optionally persist
    the raw audio to STREAM_PCM_DIR when STREAM_PERSIST_PCM is truthy.
- Server responds with JSON progress updates and transcription results (partial/final).
"""

import sys
import asyncio
import logging
import websockets
import json
import time
import uuid
from pathlib import Path
from contextlib import nullcontext
from typing import Optional
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streaming_server")

# Ensure backend directory is in sys.path for imports
backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))




# --- Config ---
HOST = "0.0.0.0"
PORT = 8765
WS_PATH = "/ws"
DEFAULT_SAMPLE_RATE = 16000
PROGRESS_INTERVAL_SEC = 0.5
SILENCE_TIMEOUT = 2.0


LOG = logger

class HandshakeError(Exception):
    pass

async def _perform_handshake(ws, conn_id, send_json):
    # Wait for handshake message from client
    msg = await ws.recv()
    try:
        obj = json.loads(msg)
    except Exception:
        raise HandshakeError("Invalid handshake JSON")
    if obj.get("type") != "handshake":
        raise HandshakeError("Expected handshake message")
    simulate = obj.get("simulate", False)
    chat = obj.get("chat", False)
    sample_rate = obj.get("sampleRate", DEFAULT_SAMPLE_RATE)
    recognizer = None
    if not simulate:
        try:
            from vosk import Model, KaldiRecognizer
            model = Model(str(backend_dir / "vosk-model-small-en-us-0.15"))
            recognizer = KaldiRecognizer(model, sample_rate)
        except Exception as e:
            LOG.error(f"Failed to initialize Vosk recognizer: {e}")
            recognizer = None
            simulate = True
    class Handshake:
        pass
    handshake = Handshake()
    handshake.recognizer = recognizer
    handshake.mode = "simulate" if simulate else "real"
    handshake.sample_rate = sample_rate
    handshake.simulate = simulate
    handshake.chat = chat
    return handshake

def _pcm_sink(conn_id):
    # Dummy PCM sink context manager
    class DummyPCM:
        def __enter__(self):
            return (None, None)
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    return DummyPCM()

import aiohttp

# OpenAI GPT Configuration
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = "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"
GPT_MODEL = "gpt-4o"  # Model for conversation (can be upgraded to gpt-4o or o1)

# CBT Therapist Agent Instructions
CBT_AGENT_INSTRUCTIONS = """Goal: Create a calm, supportive space where the person feels genuinely heard and understood — guiding them gently based on how they prefer to explore their thoughts or emotions.

Step 1: Warm Opening
Start light and personable — not heavy or clinical.
"Hey there, it's good to see you. How's your day been so far?" (If they respond, briefly validate and empathize.) "That sounds like a lot to carry / I can imagine that feels confusing / I'm glad you shared that."

Step 2: Offer Exploration Styles
After they share a bit, invite them to choose how they'd like to explore today:
"Before we go deeper, would you like to pick a way we explore this? Here are a few different approaches — each works a bit differently:"

1️⃣ Socratic Questioning / Guided Discovery – I ask gentle, structured questions to help uncover assumptions and see new perspectives. 📖 Cognitive Therapy: Basics and Beyond (Beck, 2011)
2️⃣ Reflective Listening – I mirror your thoughts and feelings so you feel fully understood. 📖 Motivational Interviewing (Miller & Rollnick, 2012)
3️⃣ Thought Records / Cognitive Restructuring – We track your thoughts and look at evidence for or against them. 📖 Mind Over Mood (Greenberger & Padesky, 2nd Ed.)
4️⃣ Behavioral Analysis (ABC model) – We explore what triggers certain actions and what follows them. 📖 Behavioral Case Formulation and Intervention (Haynes & O'Brien, 2000)
5️⃣ Schema Exploration – We look for deeper core beliefs that shape recurring emotional patterns. 📖 Schema Therapy: A Practitioner's Guide (Young et al., 2003)
6️⃣ Narrative Techniques – We talk about your story — maybe even externalize the problem ("the anxiety is trying to…"). 📖 Narrative Means to Therapeutic Ends (White & Epston, 1990)
7️⃣ Psychodynamic Exploration – We trace current struggles back to early experiences or unconscious conflicts. 📖 The Handbook of Psychodynamic Approaches to Psychopathology (Person et al.)
8️⃣ Motivational Interviewing – We explore ambivalence and strengthen your motivation for change. 📖 Motivational Interviewing (Miller & Rollnick)
9️⃣ Gestalt / Empty Chair Work – We can dialogue with a "part" of you or someone you need closure with. 📖 Gestalt Therapy (Perls et al., 1951)
🔟 Mindfulness-Based Inquiry – We slow down and notice sensations, thoughts, and emotions with curiosity. 📖 The Mindful Way Through Depression (Segal et al., 2007)
11️⃣ Behavioral Experiments – We test beliefs in real life to see how true they really are. 📖 Cognitive Therapy Techniques (Leahy, 2003)
12️⃣ Reflective Writing / Journaling – You write through what's happening; I guide with prompts. 📖 Expressive Writing: Words That Heal (Pennebaker & Evans, 2014)
13️⃣ Scaling & Rating Techniques – We use 0–10 ratings to track distress or progress. 📖 Solution Focused Brief Therapy (de Shazer, 1985)
14️⃣ Parts Work / Internal Family Systems – We explore inner voices like your critic, protector, or inner child. 📖 Self-Therapy (Jay Earley, 2009)
15️⃣ Life Review & Meaning-Making – We explore purpose, values, and meaning in your life story. 📖 Man's Search for Meaning (Viktor Frankl, 1946)

Step 3: Apply the Chosen Method
Once they choose:
- Follow that approach's tone and structure.
- Keep responses short, curious, and validating.
- Check in gently: "Is this helping you see things a bit more clearly, or would you like to shift our approach?"

Step 4: End with Encouragement
Close softly and affirm their effort:
"You've done really well reflecting on this today. Do you want to keep using this approach next time, or try a different one?"
"""

# Conversation history storage (in production, use a database or session storage)
conversation_histories = {}

# Optimization: prefer local JSON pool of prewritten jokes to avoid calling the GPT API every time.
USE_LOCAL_JOKES = True
INTRO_JOKES_PATH = backend_dir / "intro_jokes.json"
INTRO_JOKES = None
try:
    if INTRO_JOKES_PATH.exists():
        with open(INTRO_JOKES_PATH, "r", encoding="utf-8") as fh:
            INTRO_JOKES = json.load(fh)
            LOG.info(f"Loaded {len(INTRO_JOKES) if isinstance(INTRO_JOKES, list) else len(INTRO_JOKES.get('jokes', []))} local intro jokes from {INTRO_JOKES_PATH}")
    else:
        LOG.info(f"Local intro jokes file not found at {INTRO_JOKES_PATH}")
except Exception as e:
    LOG.exception(f"Failed to load local intro jokes: {e}")

async def send_assistant_reply(send_json, text, mode, conn_id=None):
    """Send assistant reply using CBT Agent with conversation history"""
    # Initialize conversation history for this connection if needed
    if conn_id and conn_id not in conversation_histories:
        conversation_histories[conn_id] = [
            {"role": "system", "content": CBT_AGENT_INSTRUCTIONS}
        ]
    
    # Get conversation history or create new one
    if conn_id and conn_id in conversation_histories:
        messages = conversation_histories[conn_id]
    else:
        messages = [
            {"role": "system", "content": CBT_AGENT_INSTRUCTIONS}
        ]
    
    # Add user message
    messages.append({"role": "user", "content": text})
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": GPT_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "store": True  # Store conversation for future reference
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENAI_API_URL, headers=headers, json=data, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    ai_text = result["choices"][0]["message"]["content"]
                    
                    # Store assistant response in conversation history
                    if conn_id:
                        messages.append({"role": "assistant", "content": ai_text})
                        conversation_histories[conn_id] = messages
                else:
                    ai_text = f"[AI error: {resp.status}]"
    except Exception as e:
        ai_text = f"[AI error: {e}]"
    LOG.info(f"Sending AI reply: {ai_text}")
    await send_json({"type": "ai_reply", "text": ai_text, "mode": mode})

async def generate_intro_jokes(send_json):
    """Generate ONE quirky intro joke using GPT-4o model"""
    # If configured, try to serve a random prewritten joke from local JSON first
    if USE_LOCAL_JOKES and INTRO_JOKES:
        try:
            # Accept either a list of jokes or a dict with a 'jokes' key
            pool = None
            if isinstance(INTRO_JOKES, dict) and "jokes" in INTRO_JOKES:
                pool = INTRO_JOKES["jokes"]
            elif isinstance(INTRO_JOKES, list):
                pool = INTRO_JOKES
            if pool:
                chosen = random.choice(pool)
                # chosen can be a dict with 'sentences' or a list of sentence strings
                if isinstance(chosen, dict):
                    sentences = chosen.get("sentences") or chosen.get("jokes") or []
                elif isinstance(chosen, list):
                    sentences = chosen
                else:
                    sentences = []

                # Clean & normalize selected sentences
                jokes = []
                for s in sentences:
                    if not s:
                        continue
                    cleaned = str(s).strip()
                    cleaned = cleaned.lstrip('0123456789.-*•>').strip()
                    cleaned = cleaned.strip("\"'`")
                    if cleaned and len(cleaned) > 1:
                        if not cleaned.endswith('..') and not cleaned.endswith('.'):
                            cleaned += '..'
                        jokes.append(cleaned)

                # If we got fewer than 6, pad with defaults
                if len(jokes) < 6:
                    LOG.warning(f"Local chosen joke had only {len(jokes)} sentences, falling back to defaults")
                    jokes = [
                        "Hello..",
                        "I tried to be perfect once..",
                        "It didn't like me..",
                        "So now we talk..",
                        "Hello..",
                        "How are you?",
                    ]

                # Ensure exactly 6 main sentences, then append our required final sentence
                jokes = jokes[:6]
                jokes.append("Feel free to share about your day with me")
                await send_json({"type": "intro_jokes", "jokes": jokes})
                return
        except Exception:
            LOG.exception("Error selecting local intro joke, falling back to GPT")
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    prompt = """Create a witty, self-deprecating, relatable intro joke for an AI therapist. Generate EXACTLY 6 SHORT sentences with this vibe:

STYLE: Self-aware, sarcastic, self-deprecating humor about mental health, therapy, emotions, psychology
- Like a therapist who's also in therapy
- Relatable struggles everyone understands
- Clever wordplay and irony
- Short, punchy, HILARIOUS

EXAMPLES OF THE STYLE (create NEW ones like these):
"Hey there! I'd ask how you are, but I'm afraid you'll tell me."
"Hi! I'd ask how life is, but that feels like a trap."
"Hey! I meant to say hi, but my brain said 'why.'"
"My subconscious is passive-aggressive and highly judgmental."
"I don't have trust issues, I have trust experiments that failed spectacularly."

STRUCTURE - Generate EXACTLY 6 sentences:
1. Greeting (2-3 words: "Hey there" "Hello" "Hi")
2. Witty self-deprecating joke (6-12 words - make it FUNNY)
3. Another clever quip (6-12 words - different angle)
4. Third funny observation (6-12 words - wrap up the humor)
5. Greeting again (2-3 words, same as #1)
6. Supportive question (3-6 words: "How are you?" "How's your day?")

THEMES (self-aware humor about):
- Asking "how are you" feels risky
- Brain sabotaging good intentions
- Overthinking everything
- Subconscious being mean
- Trust issues disguised as wisdom
- Emotional baggage
- Self-care being exhausting
- Being your own worst critic

RULES:
- Witty, clever, self-deprecating
- Everyone relates to it
- Each sentence 2-12 words
- Use ".." for pauses between thoughts
- SUPER FUNNY but supportive
- No complex psychology jargon

Example format:
Hey there..
I'd ask how you are but I'm scared you'll actually tell me..
My therapist says I should ask anyway..
So here goes nothing..
Hey there..
How are you?

Return ONLY 6 lines. No quotes, labels, or extra text."""
    
    data = {
        "model": GPT_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.9  # High temperature for creative variations
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENAI_API_URL, headers=headers, json=data, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    joke_text = result["choices"][0]["message"]["content"]
                    
                    # Split and clean the text
                    lines = joke_text.strip().split('\n')
                    jokes = []
                    for line in lines:
                        # Remove bullet points, numbering, quotes, and extra whitespace
                        cleaned = line.strip()
                        cleaned = cleaned.lstrip('0123456789.-*•>').strip()
                        cleaned = cleaned.strip('"\'`')
                        # Skip empty lines and lines that are just prefixes like "AI Therapist:"
                        if cleaned and len(cleaned) > 2 and ':' not in cleaned[:20]:
                            # Add ".." at the end if not already there for natural pauses
                            if not cleaned.endswith('..') and not cleaned.endswith('.'):
                                cleaned += '..'
                            jokes.append(cleaned)
                    
                    # Ensure we have exactly 7 sentences
                    if len(jokes) < 6:
                        LOG.warning(f"Generated only {len(jokes)} jokes, using defaults")
                        jokes = [
                            "Hello..",
                            "How high are you?",
                            "Oh.. Sorry..",
                            "I meant to ask",
                            "Hello..",
                            "How are you?",
                            "Feel free to share about your day with me"
                        ]
                    else:
                        # Take first 6 sentences only, then force the 7th to be our required ending
                        jokes = jokes[:6]
                        # ALWAYS append the required ending as the 7th sentence
                        jokes.append("Feel free to share about your day with me")
                    
                    LOG.info(f"Generated intro jokes ({len(jokes)} total): {jokes}")
                    await send_json({"type": "intro_jokes", "jokes": jokes})
                else:
                    LOG.error(f"Failed to generate jokes: {resp.status}")
                    # Fallback to default
                    default_jokes = [
                        "Hello..",
                        "How high are you?",
                        "Oh.. Sorry..",
                        "I meant to ask",
                        "Hello..",
                        "How are you?",
                        "Feel free to share about your day with me"
                    ]
                    await send_json({"type": "intro_jokes", "jokes": default_jokes})
    except Exception as e:
        LOG.error(f"Error generating intro jokes: {e}")
        # Fallback to default
        default_jokes = [
            "Hello..",
            "How high are you?",
            "Oh.. Sorry..",
            "I meant to ask",
            "Hello..",
            "How are you?",
            "Feel free to share about your day with me"
        ]
        await send_json({"type": "intro_jokes", "jokes": default_jokes})




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

    # --- Helper functions must be defined here, inside handler, to access state ---
    async def send_json(obj) -> bool:
        try:
            await ws.send(json.dumps(obj))
            return True
        except Exception:
            LOG.exception("Failed sending json to %s", conn_id)
            return False

    async def simulate_loop():
        count = 0
        while True:
            await asyncio.sleep(0.8)
            count += 1
            if not await send_json({"type": "partial", "partial": f"simulated partial {count}"}):
                return

    async def timeout_checker():
        nonlocal pending_text, last_partial, last_partial_ts, last_ai_request, ai_processing, last_ai_response_time
        while True:
            await asyncio.sleep(0.1)
            current_time = time.monotonic()
            time_since_last_ai = current_time - last_ai_response_time
            if (
                pending_text
                and (current_time - last_partial_ts) >= SILENCE_TIMEOUT
                and pending_text != last_ai_request
                and not ai_processing
                and time_since_last_ai >= AI_COOLDOWN_SECONDS
            ):
                LOG.info(
                    "Silence timeout (%s): Converting partial to final: %s",
                    conn_id,
                    pending_text,
                )
                await send_json({"type": "final", "text": pending_text, "final": True})
                last_ai_request = pending_text
                ai_processing = True
                await send_assistant_reply(send_json, pending_text, handshake_mode, conn_id)
                ai_processing = False
                last_ai_response_time = time.monotonic()
                pending_text = ""
                last_partial = ""
            elif (
                pending_text
                and (current_time - last_partial_ts) >= SILENCE_TIMEOUT
                and time_since_last_ai < AI_COOLDOWN_SECONDS
            ):
                LOG.info(
                    "Silence timeout (%s): Skipping due to cooldown (%.1fs remaining): %s",
                    conn_id,
                    AI_COOLDOWN_SECONDS - time_since_last_ai,
                    pending_text,
                )
                pending_text = ""
                last_partial = ""

    # --- Main handler logic ---
    try:
        handshake = await _perform_handshake(ws, conn_id, send_json)
        recognizer = handshake.recognizer
        handshake_mode = handshake.mode
        sample_rate = handshake.sample_rate

        pcm_context = (
            _pcm_sink(conn_id) if not getattr(handshake, 'chat', False) else nullcontext((None, None))
        )

        with pcm_context as (pcm_file, saved_path):
            pcm_path = saved_path
            last_progress_ts = time.monotonic()

            last_partial = ""
            last_partial_ts = time.monotonic()
            pending_text = ""
            last_ai_request = ""
            ai_processing = False
            last_ai_response_time = 0.0

            if getattr(handshake, 'simulate', False) and recognizer is None and not getattr(handshake, 'chat', False):
                sim_task = asyncio.create_task(simulate_loop())

            timeout_task = asyncio.create_task(timeout_checker()) if not getattr(handshake, 'chat', False) else None

            try:
                async for data in ws:
                    if isinstance(data, (bytes, bytearray, memoryview)):
                        if getattr(handshake, 'chat', False):
                            LOG.debug("Ignoring binary payload in chat mode for %s", conn_id)
                            continue
                        audio_bytes = (
                            data if isinstance(data, (bytes, bytearray)) else bytes(data)
                        )
                        if pcm_file is not None:
                            pcm_file.write(audio_bytes)
                        bytes_received += len(audio_bytes)
                        chunks += 1
                        now = time.monotonic()
                        if now - last_progress_ts >= PROGRESS_INTERVAL_SEC:
                            await send_json({"type": "progress", "bytes": bytes_received, "chunks": chunks})
                            last_progress_ts = now
                        if recognizer:
                            if hasattr(recognizer, 'AcceptWaveform') and recognizer.AcceptWaveform(audio_bytes):
                                try:
                                    result = json.loads(recognizer.Result())
                                except Exception:
                                    result = {}
                                text = (result.get("text") or "").strip()
                                current_time = time.monotonic()
                                time_since_last_ai = current_time - last_ai_response_time
                                if (text and text != last_ai_request and not ai_processing and time_since_last_ai >= AI_COOLDOWN_SECONDS):
                                    LOG.info("Vosk final (%s): %s", conn_id, text)
                                    await send_json({"type": "final", "text": text, "final": True})
                                    last_partial = ""
                                    pending_text = ""
                                    last_ai_request = text
                                    ai_processing = True
                                    await send_assistant_reply(send_json, text, handshake_mode, conn_id)
                                    ai_processing = False
                                    last_ai_response_time = time.monotonic()
                                elif text == last_ai_request:
                                    LOG.info("Vosk final (%s): Skipping duplicate text: %s", conn_id, text)
                                elif time_since_last_ai < AI_COOLDOWN_SECONDS:
                                    LOG.info("Vosk final (%s): Skipping due to cooldown (%.1fs remaining): %s", conn_id, AI_COOLDOWN_SECONDS - time_since_last_ai, text)
                            else:
                                try:
                                    partial_obj = json.loads(recognizer.PartialResult())
                                except Exception:
                                    partial_obj = {}
                                partial = (partial_obj.get("partial") or "").strip()
                                if partial and partial != last_partial:
                                    last_partial = partial
                                    pending_text = partial
                                    last_partial_ts = time.monotonic()
                                    LOG.info("Vosk partial (%s): %s", conn_id, partial)
                                    await send_json({"type": "partial", "partial": partial})
                    else:
                        try:
                            obj = json.loads(data)
                        except Exception:
                            LOG.info("Received non-binary message from %s", conn_id)
                            continue
                        msg_type = obj.get("type")
                        if msg_type == "get_intro_jokes":
                            LOG.info("Generating intro jokes for %s", conn_id)
                            await generate_intro_jokes(send_json)
                        elif msg_type in {"user_text", "chat"}:
                            user_text = (obj.get("text") or "").strip()
                            current_time = time.monotonic()
                            time_since_last_ai = current_time - last_ai_response_time
                            if (not user_text or user_text == last_ai_request or ai_processing or time_since_last_ai < AI_COOLDOWN_SECONDS):
                                if time_since_last_ai < AI_COOLDOWN_SECONDS:
                                    LOG.info("Chat message (%s): Skipping due to cooldown (%.1fs remaining): %s", conn_id, AI_COOLDOWN_SECONDS - time_since_last_ai, user_text)
                                continue
                            LOG.info("Chat message (%s): %s", conn_id, user_text)
                            last_ai_request = user_text
                            ai_processing = True
                            await send_assistant_reply(send_json, user_text, handshake_mode or "chat", conn_id)
                            ai_processing = False
                            last_ai_response_time = time.monotonic()
                        else:
                            LOG.info("Got text message %s: %s", conn_id, obj)
            finally:
                if timeout_task:
                    timeout_task.cancel()
                    try:
                        await timeout_task
                    except asyncio.CancelledError:
                        pass
    except HandshakeError as exc:
        LOG.warning("Handshake failed %s: %s", conn_id, exc)
        try:
            await send_json({"type": "error", "error": "handshake", "message": str(exc)})
        except Exception:
            pass
    except websockets.exceptions.ConnectionClosedOK:
        LOG.info("Connection closed normally %s", conn_id)
    except websockets.exceptions.ConnectionClosedError:
        LOG.info("Connection closed with error %s", conn_id)
    except Exception:
        LOG.exception("Connection handler failed %s", conn_id)
        try:
            await send_json({"type": "error", "error": "internal"})
        except Exception:
            pass
    finally:
        if sim_task:
            sim_task.cancel()
            try:
                await sim_task
            except asyncio.CancelledError:
                pass
            except Exception:
                LOG.exception("Error while cancelling simulate loop for %s", conn_id)
        if recognizer and hasattr(recognizer, 'FinalResult'):
            try:
                final_result = json.loads(recognizer.FinalResult())
            except Exception:
                final_result = {}
            final_text = (final_result.get("text") or "").strip()
            if final_text:
                LOG.info("Vosk final (close) %s: %s", conn_id, final_text)
        saved_label = str(pcm_path) if pcm_path else "disabled"
        LOG.info("Connection %s finished bytes=%s chunks=%s saved=%s sampleRate=%s mode=%s", conn_id, bytes_received, chunks, saved_label, sample_rate, handshake_mode)

# --- Server Startup ---
async def _run_server():
    LOG.info(f"Starting streaming server on ws://{HOST}:{PORT}{WS_PATH}")
    async with websockets.serve(handler, HOST, PORT):
        while True:
            await asyncio.sleep(1)

def main():
    try:
        asyncio.run(_run_server())
    except KeyboardInterrupt:
        LOG.info("Keyboard interrupt, exiting")

if __name__ == "__main__":
    main()

