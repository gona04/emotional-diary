/**
 * TTS Service Smoke Test
 * Run this to verify TTS functionality works correctly
 */

import { ttsService } from '../services/ttsService';

export async function runTTSSmokeTest(): Promise<boolean> {
  console.log('🧪 Running TTS Service Smoke Test...');

  try {
    // Test 1: Basic functionality
    console.log('📢 Testing basic TTS functionality...');
    await ttsService.speak('Hello, this is a test of the text to speech system.');

    // Test 2: Custom options
    console.log('🎛️  Testing custom voice options...');
    await ttsService.speak('Testing custom pitch and rate settings.', {
      pitch: -5,
      rate: 0.8,
      volume: 0.7
    });

    // Test 3: Error handling (empty text)
    console.log('🛡️  Testing error handling...');
    await ttsService.speak(''); // Should handle gracefully

    console.log('✅ TTS Smoke Test PASSED - All tests completed successfully');
    return true;

  } catch (error) {
    console.error('❌ TTS Smoke Test FAILED:', error);
    return false;
  }
}

// Auto-run if this file is executed directly (for manual testing)
if (typeof window !== 'undefined' && window.location) {
  // Browser environment - add to window for manual testing
  (window as any).runTTSSmokeTest = runTTSSmokeTest;
  console.log('💡 TTS Smoke Test loaded. Run runTTSSmokeTest() in the browser console to test TTS functionality.');
}