import ctypes
import os
import sys
from pathlib import Path

SERVICE_FEE_PERCENTAGE = 5.0
BASE_DIR = Path(__file__).resolve().parent / "native"


def _library_filename():
    if os.name == "nt":
        return "service_fee.dll"
    if sys.platform == "darwin":
        return "libservice_fee.dylib"
    return "libservice_fee.so"


LIBRARY_PATH = BASE_DIR / _library_filename()

try:
    _library = ctypes.CDLL(str(LIBRARY_PATH))
except OSError:
    _library = None
else:
    _library.parking_calculate_service_fee.argtypes = [ctypes.c_double, ctypes.c_double]
    _library.parking_calculate_service_fee.restype = ctypes.c_double
    _library.parking_calculate_total_service_fees.argtypes = [
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.c_double,
    ]
    _library.parking_calculate_total_service_fees.restype = ctypes.c_double


def native_library_loaded():
    return _library is not None


def calculate_service_fee(reservation_price, percentage=SERVICE_FEE_PERCENTAGE):
    reservation_price = max(float(reservation_price), 0.0)
    percentage = max(float(percentage), 0.0)
    if _library is None:
        return reservation_price * percentage / 100.0
    return float(_library.parking_calculate_service_fee(reservation_price, percentage))


def calculate_total_service_fees(reservation_prices, percentage=SERVICE_FEE_PERCENTAGE):
    prices = [max(float(price), 0.0) for price in reservation_prices]
    percentage = max(float(percentage), 0.0)
    if not prices:
        return 0.0
    if _library is None:
        return sum(price * percentage / 100.0 for price in prices)

    array_type = ctypes.c_double * len(prices)
    native_prices = array_type(*prices)
    return float(
        _library.parking_calculate_total_service_fees(
            native_prices,
            len(prices),
            percentage,
        )
    )


def total_service_fees_for_reservations(reservations, percentage=SERVICE_FEE_PERCENTAGE):
    active_prices = [
        reservation.total_price()
        for reservation in reservations
        if reservation.status == "ACTIVE"
    ]
    return calculate_total_service_fees(active_prices, percentage)
