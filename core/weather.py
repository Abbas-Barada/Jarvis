import requests
from typing import Optional
from datetime import datetime


# Uses open-meteo (free, no API key needed) + wttr.in as fallback
# IP-based location detection via ip-api.com

def _get_location():
    """Get city/lat/lon from IP."""
    try:
        r = requests.get("http://ip-api.com/json/", timeout=5)
        data = r.json()
        if data.get("status") == "success":
            return {
                "city": data.get("city", "your city"),
                "lat": data["lat"],
                "lon": data["lon"]
            }
    except Exception:
        pass
    return None


def _weather_code_to_text(code: int) -> str:
    codes = {
        0: "clear sky",
        1: "mainly clear", 2: "partly cloudy", 3: "overcast",
        45: "foggy", 48: "icy fog",
        51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
        61: "light rain", 63: "rain", 65: "heavy rain",
        71: "light snow", 73: "snow", 75: "heavy snow",
        80: "light showers", 81: "showers", 82: "heavy showers",
        95: "thunderstorm", 96: "thunderstorm with hail",
    }
    return codes.get(code, "unknown conditions")


def get_weather(city: Optional[str] = None) -> str:
    """Get current weather. Uses IP location if no city given."""
    try:
        if city:
            # geocode the city
            geo = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1},
                timeout=5
            ).json()
            results = geo.get("results", [])
            if not results:
                return f"Couldn't find weather for {city}."
            r = results[0]
            lat, lon = r["latitude"], r["longitude"]
            city_name = r["name"]
        else:
            loc = _get_location()
            if not loc:
                return "Couldn't detect your location."
            lat, lon = loc["lat"], loc["lon"]
            city_name = loc["city"]

        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                "hourly": "relativehumidity_2m",
                "forecast_days": 1
            },
            timeout=5
        ).json()

        cw = weather.get("current_weather", {})
        temp = cw.get("temperature", "?")
        wind = cw.get("windspeed", "?")
        code = cw.get("weathercode", -1)
        condition = _weather_code_to_text(code)

        return f"{city_name}: {condition}, {temp}°C, wind {wind} km/h."

    except Exception as e:
        return f"Couldn't get weather: {e}"


def get_forecast(city: Optional[str] = None) -> str:
    """Get a 3-day forecast summary."""
    try:
        if city:
            geo = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1},
                timeout=5
            ).json()
            results = geo.get("results", [])
            if not results:
                return f"Couldn't find {city}."
            r = results[0]
            lat, lon = r["latitude"], r["longitude"]
            city_name = r["name"]
        else:
            loc = _get_location()
            if not loc:
                return "Couldn't detect your location."
            lat, lon = loc["lat"], loc["lon"]
            city_name = loc["city"]

        data = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "weathercode,temperature_2m_max,temperature_2m_min",
                "timezone": "auto",
                "forecast_days": 3
            },
            timeout=5
        ).json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        codes = daily.get("weathercode", [])
        maxes = daily.get("temperature_2m_max", [])
        mins = daily.get("temperature_2m_min", [])

        lines = [f"3-day forecast for {city_name}:"]
        for i in range(min(3, len(dates))):
            day = datetime.strptime(dates[i], "%Y-%m-%d").strftime("%A")
            cond = _weather_code_to_text(codes[i])
            lines.append(f"{day}: {cond}, {mins[i]}–{maxes[i]}°C")

        return " | ".join(lines)

    except Exception as e:
        return f"Couldn't get forecast: {e}"


def get_time() -> str:
    now = datetime.now()
    return now.strftime("It's %H:%M on %A, %d %B %Y.")


def get_date() -> str:
    now = datetime.now()
    return now.strftime("Today is %A, %d %B %Y.")


def handle_time_weather(text: str):
    """
    Parse text for time/weather commands.
    Returns result string or None.
    """
    t = text.lower()

    # Time
    if any(w in t for w in ["what time", "what's the time", "current time", "tell me the time"]):
        return get_time()

    # Date
    if any(w in t for w in ["what date", "what's the date", "today's date", "what day"]):
        return get_date()

    # Forecast
    if "forecast" in t or "next few days" in t or "this week" in t:
        city = _extract_city(t)
        return get_forecast(city)

    # Weather
    if "weather" in t or "temperature" in t or "how hot" in t or "how cold" in t or "raining" in t:
        city = _extract_city(t)
        return get_weather(city)

    return None


def _extract_city(text: str) -> Optional[str]:
    """Try to extract a city name from text like 'weather in London'."""
    import re
    match = re.search(r"(?:in|for|at)\s+([a-zA-Z\s]+?)(?:\?|$|\.|,)", text)
    if match:
        city = match.group(1).strip()
        # filter out generic words
        if city and city.lower() not in ["my", "the", "a", "here", "today", "now"]:
            return city
    return None