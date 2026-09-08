import random
import shutil
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
AVATAR_DIR = BASE_DIR / "data" / "avatars"
PRAVATAR_BASE_URL = "https://i.pravatar.cc/300"
PRAVATAR_MIN_IMAGE = 1
PRAVATAR_MAX_IMAGE = 70


def avatar_path(user_id):
    """Return the local JPEG path derived from the user's stable database ID."""
    return AVATAR_DIR / f"user_{int(user_id)}.jpg"


def wget_available():
    """True when the external wget executable is installed in the current container."""
    return shutil.which("wget") is not None


def fetch_avatar(user_id):
    """Download a random Pravatar image by launching the external wget executable."""
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    destination = avatar_path(user_id)
    temporary = destination.with_suffix(".tmp")
    image_number = random.randint(PRAVATAR_MIN_IMAGE, PRAVATAR_MAX_IMAGE)
    url = f"{PRAVATAR_BASE_URL}?img={image_number}"

    try:
        completed = subprocess.run(
            [
                "wget",
                "--quiet",
                "--timeout=10",
                "--tries=1",
                "--output-document",
                str(temporary),
                url,
            ],
            check=False,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        temporary.unlink(missing_ok=True)
        return False

    if completed.returncode != 0 or not temporary.exists() or temporary.stat().st_size == 0:
        temporary.unlink(missing_ok=True)
        return False

    temporary.replace(destination)
    return True


def ensure_avatar(user_id):
    """Download an avatar only when the user does not already have one."""
    path = avatar_path(user_id)
    if path.exists() and path.stat().st_size > 0:
        return True
    return fetch_avatar(user_id)


def delete_avatar(user_id):
    avatar_path(user_id).unlink(missing_ok=True)
