"use strict";

/*
 * Functional order-processing model.
 *
 * The implementation favors pure transformations, immutable data,
 * higher-order functions, and lambda expressions represented by
 * JavaScript arrow functions.
 */

const freezeOrder = (order) =>
  Object.freeze({
    id: order.id,
    customer: order.customer,
    items: Object.freeze([...order.items]),
    discountRate: order.discountRate,
  });

const validateOrder = (order) => {
  if (!Number.isInteger(order.id) || order.id <= 0) {
    throw new TypeError("Order ID must be a positive integer.");
  }

  if (typeof order.customer !== "string" || order.customer.trim() === "") {
    throw new TypeError("Customer name must be a non-empty string.");
  }

  if (!Array.isArray(order.items) || order.items.length === 0) {
    throw new TypeError("An order must contain at least one item.");
  }

  if (
    order.items.some(
      (price) => typeof price !== "number" || !Number.isFinite(price) || price < 0
    )
  ) {
    throw new TypeError("Every item price must be a finite non-negative number.");
  }

  if (
    typeof order.discountRate !== "number" ||
    !Number.isFinite(order.discountRate) ||
    order.discountRate < 0 ||
    order.discountRate > 1
  ) {
    throw new TypeError("Discount rate must be between 0 and 1.");
  }
};

const subtotal = (order) =>
  order.items.reduce((total, price) => total + price, 0);

const total = (order) =>
  Number((subtotal(order) * (1 - order.discountRate)).toFixed(2));

const addItem = (order, price) => {
  validateOrder(order);

  if (!Number.isFinite(price) || price < 0) {
    throw new RangeError("Item price must be finite and non-negative.");
  }

  return freezeOrder({
    ...order,
    items: [...order.items, price],
  });
};

const withDiscount = (order, discountRate) => {
  validateOrder(order);

  if (discountRate < 0 || discountRate > 1) {
    throw new RangeError("Discount rate must be between 0 and 1.");
  }

  return freezeOrder({
    ...order,
    discountRate,
  });
};

// Generic higher-order transformation.
const mapWith = (values, operation) => values.map(operation);

// Function composition creates a reusable transformation pipeline.
const compose =
  (...functions) =>
  (initialValue) =>
    functions.reduce(
      (value, currentFunction) => currentFunction(value),
      initialValue
    );

const calculateInvoiceValue = compose(
  (value) => value * 1.18,
  (value) => value + 50,
  (value) => Number(value.toFixed(2))
);

const groupByCustomer = (orders) =>
  orders.reduce((groups, order) => {
    const existing = groups.get(order.customer) ?? [];
    groups.set(order.customer, [...existing, order]);
    return groups;
  }, new Map());

const processOrders = async (orders) => {
  // Promise.resolve models an asynchronous boundary without external
  // dependencies. The data transformation remains deterministic.
  const validatedOrders = await Promise.resolve(
    orders.map((order) => {
      validateOrder(order);
      return freezeOrder(order);
    })
  );

  const highValue = validatedOrders.filter((order) => total(order) >= 1000);

  const totals = mapWith(
    highValue,
    (order) => ({
      id: order.id,
      total: total(order),
    })
  );

  return Object.freeze({
    totals: Object.freeze(totals),
    count: highValue.length,
  });
};

const main = async () => {
  const orders = Object.freeze([
    freezeOrder({
      id: 201,
      customer: "Northwind",
      items: [700, 450],
      discountRate: 0.1,
    }),
    freezeOrder({
      id: 202,
      customer: "Contoso",
      items: [300, 275],
      discountRate: 0.05,
    }),
    freezeOrder({
      id: 203,
      customer: "Northwind",
      items: [1400, 800],
      discountRate: 0.15,
    }),
  ]);

  const modified = addItem(orders[0], 250);
  const repriced = withDiscount(modified, 0.2);

  console.log("Functional JavaScript Order Model");
  console.log("---------------------------------");
  console.log("Original:", orders[0]);
  console.log("Modified:", modified);
  console.log("Repriced total:", total(repriced));

  const result = await processOrders(orders);
  console.log("High-value orders:", result);
  console.log("Invoice transformation:", calculateInvoiceValue(1000));

  const customerGroups = groupByCustomer(orders);
  console.log(
    "Customer group sizes:",
    Object.fromEntries(
      [...customerGroups.entries()].map(([customer, customerOrders]) => [
        customer,
        customerOrders.length,
      ])
    )
  );

  try {
    addItem(orders[0], -20);
  } catch (error) {
    console.log(`Validation failure handled: ${error.message}`);
  }
};

main().catch((error) => {
  console.error(`Processing failed: ${error.message}`);
  process.exitCode = 1;
});
