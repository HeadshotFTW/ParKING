import subprocess
import sys
from pathlib import Path

import requests
from flask import flash, render_template, request

from app import app, admin_required, current_language, current_user, login_required, DB_PATH, DATA_DIR
from binary_store import records_for_user
from crypto_store import decrypt_notes, encrypt_notes
from hash_demo import create_integrity_hash, reservation_integrity_text, verify_by_full_pepper_scan
from json_store import list_notes
from models import Reservation
from parallel_tasks import run_thread_demo
from parking_availability import install_parking_availability


BINARY_HISTORY_PATH = DATA_DIR / "search_history.bin"
EXPORT_DIR = Path(__file__).resolve().parent / "exports"
REST_API_BASE_URL = "http://127.0.0.1:5001"

install_parking_availability(app)


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
    try:
        demo = run_thread_demo()
        error = None
    except Exception as exc:
        demo = None
        error = str(exc)
    return render_template("admin_threads.html", demo=demo, error=error)


@app.route("/admin/process", methods=["GET", "POST"])
@admin_required
def admin_process():
    result = None
    if request.method == "POST":
        worker = Path(__file__).resolve().parent / "reservation_worker.py"
        command = [sys.executable, str(worker), str(DB_PATH)]
        if request.form.get("mode") == "error":
            command.append("--simulate-error")

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            messages_hr = {
                0: "Proces B uspješno je završio posao.",
                1: "Proces B pronašao je problem u podacima.",
                2: "Proces B završio je tehničkom greškom.",
            }
            messages_en = {
                0: "Process B completed successfully.",
                1: "Process B found a data problem.",
                2: "Process B ended with a technical error.",
            }
            messages = messages_en if current_language() == "en" else messages_hr
            result = {
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
                "message": messages.get(
                    completed.returncode,
                    tech_text("Proces B vratio je neočekivani kod.", "Process B returned an unexpected code."),
                ),
            }
        except subprocess.TimeoutExpired:
            result = {
                "returncode": -1,
                "stdout": "",
                "stderr": tech_text(
                    "Proces B nije završio unutar 10 sekundi.",
                    "Process B did not finish within 10 seconds.",
                ),
                "message": tech_text(
                    "Proces A prekinuo je čekanje zbog isteka vremena.",
                    "Process A stopped waiting because the timeout expired.",
                ),
            }

    return render_template("admin_process.html", result=result)


@app.route("/search-history")
@app.route("/binary-history")
@login_required
def binary_history():
    records = list(reversed(records_for_user(BINARY_HISTORY_PATH, current_user().id)))
    return render_template("binary_history.html", records=records)


@app.route("/crypto", methods=["GET", "POST"])
@login_required
def crypto_demo():
    user = current_user()
    encrypted_path = None
    decrypted_notes = None
    output_path = EXPORT_DIR / f"notes_user_{user.id}.aes"

    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "encrypt":
                notes = list_notes(user.id)
                encrypt_notes(notes, app.config["SECRET_KEY"], user.id, output_path)
                encrypted_path = str(output_path.relative_to(Path(__file__).resolve().parent))
                flash(tech_text("Bilješke su uspješno šifrirane AES-GCM algoritmom.", "Notes were successfully encrypted with AES-GCM."), "success")
            elif action == "decrypt":
                if not output_path.exists():
                    flash(tech_text("Najprije izradite šifriranu sigurnosnu kopiju.", "Create an encrypted backup first."), "warning")
                else:
                    decrypted_notes = decrypt_notes(app.config["SECRET_KEY"], user.id, output_path)
                    flash(tech_text("Šifrirana datoteka je uspješno dešifrirana.", "The encrypted file was successfully decrypted."), "success")
        except Exception as exc:
            prefix = tech_text("Kriptografska operacija nije uspjela", "Cryptographic operation failed")
            flash(f"{prefix}: {exc}", "danger")

    return render_template(
        "crypto.html",
        encrypted_path=encrypted_path,
        decrypted_notes=decrypted_notes,
    )


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
        result = create_integrity_hash(user.id, user.username, integrity_text)
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
                verification = verify_by_full_pepper_scan(
                    user.id,
                    user.username,
                    integrity_text,
                    expected_digest,
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
