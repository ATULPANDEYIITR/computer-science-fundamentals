"use strict";

/*
 * Scope, binding, lifetime, and JavaScript's type system.
 *
 * This file deliberately uses JavaScript-specific mechanisms:
 * lexical environments, closures, var/let/const differences,
 * object references, garbage-collection eligibility, prototypes,
 * symbols, runtime type inspection, coercion, promises, and
 * event-loop scheduling.
 */

// ============================================================
// Lexical scope and shadowing
// ============================================================

const applicationName = "Repository Analyzer";

function lexicalScopeDemo() {
    const functionValue = "function scope";

    if (true) {
        const blockValue = "block scope";
        let mutableBlockValue = 10;

        console.log(applicationName);
        console.log(functionValue);
        console.log(blockValue);

        mutableBlockValue += 5;
        console.log("Updated block value:", mutableBlockValue);
    }

    // blockValue and mutableBlockValue are inaccessible here.
    console.log("Function value remains:", functionValue);
}

function varScopeDemo() {
    if (true) {
        var functionScoped = "visible outside the block";
    }

    // var is function-scoped rather than block-scoped.
    console.log("var behavior:", functionScoped);
}

// ============================================================
// Binding and closures
// ============================================================

function createCounter(start = 0) {
    let current = start;

    return {
        increment() {
            current += 1;
            return current;
        },
        value() {
            return current;
        }
    };
}

function closureBindingDemo() {
    const counter = createCounter(10);

    console.log("Closure state:", counter.value());
    console.log("Closure increment:", counter.increment());
    console.log("Closure state after increment:", counter.value());

    const handlers = [];

    for (let index = 0; index < 3; index += 1) {
        // let creates a new lexical binding for each loop iteration.
        handlers.push(() => index);
    }

    console.log("Per-iteration lexical bindings:", handlers.map(fn => fn()));
}

// ============================================================
// var versus let in loop bindings
// ============================================================

function loopBindingComparison() {
    const varHandlers = [];

    for (var index = 0; index < 3; index += 1) {
        varHandlers.push(() => index);
    }

    const letHandlers = [];

    for (let index = 0; index < 3; index += 1) {
        letHandlers.push(() => index);
    }

    console.log("var loop closures:", varHandlers.map(fn => fn()));
    console.log("let loop closures:", letHandlers.map(fn => fn()));
}

// ============================================================
// JavaScript dynamic typing and coercion
// ============================================================

function dynamicTypingDemo() {
    let value = 42;
    console.log("Number:", typeof value, value);

    value = "42";
    console.log("String:", typeof value, value);

    value = { id: 42 };
    console.log("Object:", typeof value, value);

    console.log("Loose equality:", 42 == "42");
    console.log("Strict equality:", 42 === "42");

    // Strict equality avoids implicit numeric/string conversion.
}

// ============================================================
// Runtime validation
// ============================================================

function requireFiniteNumber(value, fieldName) {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        throw new TypeError(`${fieldName} must be a finite number`);
    }

    return value;
}

function calculateRisk(score, threshold) {
    requireFiniteNumber(score, "score");
    requireFiniteNumber(threshold, "threshold");

    return score >= threshold ? "HIGH" : "LOW";
}

// ============================================================
// Structural behavior through duck typing
// ============================================================

function renderEntity(entity) {
    if (
        entity === null ||
        typeof entity !== "object" ||
        typeof entity.describe !== "function"
    ) {
        throw new TypeError("entity must provide describe()");
    }

    return entity.describe();
}

const repository = {
    name: "payment-service",
    describe() {
        return `Repository: ${this.name}`;
    }
};

const pullRequest = {
    number: 42,
    describe() {
        return `Pull Request #${this.number}`;
    }
};

function structuralTypingDemo() {
    console.log(renderEntity(repository));
    console.log(renderEntity(pullRequest));

    try {
        renderEntity({ name: "invalid" });
    } catch (error) {
        console.log("Structural validation failure:", error.message);
    }
}

// ============================================================
// Prototypes and property lookup
// ============================================================

function prototypeLookupDemo() {
    const policy = {
        requiredApprovals: 2
    };

    const repositoryPolicy = Object.create(policy);
    repositoryPolicy.requiredChecks = 3;

    console.log(
        "Inherited property:",
        repositoryPolicy.requiredApprovals
    );

    console.log(
        "Own property:",
        Object.hasOwn(repositoryPolicy, "requiredChecks")
    );

    console.log(
        "Inherited property is not own:",
        Object.hasOwn(repositoryPolicy, "requiredApprovals")
    );
}

