import hashlib
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"PKAE"
VERSION = 1
NONCE_SIZE = 12


def _derive_key(secret_key, user_id):
    material = f"{secret_key}:parking-aes:{user_id}".encode("utf-8")
    return hashlib.sha256(material).digest()


def encrypt_notes(notes, secret_key, user_id, output_path):
    payload = json.dumps(notes, ensure_ascii=False, indent=2).encode("utf-8")
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(secret_key, user_id)
    ciphertext = AESGCM(key).encrypt(nonce, payload, None)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(MAGIC + bytes([VERSION]) + nonce + ciphertext)
    return output_path


def decrypt_notes(secret_key, user_id, input_path):
    raw = Path(input_path).read_bytes()
    if len(raw) < len(MAGIC) + 1 + NONCE_SIZE:
        raise ValueError("Šifrirana datoteka je prekratka.")
    if raw[:4] != MAGIC:
        raise ValueError("Datoteka nema očekivano PKAE zaglavlje.")
    if raw[4] != VERSION:
        raise ValueError("Nepodržana verzija šifriranog formata.")

    nonce = raw[5:5 + NONCE_SIZE]
    ciphertext = raw[5 + NONCE_SIZE:]
    key = _derive_key(secret_key, user_id)
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    data = json.loads(plaintext.decode("utf-8"))
    return data if isinstance(data, list) else []
