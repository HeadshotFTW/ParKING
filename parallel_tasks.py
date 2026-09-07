import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode
from urllib.request import Request, urlopen


WEATHER_LOCATIONS = [
    {"name": "Zagreb", "latitude": 45.8150, "longitude": 15.9819},
    {"name": "Samobor", "latitude": 45.8031, "longitude": 15.7181},
    {"name": "Velika Gorica", "latitude": 45.7125, "longitude": 16.0756},
]

# Zajednički resurs kojem pristupa više dretvi.
_request_log = []
_request_log_lock = threading.Lock()
_geocode_cache = {}


def parking_city_name(location_text):
    """Iz teksta lokacije izdvoji grad koji se koristi za vremenski servis."""
    text = (location_text or "").strip()
    if not text:
        return None

    normalized = text.casefold()
    for location in WEATHER_LOCATIONS:
        if location["name"].casefold() in normalized:
            return location["name"]

    parts = [part.strip() for part in text.split(",") if part.strip()]
    if not parts:
        return None

    cleaned_parts = []
    for part in parts:
        # Podržava i unos poput "23000 Zadar".
        cleaned = re.sub(r"^\d{4,6}\s+", "", part).strip()
        if cleaned:
            cleaned_parts.append(cleaned)

    # Kod unosa "Ulica 5, Zadar" radije uzmi dio bez kućnog broja.
    for part in cleaned_parts:
        if not any(character.isdigit() for character in part):
            return part

    return cleaned_parts[0] if cleaned_parts else None


def _geocode_city(city_name):
    """Pretvori naziv hrvatskog grada u koordinate preko Open-Meteo Geocoding API-ja."""
    cache_key = city_name.casefold()
    with _request_log_lock:
        cached = _geocode_cache.get(cache_key)
    if cached is not None:
        return cached

    params = urlencode({
        "name": city_name,
        "count": 1,
        "language": "hr",
        "format": "json",
        "countryCode": "HR",
    })
    url = f"https://geocoding-api.open-meteo.com/v1/search?{params}"
    request = Request(url, headers={"User-Agent": "ParKING/1.0"})

    with urlopen(request, timeout=6) as response:
        payload = json.loads(response.read().decode("utf-8"))

    results = payload.get("results") or []
    if not results:
        resolved = None
    else:
        first = results[0]
        resolved = {
            "name": first.get("name") or city_name,
            "latitude": first["latitude"],
            "longitude": first["longitude"],
            "timezone": first.get("timezone") or "Europe/Zagreb",
        }

    with _request_log_lock:
        _geocode_cache[cache_key] = resolved
    return resolved


def weather_location_for_parking(location_text):
    """Poveži tekstualnu lokaciju parkinga s Open-Meteo koordinatama."""
    city_name = parking_city_name(location_text)
    if city_name is None:
        return None

    for location in WEATHER_LOCATIONS:
        if location["name"].casefold() == city_name.casefold():
            return location

    return _geocode_city(city_name)


def fetch_weather(location):
    """Dohvati trenutačno vrijeme iz Open-Meteo REST servisa."""
    started = time.perf_counter()
    params = urlencode({
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": "temperature_2m,wind_speed_10m,weather_code",
        "timezone": location.get("timezone", "Europe/Zagreb"),
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    request = Request(url, headers={"User-Agent": "ParKING/1.0"})

    with urlopen(request, timeout=6) as response:
        payload = json.loads(response.read().decode("utf-8"))

    elapsed = time.perf_counter() - started
    current = payload.get("current", {})
    result = {
        "location": location["name"],
        "temperature": current.get("temperature_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "weather_code": current.get("weather_code"),
        "elapsed": elapsed,
        "thread": threading.current_thread().name,
    }

    # Kritična sekcija: Lock sprječava da dvije dretve istodobno mijenjaju zapisnik.
    with _request_log_lock:
        _request_log.append({
            "location": location["name"],
            "thread": result["thread"],
            "elapsed": elapsed,
        })

    return result


def fetch_weather_for_parking(location_text):
    """Dohvati vrijeme za grad iz lokacije jednog parkinga."""
    location = weather_location_for_parking(location_text)
    return fetch_weather(location) if location is not None else None


def _fetch_weather_for_city(city_name):
    location = weather_location_for_parking(city_name)
    if location is None:
        return None
    return fetch_weather(location)


def fetch_weather_for_parking_locations(location_texts):
    """Paralelno dohvati vrijeme za jedinstvene gradove prikazanih parkinga."""
    cities = {}
    for location_text in location_texts:
        city_name = parking_city_name(location_text)
        if city_name:
            cities[city_name.casefold()] = city_name

    if not cities:
        return {}

    results = {}
    workers = min(3, len(cities))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="parking-weather") as executor:
        futures = {
            executor.submit(_fetch_weather_for_city, city_name): city_key
            for city_key, city_name in cities.items()
        }
        for future in as_completed(futures):
            city_key = futures[future]
            try:
                weather = future.result()
                if weather is None:
                    results[city_key] = {"error": "Lokacija nije pronađena."}
                else:
                    results[city_key] = weather
            except Exception as exc:
                # Nedostupnost vremenskog servisa ne smije srušiti popis parkinga.
                results[city_key] = {"error": str(exc)}

    return results


def run_sequential_weather():
    started = time.perf_counter()
    results = [fetch_weather(location) for location in WEATHER_LOCATIONS]
    return results, time.perf_counter() - started


def run_parallel_weather():
    started = time.perf_counter()
    results = []

    # Bazen od tri dretve paralelno izvršava tri neovisna mrežna zahtjeva.
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="parking-weather") as executor:
        futures = [executor.submit(fetch_weather, location) for location in WEATHER_LOCATIONS]
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda item: item["location"])
    return results, time.perf_counter() - started


def run_thread_demo():
    global _request_log
    with _request_log_lock:
        _request_log = []

    sequential_results, sequential_time = run_sequential_weather()
    parallel_results, parallel_time = run_parallel_weather()

    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    with _request_log_lock:
        log_snapshot = list(_request_log)

    return {
        "sequential_results": sequential_results,
        "parallel_results": parallel_results,
        "sequential_time": sequential_time,
        "parallel_time": parallel_time,
        "speedup": speedup,
        "request_log": log_snapshot,
    }
