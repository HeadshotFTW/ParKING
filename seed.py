from datetime import datetime, timedelta

from app import app
from avatar_fetch import ensure_avatar
from models import db, User, ParkingSpot, Reservation


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        owner = User(username="vlasnik", role="USER")
        owner.set_password("parking123")

        guest = User(username="gost", role="USER")
        guest.set_password("parking123")

        admin = User(username="admin", role="ADMIN")
        admin.set_password("admin123")

        db.session.add_all([owner, guest, admin])
        db.session.flush()

        center = ParkingSpot(
            owner_id=owner.id,
            name="Parking Centar",
            location="Zagreb, Ilica 20",
            price_per_hour=2.50,
            description="Privatno parkirno mjesto blizu centra Zagreba.",
        )
        tresnjevka = ParkingSpot(
            owner_id=owner.id,
            name="Parking Trešnjevka",
            location="Zagreb, Ozaljska 10",
            price_per_hour=1.50,
            description="Mirno parkirno mjesto uz tramvajsku stanicu.",
        )
        zadar = ParkingSpot(
            owner_id=owner.id,
            name="Parking Zadar Centar",
            location="Zadar, Obala kneza Branimira 10",
            price_per_hour=2.00,
            description="Privatni parking u blizini centra Zadra.",
        )
        split = ParkingSpot(
            owner_id=owner.id,
            name="Parking Split",
            location="Split, Vukovarska 15",
            price_per_hour=2.20,
            description="Privatno parkirno mjesto u Splitu.",
        )

        db.session.add_all([center, tresnjevka, zadar, split])
        db.session.flush()

        start = (datetime.now() + timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
        reservation = Reservation(
            parking_id=center.id,
            user_id=guest.id,
            start_time=start,
            end_time=start + timedelta(hours=2),
            status="ACTIVE",
        )
        db.session.add(reservation)
        db.session.commit()

        # Avatar download is best-effort: a temporary Pravatar/network failure must
        # not prevent the development database from being seeded.
        for user in (owner, guest, admin):
            ensure_avatar(user.id)

        print("Početni podaci su kreirani.")
        print("vlasnik / parking123")
        print("gost     / parking123")
        print("admin    / admin123")
        print("Parkinzi: Zagreb (2), Zadar (1), Split (1)")


if __name__ == "__main__":
    seed()
