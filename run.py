from pathlib import Path

import requests
from flask import flash, redirect, render_template, request, url_for

from app import app, admin_required, current_language, current_user, login_required, DATA_DIR
from binary_store import records_for_user
from crypto_store import decrypt_notes, encrypt_notes
from hash_demo import create_integrity_hash, reservation_integrity_text, verify_integrity_hash
from json_store import list_notes
from models import ParkingSpot, Reservation
from parallel_tasks import run_thread_demo
from parking_availability import install_parking_availability
from security_code_store import security_code_is_set, set_security_code, verify_security_code
from service_fee import (
    SERVICE_FEE_PERCENTAGE,
    calculate_service_fee,
    total_service_fees_for_reservations,
)


BINARY_HISTORY_PATH = DATA_DIR / "search_history.bin"
SECURITY_CODE_PATH = DATA_DIR / "security_codes.json"
EXPORT_DIR = Path(__file__).resolve().parent / "exports"
REST_API_BASE_URL = "http://127.0.0.1:5001"

install_parking_availability(app)

app.jinja_env.globals.update(
    service_fee=calculate_service_fee,
    total_service_fees=total_service_fees_for_reservations,
    service_fee_percentage=SERVICE_FEE_PERCENTAGE,
    security_code_configured=lambda user_id: security_code_is_set(SECURITY_CODE_PATH, user_id),
)


def tech_text(hr, en):
    return en if current_language() == "en" else hr


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


@app.route("/notes/security-code", methods=["POST"])
@login_required
def notes_security_code():
    """Set or change the signed-in user's backup security code."""
    user = current_user()
    new_code = request.form.get("new_code", "")
    confirm_code = request.form.get("confirm_code", "")

    if len(new_code) < 4:
        flash(
            tech_text(
                "Sigurnosni kod mora imati najmanje 4 znaka.",
                "The security code must contain at least 4 characters.",
            ),
            "danger",
        )
        return redirect(url_for("notes"))

    if new_code != confirm_code:
        flash(
            tech_text("Novi sigurnosni kodovi se ne podudaraju.", "The new security codes do not match."),
            "danger",
        )
        return redirect(url_for("notes"))

    if security_code_is_set(SECURITY_CODE_PATH, user.id):
        current_code = request.form.get("current_code", "")
        verification = verify_security_code(SECURITY_CODE_PATH, user.id, current_code)
        if not verification["valid"]:
            flash(
                tech_text(
                    "Trenutačni sigurnosni kod nije ispravan.",
                    "The current security code is not correct.",
                ),
                "danger",
            )
            return redirect(url_for("notes"))

    set_security_code(SECURITY_CODE_PATH, user.id, new_code)
    flash(
        tech_text(
            "Sigurnosni kod je spremljen. Sprema se samo SHA-256 sažetak; promjenjiva sol izvodi se iz user_id, a sol i papar se ne spremaju.",
            "The security code was saved. Only its SHA-256 digest is stored; the variable salt is derived from user_id, and neither the salt nor pepper is stored.",
        ),
        "success",
    )
    return redirect(url_for("notes"))


@app.route("/notes/backup", methods=["POST"])
@login_required
def notes_backup():
    """Encrypt or decrypt the signed-in user's notes backup with AES-GCM."""
    user = current_user()
    output_path = EXPORT_DIR / f"notes_user_{user.id}.aes"
    action = request.form.get("action", "")

    try:
        if action == "encrypt":
            if not security_code_is_set(SECURITY_CODE_PATH, user.id):
                flash(
                    tech_text(
                        "Najprije postavite sigurnosni kod za šifriranu sigurnosnu kopiju.",
                        "Set a security code for the encrypted backup first.",
                    ),
                    "warning",
                )
                return redirect(url_for("notes"))

            encrypt_notes(
                list_notes(user.id),
                app.config["SECRET_KEY"],
                user.id,
                output_path,
            )
            relative_path = output_path.relative_to(Path(__file__).resolve().parent)
            flash(
                tech_text(
                    f"Šifrirana sigurnosna kopija bilješki spremljena je u {relative_path}.",
                    f"Encrypted notes backup was saved to {relative_path}.",
                ),
                "success",
            )
            return redirect(url_for("notes"))

        if action == "decrypt":
            if not security_code_is_set(SECURITY_CODE_PATH, user.id):
                flash(
                    tech_text(
                        "Najprije postavite sigurnosni kod za šifriranu sigurnosnu kopiju.",
                        "Set a security code for the encrypted backup first.",
                    ),
                    "warning",
                )
                return redirect(url_for("notes"))

            if not output_path.exists():
                flash(
                    tech_text(
                        "Najprije izradite šifriranu sigurnosnu kopiju bilješki.",
                        "Create an encrypted notes backup first.",
                    ),
                    "warning",
                )
                return redirect(url_for("notes"))

            security_code = request.form.get("security_code", "")
            verification = verify_security_code(SECURITY_CODE_PATH, user.id, security_code)
            if not verification["valid"]:
                flash(
                    tech_text(
                        f"Sigurnosni kod nije ispravan. Provjereno je svih {verification['attempts']} mogućih vrijednosti papra.",
                        f"The security code is not correct. All {verification['attempts']} possible pepper values were checked.",
                    ),
                    "danger",
                )
                return redirect(url_for("notes"))

            decrypted_backup = decrypt_notes(
                app.config["SECRET_KEY"],
                user.id,
                output_path,
            )
            flash(
                tech_text(
                    f"Sigurnosni kod je potvrđen i kopija je dešifrirana. Provjereno je svih {verification['attempts']} mogućih vrijednosti papra.",
                    f"The security code was verified and the backup was decrypted. All {verification['attempts']} possible pepper values were checked.",
                ),
                "success",
            )
            return render_template(
                "notes.html",
                notes=list_notes(user.id),
                decrypted_backup=decrypted_backup,
                security_verification=verification,
            )

        flash(
            tech_text("Nepoznata radnja sigurnosne kopije.", "Unknown backup action."),
            "danger",
        )
    except Exception as exc:
        prefix = tech_text(
            "Kriptografska operacija nije uspjela",
            "Cryptographic operation failed",
        )
        flash(f"{prefix}: {exc}", "danger")

    return redirect(url_for("notes"))


@app.route("/crypto")
@login_required
def crypto_demo():
    """Backward-compatible redirect from the former standalone AES page."""
    return redirect(url_for("notes"))


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
