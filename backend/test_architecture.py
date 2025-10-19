#!/usr/bin/env python3
"""Test script to verify modular architecture integration"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

def test_imports():
    """Test that all imports work"""
    print("Testing imports...")
    
    try:
        from models.conversation import Message, ConversationSession, ConversationStage, MethodDefinition
        print("✅ models.conversation imports successful")
    except Exception as e:
        print(f"❌ models.conversation import failed: {e}")
        return False
    
    try:
        from core.conversation_manager import ConversationManager
        print("✅ core.conversation_manager import successful")
    except Exception as e:
        print(f"❌ core.conversation_manager import failed: {e}")
        return False
    
    try:
        from core.prompt_builder import PromptBuilder
        print("✅ core.prompt_builder import successful")
    except Exception as e:
        print(f"❌ core.prompt_builder import failed: {e}")
        return False
    
    try:
        from exploration_methods import get_all_methods, get_method, METHOD_REGISTRY
        print("✅ exploration_methods imports successful")
    except Exception as e:
        print(f"❌ exploration_methods import failed: {e}")
        return False
    
    return True

def test_conversation_manager():
    """Test ConversationManager functionality"""
    print("\nTesting ConversationManager...")
    
    from core.conversation_manager import ConversationManager
    
    # Test singleton
    manager1 = ConversationManager()
    manager2 = ConversationManager()
    assert manager1 is manager2, "ConversationManager should be a singleton"
    print("✅ Singleton pattern works")
    
    # Test session creation
    session = manager1.create_session("test_conn_123")
    assert session is not None, "Session creation failed"
    assert session.conn_id == "test_conn_123", "Session has wrong conn_id"
    print(f"✅ Session created: {session.conn_id}")
    
    # Test session retrieval
    retrieved = manager1.get_session("test_conn_123")
    assert retrieved is session, "Retrieved session should be the same object"
    print("✅ Session retrieval works")
    
    # Test session deletion
    manager1.delete_session("test_conn_123")
    deleted = manager1.get_session("test_conn_123")
    assert deleted is None, "Session should be deleted"
    print("✅ Session deletion works")
    
    return True

def test_exploration_methods():
    """Test exploration methods registry"""
    print("\nTesting exploration methods...")
    
    from exploration_methods import get_all_methods, get_method
    
    methods = get_all_methods()
    assert len(methods) == 6, f"Expected 6 methods, got {len(methods)}"
    print(f"✅ Found {len(methods)} exploration methods")
    
    for method_id, definition in methods.items():
        print(f"   {definition['icon']} {definition['name']}")
    
    # Test method retrieval
    socratic = get_method("socratic_questioning")
    assert socratic is not None, "Should retrieve Socratic Questioning method"
    assert socratic.name == "Socratic Questioning / Guided Discovery"
    print(f"✅ Method retrieval works: {socratic.name}")
    
    return True

def test_prompt_builder():
    """Test PromptBuilder functionality"""
    print("\nTesting PromptBuilder...")
    
    from core.prompt_builder import PromptBuilder
    from core.conversation_manager import ConversationManager
    
    # Create a session
    manager = ConversationManager()
    session = manager.create_session("test_prompt_123")
    session.add_message_from_text("user", "I'm feeling anxious today")
    session.add_message_from_text("assistant", "I hear you. What's making you feel anxious?")
    session.add_message_from_text("user", "Work deadlines are piling up")
    
    # Build prompts
    builder = PromptBuilder()
    messages = builder.build_messages_for_llm(session)
    
    assert len(messages) > 0, "Should have messages"
    assert messages[0]["role"] == "system", "First message should be system prompt"
    print(f"✅ Built {len(messages)} messages for LLM")
    
    # Test with method selection
    session.select_method("reflective_listening")
    messages_with_method = builder.build_messages_for_llm(session)
    assert len(messages_with_method) >= len(messages), "Should have more context with method"
    print("✅ Prompt building with method selection works")
    
    # Cleanup
    manager.delete_session("test_prompt_123")
    
    return True

def test_state_machine():
    """Test conversation stage state machine"""
    print("\nTesting state machine...")
    
    from core.conversation_manager import ConversationManager
    from models.conversation import ConversationStage
    
    manager = ConversationManager()
    session = manager.create_session("test_state_123")
    
    assert session.current_stage == ConversationStage.INTRO
    print(f"✅ Initial stage: {session.current_stage.value}")
    
    # Test valid transition
    success = session.transition_stage(ConversationStage.OPENING)
    assert success, "Should allow INTRO -> OPENING transition"
    print(f"✅ Transitioned to: {session.current_stage.value}")
    
    # Test invalid transition (should fail)
    success = session.transition_stage(ConversationStage.ENDED)
    assert not success, "Should not allow OPENING -> ENDED transition"
    print("✅ Invalid transition blocked correctly")
    
    # Cleanup
    manager.delete_session("test_state_123")
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Testing Modular Architecture Integration")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("ConversationManager", test_conversation_manager),
        ("Exploration Methods", test_exploration_methods),
        ("PromptBuilder", test_prompt_builder),
        ("State Machine", test_state_machine)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test_name} failed")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed! Architecture is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
