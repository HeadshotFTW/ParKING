import hashlib
import hmac
import os


PROMO_CODE = "POPUST"
PEPPER_MIN = 1
PEPPER_MAX = 5


def _system_pepper():
    """Return the demo pepper configured at application/system level."""
    raw = os.environ.get("PROMO_SYSTEM_PEPPER", "3")
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("PROMO_SYSTEM_PEPPER mora biti cijeli broj od 1 do 5.") from exc
    if not PEPPER_MIN <= value <= PEPPER_MAX:
        raise ValueError("PROMO_SYSTEM_PEPPER mora biti u rasponu 1-5.")
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
    """Hash POPUST with the user's derived salt and the system-level demo pepper."""
    normalized = normalize_promo_code(code)
    if normalized != PROMO_CODE:
        raise ValueError(f"Jedini podržani promo kod je {PROMO_CODE}.")
    return _promo_digest(PROMO_CODE, user_id, _system_pepper())


def verify_user_promo(code, user_id, stored_digest, guessed_pepper=None):
    """Scan the full demo range 1-5 and accept only when the user's guess is correct."""
    normalized = normalize_promo_code(code)
    try:
        guessed = int(guessed_pepper)
    except (TypeError, ValueError):
        guessed = None

    if normalized != PROMO_CODE or not stored_digest:
        return {
            "valid": False,
            "matched_pepper": None,
            "guessed_pepper": guessed,
            "attempts": 0,
            "reason": "code",
        }

    if guessed is None or not PEPPER_MIN <= guessed <= PEPPER_MAX:
        return {
            "valid": False,
            "matched_pepper": None,
            "guessed_pepper": guessed,
            "attempts": 0,
            "reason": "pepper_required",
        }

    matches = []
    for pepper in range(PEPPER_MIN, PEPPER_MAX + 1):
        candidate = _promo_digest(PROMO_CODE, user_id, pepper)
        if hmac.compare_digest(candidate, stored_digest.lower()):
            matches.append(pepper)

    matched_pepper = matches[0] if matches else None
    system_pepper = _system_pepper()
    valid = matched_pepper == system_pepper and guessed == matched_pepper

    return {
        "valid": valid,
        "matched_pepper": matched_pepper,
        "guessed_pepper": guessed,
        "attempts": PEPPER_MAX - PEPPER_MIN + 1,
        "reason": "ok" if valid else "wrong_pepper",
    }
