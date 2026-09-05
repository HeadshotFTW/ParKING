import hashlib
import hmac
import os

PEPPER_MIN = 0
PEPPER_MAX = 255
DEFAULT_PEPPER = 137


def derive_variable_salt(user_id, username):
    """Derive a per-user salt by rule; the salt is never stored separately."""
    source = f"ParKING-SHA256-salt:{user_id}:{username}".encode("utf-8")
    return hashlib.sha256(source).digest()[:16]


def configured_pepper():
    try:
        value = int(os.environ.get("HASH_DEMO_PEPPER", str(DEFAULT_PEPPER)))
    except ValueError:
        value = DEFAULT_PEPPER
    return max(PEPPER_MIN, min(value, PEPPER_MAX))


def sha256_with_salt_and_pepper(text, salt, pepper):
    payload = salt + text.encode("utf-8") + bytes([pepper])
    return hashlib.sha256(payload).hexdigest()


def create_demo_hash(user_id, username, text):
    salt = derive_variable_salt(user_id, username)
    pepper = configured_pepper()
    digest = sha256_with_salt_and_pepper(text, salt, pepper)
    return {
        "algorithm": "SHA-256",
        "salt_hex": salt.hex(),
        "digest": digest,
        "pepper_range": f"{PEPPER_MIN}-{PEPPER_MAX}",
    }


def verify_by_full_pepper_scan(user_id, username, text, expected_digest):
    salt = derive_variable_salt(user_id, username)
    matches = []
    attempts = 0

    # Namjerno prolazimo cijeli dopušteni raspon papra radi demonstracije kriterija.
    for pepper in range(PEPPER_MIN, PEPPER_MAX + 1):
        attempts += 1
        candidate = sha256_with_salt_and_pepper(text, salt, pepper)
        if hmac.compare_digest(candidate, expected_digest):
            matches.append(pepper)

    return {
        "valid": bool(matches),
        "matches": matches,
        "attempts": attempts,
        "salt_hex": salt.hex(),
    }
