from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from models import db, ParkingSpot, PromoCode, Reservation, User
from promo_code_hash import PROMO_CODE, create_user_promo_digest, verify_user_promo
from vehicle_store import get_vehicle, list_vehicles


def _add_column_if_missing(table_name, column_name, ddl):
    columns = {
        row[1]
        for row in db.session.execute(text(f"PRAGMA table_info({table_name})")).all()
    }
    if column_name in columns:
        return

    try:
        db.session.execute(text(ddl))
        db.session.commit()
    except OperationalError as exc:
        db.session.rollback()
        # The REST process and web process can start almost simultaneously.
        if "duplicate column" not in str(exc).lower():
            raise


def ensure_promo_schema(app):
    """Upgrade an existing SQLite database with user promo and vehicle columns."""
    with app.app_context():
        db.create_all()
        _add_column_if_missing(
            "promo_codes",
            "user_id",
            "ALTER TABLE promo_codes ADD COLUMN user_id INTEGER",
        )
        _add_column_if_missing(
            "reservations",
            "discount_percent",
            "ALTER TABLE reservations ADD COLUMN discount_percent FLOAT NOT NULL DEFAULT 0",
        )
        _add_column_if_missing(
            "reservations",
            "promo_code_id",
            "ALTER TABLE reservations ADD COLUMN promo_code_id INTEGER",
        )
        _add_column_if_missing(
            "reservations",
            "vehicle_id",
            "ALTER TABLE reservations ADD COLUMN vehicle_id INTEGER",
        )
        _add_column_if_missing(
            "reservations",
            "vehicle_name",
            "ALTER TABLE reservations ADD COLUMN vehicle_name VARCHAR(120)",
        )
        _add_column_if_missing(
            "reservations",
            "vehicle_registration",
            "ALTER TABLE reservations ADD COLUMN vehicle_registration VARCHAR(40)",
        )


def _assignment_for_user(user_id):
    return PromoCode.query.filter_by(user_id=user_id).order_by(PromoCode.id.desc()).first()


def verify_assigned_discount(code, user_id):
    assignment = PromoCode.query.filter_by(user_id=user_id, active=True).order_by(
        PromoCode.id.desc()
    ).first()
    if assignment is None:
        return {
            "valid": False,
            "assignment": None,
            "matched_pepper": None,
            "attempts": 0,
        }

    result = verify_user_promo(code, user_id, assignment.code_hash)
    result["assignment"] = assignment if result["valid"] else None
    return result


def install_promo_features(app, admin_required, login_required, current_user, local_text):
    ensure_promo_schema(app)

    @app.route("/admin/promos", methods=["GET", "POST"])
    @admin_required
    def admin_promos():
        users = User.query.order_by(User.username.asc()).all()

        if request.method == "POST":
            selected_ids = {
                int(value)
                for value in request.form.getlist("selected_users")
                if value.isdigit()
            }

            percentages = {}
            validation_error = False
            for user in users:
                if user.id not in selected_ids:
                    continue
                try:
                    percent = float(request.form.get(f"discount_{user.id}", ""))
                except ValueError:
                    percent = 0
                if not 1 <= percent <= 100:
                    validation_error = True
                    flash(local_text(
                        f"Popust za korisnika {user.username} mora biti između 1 i 100%.",
                        f"Discount for user {user.username} must be between 1 and 100%.",
                    ), "danger")
                percentages[user.id] = percent

            if not validation_error:
                for user in users:
                    assignments = PromoCode.query.filter_by(user_id=user.id).order_by(
                        PromoCode.id.desc()
                    ).all()
                    assignment = assignments[0] if assignments else None

                    # If an older database somehow contains duplicates, only the newest
                    # assignment remains active.
                    for duplicate in assignments[1:]:
                        duplicate.active = False

                    if user.id in selected_ids:
                        if assignment is None:
                            assignment = PromoCode(
                                user_id=user.id,
                                code_hash="",
                                discount_percent=percentages[user.id],
                                active=True,
                            )
                            db.session.add(assignment)
                        assignment.code_hash = create_user_promo_digest(user.id, PROMO_CODE)
                        assignment.discount_percent = percentages[user.id]
                        assignment.active = True
                    elif assignment is not None:
                        assignment.active = False

                db.session.commit()
                flash(local_text(
                    "Popusti za promo kod POPUST su primijenjeni.",
                    "Discounts for promo code POPUST were applied.",
                ), "success")
                return redirect(url_for("admin_promos"))

        assignment_map = {}
        for assignment in PromoCode.query.filter(PromoCode.user_id.isnot(None)).order_by(
            PromoCode.id.desc()
        ).all():
            assignment_map.setdefault(assignment.user_id, assignment)

        return render_template(
            "admin_promos.html",
            users=users,
            assignments=assignment_map,
            promo_code=PROMO_CODE,
        )

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
            assignment = None
            verification = None
            if promo_text:
                verification = verify_assigned_discount(promo_text, user.id)
                if not verification["valid"]:
                    flash(local_text(
                        "Promo kod POPUST nije dodijeljen vašem korisničkom računu ili nije valjan.",
                        "Promo code POPUST is not assigned to your account or is invalid.",
                    ), "danger")
                    return render_form()
                assignment = verification["assignment"]

            reservation = Reservation(
                parking_id=parking.id,
                user_id=user.id,
                start_time=start_time,
                end_time=end_time,
                status="ACTIVE",
                discount_percent=assignment.discount_percent if assignment else 0.0,
                promo_code_id=assignment.id if assignment else None,
                vehicle_id=selected_vehicle["id"] if selected_vehicle else None,
                vehicle_name=selected_vehicle["name"] if selected_vehicle else None,
                vehicle_registration=selected_vehicle["registration"] if selected_vehicle else None,
            )
            db.session.add(reservation)
            db.session.commit()

            if assignment:
                flash(local_text(
                    f"Promo kod POPUST je prihvaćen: {assignment.discount_percent:.0f}% popusta. Provjereno je svih {verification['attempts']} vrijednosti papra.",
                    f"Promo code POPUST accepted: {assignment.discount_percent:.0f}% discount. All {verification['attempts']} pepper values were checked.",
                ), "success")
            else:
                flash(local_text("Rezervacija je spremljena.", "Reservation saved."), "success")
            return redirect(url_for("my_reservations"))

        return render_form()

    # The base app already owns the /parking/<id>/reserve URL. Replace only its view
    # so the main business flow gains the user-specific POPUST discount and vehicle selection.
    app.view_functions["reserve"] = login_required(reserve_with_promo)
