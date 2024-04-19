import requests

class EmotionAnalyzer:
    # API_URL = "https://api-inference.huggingface.co/models/ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
    # HEADERS = {"Authorization": "Bearer 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"}
    API_URL = "https://api-inference.huggingface.co/models/DunnBC22/wav2vec2-base-Speech_Emotion_Recognition"
    HEADERS =  {"Authorization": "Bearer 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"}
    @staticmethod
    def analyze_audio(audio_data):
        try:
            response = requests.post(EmotionAnalyzer.API_URL, headers=EmotionAnalyzer.HEADERS, data=audio_data)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "Failed to analyze audio"}
        except Exception as e:
            return {"error": str(e)}
