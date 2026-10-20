"use strict";

const fs = require("node:fs/promises");

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class Employee {
    #salary;

    constructor(id, name, salary) {
        if (!Number.isInteger(id) || id <= 0) {
            throw new ValidationError("Employee ID must be a positive integer.");
        }
        if (typeof name !== "string" || name.trim() === "") {
            throw new ValidationError("Employee name cannot be empty.");
        }
        if (!Number.isFinite(salary) || salary < 0) {
            throw new ValidationError("Salary must be a non-negative number.");
        }

        this.id = id;
        this.name = name.trim();
        this.#salary = salary;
    }

    get salary() {
        return this.#salary;
    }

    set salary(value) {
        if (!Number.isFinite(value) || value < 0) {
            throw new ValidationError("Salary must be a non-negative number.");
        }
        this.#salary = value;
    }

    describe() {
        return `${this.name} earns ${this.#salary.toFixed(2)}`;
    }

    calculateBonus() {
        return this.#salary * 0.05;
    }
}

class Engineer extends Employee {
    constructor(id, name, salary, specialty) {
        super(id, name, salary);

        if (typeof specialty !== "string" || specialty.trim() === "") {
            throw new ValidationError("Engineering specialty is required.");
        }

        this.specialty = specialty.trim();
    }

    calculateBonus() {
        return this.salary * 0.10;
    }

    describe() {
        return `${super.describe()} as a ${this.specialty} engineer`;
    }
}

class Manager extends Employee {
    constructor(id, name, salary, teamSize) {
        super(id, name, salary);

        if (!Number.isInteger(teamSize) || teamSize < 0) {
            throw new ValidationError("Team size must be a non-negative integer.");
        }

        this.teamSize = teamSize;
    }

    calculateBonus() {
        return this.salary * 0.08 + this.teamSize * 500;
    }

    describe() {
        return `${super.describe()} and manages ${this.teamSize} employees`;
    }
}

class PayrollService {
    constructor(taxRate = 0.20) {
        if (!Number.isFinite(taxRate) || taxRate < 0 || taxRate >= 1) {
            throw new ValidationError("Tax rate must be between 0 and 1.");
        }
        this.taxRate = taxRate;
    }

    calculateNetPay(employee) {
        if (!(employee instanceof Employee)) {
            throw new ValidationError("Expected an Employee object.");
        }

        const gross = employee.salary + employee.calculateBonus();
        return gross * (1 - this.taxRate);
    }

    async exportReport(employees, filename) {
        if (!Array.isArray(employees) || employees.length === 0) {
            throw new ValidationError("At least one employee is required.");
        }

        const lines = employees.map((employee) => {
            const netPay = this.calculateNetPay(employee);
            return `${employee.id},${employee.name},${employee.constructor.name},${netPay.toFixed(2)}`;
        });

        try {
            await fs.writeFile(filename, lines.join("\n") + "\n", "utf8");
        } catch (error) {
            throw new Error(`Unable to write payroll report: ${error.message}`);
        }
    }
}

function inspectEmployee(employee) {
    if (!(employee instanceof Employee)) {
        throw new ValidationError("Object is not an Employee.");
    }

    return {
        description: employee.describe(),
        bonus: employee.calculateBonus(),
    };
}

async function main() {
    const employees = [
        new Engineer(101, "Asha", 80000, "Backend"),
        new Manager(102, "Daniel", 95000, 6),
        new Engineer(103, "Leena", 72000, "Security"),
    ];

    const payroll = new PayrollService(0.22);

    console.log("Polymorphic employee behavior:");

    for (const employee of employees) {
        const result = inspectEmployee(employee);
        console.log(result.description);
        console.log(`Bonus: ${result.bonus.toFixed(2)}`);
        console.log(`Net pay: ${payroll.calculateNetPay(employee).toFixed(2)}`);
    }

    // Private class state cannot be modified directly through #salary.
    try {
        employees[0].salary = -1;
    } catch (error) {
        console.log(`Validation failure: ${error.message}`);
    }

    employees[0].salary = 82000;

    const totalNetPay = employees.reduce(
        (total, employee) => total + payroll.calculateNetPay(employee),
        0
    );

    console.log(`Total net payroll: ${totalNetPay.toFixed(2)}`);

    await payroll.exportReport(employees, "payroll_report.csv");
    console.log("Payroll report written successfully.");
}

main().catch((error) => {
    console.error(`Application failure: ${error.message}`);
    process.exitCode = 1;
});
