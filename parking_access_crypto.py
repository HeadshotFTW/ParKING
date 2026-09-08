import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


MAGIC = b"PKAI"
VERSION = 1
NONCE_SIZE = 12


def _derive_key(secret_key, parking_id):
    material = f"{secret_key}:parking-access:{parking_id}".encode("utf-8")
    return hashlib.sha256(material).digest()


def encrypt_access_instructions(text, secret_key, parking_id):
    """Encrypt private parking access instructions for database storage."""
    if not text:
        return None

    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(secret_key, parking_id)
    ciphertext = AESGCM(key).encrypt(nonce, text.encode("utf-8"), None)
    return MAGIC + bytes([VERSION]) + nonce + ciphertext


def decrypt_access_instructions(payload, secret_key, parking_id):
    """Decrypt and authenticate private parking access instructions."""
    if not payload:
        return ""
    if len(payload) < len(MAGIC) + 1 + NONCE_SIZE:
        raise ValueError("Šifrirane pristupne upute su prekratke.")
    if payload[:4] != MAGIC:
        raise ValueError("Pristupne upute nemaju očekivano PKAI zaglavlje.")
    if payload[4] != VERSION:
        raise ValueError("Nepodržana verzija šifriranih pristupnih uputa.")

    nonce = payload[5:5 + NONCE_SIZE]
    ciphertext = payload[5 + NONCE_SIZE:]
    key = _derive_key(secret_key, parking_id)
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
