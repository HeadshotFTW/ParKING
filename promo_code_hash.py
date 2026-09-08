import hashlib
import hmac
import secrets


PEPPER_MIN = 0
PEPPER_MAX = 255


def normalize_promo_code(code):
    return code.strip().upper()


def derive_variable_salt(promo_id):
    """Derive a per-promo salt by rule; the salt is never stored."""
    source = f"ParKING-promo-salt:{promo_id}".encode("utf-8")
    return hashlib.sha256(source).digest()[:16]


def _promo_digest(code, promo_id, pepper):
    salt = derive_variable_salt(promo_id)
    payload = salt + normalize_promo_code(code).encode("utf-8") + bytes([pepper])
    return hashlib.sha256(payload).hexdigest()


def create_promo_digest(promo_id, code):
    """Create a SHA-256 digest using a generated salt and random one-byte pepper."""
    pepper = secrets.randbelow(PEPPER_MAX - PEPPER_MIN + 1) + PEPPER_MIN
    return _promo_digest(code, promo_id, pepper)


def verify_promo_code(code, promos):
    """Find a matching promo while scanning the full 0-255 pepper range for each candidate."""
    normalized = normalize_promo_code(code)
    if not normalized:
        return {
            "valid": False,
            "promo": None,
            "matched_pepper": None,
            "attempts_for_match": 0,
            "total_attempts": 0,
        }

    total_attempts = 0
    for promo in promos:
        matches = []
        for pepper in range(PEPPER_MIN, PEPPER_MAX + 1):
            total_attempts += 1
            candidate = _promo_digest(normalized, promo.id, pepper)
            if hmac.compare_digest(candidate, promo.code_hash.lower()):
                matches.append(pepper)

        # The complete range has been checked before accepting a match.
        if matches:
            return {
                "valid": True,
                "promo": promo,
                "matched_pepper": matches[0],
                "attempts_for_match": PEPPER_MAX - PEPPER_MIN + 1,
                "total_attempts": total_attempts,
            }

    return {
        "valid": False,
        "promo": None,
        "matched_pepper": None,
        "attempts_for_match": 0,
        "total_attempts": total_attempts,
    }
