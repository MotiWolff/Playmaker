from deep_translator import GoogleTranslator
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.odds_winer.translator")

class Translator:
    """Single responsibility class for translation operations."""
    def __init__(self, source_lang: str = "he", target_lang: str = "en"):
        self.source = source_lang
        self.target = target_lang
        self.translator = GoogleTranslator(source=self.source, target=self.target)

    def translate(self, text: str) -> str:
        if not text:
            return text
        try:
            return self.translator.translate(text)
        except Exception as e:
            # don't fail the whole pipeline for transient translation errors
            log.warning("translator.failed", extra={"text": text, "error": str(e)})
            return text
