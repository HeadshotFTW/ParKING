from datetime import datetime

from flask import flash, redirect, render_template, request, url_for

from models import db, ParkingSpot, PromoCode, Reservation, User
from promo_code_hash import PEPPER_MAX, PEPPER_MIN, PROMO_CODE, create_user_promo_digest, verify_user_promo
from schema_utils import add_column_if_missing
from vehicle_store import get_vehicle, list_vehicles


PROMO_SCHEMA_UPDATES = [
    ("promo_codes", "user_id", "ALTER TABLE promo_codes ADD COLUMN user_id INTEGER"),
    ("reservations", "discount_percent", "ALTER TABLE reservations ADD COLUMN discount_percent FLOAT NOT NULL DEFAULT 0"),
    ("reservations", "promo_code_id", "ALTER TABLE reservations ADD COLUMN promo_code_id INTEGER"),
    ("reservations", "vehicle_id", "ALTER TABLE reservations ADD COLUMN vehicle_id INTEGER"),
    ("reservations", "vehicle_name", "ALTER TABLE reservations ADD COLUMN vehicle_name VARCHAR(120)"),
    ("reservations", "vehicle_registration", "ALTER TABLE reservations ADD COLUMN vehicle_registration VARCHAR(40)"),
]


def ensure_promo_schema(app):
    with app.app_context():
        db.create_all()
        for table, column, ddl in PROMO_SCHEMA_UPDATES:
            add_column_if_missing(table, column, ddl)


def verify_assigned_discount(code, user_id, guessed_pepper):
    assignment = PromoCode.query.filter_by(user_id=user_id, active=True).order_by(
        PromoCode.id.desc()
    ).first()
    if assignment is None:
        return {
            "valid": False,
            "assignment": None,
            "matched_pepper": None,
            "guessed_pepper": guessed_pepper,
            "attempts": 0,
            "reason": "no_assignment",
        }

    result = verify_user_promo(code, user_id, assignment.code_hash, guessed_pepper)
    result["assignment"] = assignment if result["valid"] else None
    return result


