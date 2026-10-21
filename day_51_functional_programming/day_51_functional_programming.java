import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.function.Predicate;
import java.util.stream.Collectors;

public class FunctionalOrderModel {

    public record Order(
            int id,
            String customer,
            List<Double> items,
            double discountRate) {

        public Order {
            if (id <= 0) {
                throw new IllegalArgumentException("Order ID must be positive.");
            }
            if (customer == null || customer.isBlank()) {
                throw new IllegalArgumentException(
                        "Customer name cannot be blank.");
            }
            Objects.requireNonNull(items, "Items cannot be null.");

            if (items.isEmpty()) {
                throw new IllegalArgumentException(
                        "An order must contain an item.");
            }

            if (items.stream().anyMatch(
                    item -> item == null || !Double.isFinite(item) || item < 0)) {
                throw new IllegalArgumentException(
                        "Items must be finite and non-negative.");
            }

            if (!Double.isFinite(discountRate)
                    || discountRate < 0
                    || discountRate > 1) {
                throw new IllegalArgumentException(
                        "Discount rate must be between 0 and 1.");
            }

            // Defensive copying makes the record's list effectively immutable
            // from the caller's perspective.
            items = List.copyOf(items);
        }

        public double subtotal() {
            return items.stream()
                    .mapToDouble(Double::doubleValue)
                    .sum();
        }

        public double total() {
            return subtotal() * (1.0 - discountRate);
        }

        public Order withAdditionalItem(double price) {
            if (!Double.isFinite(price) || price < 0) {
                throw new IllegalArgumentException(
                        "Price must be finite and non-negative.");
            }

            List<Double> updatedItems = new ArrayList<>(items);
            updatedItems.add(price);

            return new Order(id, customer, updatedItems, discountRate);
        }

        public Order withDiscount(double newDiscountRate) {
            return new Order(
                    id,
                    customer,
                    items,
                    newDiscountRate);
        }
    }

    public enum ProcessingState {
        RECEIVED,
        VALIDATED,
        ELIGIBLE,
        REJECTED
    }

    public record ProcessingResult(
            Order order,
            ProcessingState state,
            String reason) {
    }

    public interface OrderPolicy {
        boolean accepts(Order order);
    }

    public static ProcessingResult evaluate(
            Order order,
            List<OrderPolicy> policies) {

        Objects.requireNonNull(order, "Order cannot be null.");
        Objects.requireNonNull(policies, "Policies cannot be null.");

        for (OrderPolicy policy : policies) {
            if (!policy.accepts(order)) {
                return new ProcessingResult(
                        order,
                        ProcessingState.REJECTED,
                        "A processing policy rejected the order.");
            }
        }

        return new ProcessingResult(
                order,
                ProcessingState.ELIGIBLE,
                "All policies accepted the order.");
    }

    public static <T, R> List<R> transform(
            List<T> values,
            Function<T, R> operation) {

        Objects.requireNonNull(values, "Values cannot be null.");
        Objects.requireNonNull(operation, "Operation cannot be null.");

        return List.copyOf(
                values.stream()
                        .map(operation)
                        .toList());
    }

    public static <T> List<T> select(
            List<T> values,
            Predicate<T> predicate) {

        Objects.requireNonNull(values, "Values cannot be null.");
        Objects.requireNonNull(predicate, "Predicate cannot be null.");

        return List.copyOf(
                values.stream()
                        .filter(predicate)
                        .toList());
    }

    public static <T, R> Function<T, R> compose(
            Function<T, R> first) {
        return first;
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
                new Order(
                        401,
                        "Enterprise Alpha",
                        List.of(650.0, 500.0),
                        0.10),
                new Order(
                        402,
                        "Enterprise Beta",
                        List.of(300.0, 250.0),
                        0.05),
                new Order(
                        403,
                        "Enterprise Gamma",
                        List.of(1500.0, 900.0),
                        0.15)
        );

        OrderPolicy minimumValuePolicy =
                order -> order.total() >= 500.0;

        OrderPolicy maximumValuePolicy =
                order -> order.total() <= 2500.0;

        List<OrderPolicy> policies = List.of(
                minimumValuePolicy,
                maximumValuePolicy);

        System.out.println("Functional Java 17 Order Model");
        System.out.println("--------------------------------");

        for (Order order : orders) {
            ProcessingResult result = evaluate(order, policies);

            System.out.printf(
                    "Order %d: state=%s, total=%.2f, reason=%s%n",
                    order.id(),
                    result.state(),
                    order.total(),
                    result.reason());
        }

        Order original = orders.get(0);
        Order expanded = original.withAdditionalItem(250.0);
        Order repriced = expanded.withDiscount(0.20);

        System.out.printf(
                "Original total: %.2f%n",
                original.total());

        System.out.printf(
                "Expanded total: %.2f%n",
                expanded.total());

        System.out.printf(
                "Repriced total: %.2f%n",
                repriced.total());

        List<Double> highValueTotals = transform(
                select(
                        orders,
                        order -> order.total() >= 1000.0),
                Order::total);

        System.out.println("High-value totals: " + highValueTotals);

        Map<String, Double> customerTotals = orders.stream()
                .collect(Collectors.toUnmodifiableMap(
                        Order::customer,
                        Order::total));

        System.out.println("Customer totals: " + customerTotals);

        // Function composition can create a domain-specific calculation
        // without modifying the source value.
        Function<Double, Double> invoiceValue =
                amount -> (amount + 50.0) * 1.18;

        System.out.printf(
                "Composed invoice value: %.2f%n",
                invoiceValue.apply(1000.0));

        try {
            original.withDiscount(1.5);
        } catch (IllegalArgumentException error) {
            System.out.println(
                    "Validation failure handled: " + error.getMessage());
        }

        // Stream transformations are linear in the number of orders.
        // Defensive immutable collections reduce accidental shared-state
        // mutations, while creating new Order values has allocation cost.
    }
}
