"use strict";

/*
 * Error and Exception Handling
 *
 * This Node.js program models a deployment configuration service.
 * It demonstrates:
 * - custom Error subclasses
 * - synchronous validation
 * - asynchronous failures
 * - exception propagation with async/await
 * - error classification
 * - retrying only transient failures
 * - safe error responses that avoid leaking internal details
 * - centralized event-driven error reporting
 */

const { EventEmitter } = require("node:events");

class ValidationError extends Error {
    constructor(message, field) {
        super(message);
        this.name = "ValidationError";
        this.field = field;
    }
}

class ConfigurationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ConfigurationError";
    }
}

class StorageError extends Error {
    constructor(message, cause = undefined) {
        super(message, { cause });
        this.name = "StorageError";
    }
}

class NotFoundError extends Error {
    constructor(message) {
        super(message);
        this.name = "NotFoundError";
    }
}

function validateRepository(input) {
    if (typeof input !== "object" || input === null) {
        throw new ValidationError("Repository must be an object.", "repository");
    }

    const required = ["name", "owner", "defaultBranch"];

    for (const field of required) {
        if (
            typeof input[field] !== "string" ||
            input[field].trim().length === 0
        ) {
            throw new ValidationError(
                `${field} must be a non-empty string.`,
                field
            );
        }
    }

    return Object.freeze({
        name: input.name.trim(),
        owner: input.owner.trim(),
        defaultBranch: input.defaultBranch.trim()
    });
}

class RepositoryStore extends EventEmitter {
    constructor() {
        super();
        this.repositories = new Map();
    }

    async save(repository) {
        await Promise.resolve();

        if (this.repositories.has(repository.name)) {
            throw new StorageError(
                `Repository ${repository.name} already exists.`
            );
        }

        this.repositories.set(repository.name, repository);
        this.emit("saved", repository.name);

        return repository;
    }

    async get(name) {
        await Promise.resolve();

        const repository = this.repositories.get(name);

        if (!repository) {
            throw new NotFoundError(`Repository ${name} was not found.`);
        }

        return repository;
    }

    async delete(name) {
        await Promise.resolve();

        if (!this.repositories.delete(name)) {
            throw new NotFoundError(`Repository ${name} was not found.`);
        }

        this.emit("deleted", name);
    }
}

function isTransient(error) {
    return error instanceof StorageError;
}

async function retry(operation, attempts = 3) {
    if (!Number.isInteger(attempts) || attempts <= 0) {
        throw new ValidationError(
            "Attempts must be a positive integer.",
            "attempts"
        );
    }

    let lastError;

    for (let attempt = 1; attempt <= attempts; attempt++) {
        try {
            return await operation();
        } catch (error) {
            lastError = error;

            if (!isTransient(error) || attempt === attempts) {
                throw error;
            }

            await new Promise((resolve) => setTimeout(resolve, 10));
        }
    }

    throw lastError;
}

function toSafeHttpResponse(error) {
    if (error instanceof ValidationError) {
        return {
            status: 400,
            body: {
                error: "validation_failed",
                message: error.message,
                field: error.field
            }
        };
    }

    if (error instanceof NotFoundError) {
        return {
            status: 404,
            body: {
                error: "not_found",
                message: error.message
            }
        };
    }

    if (error instanceof ConfigurationError) {
        return {
            status: 500,
            body: {
                error: "configuration_error",
                message: "The service is incorrectly configured."
            }
        };
    }

    return {
        status: 500,
        body: {
            error: "internal_error",
            message: "The operation could not be completed."
        }
    };
}

async function loadConfiguration(environment) {
    const value = environment.REPOSITORY_OWNER;

    if (typeof value !== "string" || value.trim() === "") {
        throw new ConfigurationError("REPOSITORY_OWNER is not configured.");
    }

    return value.trim();
}

async function main() {
    const store = new RepositoryStore();

    store.on("saved", (name) => {
        console.log(`event: repository saved -> ${name}`);
    });

    store.on("deleted", (name) => {
        console.log(`event: repository deleted -> ${name}`);
    });

    console.log("Validation:");

    try {
        validateRepository({
            name: "",
            owner: "platform",
            defaultBranch: "main"
        });
    } catch (error) {
        console.log(toSafeHttpResponse(error));
    }

    const repository = validateRepository({
        name: "billing-service",
        owner: "platform-team",
        defaultBranch: "main"
    });

    console.log("\nSuccessful asynchronous workflow:");

    try {
        await store.save(repository);
        const loaded = await store.get(repository.name);
        console.log(loaded);
    } catch (error) {
        console.log(toSafeHttpResponse(error));
    }

    console.log("\nException propagation:");

    async function outerWorkflow() {
        return store.get("missing-service");
    }

    try {
        await outerWorkflow();
    } catch (error) {
        console.log(toSafeHttpResponse(error));
    }

    console.log("\nRetry classification:");

    let failures = 0;

    try {
        const result = await retry(async () => {
            failures++;

            if (failures < 3) {
                throw new StorageError("Temporary storage failure.");
            }

            return "operation succeeded";
        });

        console.log(result);
    } catch (error) {
        console.log(toSafeHttpResponse(error));
    }

    console.log("\nConfiguration failure:");

    try {
        await loadConfiguration({});
    } catch (error) {
        console.log(toSafeHttpResponse(error));
    }

    console.log("\nCleanup:");

    try {
        await store.delete(repository.name);
    } catch (error) {
        console.log(toSafeHttpResponse(error));
    }
}

main().catch((error) => {
    // The final boundary prevents an unhandled rejection from escaping.
    console.error("Fatal application failure:", error.message);
    process.exitCode = 1;
});
