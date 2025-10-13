import { ttsService } from './ttsService';

// Mock Audio and URL APIs
const mockAudio = {
  play: jest.fn().mockResolvedValue(undefined),
  onended: null,
  onerror: null,
};

global.Audio = jest.fn().mockImplementation(() => mockAudio) as any;
global.URL.createObjectURL = jest.fn().mockReturnValue('mock-url');
global.URL.revokeObjectURL = jest.fn();

// Mock the EdgeTTS client
jest.mock('edge-tts-universal', () => ({
  EdgeTTS: jest.fn().mockImplementation(() => ({
    voice: 'en-US-EmmaNeural',
    pitch: '',
    rate: '',
    volume: '',
    text: '',
    synthesize: jest.fn().mockResolvedValue(new ArrayBuffer(1024)),
  })),
}));

describe('TTSService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should handle audio playback errors gracefully', async () => {
    mockAudio.play.mockRejectedValueOnce(new Error('Playback failed'));

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    await expect(ttsService.speak('Test')).resolves.toBeUndefined();

    expect(consoleSpy).toHaveBeenCalledWith('TTS failed:', expect.any(Error));
    consoleSpy.mockRestore();
  });
});