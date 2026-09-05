import configparser
import os
from pathlib import Path
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort
)

from models import db, User, ParkingSpot, Reservation
from json_store import add_note, delete_note, get_note, list_notes, update_note
from translations import TRANSLATIONS


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "parking.db"
CONFIG_PATH = BASE_DIR / "config.ini"

DEFAULT_SETTINGS = {
    "default_language": "hr",
    "items_per_page": "10",
}


def load_settings():
    parser = configparser.ConfigParser()
    parser["app"] = DEFAULT_SETTINGS.copy()
    if CONFIG_PATH.exists():
        parser.read(CONFIG_PATH, encoding="utf-8")

    language = parser.get("app", "default_language", fallback="hr").lower()
    if language not in {"hr", "en"}:
        language = "hr"

    try:
        items_per_page = int(parser.get("app", "items_per_page", fallback="10"))
    except ValueError:
        items_per_page = 10

    items_per_page = max(1, min(items_per_page, 50))
    return {
        "default_language": language,
        "items_per_page": items_per_page,
    }


def save_settings(default_language, items_per_page):
    parser = configparser.ConfigParser()
    parser["app"] = {
        "default_language": default_language,
        "items_per_page": str(items_per_page),
    }
    with CONFIG_PATH.open("w", encoding="utf-8") as handle:
        parser.write(handle)


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


def current_language():
    settings = load_settings()
    language = session.get("lang", settings["default_language"])
    return language if language in {"hr", "en"} else "hr"


