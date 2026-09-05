import base64
import json
from datetime import datetime
from pathlib import Path

from models import db, User, ParkingSpot, Reservation

BASE_DIR = Path(__file__).resolve().parent
NOTES_PATH = BASE_DIR / "data" / "parking_notes.json"
BINARY_PATH = BASE_DIR / "data" / "search_history.bin"
FORMAT_VERSION = 1


def _read_notes():
    if not NOTES_PATH.exists():
        return []
    try:
        data = json.loads(NOTES_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def export_demo_data():
    """Create a portable demo dataset without passwords or API tokens."""
    users = User.query.order_by(User.id).all()
    parkings = ParkingSpot.query.order_by(ParkingSpot.id).all()
    reservations = Reservation.query.order_by(Reservation.id).all()

    payload = {
        "format": "ParKING-demo-data",
        "version": FORMAT_VERSION,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "security_note": "Password hashes and API tokens are intentionally not exported.",
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "role": user.role,
            }
            for user in users
        ],
        "parkings": [
            {
                "id": parking.id,
                "owner_id": parking.owner_id,
                "name": parking.name,
                "location": parking.location,
                "price_per_hour": parking.price_per_hour,
                "description": parking.description,
                "photo_mime": parking.photo_mime,
                "photo_base64": base64.b64encode(parking.photo).decode("ascii") if parking.photo else None,
            }
            for parking in parkings
        ],
        "reservations": [
            {
                "id": reservation.id,
                "parking_id": reservation.parking_id,
                "user_id": reservation.user_id,
                "start_time": reservation.start_time.isoformat(),
                "end_time": reservation.end_time.isoformat(),
                "status": reservation.status,
            }
            for reservation in reservations
        ],
        "notes": _read_notes(),
        "binary_history_base64": (
            base64.b64encode(BINARY_PATH.read_bytes()).decode("ascii")
            if BINARY_PATH.exists()
            else None
        ),
    }
    return payload


def validate_demo_data(payload):
    if not isinstance(payload, dict):
        raise ValueError("Datoteka mora sadržavati JSON objekt.")
    if payload.get("format") != "ParKING-demo-data":
        raise ValueError("Datoteka nije ParKING demo export.")
    if payload.get("version") != FORMAT_VERSION:
        raise ValueError("Nepodržana verzija demo exporta.")
    for key in ("users", "parkings", "reservations", "notes"):
        if not isinstance(payload.get(key), list):
            raise ValueError(f"Nedostaje valjani niz '{key}'.")


def import_demo_data(payload):
    """Destructively replace demo data while recreating safe demo credentials."""
    validate_demo_data(payload)

    # Delete in foreign-key order.
    Reservation.query.delete()
    ParkingSpot.query.delete()
    User.query.delete()
    db.session.flush()

    for item in payload["users"]:
        role = str(item.get("role", "USER")).upper()
        if role not in {"USER", "ADMIN"}:
            role = "USER"
        user = User(
            id=int(item["id"]),
            username=str(item["username"]),
            role=role,
        )
        # Credentials are deliberately regenerated instead of exported.
        user.set_password("admin123" if role == "ADMIN" else "parking123")
        db.session.add(user)

    db.session.flush()

    for item in payload["parkings"]:
        photo = None
        if item.get("photo_base64"):
            photo = base64.b64decode(item["photo_base64"], validate=True)
        db.session.add(ParkingSpot(
            id=int(item["id"]),
            owner_id=int(item["owner_id"]),
            name=str(item["name"]),
            location=str(item["location"]),
            price_per_hour=float(item["price_per_hour"]),
            description=item.get("description"),
            photo=photo,
            photo_mime=item.get("photo_mime"),
        ))

    db.session.flush()

    for item in payload["reservations"]:
        db.session.add(Reservation(
            id=int(item["id"]),
            parking_id=int(item["parking_id"]),
            user_id=int(item["user_id"]),
            start_time=datetime.fromisoformat(item["start_time"]),
            end_time=datetime.fromisoformat(item["end_time"]),
            status=str(item.get("status", "ACTIVE")),
        ))

    db.session.commit()

    NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTES_PATH.write_text(
        json.dumps(payload["notes"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    encoded_binary = payload.get("binary_history_base64")
    if encoded_binary:
        BINARY_PATH.write_bytes(base64.b64decode(encoded_binary, validate=True))
    elif BINARY_PATH.exists():
        BINARY_PATH.unlink()

    return {
        "users": len(payload["users"]),
        "parkings": len(payload["parkings"]),
        "reservations": len(payload["reservations"]),
        "notes": len(payload["notes"]),
        "binary_history": bool(encoded_binary),
    }
