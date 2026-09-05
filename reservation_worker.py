import argparse
import sqlite3
import sys


def check_reservations(db_path):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT id, parking_id, start_time, end_time, status FROM reservations ORDER BY parking_id, start_time"
        ).fetchall()
    finally:
        connection.close()

    problems = []
    active_by_parking = {}

    for row in rows:
        if row["end_time"] <= row["start_time"]:
            problems.append(f"Rezervacija {row['id']}: završetak nije nakon početka.")

        if row["status"] != "ACTIVE":
            continue

        parking_rows = active_by_parking.setdefault(row["parking_id"], [])
        for previous in parking_rows:
            if previous["start_time"] < row["end_time"] and previous["end_time"] > row["start_time"]:
                problems.append(
                    f"Preklapanje rezervacija {previous['id']} i {row['id']} za parking {row['parking_id']}."
                )
        parking_rows.append(row)

    if problems:
        print("Provjera je pronašla probleme:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print(f"Provjera uspješna. Pregledano rezervacija: {len(rows)}.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="ParKING worker za provjeru rezervacija")
    parser.add_argument("db_path")
    parser.add_argument("--simulate-error", action="store_true")
    args = parser.parse_args()

    if args.simulate_error:
        print("Simulirana tehnička greška procesa B.", file=sys.stderr)
        return 2

    try:
        return check_reservations(args.db_path)
    except Exception as exc:
        print(f"Tehnička greška: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
