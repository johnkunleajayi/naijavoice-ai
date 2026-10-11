from app.modules.tts.diacritization import PassthroughYorubaDiacritizer
from app.modules.tts.engine import TTSEngine
from app.modules.tts.preprocessing import YorubaPreprocessor
from app.modules.tts.schemas import TTSRequest


class TTSService:
    def __init__(self, engine: TTSEngine, preprocessor: YorubaPreprocessor | None = None) -> None:
        self.engine = engine
        self.preprocessor = preprocessor or YorubaPreprocessor(PassthroughYorubaDiacritizer())

    def synthesize(self, request: TTSRequest) -> bytes:
        text = self.preprocessor.preprocess(request.text)
        return self.engine.synthesize(text=text, language=request.language)
