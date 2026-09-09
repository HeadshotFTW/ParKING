import hashlib
import hmac
import os


PROMO_CODE = "POPUST"
PEPPER_MIN = 1
PEPPER_MAX = 5


def _system_pepper():
    try:
        pepper = int(os.environ.get("PROMO_SYSTEM_PEPPER", "3"))
    except ValueError as exc:
        raise ValueError("PROMO_SYSTEM_PEPPER mora biti cijeli broj od 1 do 5.") from exc
    if pepper not in range(PEPPER_MIN, PEPPER_MAX + 1):
        raise ValueError("PROMO_SYSTEM_PEPPER mora biti u rasponu 1-5.")
    return pepper


def normalize_promo_code(code):
    return (code or "").strip().upper()


def derive_user_salt(user_id):
    """Sol se izvodi iz user_id-a i zato se ne sprema u bazu."""
    text = f"ParKING-user-promo-salt:{int(user_id)}".encode()
    return hashlib.sha256(text).digest()[:16]


def user_salt_hex(user_id):
    return derive_user_salt(user_id).hex()


def _promo_digest(code, user_id, pepper):
    data = derive_user_salt(user_id) + normalize_promo_code(code).encode() + bytes([pepper])
    return hashlib.sha256(data).hexdigest()


def create_user_promo_digest(user_id, code=PROMO_CODE):
    if normalize_promo_code(code) != PROMO_CODE:
        raise ValueError(f"Jedini podržani promo kod je {PROMO_CODE}.")
    return _promo_digest(PROMO_CODE, user_id, _system_pepper())


def _verification(valid=False, matched=None, guessed=None, attempts=0, reason="code"):
    return {
        "valid": valid,
        "matched_pepper": matched,
        "guessed_pepper": guessed,
        "attempts": attempts,
        "reason": reason,
    }


def verify_user_promo(code, user_id, stored_digest, guessed_pepper=None):
    """Provjeri svih 5 vrijednosti papra i prihvati samo točan korisnikov odabir."""
    try:
        guessed = int(guessed_pepper)
    except (TypeError, ValueError):
        guessed = None

    if normalize_promo_code(code) != PROMO_CODE or not stored_digest:
        return _verification(guessed=guessed)
    if guessed not in range(PEPPER_MIN, PEPPER_MAX + 1):
        return _verification(guessed=guessed, reason="pepper_required")

    matched = None
    for pepper in range(PEPPER_MIN, PEPPER_MAX + 1):
        candidate = _promo_digest(PROMO_CODE, user_id, pepper)
        if hmac.compare_digest(candidate, stored_digest.lower()):
            matched = pepper

    valid = matched == _system_pepper() and guessed == matched
    return _verification(
        valid=valid,
        matched=matched,
        guessed=guessed,
        attempts=PEPPER_MAX - PEPPER_MIN + 1,
        reason="ok" if valid else "wrong_pepper",
    )
