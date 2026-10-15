import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

/*
 * Introduction to Programming Concepts
 *
 * Enterprise case study: an order-processing service validates orders,
 * applies a pricing policy, records explicit state transitions, and calculates
 * a reproducible invoice using decimal arithmetic.
 *
 * Compile:
 *   javac ProgrammingConcepts.java
 *
 * Execute:
 *   java ProgrammingConcepts
 *
 * Requires Java 17 or later.
 */
public class ProgrammingConcepts {

    enum OrderStatus {
        CREATED,
        VALIDATED,
        PRICED,
        APPROVED,
        REJECTED
    }

    enum ProductCategory {
        HARDWARE,
        SOFTWARE,
        SUPPORT
    }

    record Product(String sku, String name, ProductCategory category,
                   BigDecimal unitPrice) {
        Product {
            if (sku == null || sku.isBlank()) {
                throw new IllegalArgumentException("SKU is required.");
            }
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Product name is required.");
            }
            Objects.requireNonNull(category, "Category is required.");
            Objects.requireNonNull(unitPrice, "Unit price is required.");

            if (unitPrice.signum() < 0) {
                throw new IllegalArgumentException("Unit price cannot be negative.");
            }
        }
    }

    record OrderLine(Product product, int quantity) {
        OrderLine {
            Objects.requireNonNull(product, "Product is required.");
            if (quantity <= 0) {
                throw new IllegalArgumentException("Quantity must be positive.");
            }
        }

        BigDecimal lineTotal() {
            return product.unitPrice().multiply(BigDecimal.valueOf(quantity));
        }
    }

    record PricingPolicy(BigDecimal discountThreshold,
                         BigDecimal discountRate,
                         BigDecimal taxRate) {
        PricingPolicy {
            Objects.requireNonNull(discountThreshold);
            Objects.requireNonNull(discountRate);
            Objects.requireNonNull(taxRate);

            if (discountThreshold.signum() < 0) {
                throw new IllegalArgumentException("Discount threshold cannot be negative.");
            }
            if (discountRate.signum() < 0 ||
                discountRate.compareTo(BigDecimal.ONE) > 0) {
                throw new IllegalArgumentException("Discount rate must be from 0 to 1.");
            }
            if (taxRate.signum() < 0 ||
                taxRate.compareTo(BigDecimal.ONE) > 0) {
                throw new IllegalArgumentException("Tax rate must be from 0 to 1.");
            }
        }

        boolean qualifiesForDiscount(BigDecimal subtotal) {
            return subtotal.compareTo(discountThreshold) >= 0;
        }
    }

    record Invoice(BigDecimal subtotal,
                   BigDecimal discount,
                   BigDecimal taxableAmount,
                   BigDecimal tax,
                   BigDecimal total) {
        Invoice {
            Objects.requireNonNull(subtotal);
            Objects.requireNonNull(discount);
            Objects.requireNonNull(taxableAmount);
            Objects.requireNonNull(tax);
            Objects.requireNonNull(total);
        }
    }

    static final class Order {
        private final String orderId;
        private final String customerId;
        private final LocalDate orderDate;
        private final List<OrderLine> lines;
        private OrderStatus status;
        private Invoice invoice;

        Order(String orderId, String customerId, LocalDate orderDate,
              List<OrderLine> lines) {
            if (orderId == null || orderId.isBlank()) {
                throw new IllegalArgumentException("Order ID is required.");
            }
            if (customerId == null || customerId.isBlank()) {
                throw new IllegalArgumentException("Customer ID is required.");
            }
            this.orderDate = Objects.requireNonNull(orderDate);
            if (lines == null || lines.isEmpty()) {
                throw new IllegalArgumentException("An order needs at least one line.");
            }

            this.orderId = orderId;
            this.customerId = customerId;
            this.lines = List.copyOf(lines);
            this.status = OrderStatus.CREATED;
        }

        synchronized void validate() {
            requireStatus(OrderStatus.CREATED);

            Map<String, Long> skuCounts = lines.stream()
                .collect(Collectors.groupingBy(
                    line -> line.product().sku(),
                    Collectors.counting()
                ));

            if (skuCounts.values().stream().anyMatch(count -> count > 1)) {
                throw new IllegalStateException(
                    "Duplicate SKUs must be consolidated before pricing."
                );
            }

            status = OrderStatus.VALIDATED;
        }

        synchronized Invoice price(PricingPolicy policy) {
            requireStatus(OrderStatus.VALIDATED);
            Objects.requireNonNull(policy);

            BigDecimal subtotal = lines.stream()
                .map(OrderLine::lineTotal)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

            BigDecimal discount = policy.qualifiesForDiscount(subtotal)
                ? subtotal.multiply(policy.discountRate())
                    .setScale(2, RoundingMode.HALF_UP)
                : BigDecimal.ZERO.setScale(2);

            BigDecimal taxableAmount = subtotal.subtract(discount);
            BigDecimal tax = taxableAmount.multiply(policy.taxRate())
                .setScale(2, RoundingMode.HALF_UP);
            BigDecimal total = taxableAmount.add(tax)
                .setScale(2, RoundingMode.HALF_UP);

            invoice = new Invoice(
                subtotal.setScale(2, RoundingMode.HALF_UP),
                discount,
                taxableAmount.setScale(2, RoundingMode.HALF_UP),
                tax,
                total
            );

            status = OrderStatus.PRICED;
            return invoice;
        }

        synchronized void approve() {
            requireStatus(OrderStatus.PRICED);
            if (invoice == null || invoice.total().signum() < 0) {
                throw new IllegalStateException("A valid invoice is required.");
            }
            status = OrderStatus.APPROVED;
        }

        synchronized void reject(String reason) {
            if (status == OrderStatus.APPROVED || status == OrderStatus.REJECTED) {
                throw new IllegalStateException("Order is already terminal.");
            }
            if (reason == null || reason.isBlank()) {
                throw new IllegalArgumentException("Rejection reason is required.");
            }
            status = OrderStatus.REJECTED;
        }

        private void requireStatus(OrderStatus expected) {
            if (status != expected) {
                throw new IllegalStateException(
                    "Expected " + expected + " but found " + status
                );
            }
        }

        String orderId() {
            return orderId;
        }

        String customerId() {
            return customerId;
        }

        LocalDate orderDate() {
            return orderDate;
        }

        OrderStatus status() {
            return status;
        }

        List<OrderLine> lines() {
            return lines;
        }

        Invoice invoice() {
            return invoice;
        }
    }

    private static BigDecimal money(String value) {
        return new BigDecimal(value).setScale(2, RoundingMode.HALF_UP);
    }

    private static void printInvoice(Order order) {
        Invoice invoice = order.invoice();
        System.out.printf(
            "%s | customer=%s | date=%s | status=%s%n",
            order.orderId(), order.customerId(), order.orderDate(), order.status()
        );

        for (OrderLine line : order.lines()) {
            System.out.printf(
                "  %-18s x %d = %s%n",
                line.product().name(),
                line.quantity(),
                line.lineTotal().setScale(2, RoundingMode.HALF_UP)
            );
        }

        System.out.printf(
            "  Subtotal: %s%n  Discount: %s%n  Taxable: %s%n"
                + "  Tax: %s%n  Total: %s%n",
            invoice.subtotal(),
            invoice.discount(),
            invoice.taxableAmount(),
            invoice.tax(),
            invoice.total()
        );
    }

    public static void main(String[] args) {
        Product laptop = new Product(
            "HW-100", "Engineering laptop",
            ProductCategory.HARDWARE, money("65000.00")
        );
        Product support = new Product(
            "SV-200", "Installation support",
            ProductCategory.SUPPORT, money("5000.00")
        );
        Product license = new Product(
            "SW-300", "Development license",
            ProductCategory.SOFTWARE, money("12000.00")
        );

        PricingPolicy policy = new PricingPolicy(
            money("50000.00"),
            new BigDecimal("0.05"),
            new BigDecimal("0.18")
        );

        Order enterpriseOrder = new Order(
            "ORD-2026-001",
            "CUST-500",
            LocalDate.of(2026, 10, 15),
            List.of(
                new OrderLine(laptop, 1),
                new OrderLine(support, 2),
                new OrderLine(license, 1)
            )
        );

        enterpriseOrder.validate();
        enterpriseOrder.price(policy);
        enterpriseOrder.approve();
        printInvoice(enterpriseOrder);

        System.out.println("\nValidation and state failures");

        try {
            enterpriseOrder.validate();
        } catch (IllegalStateException error) {
            System.out.println("Repeated validation rejected: " + error.getMessage());
        }

        try {
            new Order(
                "ORD-INVALID",
                "CUST-500",
                LocalDate.now(),
                List.of(new OrderLine(laptop, 0))
            );
        } catch (IllegalArgumentException error) {
            System.out.println("Invalid quantity rejected: " + error.getMessage());
        }

        try {
            new Product(
                "HW-BAD", "Invalid product",
                ProductCategory.HARDWARE, money("-1.00")
            );
        } catch (IllegalArgumentException error) {
            System.out.println("Invalid price rejected: " + error.getMessage());
        }

        Order rejectedOrder = new Order(
            "ORD-2026-002",
            "CUST-501",
            LocalDate.of(2026, 10, 15),
            List.of(new OrderLine(support, 1))
        );

        rejectedOrder.reject("Customer cancelled before validation.");
        System.out.println(
            "Cancelled order status: " + rejectedOrder.status()
        );

        try {
            rejectedOrder.reject("Second rejection");
        } catch (IllegalStateException error) {
            System.out.println("Terminal-state rule enforced: " + error.getMessage());
        }

        // Streams aggregate domain data without mutating the source collection.
        List<Order> orders = List.of(enterpriseOrder, rejectedOrder);
        Map<OrderStatus, Long> statusCounts = orders.stream()
            .collect(Collectors.groupingBy(
                Order::status,
                Collectors.counting()
            ));

        System.out.println("\nOrder status distribution:");
        statusCounts.entrySet().stream()
            .sorted(Comparator.comparing(entry -> entry.getKey().name()))
            .forEach(entry ->
                System.out.println(entry.getKey() + ": " + entry.getValue())
            );
    }
}
