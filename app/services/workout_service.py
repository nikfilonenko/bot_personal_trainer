import requests
from typing import Optional, List, Dict

from app.settings.config import config
from app.services.translation_service import TranslationService


__all__ = ['WorkoutService']


class WorkoutService:
    def __init__(self):
        self.translation_service = TranslationService()

    def get_calories_burned(self, activity: str, duration: int) -> Optional[List[Dict[str, float]]]:
        try:
            translated_activity = self.translation_service.translate_to_english(activity)

            print(translated_activity)

            response = requests.get(
                f"https://api.api-ninjas.com/v1/caloriesburned?activity={translated_activity}",
                headers={'X-Api-Key': config.api_key_nutrition_training.get_secret_value()}
            )

            if response.status_code == 200:
                data = response.json()

                for item in data:
                    calories_per_hour = item.get('calories_per_hour', 0)

                    item['total_calories'] = (calories_per_hour / 60) * duration

                    item['name'] = self.translation_service.translate_to_russian(item['name'])
                return data

            return None
        except Exception as e:
            print(f"Ошибка при запросе к API: {e}")
            return None

