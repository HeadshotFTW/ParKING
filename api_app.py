import secrets
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, g, jsonify, request
from sqlalchemy import text

from models import db, ParkingSpot, Reservation, User

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "parking.db"

api_app = Flask(__name__)
api_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
api_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(api_app)


def ensure_database():
    """Ensure the shared SQLite schema and API tokens exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with api_app.app_context():
        db.create_all()
        columns = {row[1] for row in db.session.execute(text("PRAGMA table_info(users)")).all()}
        if "api_token" not in columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN api_token VARCHAR(64)"))
            db.session.commit()

        changed = False
        for user in User.query.all():
            if not user.api_token:
                user.api_token = secrets.token_hex(24)
                changed = True
        if changed:
            db.session.commit()


def api_auth_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Nedostaje Bearer token."}), 401

        token = header.removeprefix("Bearer ").strip()
        user = User.query.filter_by(api_token=token).first()
        if not user:
            return jsonify({"error": "Neispravan API token."}), 401

        g.api_user = user
        return view_func(*args, **kwargs)

    return wrapped


def parking_to_dict(parking):
    return {
        "id": parking.id,
        "name": parking.name,
        "location": parking.location,
        "price_per_hour": parking.price_per_hour,
        "owner": parking.owner.username,
    }


def reservation_to_dict(reservation):
    return {
        "id": reservation.id,
        "parking_id": reservation.parking_id,
        "parking": reservation.parking.name,
        "user": reservation.user.username,
        "start_time": reservation.start_time.isoformat(timespec="minutes"),
        "end_time": reservation.end_time.isoformat(timespec="minutes"),
        "status": reservation.status,
        "total_price": round(reservation.total_price(), 2),
    }


@api_app.route("/api/health")
def api_health():
    return jsonify({"service": "ParKING REST API", "port": 5001, "status": "ok"})


@api_app.route("/api/parkings", methods=["GET", "POST"])
@api_auth_required
def api_parkings():
    user = g.api_user

    if request.method == "GET":
        parkings = ParkingSpot.query.order_by(ParkingSpot.id.asc()).all()
        return jsonify({"items": [parking_to_dict(item) for item in parkings]})

    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    location = str(data.get("location", "")).strip()
    try:
        price = float(data.get("price_per_hour"))
    except (TypeError, ValueError):
        return jsonify({"error": "price_per_hour mora biti broj."}), 400

    if not name or not location or price < 0:
        return jsonify({"error": "Naziv, lokacija i cijena su obavezni."}), 400

    parking = ParkingSpot(
        owner_id=user.id,
        name=name,
        location=location,
        price_per_hour=price,
        description=str(data.get("description", "")).strip(),
    )
    db.session.add(parking)
    db.session.commit()
    return jsonify(parking_to_dict(parking)), 201


@api_app.route("/api/parkings/<int:parking_id>", methods=["GET", "PUT", "DELETE"])
@api_auth_required
def api_parking_detail(parking_id):
    user = g.api_user
    parking = db.get_or_404(ParkingSpot, parking_id)

    if request.method == "GET":
        return jsonify(parking_to_dict(parking))

    if parking.owner_id != user.id and not user.is_admin():
        return jsonify({"error": "Niste ovlašteni mijenjati ovaj parking."}), 403

    if request.method == "DELETE":
        db.session.delete(parking)
        db.session.commit()
        return jsonify({"message": "Parking je obrisan."})

    data = request.get_json(silent=True) or {}
    if "name" in data:
        parking.name = str(data["name"]).strip() or parking.name
    if "location" in data:
        parking.location = str(data["location"]).strip() or parking.location
    if "price_per_hour" in data:
        try:
            price = float(data["price_per_hour"])
        except (TypeError, ValueError):
            return jsonify({"error": "price_per_hour mora biti broj."}), 400
        if price < 0:
            return jsonify({"error": "Cijena ne može biti negativna."}), 400
        parking.price_per_hour = price
    if "description" in data:
        parking.description = str(data["description"]).strip()

    db.session.commit()
    return jsonify(parking_to_dict(parking))


@api_app.route("/api/reservations", methods=["GET", "POST"])
@api_auth_required
def api_reservations():
    user = g.api_user

    if request.method == "GET":
        query = Reservation.query
        if not user.is_admin():
            query = query.filter_by(user_id=user.id)
        items = query.order_by(Reservation.start_time.desc()).all()
        return jsonify({"items": [reservation_to_dict(item) for item in items]})

    data = request.get_json(silent=True) or {}
    try:
        parking_id = int(data.get("parking_id"))
        start_time = datetime.fromisoformat(str(data.get("start_time", "")))
        end_time = datetime.fromisoformat(str(data.get("end_time", "")))
    except (TypeError, ValueError):
        return jsonify({"error": "Neispravni podaci rezervacije."}), 400

    parking = db.session.get(ParkingSpot, parking_id)
    if not parking:
        return jsonify({"error": "Parking ne postoji."}), 404
    if parking.owner_id == user.id:
        return jsonify({"error": "Ne možete rezervirati vlastiti parking."}), 403
    if end_time <= start_time:
        return jsonify({"error": "Završetak mora biti nakon početka."}), 400

    conflict = Reservation.query.filter_by(parking_id=parking_id, status="ACTIVE").filter(
        Reservation.start_time < end_time,
        Reservation.end_time > start_time,
    ).first()
    if conflict:
        return jsonify({"error": "Parking je već rezerviran u tom terminu."}), 409

    reservation = Reservation(
        parking_id=parking_id,
        user_id=user.id,
        start_time=start_time,
        end_time=end_time,
        status="ACTIVE",
    )
    db.session.add(reservation)
    db.session.commit()
    return jsonify(reservation_to_dict(reservation)), 201


@api_app.route("/api/reservations/<int:reservation_id>", methods=["GET", "DELETE"])
@api_auth_required
def api_reservation_detail(reservation_id):
    user = g.api_user
    reservation = db.get_or_404(Reservation, reservation_id)

    if reservation.user_id != user.id and not user.is_admin():
        return jsonify({"error": "Niste ovlašteni za ovu rezervaciju."}), 403

    if request.method == "GET":
        return jsonify(reservation_to_dict(reservation))

    db.session.delete(reservation)
    db.session.commit()
    return jsonify({"message": "Rezervacija je obrisana."})


if __name__ == "__main__":
    ensure_database()
    api_app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
