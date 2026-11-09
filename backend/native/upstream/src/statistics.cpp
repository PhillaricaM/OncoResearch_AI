
#include "oncocompute/statistics.hpp"

#include <numeric>
#include <stdexcept>

namespace oncocompute {

    double mean(const std::vector<double>& values) {

        if (values.empty()) {
            throw std::invalid_argument(
                "Cannot calculate the mean of empty data"
            );
        }

        double total = 0.0;

        for (double value : values) {
            total += value;
        }

        return total / values.size();
    }

}

