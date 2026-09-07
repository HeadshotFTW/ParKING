#include <cstddef>

class ServiceFeeCalculator {
public:
    double calculateFee(double reservation_price, double percentage) const;
    double calculateTotalFees(const double* reservation_prices, int count, double percentage) const;
};

double ServiceFeeCalculator::calculateFee(double reservation_price, double percentage) const {
    if (reservation_price <= 0.0 || percentage <= 0.0) {
        return 0.0;
    }
    return reservation_price * percentage / 100.0;
}

double ServiceFeeCalculator::calculateTotalFees(
    const double* reservation_prices,
    int count,
    double percentage
) const {
    if (reservation_prices == nullptr || count <= 0 || percentage <= 0.0) {
        return 0.0;
    }

    double total = 0.0;
    for (int index = 0; index < count; ++index) {
        total += calculateFee(reservation_prices[index], percentage);
    }
    return total;
}

extern "C" {

double parking_calculate_service_fee(double reservation_price, double percentage) {
    static const ServiceFeeCalculator calculator;
    return calculator.calculateFee(reservation_price, percentage);
}

double parking_calculate_total_service_fees(
    const double* reservation_prices,
    int count,
    double percentage
) {
    static const ServiceFeeCalculator calculator;
    return calculator.calculateTotalFees(reservation_prices, count, percentage);
}

}
