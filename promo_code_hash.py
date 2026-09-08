import hashlib
import hmac
import os


PROMO_CODE = "POPUST"
PEPPER_MIN = 0
PEPPER_MAX = 255


def _system_pepper():
    """Return the one-byte pepper configured at application/system level."""
    raw = os.environ.get("PROMO_SYSTEM_PEPPER", "173")
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("PROMO_SYSTEM_PEPPER mora biti cijeli broj od 0 do 255.") from exc
    if not PEPPER_MIN <= value <= PEPPER_MAX:
        raise ValueError("PROMO_SYSTEM_PEPPER mora biti u rasponu 0-255.")
    return value


def normalize_promo_code(code):
    return code.strip().upper()


def derive_user_salt(user_id):
    """Derive one stable, unique salt per user by rule; the salt is never stored."""
    source = f"ParKING-user-promo-salt:{int(user_id)}".encode("utf-8")
    return hashlib.sha256(source).digest()[:16]


def user_salt_hex(user_id):
    """Human-readable form used only for demonstration/debugging."""
    return derive_user_salt(user_id).hex()


def _promo_digest(code, user_id, pepper):
    salt = derive_user_salt(user_id)
    payload = salt + normalize_promo_code(code).encode("utf-8") + bytes([pepper])
    return hashlib.sha256(payload).hexdigest()


def create_user_promo_digest(user_id, code=PROMO_CODE):
    """Hash POPUST with the user's derived salt and the system-level pepper."""
    normalized = normalize_promo_code(code)
    if normalized != PROMO_CODE:
        raise ValueError(f"Jedini podržani promo kod je {PROMO_CODE}.")
    return _promo_digest(PROMO_CODE, user_id, _system_pepper())


def verify_user_promo(code, user_id, stored_digest):
    """Verify POPUST for one user while intentionally scanning all 256 pepper values."""
    normalized = normalize_promo_code(code)
    if normalized != PROMO_CODE or not stored_digest:
        return {
            "valid": False,
            "matched_pepper": None,
            "attempts": 0 if not normalized else 256,
        }

    matches = []
    for pepper in range(PEPPER_MIN, PEPPER_MAX + 1):
        candidate = _promo_digest(PROMO_CODE, user_id, pepper)
        if hmac.compare_digest(candidate, stored_digest.lower()):
            matches.append(pepper)

    system_pepper = _system_pepper()
    return {
        "valid": system_pepper in matches,
        "matched_pepper": system_pepper if system_pepper in matches else None,
        "attempts": PEPPER_MAX - PEPPER_MIN + 1,
    }
