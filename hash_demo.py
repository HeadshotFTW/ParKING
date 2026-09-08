import hashlib
import hmac


def reservation_integrity_text(reservation):
    """Create a stable textual representation of the reservation state."""
    return "|".join([
        f"reservation_id={reservation.id}",
        f"user_id={reservation.user_id}",
        f"username={reservation.user.username}",
        f"parking_id={reservation.parking_id}",
        f"parking_name={reservation.parking.name}",
        f"location={reservation.parking.location}",
        f"vehicle_id={reservation.vehicle_id or ''}",
        f"vehicle_name={reservation.vehicle_name or ''}",
        f"vehicle_registration={reservation.vehicle_registration or ''}",
        f"start={reservation.start_time.isoformat(timespec='minutes')}",
        f"end={reservation.end_time.isoformat(timespec='minutes')}",
        f"status={reservation.status}",
        f"price_per_hour={reservation.parking.price_per_hour:.2f}",
        f"promo_code_id={reservation.promo_code_id or ''}",
        f"discount_percent={float(reservation.discount_percent or 0):.2f}",
        f"base_price={reservation.base_price():.2f}",
        f"total_price={reservation.total_price():.2f}",
    ])


def create_integrity_hash(text):
    """Create a plain SHA-256 digest for reservation-integrity verification."""
    return {
        "algorithm": "SHA-256",
        "digest": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def verify_integrity_hash(text, expected_digest):
    """Compare the current reservation digest with a supplied SHA-256 digest."""
    current_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "valid": hmac.compare_digest(current_digest, expected_digest.lower()),
        "current_digest": current_digest,
    }
