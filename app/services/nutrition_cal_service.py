import requests
from app.services.translation_service import TranslationService
from typing import Optional, Dict


__all__ = ["NutritionService"]


class NutritionService:
    def __init__(self):
        self.translation_service = TranslationService()

    async def get_nutrition_info(self, product_name: str) -> Optional[Dict[str, str | float]]:
        translated_query = self.translation_service.translate_to_english(product_name)

        url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={translated_query}&json=true"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Ошибка: {response.status_code}")
            return None

        data = response.json()
        products = data.get('products', [])

        if not products:
            return None

        first_product = products[0]
        calories = first_product.get('nutriments', {}).get('energy-kcal_100g', 0)

        return {
            'name': product_name,
            'calories': calories
        }