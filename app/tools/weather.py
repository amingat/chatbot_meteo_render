import requests
from langchain_core.tools import tool


GEOCODING_URL = 'https://geocoding-api.open-meteo.com/v1/search'
FORECAST_URL = 'https://api.open-meteo.com/v1/forecast'


def _geocode(city: str) -> dict:
    response = requests.get(
        GEOCODING_URL,
        params={'name': city, 'count': 1, 'language': 'fr', 'format': 'json'},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get('results') or []
    if not results:
        raise ValueError(f'Ville introuvable: {city}')
    return results[0]


@tool
def weather_tool(location: str) -> str:
    """Renvoie la météo actuelle et la prévision du jour pour une ville ou un lieu."""
    try:
        geo = _geocode(location)
        forecast = requests.get(
            FORECAST_URL,
            params={
                'latitude': geo['latitude'],
                'longitude': geo['longitude'],
                'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code',
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_probability_max',
                'timezone': 'auto',
                'forecast_days': 1,
            },
            timeout=20,
        )
        forecast.raise_for_status()
        data = forecast.json()
        current = data.get('current', {})
        daily = data.get('daily', {})

        city_label = geo.get('name', location)
        country = geo.get('country', '')
        temp = current.get('temperature_2m', 'N/A')
        humidity = current.get('relative_humidity_2m', 'N/A')
        wind = current.get('wind_speed_10m', 'N/A')
        tmin = (daily.get('temperature_2m_min') or ['N/A'])[0]
        tmax = (daily.get('temperature_2m_max') or ['N/A'])[0]
        rain = (daily.get('precipitation_probability_max') or ['N/A'])[0]

        return (
            f"Météo pour {city_label}, {country}: température actuelle {temp}°C, humidité {humidity}%, vent {wind} km/h. "
            f"Aujourd'hui: min {tmin}°C, max {tmax}°C, probabilité maximale de pluie {rain}%."
        )
    except Exception as exc:
        return f'Impossible de récupérer la météo: {exc}'
