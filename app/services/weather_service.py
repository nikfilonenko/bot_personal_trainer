import requests
from app.settings.config import config


class WeatherService:
    def __init__(self):
        self.api_key = config.api_key_open_weather.get_secret_value()

    def get_temperature(self, city: str) -> float:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['main']['temp']
        return None