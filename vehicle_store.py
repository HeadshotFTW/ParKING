import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "vehicles.json"


def _read_all():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]\n", encoding="utf-8")
        return []

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    return data if isinstance(data, list) else []


def _write_all(vehicles):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(vehicles, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def reset_vehicles():
    _write_all([])


def list_vehicles(user_id):
    return [vehicle for vehicle in _read_all() if vehicle.get("user_id") == user_id]


def get_vehicle(user_id, vehicle_id):
    return next(
        (
            vehicle for vehicle in _read_all()
            if vehicle.get("id") == vehicle_id and vehicle.get("user_id") == user_id
        ),
        None,
    )


def add_vehicle(user_id, name, registration):
    vehicles = _read_all()
    next_id = max((vehicle.get("id", 0) for vehicle in vehicles), default=0) + 1
    vehicle = {
        "id": next_id,
        "user_id": user_id,
        "name": name,
        "registration": registration.upper(),
    }
    vehicles.append(vehicle)
    _write_all(vehicles)
    return vehicle


def update_vehicle(user_id, vehicle_id, name, registration):
    vehicles = _read_all()
    for vehicle in vehicles:
        if vehicle.get("id") == vehicle_id and vehicle.get("user_id") == user_id:
            vehicle["name"] = name
            vehicle["registration"] = registration.upper()
            _write_all(vehicles)
            return vehicle
    return None


def delete_vehicle(user_id, vehicle_id):
    vehicles = _read_all()
    remaining = [
        vehicle for vehicle in vehicles
        if not (vehicle.get("id") == vehicle_id and vehicle.get("user_id") == user_id)
    ]
    if len(remaining) == len(vehicles):
        return False
    _write_all(remaining)
    return True
