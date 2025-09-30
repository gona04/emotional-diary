import pathlib
from vosk import KaldiRecognizer, Model, SetLogLevel
import logging
from backend import config

SetLogLevel(-1)

class SpeechService:
    def __init__(self):
        self._model = None
        self.logger = logging.getLogger("SpeechService")

    def ensure_model(self):
        if self._model is None:
            model_dir = self._discover_model_path()
            self.logger.info(f"Loading Vosk model from {model_dir}")
            self._model = Model(str(model_dir))
        return self._model

    def _discover_model_path(self) -> pathlib.Path:
        if config.VOSK_MODEL_PATH.exists():
            return config.VOSK_MODEL_PATH
        backend_dir = pathlib.Path(__file__).resolve().parent.parent
        for child in backend_dir.iterdir():
            if child.is_dir() and child.name.startswith("vosk-model"):
                return child
        raise FileNotFoundError("Vosk model directory not found.")

    def create_recognizer(self, sample_rate: int):
        model = self.ensure_model()
        recognizer = KaldiRecognizer(model, sample_rate)
        try:
            recognizer.SetWords(True)
        except AttributeError:
            pass
        return recognizer
