import hashlib
import hmac
import json
import secrets
from pathlib import Path


PEPPER_MIN = 0
PEPPER_MAX = 255
STORE_VERSION = 1


def derive_variable_salt(user_id):
    """Derive a per-user salt by rule; the salt itself is never stored."""
    source = f"ParKING-security-code-salt:{user_id}".encode("utf-8")
    return hashlib.sha256(source).digest()[:16]


def _hash_security_code(code, salt, pepper):
    payload = salt + code.encode("utf-8") + bytes([pepper])
    return hashlib.sha256(payload).hexdigest()


def _read_store(path):
    path = Path(path)
    if not path.exists():
        return {"version": STORE_VERSION, "digests": {}}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": STORE_VERSION, "digests": {}}

    digests = data.get("digests") if isinstance(data, dict) else None
    if not isinstance(digests, dict):
        digests = {}
    return {"version": STORE_VERSION, "digests": digests}


def _write_store(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def security_code_is_set(path, user_id):
    data = _read_store(path)
    return str(user_id) in data["digests"]


def set_security_code(path, user_id, code):
    """Store only the salted-and-peppered SHA-256 digest of a security code."""
    salt = derive_variable_salt(user_id)
    pepper = secrets.randbelow(PEPPER_MAX - PEPPER_MIN + 1) + PEPPER_MIN
    digest = _hash_security_code(code, salt, pepper)

    data = _read_store(path)
    data["digests"][str(user_id)] = digest
    _write_store(path, data)

    return {
        "digest": digest,
        "salt_hex": salt.hex(),
        "pepper_range": f"{PEPPER_MIN}-{PEPPER_MAX}",
    }


def verify_security_code(path, user_id, code):
    """Verify a code by checking every possible one-byte pepper value."""
    data = _read_store(path)
    expected_digest = data["digests"].get(str(user_id))
    if not expected_digest:
        return {"valid": False, "attempts": 0, "matches": [], "salt_hex": derive_variable_salt(user_id).hex()}

    salt = derive_variable_salt(user_id)
    matches = []
    attempts = 0

    # Intentionally scan the full range required by the project criterion.
    for pepper in range(PEPPER_MIN, PEPPER_MAX + 1):
        attempts += 1
        candidate = _hash_security_code(code, salt, pepper)
        if hmac.compare_digest(candidate, expected_digest.lower()):
            matches.append(pepper)

    return {
        "valid": bool(matches),
        "attempts": attempts,
        "matches": matches,
        "salt_hex": salt.hex(),
    }
