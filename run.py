import requests
from flask import flash, render_template, request

from app import app, admin_required, current_language, current_user, login_required, DATA_DIR
from binary_store import records_for_user
from hash_demo import create_integrity_hash, reservation_integrity_text, verify_integrity_hash
from models import ParkingSpot, Reservation
from parallel_tasks import run_thread_demo
from parking_availability import install_parking_availability
from promo_web import install_promo_features
from service_fee import (
    SERVICE_FEE_PERCENTAGE,
    calculate_service_fee,
    total_service_fees_for_reservations,
)


BINARY_HISTORY_PATH = DATA_DIR / "search_history.bin"
REST_API_BASE_URL = "http://127.0.0.1:5001"

install_parking_availability(app)

app.jinja_env.globals.update(
    service_fee=calculate_service_fee,
    total_service_fees=total_service_fees_for_reservations,
    service_fee_percentage=SERVICE_FEE_PERCENTAGE,
)


def tech_text(hr, en):
    return en if current_language() == "en" else hr


install_promo_features(
    app,
    admin_required=admin_required,
    login_required=login_required,
    current_user=current_user,
    local_text=tech_text,
)


@app.route("/rest-client")
@login_required
def rest_client():
    """REST client in the main app calling the separate API process on port 5001."""
    user = current_user()
    headers = {"Authorization": f"Bearer {user.api_token}"}
    results = []

    for label, endpoint in (
        ("GET /api/parkings", "/api/parkings"),
        ("GET /api/reservations", "/api/reservations"),
    ):
        try:
            response = requests.get(
                REST_API_BASE_URL + endpoint,
                headers=headers,
                timeout=5,
            )
            try:
                body = response.json()
            except ValueError:
                body = {"raw": response.text[:500]}
            results.append({
                "label": label,
                "status": response.status_code,
                "body": body,
            })
        except requests.RequestException as exc:
            results.append({
                "label": label,
                "status": "ERROR",
                "body": {"error": str(exc)},
            })

    return render_template(
        "rest_client.html",
        results=results,
        api_token=user.api_token,
        api_base_url=REST_API_BASE_URL,
    )


@app.route("/admin/threads")
@admin_required
def admin_threads():
    parking_locations = [
        row[0]
        for row in ParkingSpot.query.with_entities(ParkingSpot.location).order_by(ParkingSpot.id).all()
        if row[0]
    ]
    try:
        demo = run_thread_demo(parking_locations)
        error = None
    except Exception as exc:
        demo = None
        error = str(exc)
    return render_template("admin_threads.html", demo=demo, error=error)


@app.route("/search-history")
@app.route("/binary-history")
@login_required
def binary_history():
    records = list(reversed(records_for_user(BINARY_HISTORY_PATH, current_user().id)))
    return render_template("binary_history.html", records=records)


@app.route("/hash", methods=["GET", "POST"])
@login_required
def hash_demo_page():
    user = current_user()
    reservations = Reservation.query.filter_by(user_id=user.id).order_by(
        Reservation.start_time.desc()
    ).all()

    selected_id = request.values.get("reservation_id", type=int)
    reservation = None
    if selected_id is not None:
        reservation = Reservation.query.filter_by(id=selected_id, user_id=user.id).first()
    elif reservations:
        reservation = reservations[0]

    result = None
    verification = None
    integrity_text = None
    expected_digest = ""

    if reservation is not None:
        integrity_text = reservation_integrity_text(reservation)
        result = create_integrity_hash(integrity_text)
        expected_digest = request.form.get("expected_digest", "").strip() if request.method == "POST" else result["digest"]

        if request.method == "POST":
            try:
                valid_format = len(expected_digest) == 64
                int(expected_digest, 16)
            except ValueError:
                valid_format = False

            if not valid_format:
                flash(
                    tech_text(
                        "Kontrolni SHA-256 sažetak mora sadržavati 64 heksadekadska znaka.",
                        "The SHA-256 verification digest must contain 64 hexadecimal characters.",
                    ),
                    "danger",
                )
            else:
                verification = verify_integrity_hash(integrity_text, expected_digest)

    return render_template(
        "hash_demo.html",
        reservations=reservations,
        reservation=reservation,
        integrity_text=integrity_text,
        expected_digest=expected_digest,
        result=result,
        verification=verification,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True, use_reloader=False)
