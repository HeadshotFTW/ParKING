import random
import shutil
import subprocess
from pathlib import Path


AVATAR_DIR = Path(__file__).resolve().parent / "data" / "avatars"
PRAVATAR_URL = "https://i.pravatar.cc/300?img={}"


def avatar_path(user_id):
    return AVATAR_DIR / f"user_{int(user_id)}.jpg"


def wget_available():
    return shutil.which("wget") is not None


def fetch_avatar(user_id):
    """Pokreni vanjski wget i spremi slučajni Pravatar avatar."""
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    destination = avatar_path(user_id)
    temporary = destination.with_suffix(".tmp")
    url = PRAVATAR_URL.format(random.randint(1, 70))

    command = [
        "wget",
        "--quiet",
        "--timeout=10",
        "--tries=1",
        "--output-document",
        str(temporary),
        url,
    ]

    try:
        subprocess.run(command, check=True, timeout=15)
        if not temporary.exists() or temporary.stat().st_size == 0:
            raise OSError("Prazna datoteka avatara")
        temporary.replace(destination)
        return True
    except (OSError, subprocess.SubprocessError):
        temporary.unlink(missing_ok=True)
        return False


def ensure_avatar(user_id):
    path = avatar_path(user_id)
    return bool(path.exists() and path.stat().st_size > 0) or fetch_avatar(user_id)


def delete_avatar(user_id):
    avatar_path(user_id).unlink(missing_ok=True)
