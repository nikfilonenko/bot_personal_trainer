import requests
from app.settings.config import config
from app.services.translation_service import TranslationService


__all__ = ["NutritionService"]


class NutritionService:
    def __init__(self):
        self.api_key = config.api_key_nutrition_training.get_secret_value()
        self.translator = TranslationService()

    async def get_nutrition_info(self, query: str):
        translated_query = await self.translator.translate_to_english(query)

        url = f"https://api.api-ninjas.com/v1/nutrition?query={translated_query}"
        response = requests.get(url, headers={'X-Api-Key': self.api_key})

        if response.status_code == 200:
            data = response.json()
            if data:
                translated_name = await self.translator.translate_to_russian(data[0]['name'])
                data[0]['name'] = translated_name
            return data
        return None