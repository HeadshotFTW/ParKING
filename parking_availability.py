from datetime import datetime

from flask import redirect, render_template, request, url_for

from app import DATA_DIR, current_language, current_user, load_settings
from binary_store import add_record
from models import db, ParkingSpot, Reservation
from parallel_tasks import (
    fetch_weather_for_parking,
    fetch_weather_for_parking_locations,
    parking_city_name,
)


BINARY_HISTORY_PATH = DATA_DIR / "search_history.bin"
VALID_SORTS = {"price_asc", "price_desc", "name"}


def _text(hr, en):
    return en if current_language() == "en" else hr


def parkings_with_availability():
    location = request.args.get("location", "").strip()
    sort = request.args.get("sort", "price_asc")
    if sort not in VALID_SORTS:
        sort = "price_asc"

    start_time_raw = request.args.get("start_time", "").strip()
    end_time_raw = request.args.get("end_time", "").strip()
    max_price_raw = request.args.get("max_price", "").strip()

    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1

    availability_start = None
    availability_end = None
    max_price = None
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

    if max_price_raw:
        try:
            max_price = float(max_price_raw)
            if max_price < 0:
                raise ValueError
        except ValueError:
            if availability_error is None:
                availability_error = _text(
                    "Maksimalna cijena mora biti broj jednak ili veći od 0.",
                    "Maximum price must be a number greater than or equal to 0.",
                )
            max_price = None

    valid_search = (
        availability_error is None
        and availability_start is not None
        and availability_end is not None
    )

    # Klik na Pretraži stvara jedan stvarni zapis povijesti. Nakon spremanja
    # preusmjeravamo na isti rezultat bez oznake search=1, pa refresh i
    # paginacija ne stvaraju duplikate u binarnoj datoteci.
    if request.args.get("search") == "1" and valid_search:
        user = current_user()
        if user is not None:
            add_record(
                BINARY_HISTORY_PATH,
                user.id,
                location=location,
                max_price=max_price,
                start_time=start_time_raw,
                end_time=end_time_raw,
                sort=sort,
            )
        return redirect(
            url_for(
                "parkings",
                location=location,
                sort=sort,
                start_time=start_time_raw,
                end_time=end_time_raw,
                max_price=max_price_raw,
            )
        )

    per_page = load_settings()["items_per_page"]
    query = ParkingSpot.query

    if location:
        query = query.filter(ParkingSpot.location.ilike(f"%{location}%"))

    if max_price is not None:
        query = query.filter(ParkingSpot.price_per_hour <= max_price)

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
                max_price=max_price_raw,
                page=total_pages,
            )
        )

    items = query.offset((page - 1) * per_page).limit(per_page).all()

    # Za jedinstvene gradove parkinga grad se automatski geokodira preko
    # Open-Meteo Geocoding API-ja, a vremenski pozivi izvršavaju se paralelno.
    weather_by_city = fetch_weather_for_parking_locations(
        [item.location for item in items]
    )
    parking_weather = {}
    for item in items:
        city_name = parking_city_name(item.location)
        if city_name is None:
            continue
        weather = weather_by_city.get(city_name.casefold())
        if weather and not weather.get("error"):
            parking_weather[item.id] = weather

    return render_template(
        "parkings.html",
        parkings=items,
        parking_weather=parking_weather,
        location=location,
        sort=sort,
        start_time=start_time_raw,
        end_time=end_time_raw,
        max_price=max_price_raw,
        availability_active=valid_search,
        availability_error=availability_error,
        page=page,
        total_pages=total_pages,
        total=total,
    )


def parking_detail_with_weather(parking_id):
    parking = db.get_or_404(ParkingSpot, parking_id)
    try:
        weather = fetch_weather_for_parking(parking.location)
    except Exception:
        # Parking detalji moraju ostati dostupni i ako Open-Meteo privremeno ne radi.
        weather = None
    return render_template("parking_detail.html", parking=parking, weather=weather)


def install_parking_availability(app):
    """Install availability and weather views while preserving existing endpoints."""
    app.view_functions["parkings"] = parkings_with_availability
    app.view_functions["parking_detail"] = parking_detail_with_weather
