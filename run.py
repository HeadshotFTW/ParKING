import subprocess
import sys
from pathlib import Path

from flask import flash, redirect, render_template, request, url_for

from app import app, admin_required, current_user, login_required, DB_PATH, DATA_DIR
from binary_store import add_record, records_for_user
from parallel_tasks import run_thread_demo
import api_routes  # noqa: F401 - registrira REST rute i REST klijent


BINARY_HISTORY_PATH = DATA_DIR / "search_history.bin"


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
            messages = {
                0: "Proces B uspješno je završio posao.",
                1: "Proces B pronašao je problem u podacima.",
                2: "Proces B završio je tehničkom greškom.",
            }
            result = {
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
                "message": messages.get(completed.returncode, "Proces B vratio je neočekivani kod."),
            }
        except subprocess.TimeoutExpired:
            result = {
                "returncode": -1,
                "stdout": "",
                "stderr": "Proces B nije završio unutar 10 sekundi.",
                "message": "Proces A prekinuo je čekanje zbog isteka vremena.",
            }

    return render_template("admin_process.html", result=result)


@app.route("/binary-history", methods=["GET", "POST"])
@login_required
def binary_history():
    user = current_user()

    if request.method == "POST":
        location = request.form.get("location", "").strip()
        try:
            max_price = float(request.form.get("max_price", ""))
        except ValueError:
            max_price = -1

        if not location or max_price < 0:
            flash("Unesite ispravnu lokaciju i maksimalnu cijenu.", "danger")
        else:
            add_record(BINARY_HISTORY_PATH, user.id, location, max_price)
            flash("Zapis je spremljen u prilagođenu binarnu datoteku.", "success")
            return redirect(url_for("binary_history"))

    records = list(reversed(records_for_user(BINARY_HISTORY_PATH, user.id)))
    return render_template("binary_history.html", records=records)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
