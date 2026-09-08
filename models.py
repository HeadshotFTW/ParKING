import secrets

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="USER")
    api_token = db.Column(db.String(64), unique=True, nullable=False,
                          default=lambda: secrets.token_hex(24))

    parkings = db.relationship(
        "ParkingSpot",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="ParkingSpot.owner_id",
    )
    reservations = db.relationship(
        "Reservation",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Reservation.user_id",
    )
    promo_assignment = db.relationship(
        "PromoCode",
        back_populates="user",
        uselist=False,
        foreign_keys="PromoCode.user_id",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "ADMIN"


class ParkingSpot(db.Model):
    __tablename__ = "parking_spots"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    photo = db.Column(db.LargeBinary, nullable=True)
    photo_mime = db.Column(db.String(100), nullable=True)
    access_instructions = db.Column(db.LargeBinary, nullable=True)

    owner = db.relationship("User", back_populates="parkings", foreign_keys=[owner_id])
    reservations = db.relationship(
        "Reservation",
        back_populates="parking",
        cascade="all, delete-orphan",
    )

    def display_price(self):
        return f"{self.price_per_hour:.2f} € / sat"

    def is_owned_by(self, user):
        return bool(user and self.owner_id == user.id)


class PromoCode(db.Model):
    __tablename__ = "promo_codes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    code_hash = db.Column(db.String(64), nullable=False)
    discount_percent = db.Column(db.Float, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship("User", back_populates="promo_assignment", foreign_keys=[user_id])
    reservations = db.relationship("Reservation", back_populates="promo_code")


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    parking_id = db.Column(db.Integer, db.ForeignKey("parking_spots.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    discount_percent = db.Column(db.Float, nullable=False, default=0.0)
    promo_code_id = db.Column(db.Integer, db.ForeignKey("promo_codes.id"), nullable=True)

    # Vehicle data originates from data/vehicles.json. We keep a snapshot on the
    # reservation so an old reservation remains understandable even if the user
    # later edits or deletes that JSON vehicle record.
    vehicle_id = db.Column(db.Integer, nullable=True)
    vehicle_name = db.Column(db.String(120), nullable=True)
    vehicle_registration = db.Column(db.String(40), nullable=True)

    parking = db.relationship("ParkingSpot", back_populates="reservations")
    user = db.relationship("User", back_populates="reservations", foreign_keys=[user_id])
    promo_code = db.relationship("PromoCode", back_populates="reservations")

    def duration_hours(self):
        seconds = (self.end_time - self.start_time).total_seconds()
        return max(seconds / 3600, 0)

    def base_price(self):
        return self.duration_hours() * self.parking.price_per_hour

    def discount_amount(self):
        percent = max(0.0, min(float(self.discount_percent or 0.0), 100.0))
        return self.base_price() * percent / 100.0

    def total_price(self):
        return self.base_price() - self.discount_amount()

    def vehicle_display(self):
        if not self.vehicle_name and not self.vehicle_registration:
            return ""
        if self.vehicle_name and self.vehicle_registration:
            return f"{self.vehicle_name} ({self.vehicle_registration})"
        return self.vehicle_name or self.vehicle_registration or ""

    def overlaps(self, start_time, end_time):
        return self.status == "ACTIVE" and start_time < self.end_time and end_time > self.start_time
