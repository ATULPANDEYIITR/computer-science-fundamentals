#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Introduction to Programming Concepts
 *
 * Case study: a manufacturing facility calculates production batches,
 * validates machine parameters, classifies results, and produces a report.
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -Wpedantic programming_concepts.cpp -o concepts
 *
 * Execute:
 *   ./concepts
 */

namespace manufacturing {

enum class BatchStatus {
    Accepted,
    NeedsInspection,
    Rejected
};

std::string toString(BatchStatus status) {
    switch (status) {
        case BatchStatus::Accepted:
            return "Accepted";
        case BatchStatus::NeedsInspection:
            return "Needs inspection";
        case BatchStatus::Rejected:
            return "Rejected";
    }
    throw std::logic_error("Unknown batch status.");
}

struct MachineParameters {
    double targetTemperatureCelsius;
    double measuredTemperatureCelsius;
    double targetPressureKPa;
    double measuredPressureKPa;
};

struct ProductionBatch {
    std::string batchId;
    int unitsProduced;
    int defectiveUnits;
    MachineParameters machine;
};

struct BatchAssessment {
    std::string batchId;
    double defectRatePercent;
    double temperatureDeviation;
    double pressureDeviation;
    BatchStatus status;
    std::vector<std::string> findings;
};

class QualityPolicy {
public:
    QualityPolicy(double maximumDefectRate,
                  double temperatureTolerance,
                  double pressureTolerance)
        : maximumDefectRate_(maximumDefectRate),
          temperatureTolerance_(temperatureTolerance),
          pressureTolerance_(pressureTolerance) {
        if (!std::isfinite(maximumDefectRate_) ||
            maximumDefectRate_ < 0.0 ||
            maximumDefectRate_ > 100.0) {
            throw std::invalid_argument("Defect threshold must be between 0 and 100.");
        }
        if (!std::isfinite(temperatureTolerance_) ||
            temperatureTolerance_ < 0.0) {
            throw std::invalid_argument("Temperature tolerance must be non-negative.");
        }
        if (!std::isfinite(pressureTolerance_) ||
            pressureTolerance_ < 0.0) {
            throw std::invalid_argument("Pressure tolerance must be non-negative.");
        }
    }

    BatchAssessment assess(const ProductionBatch& batch) const {
        validate(batch);

        const double defectRate =
            100.0 * static_cast<double>(batch.defectiveUnits) /
            static_cast<double>(batch.unitsProduced);

        const double temperatureDeviation = std::abs(
            batch.machine.measuredTemperatureCelsius -
            batch.machine.targetTemperatureCelsius
        );

        const double pressureDeviation = std::abs(
            batch.machine.measuredPressureKPa -
            batch.machine.targetPressureKPa
        );

        BatchAssessment assessment{
            batch.batchId,
            defectRate,
            temperatureDeviation,
            pressureDeviation,
            BatchStatus::Accepted,
            {}
        };

        // Independent checks produce explicit findings rather than hiding
        // multiple failure causes behind one boolean result.
        if (defectRate > maximumDefectRate_) {
            assessment.findings.push_back("Defect rate exceeds policy.");
            assessment.status = BatchStatus::Rejected;
        }

        if (temperatureDeviation > temperatureTolerance_) {
            assessment.findings.push_back("Temperature is outside tolerance.");
            if (assessment.status != BatchStatus::Rejected) {
                assessment.status = BatchStatus::NeedsInspection;
            }
        }

        if (pressureDeviation > pressureTolerance_) {
            assessment.findings.push_back("Pressure is outside tolerance.");
            if (assessment.status != BatchStatus::Rejected) {
                assessment.status = BatchStatus::NeedsInspection;
            }
        }

        if (assessment.findings.empty()) {
            assessment.findings.push_back("All quality checks passed.");
        }

        return assessment;
    }

private:
    double maximumDefectRate_;
    double temperatureTolerance_;
    double pressureTolerance_;

