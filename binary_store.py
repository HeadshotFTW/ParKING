import struct
from datetime import datetime, timezone
from pathlib import Path

MAGIC = b"PKSR"
VERSION = 1
HEADER = struct.Struct("<4sBI")  # magic, verzija, broj zapisa
FIXED = struct.Struct("<IqdH")    # user_id, unix vrijeme, max_price, duljina lokacije


def _empty_file(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(HEADER.pack(MAGIC, VERSION, 0))


def read_records(path):
    path = Path(path)
    if not path.exists():
        _empty_file(path)
        return []

    with path.open("rb") as handle:
        header = handle.read(HEADER.size)
        if len(header) != HEADER.size:
            raise ValueError("Neispravna binarna datoteka: zaglavlje nedostaje.")
        magic, version, count = HEADER.unpack(header)
        if magic != MAGIC or version != VERSION:
            raise ValueError("Nepoznat ParKING binarni format.")

        records = []
        for _ in range(count):
            fixed = handle.read(FIXED.size)
            if len(fixed) != FIXED.size:
                raise ValueError("Neispravna binarna datoteka: nepotpun zapis.")
            user_id, timestamp, max_price, location_len = FIXED.unpack(fixed)
            location_bytes = handle.read(location_len)
            if len(location_bytes) != location_len:
                raise ValueError("Neispravna binarna datoteka: nepotpuna lokacija.")
            records.append({
                "user_id": user_id,
                "timestamp": timestamp,
                "created_at": datetime.fromtimestamp(timestamp, tz=timezone.utc),
                "max_price": max_price,
                "location": location_bytes.decode("utf-8"),
            })
        return records


def write_records(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(HEADER.pack(MAGIC, VERSION, len(records)))
        for record in records:
            location = record["location"].encode("utf-8")
            if len(location) > 65535:
                raise ValueError("Lokacija je preduga za binarni format.")
            handle.write(FIXED.pack(
                int(record["user_id"]),
                int(record["timestamp"]),
                float(record["max_price"]),
                len(location),
            ))
            handle.write(location)


def add_record(path, user_id, location, max_price):
    records = read_records(path)
    records.append({
        "user_id": int(user_id),
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
        "max_price": float(max_price),
        "location": location.strip(),
    })
    write_records(path, records)
    return records[-1]


def records_for_user(path, user_id):
    return [record for record in read_records(path) if record["user_id"] == int(user_id)]
