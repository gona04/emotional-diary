# CBT Therapist Agent Integration

## Overview
Replaced the simple GPT conversation model with a sophisticated CBT (Cognitive Behavioral Therapy) agent that provides therapeutic support with multiple exploration approaches.

## Key Changes

### 1. Agent Instructions (System Prompt)
Added comprehensive CBT agent instructions with:
- **Warm Opening**: Light, personable greeting to create a safe space
- **15 Exploration Styles**: Multiple therapeutic approaches the user can choose from
- **Adaptive Application**: Follows the chosen approach's tone and structure
- **Encouraging Closure**: Affirms effort and invites feedback

### 2. Exploration Styles Available
1. Socratic Questioning / Guided Discovery
2. Reflective Listening
3. Thought Records / Cognitive Restructuring
4. Behavioral Analysis (ABC model)
5. Schema Exploration
6. Narrative Techniques
7. Psychodynamic Exploration
8. Motivational Interviewing
9. Gestalt / Empty Chair Work
10. Mindfulness-Based Inquiry
11. Behavioral Experiments
12. Reflective Writing / Journaling
13. Scaling & Rating Techniques
14. Parts Work / Internal Family Systems
15. Life Review & Meaning-Making

Each approach is grounded in evidence-based therapeutic literature.

### 3. Conversation History Management
- **Persistent Context**: Maintains conversation history per connection (conn_id)
- **System Instructions**: CBT agent instructions sent as system message
- **Message Threading**: User and assistant messages stored in order
- **Automatic Cleanup**: Conversation history removed when connection closes

### 4. Technical Implementation
- Model: `gpt-4o` (can be upgraded to `gpt-4.5` or `o1` series)
- Temperature: `0.7` for balanced creativity and consistency
- Store: `True` for conversation persistence
- Connection-based history using `conn_id` as key

## Benefits

### Therapeutic Quality
- Evidence-based approaches from established therapeutic modalities
- User choice empowers autonomy in their healing process
- Short, validating responses prevent overwhelming the user
- Gentle check-ins allow course correction

### Technical Quality
- Maintains conversation context across multiple interactions
- Memory-efficient cleanup when connections close
- Fallback handling for API errors
- Comprehensive logging for debugging

## Usage Flow

1. **App Start**: User sees quirky intro joke (from local JSON pool)
2. **Mic Unlock**: After joke completes with "Feel free to share about your day with me"
3. **Warm Opening**: Agent greets warmly and validates initial sharing
4. **Style Selection**: Agent offers 15 therapeutic approaches to choose from
5. **Guided Exploration**: Agent applies chosen method with short, curious questions
6. **Ongoing Support**: Maintains conversation context throughout session
7. **Encouraging Close**: Affirms progress and invites feedback

## Model Settings

```python
GPT_MODEL = "gpt-4o"  # Can upgrade to gpt-4.5 or o1 series
temperature = 0.7
store = True  # Enables conversation persistence
```

## Future Enhancements
- Add session persistence across app restarts (database storage)
- Implement therapy technique suggestions based on conversation patterns
- Add progress tracking and journaling features
- Support multi-session continuity with user accounts
