import json
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


def weather_location_for_parking(location_text):
    """Poveži tekstualnu lokaciju parkinga s podržanom Open-Meteo lokacijom."""
    normalized = (location_text or "").casefold()
    for location in WEATHER_LOCATIONS:
        if location["name"].casefold() in normalized:
            return location
    return None


def fetch_weather(location):
    """Dohvati trenutačno vrijeme iz Open-Meteo REST servisa."""
    started = time.perf_counter()
    params = urlencode({
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": "temperature_2m,wind_speed_10m,weather_code",
        "timezone": "Europe/Zagreb",
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

    # Lock sprječava da dvije dretve istodobno mijenjaju zajednički zapisnik.
    with _request_log_lock:
        _request_log.append({
            "location": location["name"],
            "thread": result["thread"],
            "elapsed": elapsed,
        })

    return result


def fetch_weather_for_parking(location_text):
    """Dohvati vrijeme za jednu lokaciju parkinga ako je grad podržan."""
    location = weather_location_for_parking(location_text)
    return fetch_weather(location) if location is not None else None


def fetch_weather_for_parking_locations(location_texts):
    """Paralelno dohvati vrijeme za jedinstvene gradove prikazanih parkinga."""
    matched_locations = {}
    for location_text in location_texts:
        location = weather_location_for_parking(location_text)
        if location is not None:
            matched_locations[location["name"]] = location

    if not matched_locations:
        return {}

    results = {}
    workers = min(3, len(matched_locations))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="parking-weather") as executor:
        futures = {
            executor.submit(fetch_weather, location): name
            for name, location in matched_locations.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as exc:
                # Nedostupnost vremenskog servisa ne smije srušiti popis parkinga.
                results[name] = {"location": name, "error": str(exc)}

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