def tr(key):
    language = current_language()
    return TRANSLATIONS.get(language, {}).get(
        key,
        TRANSLATIONS["hr"].get(key, key),
    )


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            flash(tr("flash.login_required"), "warning")
            return redirect(url_for("login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            flash(tr("flash.login_required"), "warning")
            return redirect(url_for("login", next=request.path))
        if not user.is_admin():
            abort(403)
        return view_func(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    return {
        "current_user": current_user(),
        "tr": tr,
        "lang": current_language(),
        "settings": load_settings(),
    }


@app.route("/")
def index():
    return redirect(url_for("parkings"))


@app.route("/language/<language>")
def set_language(language):
    if language in {"hr", "en"}:
        session["lang"] = language
    return redirect(request.referrer or url_for("parkings"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("parkings"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3:
            flash(tr("flash.username_short"), "danger")
            return render_template("register.html")
        if len(password) < 4:
            flash(tr("flash.password_short"), "danger")
            return render_template("register.html")
        if User.query.filter_by(username=username).first():
            flash(tr("flash.username_exists"), "danger")
            return render_template("register.html")

        user = User(username=username, role="USER")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        flash(tr("flash.register_ok"), "success")
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
            flash(tr("flash.login_bad"), "danger")
            return render_template("login.html")

        session["user_id"] = user.id
        flash(tr("flash.login_ok"), "success")
        return redirect(url_for("parkings"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    language = current_language()
    session.clear()
    session["lang"] = language
    flash(tr("flash.logout_ok"), "info")
    return redirect(url_for("login"))


@app.route("/parkings")
def parkings():
    location = request.args.get("location", "").strip()
    sort = request.args.get("sort", "price_asc")
    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1

    settings = load_settings()
    per_page = settings["items_per_page"]
    query = ParkingSpot.query

    if location:
        query = query.filter(ParkingSpot.location.ilike(f"%{location}%"))

    if sort == "price_desc":
        query = query.order_by(ParkingSpot.price_per_hour.desc())
    elif sort == "name":
        query = query.order_by(ParkingSpot.name.asc())
    else:
        query = query.order_by(ParkingSpot.price_per_hour.asc())

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    if page > total_pages and total > 0:
        return redirect(url_for(
            "parkings", location=location, sort=sort, page=total_pages
        ))

    return render_template(
        "parkings.html",
        parkings=items,
        location=location,
        sort=sort,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@app.route("/parking/<int:parking_id>")
def parking_detail(parking_id):
    parking = db.get_or_404(ParkingSpot, parking_id)
    return render_template("parking_detail.html", parking=parking)


@app.route("/my-parkings")
@login_required
def my_parkings():
    user = current_user()
    items = ParkingSpot.query.filter_by(
        owner_id=user.id
    ).order_by(ParkingSpot.id.desc()).all()
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
            flash(tr("flash.parking_invalid"), "danger")
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
        flash(tr("flash.parking_added"), "success")
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
            flash(tr("flash.parking_invalid"), "danger")
            return render_template("parking_form.html", parking=parking)

        parking.name = name
        parking.location = location
        parking.price_per_hour = price
        parking.description = description
        db.session.commit()
        flash(tr("flash.parking_updated"), "success")
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
    flash(tr("flash.parking_deleted"), "info")
    return redirect(url_for("my_parkings"))


@app.route("/parking/<int:parking_id>/reserve", methods=["GET", "POST"])
@login_required
def reserve(parking_id):
    parking = db.get_or_404(ParkingSpot, parking_id)
    user = current_user()

    if parking.owner_id == user.id:
        flash(tr("flash.reserve_own"), "warning")
        return redirect(url_for("parking_detail", parking_id=parking.id))

    if request.method == "POST":
        start_raw = request.form.get("start_time", "")
        end_raw = request.form.get("end_time", "")

        try:
            start_time = datetime.fromisoformat(start_raw)
            end_time = datetime.fromisoformat(end_raw)
        except ValueError:
            flash(tr("flash.datetime_invalid"), "danger")
            return render_template("reservation_form.html", parking=parking)

        if end_time <= start_time:
            flash(tr("flash.end_after_start"), "danger")
            return render_template("reservation_form.html", parking=parking)

        conflict = Reservation.query.filter_by(
            parking_id=parking.id,
            status="ACTIVE",
        ).filter(
            Reservation.start_time < end_time,
            Reservation.end_time > start_time,
        ).first()

        if conflict:
            flash(tr("flash.reservation_conflict"), "danger")
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
        flash(tr("flash.reservation_saved"), "success")
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
    flash(tr("flash.reservation_cancelled"), "info")
    return redirect(url_for("my_reservations"))


# --- JSON CRUD: korisničke bilješke ---

@app.route("/notes")
@login_required
def notes():
    return render_template("notes.html", notes=list_notes(current_user().id))


@app.route("/notes/new", methods=["GET", "POST"])
@login_required
def note_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        text = request.form.get("text", "").strip()
        if not title:
            flash(tr("flash.note_title_required"), "danger")
            return render_template("note_form.html", note=None)
        add_note(current_user().id, title, text)
        flash(tr("flash.note_added"), "success")
        return redirect(url_for("notes"))
    return render_template("note_form.html", note=None)


@app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
@login_required
def note_edit(note_id):
    note = get_note(current_user().id, note_id)
    if not note:
        abort(404)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        text = request.form.get("text", "").strip()
        if not title:
            flash(tr("flash.note_title_required"), "danger")
            return render_template("note_form.html", note=note)
        update_note(current_user().id, note_id, title, text)
        flash(tr("flash.note_updated"), "success")
        return redirect(url_for("notes"))

    return render_template("note_form.html", note=note)


@app.route("/notes/<int:note_id>/delete", methods=["POST"])
@login_required
def note_delete(note_id):
    if not delete_note(current_user().id, note_id):
        abort(404)
    flash(tr("flash.note_deleted"), "info")
    return redirect(url_for("notes"))


# --- Administracija: CRUD nad tablicom users ---

@app.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.username.asc()).all()
    return render_template("admin_users.html", users=users)


@app.route("/admin/users/new", methods=["GET", "POST"])
@admin_required
def admin_user_new():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "USER").upper()

        if len(username) < 3 or len(password) < 4:
            flash("Korisničko ime mora imati barem 3, a lozinka barem 4 znaka.", "danger")
            return render_template("admin_user_form.html", user=None)
        if role not in {"USER", "ADMIN"}:
            role = "USER"
        if User.query.filter_by(username=username).first():
            flash("Korisničko ime već postoji.", "danger")
            return render_template("admin_user_form.html", user=None)

        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Korisnik je dodan.", "success")
        return redirect(url_for("admin_users"))

    return render_template("admin_user_form.html", user=None)


@app.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_user_edit(user_id):
    user = db.get_or_404(User, user_id)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "USER").upper()

        duplicate = User.query.filter(User.username == username, User.id != user.id).first()
        if len(username) < 3 or duplicate:
            flash("Korisničko ime nije ispravno ili već postoji.", "danger")
            return render_template("admin_user_form.html", user=user)
        if role not in {"USER", "ADMIN"}:
            role = "USER"

        user.username = username
        user.role = role
        if password:
            if len(password) < 4:
                flash("Nova lozinka mora imati barem 4 znaka.", "danger")
                return render_template("admin_user_form.html", user=user)
            user.set_password(password)

        db.session.commit()
        flash("Korisnik je ažuriran.", "success")
        return redirect(url_for("admin_users"))

    return render_template("admin_user_form.html", user=user)


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_user_delete(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user().id:
        flash("Ne možete obrisati trenutno prijavljenog administratora.", "warning")
        return redirect(url_for("admin_users"))

    db.session.delete(user)
    db.session.commit()
    flash("Korisnik je obrisan.", "info")
    return redirect(url_for("admin_users"))


# --- Administracija: CRUD nad tablicom reservations ---

@app.route("/admin/reservations")
@admin_required
def admin_reservations():
    reservations = Reservation.query.order_by(Reservation.start_time.desc()).all()
    return render_template("admin_reservations.html", reservations=reservations)


@app.route("/admin/reservations/new", methods=["GET", "POST"])
@admin_required
def admin_reservation_new():
    users = User.query.order_by(User.username.asc()).all()
    parkings = ParkingSpot.query.order_by(ParkingSpot.name.asc()).all()

    if request.method == "POST":
        try:
            user_id = int(request.form.get("user_id", ""))
            parking_id = int(request.form.get("parking_id", ""))
            start_time = datetime.fromisoformat(request.form.get("start_time", ""))
            end_time = datetime.fromisoformat(request.form.get("end_time", ""))
        except (ValueError, TypeError):
            flash("Unesite ispravne podatke rezervacije.", "danger")
            return render_template(
                "admin_reservation_form.html",
                reservation=None, users=users, parkings=parkings
            )

        status = request.form.get("status", "ACTIVE").upper()
        if status not in {"ACTIVE", "CANCELLED"}:
            status = "ACTIVE"
        if end_time <= start_time:
            flash("Završetak mora biti nakon početka.", "danger")
            return render_template(
                "admin_reservation_form.html",
                reservation=None, users=users, parkings=parkings
            )

        reservation = Reservation(
            user_id=user_id,
            parking_id=parking_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )
        db.session.add(reservation)
        db.session.commit()
        flash("Rezervacija je dodana.", "success")
        return redirect(url_for("admin_reservations"))

    return render_template(
        "admin_reservation_form.html",
        reservation=None, users=users, parkings=parkings
    )


@app.route("/admin/reservations/<int:reservation_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_reservation_edit(reservation_id):
    reservation = db.get_or_404(Reservation, reservation_id)
    users = User.query.order_by(User.username.asc()).all()
    parkings = ParkingSpot.query.order_by(ParkingSpot.name.asc()).all()

    if request.method == "POST":
        try:
            user_id = int(request.form.get("user_id", ""))
            parking_id = int(request.form.get("parking_id", ""))
            start_time = datetime.fromisoformat(request.form.get("start_time", ""))
            end_time = datetime.fromisoformat(request.form.get("end_time", ""))
        except (ValueError, TypeError):
            flash("Unesite ispravne podatke rezervacije.", "danger")
            return render_template(
                "admin_reservation_form.html",
                reservation=reservation, users=users, parkings=parkings
            )

        status = request.form.get("status", "ACTIVE").upper()
        if status not in {"ACTIVE", "CANCELLED"}:
            status = "ACTIVE"
        if end_time <= start_time:
            flash("Završetak mora biti nakon početka.", "danger")
            return render_template(
                "admin_reservation_form.html",
                reservation=reservation, users=users, parkings=parkings
            )

        reservation.user_id = user_id
        reservation.parking_id = parking_id
        reservation.start_time = start_time
        reservation.end_time = end_time
        reservation.status = status
        db.session.commit()
        flash("Rezervacija je ažurirana.", "success")
        return redirect(url_for("admin_reservations"))

    return render_template(
        "admin_reservation_form.html",
        reservation=reservation, users=users, parkings=parkings
    )


@app.route("/admin/reservations/<int:reservation_id>/delete", methods=["POST"])
@admin_required
def admin_reservation_delete(reservation_id):
    reservation = db.get_or_404(Reservation, reservation_id)
    db.session.delete(reservation)
    db.session.commit()
    flash("Rezervacija je obrisana.", "info")
    return redirect(url_for("admin_reservations"))


# --- INI postavke ---

@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    settings = load_settings()

    if request.method == "POST":
        language = request.form.get("default_language", "hr").lower()
        if language not in {"hr", "en"}:
            language = "hr"

        try:
            items_per_page = int(request.form.get("items_per_page", "10"))
        except ValueError:
            items_per_page = 10
        items_per_page = max(1, min(items_per_page, 50))

        save_settings(language, items_per_page)
        flash(tr("flash.settings_saved"), "success")
        return redirect(url_for("admin_settings"))

    return render_template("admin_settings.html", app_settings=settings)


@app.errorhandler(403)
def forbidden(_error):
    return render_template("403.html"), 403


def create_database():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        db.create_all()


create_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
