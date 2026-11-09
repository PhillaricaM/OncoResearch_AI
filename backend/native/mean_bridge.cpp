// Small stdin/stdout adapter; the numerical algorithm remains in OncoCompute.
#include "oncocompute/statistics.hpp"
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <locale>
#include <vector>

int main() {
    std::cin.imbue(std::locale::classic());
    std::cout.imbue(std::locale::classic());
    unsigned int count = 0;
    if (!(std::cin >> count) || count == 0 || count > 10000) return 2;
    std::vector<double> values(count);
    for (auto& value : values) {
        if (!(std::cin >> value) || !std::isfinite(value) || std::abs(value) > 1e100) return 2;
    }
    std::cin >> std::ws;
    if (!std::cin.eof()) return 2;
    const double result = oncocompute::mean(values);
    if (!std::isfinite(result)) return 3;
    std::cout << std::setprecision(std::numeric_limits<double>::max_digits10) << result << '\n';
    return 0;
}