// ============================================================
// Symbols demonstrate unique property identity
// ============================================================

const internalIdentifier = Symbol("internalIdentifier");

function symbolBindingDemo() {
    const record = {
        name: "production",
        [internalIdentifier]: 9182
    };

    console.log("Public property:", record.name);
    console.log("Symbol property:", record[internalIdentifier]);
}

// ============================================================
// Lifetime and garbage-collection eligibility
// ============================================================

function lifetimeDemo() {
    let temporaryObject = {
        payload: new Array(1000).fill("data")
    };

    const retainedReference = temporaryObject;

    // Removing one reference does not make the object collectible because
    // retainedReference still reaches it.
    temporaryObject = null;

    console.log(
        "Object remains reachable:",
        retainedReference.payload.length
    );

    /*
     * JavaScript does not provide a deterministic destructor call.
     * Once no reachable reference exists, an object becomes eligible for
     * garbage collection, but the exact collection time is implementation-
     * dependent. External resources such as files or sockets should use
     * explicit close/dispose APIs when the platform provides them.
     */
}

// ============================================================
// Explicit resource lifetime model
// ============================================================

class ManagedConnection {
    #closed = false;

    constructor(name) {
        this.name = name;
    }

    close() {
        if (this.#closed) {
            throw new Error(`Connection ${this.name} is already closed`);
        }

        this.#closed = true;
        console.log(`Closed ${this.name}`);
    }

    execute(query) {
        if (this.#closed) {
            throw new Error("Cannot execute against a closed connection");
        }

        return `Executed: ${query}`;
    }
}

function explicitLifetimeDemo() {
    const connection = new ManagedConnection("analytics-db");

    console.log(connection.execute("SELECT 1"));

    try {
        connection.close();
        connection.close();
    } catch (error) {
        console.log("Invalid lifetime transition:", error.message);
    }
}

// ============================================================
// Type tags, null, arrays, and objects
// ============================================================

function runtimeTypeInspection() {
    const values = [
        42,
        "text",
        true,
        undefined,
        null,
        10n,
        Symbol("x"),
        [],
        {},
        () => {}
    ];

    for (const value of values) {
        console.log(
            String(value),
            "=> typeof:",
            typeof value,
            "Array:",
            Array.isArray(value)
        );
    }
}

// ============================================================
// Asynchronous binding and event-loop behavior
// ============================================================

function asynchronousBindingDemo() {
    return new Promise(resolve => {
        const state = { phase: "scheduled" };

        setTimeout(() => {
            state.phase = "callback";
            console.log("Timer callback sees current object state:", state);
            resolve(state.phase);
        }, 0);

        console.log("Synchronous code runs before timer callback");
    });
}

// ============================================================
// Immutable binding versus mutable object
// ============================================================

function constBindingDemo() {
    const configuration = {
        retries: 3
    };

    // const prevents rebinding the variable, but it does not freeze the object.
    configuration.retries = 5;

    console.log("Mutated object through const binding:", configuration);

    try {
        // The following would fail:
        // configuration = {};
        throw new TypeError("Rebinding a const variable is prohibited");
    } catch (error) {
        console.log("Binding rule:", error.message);
    }
}

// ============================================================
// Main
// ============================================================

async function main() {
    console.log("\n=== Lexical scope ===");
    lexicalScopeDemo();
    varScopeDemo();

    console.log("\n=== Binding and closures ===");
    closureBindingDemo();
    loopBindingComparison();

    console.log("\n=== Dynamic typing ===");
    dynamicTypingDemo();

    console.log("\n=== Runtime type validation ===");
    console.log("Risk:", calculateRisk(87, 70));

    try {
        calculateRisk("87", 70);
    } catch (error) {
        console.log("Validation failure:", error.message);
    }

    console.log("\n=== Structural behavior ===");
    structuralTypingDemo();

    console.log("\n=== Prototype lookup ===");
    prototypeLookupDemo();

    console.log("\n=== Symbol identity ===");
    symbolBindingDemo();

    console.log("\n=== Object lifetime ===");
    lifetimeDemo();
    explicitLifetimeDemo();

    console.log("\n=== Runtime type inspection ===");
    runtimeTypeInspection();

    console.log("\n=== Const binding ===");
    constBindingDemo();

    console.log("\n=== Event-loop lifetime and binding ===");
    await asynchronousBindingDemo();

    console.log(
        "\nJavaScript combines lexical scope, runtime binding, " +
        "garbage-collected object lifetime, and dynamic runtime typing."
    );
}

main().catch(error => {
    console.error("Fatal execution error:", error);
    process.exitCode = 1;
});
