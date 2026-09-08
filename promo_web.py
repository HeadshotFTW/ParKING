from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from sqlalchemy import text

from models import db, ParkingSpot, PromoCode, Reservation
from promo_code_hash import create_promo_digest, verify_promo_code


def ensure_promo_schema(app):
    """Upgrade an existing SQLite database with reservation promo columns."""
    with app.app_context():
        db.create_all()
        columns = {
            row[1]
            for row in db.session.execute(text("PRAGMA table_info(reservations)")).all()
        }
        if "discount_percent" not in columns:
            db.session.execute(
                text("ALTER TABLE reservations ADD COLUMN discount_percent FLOAT NOT NULL DEFAULT 0")
            )
        if "promo_code_id" not in columns:
            db.session.execute(
                text("ALTER TABLE reservations ADD COLUMN promo_code_id INTEGER")
            )
        db.session.commit()


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
                return render_template("reservation_form.html", parking=parking)

            if end_time <= start_time:
                flash(local_text(
                    "Završetak mora biti nakon početka.",
                    "The end must be after the start.",
                ), "danger")
                return render_template("reservation_form.html", parking=parking)

            conflict = Reservation.query.filter_by(parking_id=parking.id, status="ACTIVE").filter(
                Reservation.start_time < end_time,
                Reservation.end_time > start_time,
            ).first()
            if conflict:
                flash(local_text(
                    "Parking je već rezerviran u tom terminu.",
                    "The parking spot is already reserved for that time.",
                ), "danger")
                return render_template("reservation_form.html", parking=parking)

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
                    return render_template("reservation_form.html", parking=parking)
                promo = verification["promo"]

            reservation = Reservation(
                parking_id=parking.id,
                user_id=user.id,
                start_time=start_time,
                end_time=end_time,
                status="ACTIVE",
                discount_percent=promo.discount_percent if promo else 0.0,
                promo_code_id=promo.id if promo else None,
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

        return render_template("reservation_form.html", parking=parking)

    # The base app already owns the /parking/<id>/reserve URL. Replace only its view
    # so the main business flow gains promo verification without creating a second route.
    app.view_functions["reserve"] = login_required(reserve_with_promo)
