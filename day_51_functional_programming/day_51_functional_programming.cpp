#include <algorithm>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

struct Order {
    int id;
    std::string customer;
    std::vector<double> items;
    double discountRate;

    // The methods do not mutate the order, making the domain object suitable
    // for functional-style transformations.
    double subtotal() const {
        return std::accumulate(items.begin(), items.end(), 0.0);
    }

    double total() const {
        return subtotal() * (1.0 - discountRate);
    }
};

void validate(const Order& order) {
    if (order.id <= 0) {
        throw std::invalid_argument("Order ID must be positive.");
    }

    if (order.customer.empty()) {
        throw std::invalid_argument("Customer name cannot be empty.");
    }

    if (order.items.empty()) {
        throw std::invalid_argument("Order must contain at least one item.");
    }

    if (order.discountRate < 0.0 || order.discountRate > 1.0) {
        throw std::invalid_argument("Discount rate must be between 0 and 1.");
    }

    if (std::any_of(
            order.items.begin(),
            order.items.end(),
            [](double price) { return price < 0.0; })) {
        throw std::invalid_argument("Item prices cannot be negative.");
    }
}

// Returns a new order instead of changing the supplied object.
Order addItem(const Order& order, double price) {
    validate(order);

    if (price < 0.0) {
        throw std::invalid_argument("Item price cannot be negative.");
    }

    Order result = order;
    result.items.push_back(price);
    return result;
}

Order changeDiscount(const Order& order, double discountRate) {
    validate(order);

    if (discountRate < 0.0 || discountRate > 1.0) {
        throw std::invalid_argument("Discount rate must be between 0 and 1.");
    }

    Order result = order;
    result.discountRate = discountRate;
    return result;
}

template <typename Input, typename Output, typename Function>
std::vector<Output> mapValues(
    const std::vector<Input>& values,
    Function operation) {
    std::vector<Output> result;
    result.reserve(values.size());

    std::transform(
        values.begin(),
        values.end(),
        std::back_inserter(result),
        operation);

    return result;
}

template <typename T, typename Predicate>
std::vector<T> filterValues(
    const std::vector<T>& values,
    Predicate predicate) {
    std::vector<T> result;

    std::copy_if(
        values.begin(),
        values.end(),
        std::back_inserter(result),
        predicate);

    return result;
}

double composeInvoice(double amount) {
    // Lambda expressions represent individual pure transformations.
    const auto addServiceFee = [](double value) {
        return value + 50.0;
    };

    const auto addTax = [](double value) {
        return value * 1.18;
    };

    return addTax(addServiceFee(amount));
}

double sumTotals(const std::vector<Order>& orders) {
    return std::accumulate(
        orders.begin(),
        orders.end(),
        0.0,
        [](double current, const Order& order) {
            return current + order.total();
        });
}

int main() {
    try {
        const std::vector<Order> orders{
            {301, "Atlas Systems", {600.0, 550.0}, 0.10},
            {302, "Beacon Labs", {300.0, 250.0}, 0.05},
            {303, "Cedar Group", {1400.0, 900.0}, 0.15},
        };

        for (const auto& order : orders) {
            validate(order);
        }

        const Order expanded = addItem(orders[0], 250.0);
        const Order repriced = changeDiscount(expanded, 0.20);

        std::cout << std::fixed << std::setprecision(2);
        std::cout << "Functional C++ Order Model\n";
        std::cout << "-------------------------\n";
        std::cout << "Original total: " << orders[0].total() << '\n';
        std::cout << "Expanded total: " << expanded.total() << '\n';
        std::cout << "Repriced total: " << repriced.total() << '\n';

        // Higher-order functions accept behavior rather than hard-coding it.
        const auto highValue = filterValues<Order>(
            orders,
            [](const Order& order) {
                return order.total() >= 1000.0;
            });

        const auto highValueTotals = mapValues<Order, double>(
            highValue,
            [](const Order& order) {
                return order.total();
            });

        std::cout << "High-value totals:";
        for (double value : highValueTotals) {
            std::cout << ' ' << value;
        }
        std::cout << '\n';

        std::cout << "Combined total: "
                  << sumTotals(orders)
                  << '\n';

        std::cout << "Composed invoice value: "
                  << composeInvoice(1000.0)
                  << '\n';

        // Invalid transformations fail before state is changed.
        try {
            changeDiscount(orders[0], 1.25);
        } catch (const std::exception& error) {
            std::cout << "Validation failure handled: "
                      << error.what()
                      << '\n';
        }

        // Complexity:
        // subtotal is O(n) for the number of line items.
        // filter/map are O(m) for the number of orders.
        // The implementation uses copies when producing modified values,
        // which favors safety and clarity over mutation-based optimization.
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
