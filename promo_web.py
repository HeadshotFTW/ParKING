from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from models import db, ParkingSpot, PromoCode, Reservation
from promo_code_hash import create_promo_digest, verify_promo_code
from vehicle_store import get_vehicle, list_vehicles


def _add_column_if_missing(column_name, ddl):
    columns = {
        row[1]
        for row in db.session.execute(text("PRAGMA table_info(reservations)")).all()
    }
    if column_name in columns:
        return

    try:
        db.session.execute(text(ddl))
        db.session.commit()
    except OperationalError as exc:
        db.session.rollback()
        # The REST process and web process can start almost simultaneously.
        # If the other process added the same column first, the schema is already correct.
        if "duplicate column" not in str(exc).lower():
            raise


def ensure_promo_schema(app):
    """Upgrade an existing SQLite database with reservation promo and vehicle columns."""
    with app.app_context():
        db.create_all()
        _add_column_if_missing(
            "discount_percent",
            "ALTER TABLE reservations ADD COLUMN discount_percent FLOAT NOT NULL DEFAULT 0",
        )
        _add_column_if_missing(
            "promo_code_id",
            "ALTER TABLE reservations ADD COLUMN promo_code_id INTEGER",
        )
        _add_column_if_missing(
            "vehicle_id",
            "ALTER TABLE reservations ADD COLUMN vehicle_id INTEGER",
        )
        _add_column_if_missing(
            "vehicle_name",
            "ALTER TABLE reservations ADD COLUMN vehicle_name VARCHAR(120)",
        )
        _add_column_if_missing(
            "vehicle_registration",
            "ALTER TABLE reservations ADD COLUMN vehicle_registration VARCHAR(40)",
        )


def find_active_promo(code):
    promos = PromoCode.query.filter_by(active=True).order_by(PromoCode.id.asc()).all()
    return verify_promo_code(code, promos)


