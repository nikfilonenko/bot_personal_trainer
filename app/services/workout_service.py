import requests
from app.settings.config import config
from app.services.translation_service import TranslationService


class WorkoutService:
    def __init__(self):
        self.api_key = config.api_key_nutrition_training.get_secret_value()
        self.translator = TranslationService()

    async def get_calories_burned(self, activity: str, duration: int):
        translated_activity = await self.translator.translate_to_english(activity)

        url = f"https://api.api-ninjas.com/v1/caloriesburned?activity={translated_activity}&duration={duration}"
        response = requests.get(url, headers={'X-Api-Key': self.api_key})

        if response.status_code == 200:
            data = response.json()
            if data:
                translated_activity = await self.translator.translate_to_russian(data[0]['activity'])
                data[0]['activity'] = translated_activity
            return data
        return None