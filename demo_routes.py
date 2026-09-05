import json
from datetime import datetime

from flask import Response, flash, redirect, render_template, request, url_for

from app import app, admin_required, current_language
from demo_data import export_demo_data, import_demo_data


def _text(hr, en):
    return en if current_language() == "en" else hr


@app.route("/admin/demo-data", methods=["GET", "POST"])
@admin_required
def admin_demo_data():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "export":
            payload = export_demo_data()
            content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
            filename = f"parking-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            return Response(
                content,
                mimetype="application/json",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        if action == "import":
            uploaded = request.files.get("dataset")
            if not uploaded or not uploaded.filename:
                flash(_text("Odaberite JSON datoteku.", "Select a JSON file."), "danger")
                return redirect(url_for("admin_demo_data"))

            try:
                payload = json.loads(uploaded.read().decode("utf-8"))
                result = import_demo_data(payload)
            except Exception as exc:
                flash(
                    _text("Uvoz nije uspio", "Import failed") + f": {exc}",
                    "danger",
                )
                return redirect(url_for("admin_demo_data"))

            flash(
                _text(
                    f"Demo podaci su uvezeni: {result['users']} korisnika, {result['parkings']} parkinga, {result['reservations']} rezervacija i {result['notes']} bilješki.",
                    f"Demo data imported: {result['users']} users, {result['parkings']} parking spaces, {result['reservations']} reservations and {result['notes']} notes.",
                ),
                "success",
            )
            return redirect(url_for("admin_demo_data"))

    return render_template("demo_data.html")