def install_promo_features(app, admin_required, login_required, current_user, local_text):
    ensure_promo_schema(app)

    @app.route("/admin/promos", methods=["GET", "POST"])
    @admin_required
    def admin_promos():
        if request.method == "POST":
            code = request.form.get("code", "").strip()
            try:
                discount_percent = float(request.form.get("discount_percent", ""))
            except ValueError:
                discount_percent = 0

            if len(code) < 4 or not 1 <= discount_percent <= 100:
                flash(local_text(
                    "Promo kod mora imati najmanje 4 znaka, a popust mora biti između 1 i 100%.",
                    "The promo code must have at least 4 characters and the discount must be between 1 and 100%.",
                ), "danger")
            else:
                existing = PromoCode.query.order_by(PromoCode.id.asc()).all()
                if verify_promo_code(code, existing)["valid"]:
                    flash(local_text(
                        "Promo kod s tom vrijednošću već postoji.",
                        "A promo code with that value already exists.",
                    ), "danger")
                else:
                    promo = PromoCode(code_hash="", discount_percent=discount_percent, active=True)
                    db.session.add(promo)
                    db.session.flush()
                    promo.code_hash = create_promo_digest(promo.id, code)
                    db.session.commit()
                    flash(local_text(
                        "Promo kod je kreiran. Izvorni kod, sol i papar nisu spremljeni; spremljen je samo SHA-256 sažetak.",
                        "Promo code created. The original code, salt and pepper were not stored; only the SHA-256 digest was saved.",
                    ), "success")

        promos = PromoCode.query.order_by(PromoCode.id.desc()).all()
        return render_template("admin_promos.html", promos=promos)

    @app.route("/admin/promos/<int:promo_id>/toggle", methods=["POST"])
    @admin_required
    def admin_promo_toggle(promo_id):
        promo = db.get_or_404(PromoCode, promo_id)
        promo.active = not promo.active
        db.session.commit()
        flash(local_text(
            "Status promo koda je promijenjen.",
            "Promo code status changed.",
        ), "success")
        return redirect(url_for("admin_promos"))

    @app.route("/admin/promos/<int:promo_id>/delete", methods=["POST"])
    @admin_required
    def admin_promo_delete(promo_id):
        promo = db.get_or_404(PromoCode, promo_id)
        if Reservation.query.filter_by(promo_code_id=promo.id).first():
            flash(local_text(
                "Promo kod je već korišten u rezervaciji. Deaktivirajte ga umjesto brisanja.",
                "This promo code has already been used by a reservation. Deactivate it instead of deleting it.",
            ), "warning")
        else:
            db.session.delete(promo)
            db.session.commit()
            flash(local_text("Promo kod je obrisan.", "Promo code deleted."), "info")
        return redirect(url_for("admin_promos"))

    def reserve_with_promo(parking_id):
        parking = db.get_or_404(ParkingSpot, parking_id)
        user = current_user()
        vehicles = list_vehicles(user.id)

        def render_form():
            return render_template(
                "reservation_form.html",
                parking=parking,
                vehicles=vehicles,
            )

        if parking.owner_id == user.id:
            flash(local_text(
                "Ne možete rezervirati vlastiti parking.",
                "You cannot reserve your own parking.",
            ), "warning")
            return redirect(url_for("parking_detail", parking_id=parking.id))

        if request.method == "POST":
            try:
                start_time = datetime.fromisoformat(request.form.get("start_time", ""))
                end_time = datetime.fromisoformat(request.form.get("end_time", ""))
            except ValueError:
                flash(local_text(
                    "Unesite ispravan datum i vrijeme.",
                    "Enter a valid date and time.",
                ), "danger")
                return render_form()

            if end_time <= start_time:
                flash(local_text(
                    "Završetak mora biti nakon početka.",
                    "The end must be after the start.",
                ), "danger")
                return render_form()

            conflict = Reservation.query.filter_by(parking_id=parking.id, status="ACTIVE").filter(
                Reservation.start_time < end_time,
                Reservation.end_time > start_time,
            ).first()
            if conflict:
                flash(local_text(
                    "Parking je već rezerviran u tom terminu.",
                    "The parking spot is already reserved for that time.",
                ), "danger")
                return render_form()

            selected_vehicle = None
            vehicle_text = request.form.get("vehicle_id", "").strip()
            if vehicle_text:
                try:
                    vehicle_id = int(vehicle_text)
                except ValueError:
                    vehicle_id = None
                selected_vehicle = get_vehicle(user.id, vehicle_id) if vehicle_id is not None else None
                if selected_vehicle is None:
                    flash(local_text(
                        "Odabrano vozilo nije pronađeno među vašim vozilima.",
                        "The selected vehicle was not found among your vehicles.",
                    ), "danger")
                    return render_form()

            promo_text = request.form.get("promo_code", "").strip()
            promo = None
            verification = None
            if promo_text:
                verification = find_active_promo(promo_text)
                if not verification["valid"]:
                    flash(local_text(
                        "Promo kod nije valjan ili nije aktivan.",
                        "The promo code is invalid or inactive.",
                    ), "danger")
                    return render_form()
                promo = verification["promo"]

            reservation = Reservation(
                parking_id=parking.id,
                user_id=user.id,
                start_time=start_time,
                end_time=end_time,
                status="ACTIVE",
                discount_percent=promo.discount_percent if promo else 0.0,
                promo_code_id=promo.id if promo else None,
                vehicle_id=selected_vehicle["id"] if selected_vehicle else None,
                vehicle_name=selected_vehicle["name"] if selected_vehicle else None,
                vehicle_registration=selected_vehicle["registration"] if selected_vehicle else None,
            )
            db.session.add(reservation)
            db.session.commit()

            if promo:
                flash(local_text(
                    f"Promo kod je prihvaćen: {promo.discount_percent:.0f}% popusta. Provjereno je svih {verification['attempts_for_match']} mogućih vrijednosti papra.",
                    f"Promo code accepted: {promo.discount_percent:.0f}% discount. All {verification['attempts_for_match']} possible pepper values were checked.",
                ), "success")
            else:
                flash(local_text("Rezervacija je spremljena.", "Reservation saved."), "success")
            return redirect(url_for("my_reservations"))

        return render_form()

    # The base app already owns the /parking/<id>/reserve URL. Replace only its view
    # so the main business flow gains promo and vehicle selection without a second route.
    app.view_functions["reserve"] = login_required(reserve_with_promo)
