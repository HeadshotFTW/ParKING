from flask import abort, flash, redirect, render_template, send_file, url_for
from sqlalchemy import event

from avatar_fetch import avatar_path, ensure_avatar, fetch_avatar, wget_available
from models import db, User


def _download_avatar_after_insert(_mapper, _connection, user):
    """Best-effort avatar assignment after a new User receives its database ID."""
    ensure_avatar(user.id)


def install_avatar_features(app, login_required, current_user, local_text):
    # Registration and Admin -> Add user both insert the same User model, so one
    # model event covers both creation paths without adding a second container/process.
    if not event.contains(User, "after_insert", _download_avatar_after_insert):
        event.listen(User, "after_insert", _download_avatar_after_insert)

    @app.route("/profile")
    @login_required
    def profile():
        user = current_user()
        avatar_exists = ensure_avatar(user.id)
        return render_template(
            "profile.html",
            user=user,
            avatar_exists=avatar_exists,
            wget_available=wget_available(),
        )

    @app.route("/profile/avatar/refresh", methods=["POST"])
    @login_required
    def refresh_avatar():
        if fetch_avatar(current_user().id):
            flash(local_text(
                "Novi avatar je preuzet s Pravatara pomoću wget aplikacije.",
                "A new avatar was downloaded from Pravatar using the wget application.",
            ), "success")
        else:
            flash(local_text(
                "Avatar nije moguće preuzeti. Provjerite mrežu i dostupnost wget aplikacije.",
                "The avatar could not be downloaded. Check the network and wget availability.",
            ), "danger")
        return redirect(url_for("profile"))

    @app.route("/avatar/<int:user_id>.jpg")
    @login_required
    def user_avatar(user_id):
        user = db.session.get(User, user_id)
        if user is None:
            abort(404)

        viewer = current_user()
        if viewer.id != user.id and not viewer.is_admin():
            abort(403)

        if not ensure_avatar(user.id):
            abort(404)

        response = send_file(avatar_path(user.id), mimetype="image/jpeg")
        response.cache_control.no_store = True
        response.cache_control.max_age = 0
        return response
