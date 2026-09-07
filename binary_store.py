import struct
from datetime import datetime, timezone
from pathlib import Path

MAGIC = b"PKSR"
VERSION = 2
HEADER = struct.Struct("<4sBI")  # magic, verzija, broj zapisa
FIXED_V1 = struct.Struct("<IqdH")  # user_id, unix vrijeme, max_price, duljina lokacije
FIXED_V2 = struct.Struct("<IqdHHHH")  # user_id, unix vrijeme, max_price, duljine tekstualnih polja


def _empty_file(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(HEADER.pack(MAGIC, VERSION, 0))


def _read_exact(handle, size, error_message):
    data = handle.read(size)
    if len(data) != size:
        raise ValueError(error_message)
    return data


def _record(user_id, timestamp, max_price, location, start_time="", end_time="", sort="price_asc"):
    normalized_max_price = None
    if max_price is not None and float(max_price) >= 0:
        normalized_max_price = float(max_price)
    return {
        "user_id": int(user_id),
        "timestamp": int(timestamp),
        "created_at": datetime.fromtimestamp(int(timestamp), tz=timezone.utc),
        "max_price": normalized_max_price,
        "location": location,
        "start_time": start_time,
        "end_time": end_time,
        "sort": sort or "price_asc",
    }


def read_records(path):
    path = Path(path)
    if not path.exists():
        _empty_file(path)
        return []

    with path.open("rb") as handle:
        header = _read_exact(
            handle,
            HEADER.size,
            "Neispravna binarna datoteka: zaglavlje nedostaje.",
        )
        magic, version, count = HEADER.unpack(header)
        if magic != MAGIC:
            raise ValueError("Nepoznat ParKING binarni format.")
        if version not in {1, VERSION}:
            raise ValueError(f"Nepodržana verzija ParKING binarnog formata: {version}.")

        records = []
        for _ in range(count):
            if version == 1:
                fixed = _read_exact(
                    handle,
                    FIXED_V1.size,
                    "Neispravna binarna datoteka: nepotpun zapis.",
                )
                user_id, timestamp, max_price, location_len = FIXED_V1.unpack(fixed)
                location = _read_exact(
                    handle,
                    location_len,
                    "Neispravna binarna datoteka: nepotpuna lokacija.",
                ).decode("utf-8")
                records.append(_record(user_id, timestamp, max_price, location))
                continue

            fixed = _read_exact(
                handle,
                FIXED_V2.size,
                "Neispravna binarna datoteka: nepotpun zapis.",
            )
            user_id, timestamp, max_price, location_len, start_len, end_len, sort_len = FIXED_V2.unpack(fixed)

            location = _read_exact(handle, location_len, "Neispravna binarna datoteka: nepotpuna lokacija.").decode("utf-8")
            start_time = _read_exact(handle, start_len, "Neispravna binarna datoteka: nepotpun početak termina.").decode("utf-8")
            end_time = _read_exact(handle, end_len, "Neispravna binarna datoteka: nepotpun završetak termina.").decode("utf-8")
            sort = _read_exact(handle, sort_len, "Neispravna binarna datoteka: nepotpuno sortiranje.").decode("utf-8")
            records.append(_record(user_id, timestamp, max_price, location, start_time, end_time, sort))

        return records


def write_records(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(HEADER.pack(MAGIC, VERSION, len(records)))
        for record in records:
            fields = [
                str(record.get("location", "")).encode("utf-8"),
                str(record.get("start_time", "")).encode("utf-8"),
                str(record.get("end_time", "")).encode("utf-8"),
                str(record.get("sort", "price_asc")).encode("utf-8"),
            ]
            if any(len(field) > 65535 for field in fields):
                raise ValueError("Tekstualno polje je predugo za binarni format.")

            max_price = record.get("max_price")
            stored_max_price = -1.0 if max_price is None else float(max_price)
            handle.write(FIXED_V2.pack(
                int(record["user_id"]),
                int(record["timestamp"]),
                stored_max_price,
                *(len(field) for field in fields),
            ))
            for field in fields:
                handle.write(field)


def add_record(path, user_id, location="", max_price=None, start_time="", end_time="", sort="price_asc"):
    records = read_records(path)
    record = {
        "user_id": int(user_id),
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
        "max_price": None if max_price is None else float(max_price),
        "location": location.strip(),
        "start_time": start_time.strip(),
        "end_time": end_time.strip(),
        "sort": sort.strip() or "price_asc",
    }
    records.append(record)
    # Svaki novi zapis prepisuje datoteku u aktualnu verziju formata,
    # pa se postojeći v1 zapisi automatski migriraju u v2.
    write_records(path, records)
    return _record(**record)


def records_for_user(path, user_id):
    return [record for record in read_records(path) if record["user_id"] == int(user_id)]
