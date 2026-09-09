from datetime import datetime

from flask import redirect, render_template, request, url_for

from app import DATA_DIR, current_language, current_user, load_settings
from binary_store import add_record
from models import db, ParkingSpot, Reservation
from parallel_tasks import fetch_weather_for_parking, fetch_weather_for_parking_locations, parking_city_name


BINARY_HISTORY_PATH = DATA_DIR / "search_history.bin"
VALID_SORTS = {"price_asc", "price_desc", "name"}


def _text(hr, en):
    return en if current_language() == "en" else hr


def _parse_interval(start_raw, end_raw):
    if not start_raw and not end_raw:
        return None, None, None
    if not start_raw or not end_raw:
        return None, None, _text(
            "Za provjeru dostupnosti unesite početak i završetak termina.",
            "Enter both the start and end time to check availability.",
        )
    try:
        start = datetime.fromisoformat(start_raw)
        end = datetime.fromisoformat(end_raw)
    except ValueError:
        return None, None, _text(
            "Unesite ispravan početak i završetak termina.",
            "Enter a valid start and end time.",
        )
    if end <= start:
        return None, None, _text(
            "Završetak termina mora biti nakon početka.",
            "The end time must be after the start time.",
        )
    return start, end, None


def _parse_max_price(raw):
    if not raw:
        return None, None
    try:
        value = float(raw)
        if value < 0:
            raise ValueError
        return value, None
    except ValueError:
        return None, _text(
            "Maksimalna cijena mora biti broj jednak ili veći od 0.",
            "Maximum price must be a number greater than or equal to 0.",
        )


def _search_url(location, sort, start_raw, end_raw, max_price_raw, **extra):
    return url_for(
        "parkings",
        location=location,
        sort=sort,
        start_time=start_raw,
        end_time=end_raw,
        max_price=max_price_raw,
        **extra,
    )


def parkings_with_availability():
    location = request.args.get("location", "").strip()
    sort = request.args.get("sort", "price_asc")
    sort = sort if sort in VALID_SORTS else "price_asc"
    start_raw = request.args.get("start_time", "").strip()
    end_raw = request.args.get("end_time", "").strip()
    max_price_raw = request.args.get("max_price", "").strip()
    page = request.args.get("page", default=1, type=int) or 1
    page = max(1, page)

    start, end, interval_error = _parse_interval(start_raw, end_raw)
    max_price, price_error = _parse_max_price(max_price_raw)
    error = interval_error or price_error
    valid_search = error is None and start is not None and end is not None

    # Samo klik na Pretraži zapisuje povijest; redirect sprječava duplikat na refreshu.
    if request.args.get("search") == "1" and valid_search:
        user = current_user()
        if user:
            add_record(
                BINARY_HISTORY_PATH,
                user.id,
                location=location,
                max_price=max_price,
                start_time=start_raw,
                end_time=end_raw,
                sort=sort,
            )
        return redirect(_search_url(location, sort, start_raw, end_raw, max_price_raw))

    query = ParkingSpot.query
    if location:
        query = query.filter(ParkingSpot.location.ilike(f"%{location}%"))
    if max_price is not None:
        query = query.filter(ParkingSpot.price_per_hour <= max_price)
    if start is not None and end is not None:
        conflict = db.session.query(Reservation.id).filter(
            Reservation.parking_id == ParkingSpot.id,
            Reservation.status == "ACTIVE",
            Reservation.start_time < end,
            Reservation.end_time > start,
        ).exists()
        query = query.filter(~conflict)

    order = {
        "price_asc": ParkingSpot.price_per_hour.asc(),
        "price_desc": ParkingSpot.price_per_hour.desc(),
        "name": ParkingSpot.name.asc(),
    }[sort]
    query = query.order_by(order)

    per_page = load_settings()["items_per_page"]
    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    if page > total_pages and total:
        return redirect(
            _search_url(location, sort, start_raw, end_raw, max_price_raw, page=total_pages)
        )

    items = query.offset((page - 1) * per_page).limit(per_page).all()
    weather_by_city = fetch_weather_for_parking_locations([item.location for item in items])
    parking_weather = {}
    for item in items:
        city = parking_city_name(item.location)
        weather = weather_by_city.get(city.casefold()) if city else None
        if weather and not weather.get("error"):
            parking_weather[item.id] = weather

    return render_template(
        "parkings.html",
        parkings=items,
        parking_weather=parking_weather,
        location=location,
        sort=sort,
        start_time=start_raw,
        end_time=end_raw,
        max_price=max_price_raw,
        availability_active=valid_search,
        availability_error=error,
        page=page,
        total_pages=total_pages,
        total=total,
    )


def parking_detail_with_weather(parking_id):
    parking = db.get_or_404(ParkingSpot, parking_id)
    try:
        weather = fetch_weather_for_parking(parking.location)
    except Exception:
        weather = None
    return render_template("parking_detail.html", parking=parking, weather=weather)


def install_parking_availability(app):
    app.view_functions["parkings"] = parkings_with_availability
    app.view_functions["parking_detail"] = parking_detail_with_weather
