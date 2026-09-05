import os
from pathlib import Path
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort
)

from models import db, User, ParkingSpot, Reservation


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "parking.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-later")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            flash("Za ovu radnju morate biti prijavljeni.", "warning")
            return redirect(url_for("login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


@app.route("/")
def index():
    return redirect(url_for("parkings"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("parkings"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3:
            flash("Korisničko ime mora imati najmanje 3 znaka.", "danger")
            return render_template("register.html")
        if len(password) < 4:
            flash("Lozinka mora imati najmanje 4 znaka.", "danger")
            return render_template("register.html")
        if User.query.filter_by(username=username).first():
            flash("Korisničko ime već postoji.", "danger")
            return render_template("register.html")

        user = User(username=username, role="USER")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        flash("Registracija je uspješna.", "success")
        return redirect(url_for("parkings"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("parkings"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Neispravno korisničko ime ili lozinka.", "danger")
            return render_template("login.html")

        session["user_id"] = user.id
        flash("Prijava uspješna.", "success")
        return redirect(url_for("parkings"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Odjavljeni ste.", "info")
    return redirect(url_for("login"))


@app.route("/parkings")
def parkings():
    location = request.args.get("location", "").strip()
    sort = request.args.get("sort", "price_asc")
    query = ParkingSpot.query

    if location:
        query = query.filter(ParkingSpot.location.ilike(f"%{location}%"))

    if sort == "price_desc":
        query = query.order_by(ParkingSpot.price_per_hour.desc())
    elif sort == "name":
        query = query.order_by(ParkingSpot.name.asc())
    else:
        query = query.order_by(ParkingSpot.price_per_hour.asc())

    return render_template(
        "parkings.html",
        parkings=query.all(),
        location=location,
        sort=sort,
    )


@app.route("/parking/<int:parking_id>")
def parking_detail(parking_id):
    parking = db.get_or_404(ParkingSpot, parking_id)
    return render_template("parking_detail.html", parking=parking)


@app.route("/my-parkings")
@login_required
def my_parkings():
    user = current_user()
    items = ParkingSpot.query.filter_by(owner_id=user.id).order_by(ParkingSpot.id.desc()).all()
    return render_template("my_parkings.html", parkings=items)


@app.route("/parking/new", methods=["GET", "POST"])
@login_required
def parking_new():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()
        try:
            price = float(request.form.get("price_per_hour", ""))
        except ValueError:
            price = -1

        if not name or not location or price < 0:
            flash("Unesite naziv, lokaciju i ispravnu cijenu.", "danger")
            return render_template("parking_form.html", parking=None)

        parking = ParkingSpot(
            owner_id=current_user().id,
            name=name,
            location=location,
            price_per_hour=price,
            description=description,
        )
        db.session.add(parking)
        db.session.commit()
        flash("Parking je dodan.", "success")
        return redirect(url_for("my_parkings"))

    return render_template("parking_form.html", parking=None)


@app.route("/parking/<int:parking_id>/edit", methods=["GET", "POST"])
@login_required
def parking_edit(parking_id):
    parking = db.get_or_404(ParkingSpot, parking_id)
    if not parking.is_owned_by(current_user()):
        abort(403)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()
        try:
            price = float(request.form.get("price_per_hour", ""))
        except ValueError:
            price = -1

        if not name or not location or price < 0:
            flash("Unesite naziv, lokaciju i ispravnu cijenu.", "danger")
            return render_template("parking_form.html", parking=parking)

        parking.name = name
        parking.location = location
        parking.price_per_hour = price
        parking.description = description
        db.session.commit()
        flash("Parking je ažuriran.", "success")
        return redirect(url_for("my_parkings"))

    return render_template("parking_form.html", parking=parking)


@app.route("/parking/<int:parking_id>/delete", methods=["POST"])
@login_required
def parking_delete(parking_id):
    parking = db.get_or_404(ParkingSpot, parking_id)
    if not parking.is_owned_by(current_user()):
        abort(403)

    db.session.delete(parking)
    db.session.commit()
    flash("Parking je obrisan.", "info")
    return redirect(url_for("my_parkings"))


@app.route("/parking/<int:parking_id>/reserve", methods=["GET", "POST"])
@login_required
def reserve(parking_id):
    parking = db.get_or_404(ParkingSpot, parking_id)
    user = current_user()

    if parking.owner_id == user.id:
        flash("Ne možete rezervirati vlastiti parking.", "warning")
        return redirect(url_for("parking_detail", parking_id=parking.id))

    if request.method == "POST":
        start_raw = request.form.get("start_time", "")
        end_raw = request.form.get("end_time", "")

        try:
            start_time = datetime.fromisoformat(start_raw)
            end_time = datetime.fromisoformat(end_raw)
        except ValueError:
            flash("Unesite ispravan datum i vrijeme.", "danger")
            return render_template("reservation_form.html", parking=parking)

        if end_time <= start_time:
            flash("Završetak mora biti nakon početka.", "danger")
            return render_template("reservation_form.html", parking=parking)

        conflict = Reservation.query.filter_by(
            parking_id=parking.id,
            status="ACTIVE",
        ).filter(
            Reservation.start_time < end_time,
            Reservation.end_time > start_time,
        ).first()

        if conflict:
            flash("Parking je već rezerviran u tom terminu.", "danger")
            return render_template("reservation_form.html", parking=parking)

        reservation = Reservation(
            parking_id=parking.id,
            user_id=user.id,
            start_time=start_time,
            end_time=end_time,
            status="ACTIVE",
        )
        db.session.add(reservation)
        db.session.commit()
        flash("Rezervacija je spremljena.", "success")
        return redirect(url_for("my_reservations"))

    return render_template("reservation_form.html", parking=parking)


@app.route("/my-reservations")
@login_required
def my_reservations():
    items = Reservation.query.filter_by(
        user_id=current_user().id
    ).order_by(Reservation.start_time.desc()).all()
    return render_template("reservations.html", reservations=items)


@app.route("/reservation/<int:reservation_id>/cancel", methods=["POST"])
@login_required
def cancel_reservation(reservation_id):
    reservation = db.get_or_404(Reservation, reservation_id)
    if reservation.user_id != current_user().id:
        abort(403)

    reservation.status = "CANCELLED"
    db.session.commit()
    flash("Rezervacija je otkazana.", "info")
    return redirect(url_for("my_reservations"))


@app.errorhandler(403)
def forbidden(_error):
    return render_template("403.html"), 403


def create_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        db.create_all()


create_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
