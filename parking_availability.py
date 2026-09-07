from datetime import datetime

from flask import redirect, render_template, request, url_for

from app import current_language, load_settings
from models import db, ParkingSpot, Reservation


def _text(hr, en):
    return en if current_language() == "en" else hr


def parkings_with_availability():
    location = request.args.get("location", "").strip()
    sort = request.args.get("sort", "price_asc")
    start_time_raw = request.args.get("start_time", "").strip()
    end_time_raw = request.args.get("end_time", "").strip()

    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1

    availability_start = None
    availability_end = None
    availability_error = None

    if start_time_raw or end_time_raw:
        if not start_time_raw or not end_time_raw:
            availability_error = _text(
                "Za provjeru dostupnosti unesite početak i završetak termina.",
                "Enter both the start and end time to check availability.",
            )
        else:
            try:
                availability_start = datetime.fromisoformat(start_time_raw)
                availability_end = datetime.fromisoformat(end_time_raw)
            except ValueError:
                availability_error = _text(
                    "Unesite ispravan početak i završetak termina.",
                    "Enter a valid start and end time.",
                )
            else:
                if availability_end <= availability_start:
                    availability_error = _text(
                        "Završetak termina mora biti nakon početka.",
                        "The end time must be after the start time.",
                    )
                    availability_start = None
                    availability_end = None

    per_page = load_settings()["items_per_page"]
    query = ParkingSpot.query

    if location:
        query = query.filter(ParkingSpot.location.ilike(f"%{location}%"))

    if availability_start is not None and availability_end is not None:
        conflicting_reservation = db.session.query(Reservation.id).filter(
            Reservation.parking_id == ParkingSpot.id,
            Reservation.status == "ACTIVE",
            Reservation.start_time < availability_end,
            Reservation.end_time > availability_start,
        ).exists()
        query = query.filter(~conflicting_reservation)

    if sort == "price_desc":
        query = query.order_by(ParkingSpot.price_per_hour.desc())
    elif sort == "name":
        query = query.order_by(ParkingSpot.name.asc())
    else:
        query = query.order_by(ParkingSpot.price_per_hour.asc())

    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)

    if page > total_pages and total:
        return redirect(
            url_for(
                "parkings",
                location=location,
                sort=sort,
                start_time=start_time_raw,
                end_time=end_time_raw,
                page=total_pages,
            )
        )

    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return render_template(
        "parkings.html",
        parkings=items,
        location=location,
        sort=sort,
        start_time=start_time_raw,
        end_time=end_time_raw,
        availability_active=availability_start is not None and availability_end is not None,
        availability_error=availability_error,
        page=page,
        total_pages=total_pages,
        total=total,
    )


def install_parking_availability(app):
    """Replace the existing /parkings endpoint view while keeping its URL and endpoint name."""
    app.view_functions["parkings"] = parkings_with_availability