    static void validate(const ProductionBatch& batch) {
        if (batch.batchId.empty()) {
            throw std::invalid_argument("Batch ID cannot be empty.");
        }
        if (batch.unitsProduced <= 0) {
            throw std::invalid_argument("Units produced must be positive.");
        }
        if (batch.defectiveUnits < 0 ||
            batch.defectiveUnits > batch.unitsProduced) {
            throw std::invalid_argument(
                "Defective units must be between zero and total production."
            );
        }

        const auto& machine = batch.machine;
        const double values[] = {
            machine.targetTemperatureCelsius,
            machine.measuredTemperatureCelsius,
            machine.targetPressureKPa,
            machine.measuredPressureKPa
        };

        for (double value : values) {
            if (!std::isfinite(value)) {
                throw std::invalid_argument(
                    "Machine readings must be finite numbers."
                );
            }
        }

        if (machine.targetPressureKPa <= 0.0 ||
            machine.measuredPressureKPa <= 0.0) {
            throw std::invalid_argument("Pressure must be positive.");
        }
    }
};

class ProductionReport {
public:
    void add(BatchAssessment assessment) {
        // IDs are unique within the report so an accidental duplicate import
        // cannot inflate production statistics.
        if (assessment.batchId.empty()) {
            throw std::invalid_argument("Assessment ID cannot be empty.");
        }
        const auto inserted = assessments_.emplace(
            assessment.batchId, std::move(assessment)
        );
        if (!inserted.second) {
            throw std::invalid_argument("Duplicate batch assessment.");
        }
    }

    void print() const {
        int accepted = 0;
        int inspection = 0;
        int rejected = 0;
        double totalDefectRate = 0.0;

        std::cout << std::fixed << std::setprecision(2);
        std::cout << "\nProduction quality report\n";
        std::cout << "------------------------------------------------------------\n";

        for (const auto& entry : assessments_) {
            const auto& assessment = entry.second;

            std::cout << assessment.batchId
                      << " | defect rate=" << assessment.defectRatePercent
                      << "% | status=" << toString(assessment.status) << '\n';

            for (const auto& finding : assessment.findings) {
                std::cout << "    " << finding << '\n';
            }

            totalDefectRate += assessment.defectRatePercent;

            switch (assessment.status) {
                case BatchStatus::Accepted:
                    ++accepted;
                    break;
                case BatchStatus::NeedsInspection:
                    ++inspection;
                    break;
                case BatchStatus::Rejected:
                    ++rejected;
                    break;
            }
        }

        const std::size_t count = assessments_.size();
        std::cout << "\nAccepted: " << accepted
                  << ", inspection: " << inspection
                  << ", rejected: " << rejected << '\n';

        if (count > 0) {
            std::cout << "Mean batch defect rate: "
                      << totalDefectRate / static_cast<double>(count)
                      << "%\n";
        }
    }

private:
    std::map<std::string, BatchAssessment> assessments_;
};

ProductionBatch makeBatch(
    std::string id,
    int produced,
    int defective,
    double measuredTemperature,
    double measuredPressure
) {
    return ProductionBatch{
        std::move(id),
        produced,
        defective,
        MachineParameters{
            200.0,
            measuredTemperature,
            500.0,
            measuredPressure
        }
    };
}

}  // namespace manufacturing

int main() {
    using namespace manufacturing;

    try {
        const QualityPolicy policy(2.0, 5.0, 20.0);

        const std::vector<ProductionBatch> batches{
            makeBatch("BATCH-100", 1000, 8, 202.0, 505.0),
            makeBatch("BATCH-101", 1200, 30, 201.0, 503.0),
            makeBatch("BATCH-102", 800, 7, 208.0, 530.0),
            makeBatch("BATCH-103", 500, 2, 199.0, 498.0)
        };

        ProductionReport report;

        for (const auto& batch : batches) {
            report.add(policy.assess(batch));
        }

        report.print();

        std::cout << "\nValidation behavior\n";
        try {
            const auto invalid = makeBatch("BATCH-BAD", 100, 101, 200.0, 500.0);
            (void)policy.assess(invalid);
        } catch (const std::invalid_argument& error) {
            std::cout << "Invalid batch rejected: " << error.what() << '\n';
        }

        std::cout << "\nDuplicate handling\n";
        try {
            const auto assessment = policy.assess(batches.front());
            report.add(assessment);
        } catch (const std::invalid_argument& error) {
            std::cout << "Duplicate record rejected: " << error.what() << '\n';
        }

        std::cout << "\nPolicy validation\n";
        try {
            const QualityPolicy invalidPolicy(110.0, 5.0, 20.0);
            (void)invalidPolicy;
        } catch (const std::invalid_argument& error) {
            std::cout << "Invalid policy rejected: " << error.what() << '\n';
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }
}
