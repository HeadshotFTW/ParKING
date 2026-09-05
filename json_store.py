import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "parking_notes.json"


def _read_all():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]\n", encoding="utf-8")
        return []

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    return data if isinstance(data, list) else []


def _write_all(notes):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(notes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def list_notes(user_id):
    return [
        note for note in _read_all()
        if note.get("user_id") == user_id
    ]


def get_note(user_id, note_id):
    return next(
        (
            note for note in _read_all()
            if note.get("id") == note_id and note.get("user_id") == user_id
        ),
        None,
    )


def add_note(user_id, title, text):
    notes = _read_all()
    next_id = max((note.get("id", 0) for note in notes), default=0) + 1
    note = {
        "id": next_id,
        "user_id": user_id,
        "title": title,
        "text": text,
    }
    notes.append(note)
    _write_all(notes)
    return note


def update_note(user_id, note_id, title, text):
    notes = _read_all()
    for note in notes:
        if note.get("id") == note_id and note.get("user_id") == user_id:
            note["title"] = title
            note["text"] = text
            _write_all(notes)
            return note
    return None


def delete_note(user_id, note_id):
    notes = _read_all()
    remaining = [
        note for note in notes
        if not (note.get("id") == note_id and note.get("user_id") == user_id)
    ]
    if len(remaining) == len(notes):
        return False
    _write_all(remaining)
    return True
