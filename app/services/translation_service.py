from googletrans import Translator


__all__ = ['TranslationService']


class TranslationService:
    def __init__(self):
        self.translator = Translator()

    def translate_to_english(self, text: str) -> str:
        try:
            translated = self.translator.translate(text, src='ru', dest='en')
            return translated.text
        except Exception as e:
            print(f"Ошибка перевода на английский: {e}")
            return text

    def translate_to_russian(self, text: str) -> str:
        try:
            translated = self.translator.translate(text, src='en', dest='ru')
            return translated.text
        except Exception as e:
            print(f"Ошибка перевода на русский: {e}")
            return text