from googletrans import Translator

class TranslationService:
    def __init__(self):
        self.translator = Translator()

    async def translate_to_russian(self, text: str) -> str:
        try:
            translation = await self.translator.translate(text, src='en', dest='ru')
            return translation.text
        except Exception as e:
            print(f"Ошибка перевода: {e}")
            return text

    async def translate_to_english(self, text: str) -> str:
        try:
            translation = await self.translator.translate(text, src='ru', dest='en')
            return translation.text
        except Exception as e:
            print(f"Ошибка перевода: {e}")
            return text
