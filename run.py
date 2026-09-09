import requests
from flask import flash, render_template, request

from app import app, admin_required, current_language, current_user, login_required, DATA_DIR
from avatar_web import install_avatar_features
from binary_store import records_for_user
from hash_demo import create_integrity_hash, reservation_integrity_text, verify_integrity_hash
from models import ParkingSpot, Reservation
from parallel_tasks import run_thread_demo
from parking_availability import install_parking_availability
from promo_web import install_promo_features
from service_fee import SERVICE_FEE_PERCENTAGE, calculate_service_fee, total_service_fees_for_reservations


BINARY_HISTORY_PATH = DATA_DIR / "search_history.bin"
REST_API_BASE_URL = "http://127.0.0.1:5001"


def tech_text(hr, en):
    return en if current_language() == "en" else hr


# Uključivanje dodatnih funkcionalnosti u glavnu Flask aplikaciju.
install_parking_availability(app)
install_promo_features(app, admin_required, login_required, current_user, tech_text)
install_avatar_features(app, login_required, current_user, tech_text)

app.jinja_env.globals.update(
    service_fee=calculate_service_fee,
    total_service_fees=total_service_fees_for_reservations,
    service_fee_percentage=SERVICE_FEE_PERCENTAGE,
)


def _api_get(endpoint, headers):
    """Jedan GET poziv prema našem REST procesu na portu 5001."""
    try:
        response = requests.get(REST_API_BASE_URL + endpoint, headers=headers, timeout=5)
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text[:500]}
        return {"label": f"GET {endpoint}", "status": response.status_code, "body": body}
    except requests.RequestException as exc:
        return {"label": f"GET {endpoint}", "status": "ERROR", "body": {"error": str(exc)}}


@app.route("/rest-client")
@admin_required
def rest_client():
    user = current_user()
    headers = {"Authorization": f"Bearer {user.api_token}"}
    results = [
        _api_get(endpoint, headers)
        for endpoint in ("/api/parkings", "/api/reservations")
    ]
    return render_template(
        "rest_client.html",
        results=results,
        api_token=user.api_token,
        api_base_url=REST_API_BASE_URL,
    )


@app.route("/admin/threads")
@admin_required
def admin_threads():
    rows = ParkingSpot.query.with_entities(ParkingSpot.location).order_by(ParkingSpot.id).all()
    locations = [location for (location,) in rows if location]

    try:
        demo, error = run_thread_demo(locations), None
    except Exception as exc:
        demo, error = None, str(exc)

    return render_template("admin_threads.html", demo=demo, error=error)


@app.route("/search-history")
@app.route("/binary-history")
@admin_required
def binary_history():
    records = records_for_user(BINARY_HISTORY_PATH, current_user().id)
    return render_template("binary_history.html", records=list(reversed(records)))


def _valid_sha256(value):
    if len(value) != 64:
        return False
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


@app.route("/hash", methods=["GET", "POST"])
@login_required
def hash_demo_page():
    user = current_user()
    reservations = Reservation.query.filter_by(user_id=user.id).order_by(
        Reservation.start_time.desc()
    ).all()

    selected_id = request.values.get("reservation_id", type=int)
    reservation = (
        Reservation.query.filter_by(id=selected_id, user_id=user.id).first()
        if selected_id is not None
        else (reservations[0] if reservations else None)
    )

    integrity_text = result = verification = None
    expected_digest = ""

    if reservation:
        integrity_text = reservation_integrity_text(reservation)
        result = create_integrity_hash(integrity_text)
        expected_digest = (
            request.form.get("expected_digest", "").strip()
            if request.method == "POST"
            else result["digest"]
        )

        if request.method == "POST":
            if _valid_sha256(expected_digest):
                verification = verify_integrity_hash(integrity_text, expected_digest)
            else:
                flash(
                    tech_text(
                        "Kontrolni SHA-256 sažetak mora sadržavati 64 heksadekadska znaka.",
                        "The SHA-256 verification digest must contain 64 hexadecimal characters.",
                    ),
                    "danger",
                )

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
