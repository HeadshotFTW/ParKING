from flask import flash, redirect, render_template, request, url_for

from models import db, PromoCode, Reservation
from promo_code_hash import create_promo_digest, verify_promo_code


def find_active_promo(code):
    promos = PromoCode.query.filter_by(active=True).order_by(PromoCode.id.asc()).all()
    return verify_promo_code(code, promos)


def install_promo_routes(app, admin_required, local_text):
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