def install_promo_features(app, admin_required, login_required, current_user, local_text):
    ensure_promo_schema(app)

    def say(hr, en, category):
        flash(local_text(hr, en), category)

    @app.route("/admin/promos", methods=["GET", "POST"])
    @admin_required
    def admin_promos():
        users = User.query.order_by(User.username.asc()).all()

        if request.method == "POST":
            selected = {
                int(value)
                for value in request.form.getlist("selected_users")
                if value.isdigit()
            }
            percentages = {}
            invalid = False

            for user in users:
                if user.id not in selected:
                    continue
                try:
                    percent = float(request.form.get(f"discount_{user.id}", ""))
                except ValueError:
                    percent = 0
                percentages[user.id] = percent
                if not 1 <= percent <= 100:
                    invalid = True
                    say(
                        f"Popust za korisnika {user.username} mora biti između 1 i 100%.",
                        f"Discount for user {user.username} must be between 1 and 100%.",
                        "danger",
                    )

            if not invalid:
                for user in users:
                    assignments = PromoCode.query.filter_by(user_id=user.id).order_by(
                        PromoCode.id.desc()
                    ).all()
                    assignment = assignments[0] if assignments else None
                    for old in assignments[1:]:
                        old.active = False

                    if user.id in selected:
                        if assignment is None:
                            assignment = PromoCode(user_id=user.id, code_hash="")
                            db.session.add(assignment)
                        assignment.code_hash = create_user_promo_digest(user.id)
                        assignment.discount_percent = percentages[user.id]
                        assignment.active = True
                    elif assignment:
                        assignment.active = False

                db.session.commit()
                say(
                    "Popusti za promo kod POPUST su primijenjeni.",
                    "Discounts for promo code POPUST were applied.",
                    "success",
                )
                return redirect(url_for("admin_promos"))

        assignments = {}
        for assignment in PromoCode.query.filter(PromoCode.user_id.isnot(None)).order_by(
            PromoCode.id.desc()
        ).all():
            assignments.setdefault(assignment.user_id, assignment)

        return render_template(
            "admin_promos.html",
            users=users,
            assignments=assignments,
            promo_code=PROMO_CODE,
        )

    def reserve_with_promo(parking_id):
        parking = db.get_or_404(ParkingSpot, parking_id)
        user = current_user()
        vehicles = list_vehicles(user.id)

        def show_form():
            return render_template(
                "reservation_form.html",
                parking=parking,
                vehicles=vehicles,
                pepper_values=range(PEPPER_MIN, PEPPER_MAX + 1),
            )

        def reject(hr, en, category="danger"):
            say(hr, en, category)
            return show_form()

        if parking.owner_id == user.id:
            say("Ne možete rezervirati vlastiti parking.", "You cannot reserve your own parking.", "warning")
            return redirect(url_for("parking_detail", parking_id=parking.id))

        if request.method != "POST":
            return show_form()

        try:
            start_time = datetime.fromisoformat(request.form.get("start_time", ""))
            end_time = datetime.fromisoformat(request.form.get("end_time", ""))
        except ValueError:
            return reject("Unesite ispravan datum i vrijeme.", "Enter a valid date and time.")

        if end_time <= start_time:
            return reject("Završetak mora biti nakon početka.", "The end must be after the start.")

        conflict = Reservation.query.filter_by(parking_id=parking.id, status="ACTIVE").filter(
            Reservation.start_time < end_time,
            Reservation.end_time > start_time,
        ).first()
        if conflict:
            return reject(
                "Parking je već rezerviran u tom terminu.",
                "The parking spot is already reserved for that time.",
            )

        selected_vehicle = None
        vehicle_text = request.form.get("vehicle_id", "").strip()
        if vehicle_text:
            vehicle_id = request.form.get("vehicle_id", type=int)
            selected_vehicle = get_vehicle(user.id, vehicle_id) if vehicle_id is not None else None
            if selected_vehicle is None:
                return reject(
                    "Odabrano vozilo nije pronađeno među vašim vozilima.",
                    "The selected vehicle was not found among your vehicles.",
                )

        promo_text = request.form.get("promo_code", "").strip()
        assignment = verification = None
        if promo_text:
            guessed_pepper = request.form.get("promo_pepper", type=int)
            if guessed_pepper not in range(PEPPER_MIN, PEPPER_MAX + 1):
                return reject(
                    "DEMONSTRACIJA: za promo kod odaberite papar od 1 do 5.",
                    "DEMONSTRATION: select a pepper value from 1 to 5 for the promo code.",
                    "warning",
                )

            verification = verify_assigned_discount(promo_text, user.id, guessed_pepper)
            if not verification["valid"]:
                if verification["reason"] == "wrong_pepper":
                    return reject(
                        "DEMONSTRACIJA: odabrani papar nije ispravan. Popust nije primijenjen; pokušajte drugu vrijednost od 1 do 5.",
                        "DEMONSTRATION: the selected pepper is incorrect. The discount was not applied; try another value from 1 to 5.",
                    )
                return reject(
                    "Promo kod POPUST nije dodijeljen vašem korisničkom računu ili nije valjan.",
                    "Promo code POPUST is not assigned to your account or is invalid.",
                )
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
            say(
                f"DEMONSTRACIJA: pogođen je ispravan papar. Promo kod POPUST je prihvaćen: {assignment.discount_percent:.0f}% popusta. Provjereno je svih {verification['attempts']} vrijednosti papra.",
                f"DEMONSTRATION: the correct pepper was guessed. Promo code POPUST was accepted: {assignment.discount_percent:.0f}% discount. All {verification['attempts']} pepper values were checked.",
                "success",
            )
        else:
            say("Rezervacija je spremljena.", "Reservation saved.", "success")
        return redirect(url_for("my_reservations"))

    app.view_functions["reserve"] = login_required(reserve_with_promo)
