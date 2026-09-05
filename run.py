import subprocess
import sys
from pathlib import Path

from flask import render_template, request

from app import app, admin_required, DB_PATH
from parallel_tasks import run_thread_demo


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
