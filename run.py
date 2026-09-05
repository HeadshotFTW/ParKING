from flask import render_template

from app import app, admin_required
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
