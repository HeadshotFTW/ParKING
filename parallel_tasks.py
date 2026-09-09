import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests


KNOWN_WEATHER_LOCATIONS = [
    {"name": "Zagreb", "latitude": 45.8150, "longitude": 15.9819},
    {"name": "Samobor", "latitude": 45.8031, "longitude": 15.7181},
    {"name": "Velika Gorica", "latitude": 45.7125, "longitude": 16.0756},
]

_request_log = []
_request_log_lock = threading.Lock()
_geocode_cache = {}


def parking_city_name(location_text):
    """Iz teksta adrese izdvoji grad."""
    text = (location_text or "").strip()
    if not text:
        return None

    for location in KNOWN_WEATHER_LOCATIONS:
        if location["name"].casefold() in text.casefold():
            return location["name"]

    parts = [
        re.sub(r"^\d{4,6}\s+", "", part.strip())
        for part in text.split(",")
        if part.strip()
    ]
    for part in parts:
        if not any(char.isdigit() for char in part):
            return part
    return parts[0] if parts else None


def parking_cities(location_texts):
    """Vrati sortirani popis jedinstvenih gradova."""
    cities = {}
    for text in location_texts:
        city = parking_city_name(text)
        if city:
            cities[city.casefold()] = city
    return sorted(cities.values(), key=str.casefold)


def _geocode_city(city_name):
    key = city_name.casefold()
    with _request_log_lock:
        if key in _geocode_cache:
            return _geocode_cache[key]

    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": city_name,
            "count": 1,
            "language": "hr",
            "format": "json",
            "countryCode": "HR",
        },
        headers={"User-Agent": "ParKING/1.0"},
        timeout=6,
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    first = results[0] if results else None
    location = None if first is None else {
        "name": first.get("name") or city_name,
        "latitude": first["latitude"],
        "longitude": first["longitude"],
        "timezone": first.get("timezone") or "Europe/Zagreb",
    }

    with _request_log_lock:
        _geocode_cache[key] = location
    return location


def weather_location_for_parking(location_text):
    city = parking_city_name(location_text)
    if city is None:
        return None
    for location in KNOWN_WEATHER_LOCATIONS:
        if location["name"].casefold() == city.casefold():
            return location
    return _geocode_city(city)


def fetch_weather(location):
    """Jedan HTTP zahtjev prema Open-Meteo servisu."""
    started = time.perf_counter()
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": "temperature_2m,wind_speed_10m,weather_code",
            "timezone": location.get("timezone", "Europe/Zagreb"),
        },
        headers={"User-Agent": "ParKING/1.0"},
        timeout=6,
    )
    response.raise_for_status()
    current = response.json().get("current", {})
    elapsed = time.perf_counter() - started

    result = {
        "location": location["name"],
        "temperature": current.get("temperature_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "weather_code": current.get("weather_code"),
        "elapsed": elapsed,
        "thread": threading.current_thread().name,
    }

    # Kritična sekcija: samo jedna dretva smije mijenjati zajednički log.
    with _request_log_lock:
        _request_log.append({
            "location": result["location"],
            "thread": result["thread"],
            "elapsed": elapsed,
        })
    return result


def fetch_weather_for_parking(location_text):
    location = weather_location_for_parking(location_text)
    return fetch_weather(location) if location else None


def _fetch_city_safely(city_name):
    try:
        location = weather_location_for_parking(city_name)
        if location is None:
            raise ValueError(f"Lokacija nije pronađena: {city_name}")
        return city_name.casefold(), fetch_weather(location)
    except Exception as exc:
        return city_name.casefold(), {"error": str(exc)}


def fetch_weather_for_parking_locations(location_texts):
    """Paralelno dohvati vrijeme za jedinstvene gradove parkinga."""
    cities = parking_cities(location_texts)
    if not cities:
        return {}

    workers = min(3, len(cities))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="parking-weather") as executor:
        pairs = executor.map(_fetch_city_safely, cities)
        return dict(pairs)


def resolve_weather_locations(city_names):
    """Razriješi koordinate prije mjerenja dretvi."""
    locations = []
    for city in city_names:
        location = weather_location_for_parking(city)
        if location is None:
            raise ValueError(f"Lokacija nije pronađena: {city}")
        locations.append(location)
    return locations


def run_weather_with_workers(locations, max_workers):
    """Izvrši isti posao sa zadanim brojem radnih dretvi."""
    if not locations:
        return [], 0.0, 0

    workers = min(max_workers, len(locations))
    started = time.perf_counter()
    with ThreadPoolExecutor(
        max_workers=workers,
        thread_name_prefix=f"parking-weather-{workers}",
    ) as executor:
        results = list(executor.map(fetch_weather, locations))

    results.sort(key=lambda item: item["location"].casefold())
    return results, time.perf_counter() - started, workers


def run_thread_demo(location_texts):
    """Usporedi isti posao s 1 i s najviše 3 dretve."""
    with _request_log_lock:
        _request_log.clear()

    city_names = parking_cities(location_texts)
    if not city_names:
        return {
            "city_names": [],
            "one_thread_results": [],
            "multi_thread_results": [],
            "one_thread_time": 0.0,
            "multi_thread_time": 0.0,
            "multi_thread_workers": 0,
            "speedup": 0.0,
            "request_log": [],
        }

    locations = resolve_weather_locations(city_names)
    one_results, one_time, _ = run_weather_with_workers(locations, 1)
    multi_results, multi_time, workers = run_weather_with_workers(locations, 3)

    with _request_log_lock:
        log = list(_request_log)

    return {
        "city_names": city_names,
        "one_thread_results": one_results,
        "multi_thread_results": multi_results,
        "one_thread_time": one_time,
        "multi_thread_time": multi_time,
        "multi_thread_workers": workers,
        "speedup": one_time / multi_time if multi_time else 0.0,
        "request_log": log,
    }
