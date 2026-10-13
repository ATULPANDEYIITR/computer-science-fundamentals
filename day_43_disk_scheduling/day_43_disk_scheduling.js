"use strict";

/*
 * Disk Scheduling in JavaScript
 *
 * The implementation models six scheduling strategies:
 * FCFS, SSTF, SCAN, C-SCAN, LOOK, and C-LOOK.
 *
 * The event-driven portion exposes a small repository-style event stream:
 * request submission, scheduling, and policy evaluation happen as separate
 * events. This makes the example useful for Node.js applications where disk
 * scheduling can be treated as a service component.
 */

class DiskScheduler {
  constructor(diskSize, initialHead) {
    if (!Number.isInteger(diskSize) || diskSize < 2) {
      throw new Error("diskSize must be an integer >= 2");
    }
    if (!Number.isInteger(initialHead) || initialHead < 0 || initialHead >= diskSize) {
      throw new Error("initialHead must be inside the disk");
    }

    this.diskSize = diskSize;
    this.initialHead = initialHead;
  }

  validateRequests(requests) {
    if (!Array.isArray(requests) || requests.length === 0) {
      throw new Error("At least one request is required");
    }

    if (requests.some((r) => !Number.isInteger(r))) {
      throw new Error("Every request must be an integer");
    }

    const invalid = requests.filter(
      (r) => r < 0 || r >= this.diskSize
    );

    if (invalid.length > 0) {
      throw new Error(
        `Requests outside range 0..${this.diskSize - 1}: ${invalid.join(", ")}`
      );
    }

    return [...requests];
  }

  calculateMovement(path) {
    let current = this.initialHead;
    let total = 0;

    for (const cylinder of path) {
      total += Math.abs(cylinder - current);
      current = cylinder;
    }

    return total;
  }

  makeResult(name, order, physicalPath = order) {
    const movement = this.calculateMovement(physicalPath);
    return {
      algorithm: name,
      order,
      physicalPath,
      movement,
      averageSeek: order.length ? movement / order.length : 0,
    };
  }

  fcfs(requests) {
    const valid = this.validateRequests(requests);
    return this.makeResult("FCFS", valid);
  }

  sstf(requests) {
    const remaining = this.validateRequests(requests);
    const order = [];
    let current = this.initialHead;

    while (remaining.length) {
      let selectedIndex = 0;

      for (let i = 1; i < remaining.length; i += 1) {
        const currentDistance = Math.abs(remaining[selectedIndex] - current);
        const candidateDistance = Math.abs(remaining[i] - current);

        if (
          candidateDistance < currentDistance ||
          (candidateDistance === currentDistance &&
            remaining[i] < remaining[selectedIndex])
        ) {
          selectedIndex = i;
        }
      }

      const [selected] = remaining.splice(selectedIndex, 1);
      order.push(selected);
      current = selected;
    }

    return this.makeResult("SSTF", order);
  }

  scan(requests, direction = "right") {
    const valid = this.validateRequests(requests);
    this.validateDirection(direction);

    const left = valid
      .filter((r) => r < this.initialHead)
      .sort((a, b) => b - a);

    const right = valid
      .filter((r) => r >= this.initialHead)
      .sort((a, b) => a - b);

    let path;

    if (direction === "right") {
      path = [...right];

      if (left.length) {
        path.push(this.diskSize - 1);
        path.push(...left);
      }
    } else {
      path = [...left];

      if (right.length) {
        path.push(0);
        path.push(...right);
      }
    }

    return this.makeResult("SCAN", path.filter((r, i) =>
      i === 0 || valid.includes(r)
    ), path);
  }

  cscan(requests, direction = "right") {
    const valid = this.validateRequests(requests);
    this.validateDirection(direction);

    const leftAscending = valid
      .filter((r) => r < this.initialHead)
      .sort((a, b) => a - b);

    const rightAscending = valid
      .filter((r) => r >= this.initialHead)
      .sort((a, b) => a - b);

    let path;

    if (direction === "right") {
      path = [...rightAscending];

      if (leftAscending.length) {
        path.push(this.diskSize - 1, 0);
        path.push(...leftAscending);
      }
    } else {
      const leftDescending = [...leftAscending].reverse();
      const rightDescending = [...rightAscending].reverse();

      path = [...leftDescending];

      if (rightDescending.length) {
        path.push(0, this.diskSize - 1);
        path.push(...rightDescending);
      }
    }

    return this.makeResult("C-SCAN", path.filter((c) => valid.includes(c)), path);
  }

  look(requests, direction = "right") {
    const valid = this.validateRequests(requests);
    this.validateDirection(direction);

    const left = valid
      .filter((r) => r < this.initialHead)
      .sort((a, b) => b - a);

    const right = valid
      .filter((r) => r >= this.initialHead)
      .sort((a, b) => a - b);

    const order = direction === "right"
      ? [...right, ...left]
      : [...left, ...right];

    return this.makeResult("LOOK", order);
  }

  clook(requests, direction = "right") {
    const valid = this.validateRequests(requests);
    this.validateDirection(direction);

    const left = valid
      .filter((r) => r < this.initialHead)
      .sort((a, b) => a - b);

    const right = valid
      .filter((r) => r >= this.initialHead)
      .sort((a, b) => a - b);

    const order = direction === "right"
      ? [...right, ...left]
      : [...left.reverse(), ...right.reverse()];

    return this.makeResult("C-LOOK", order);
  }

  validateDirection(direction) {
    if (!["left", "right"].includes(direction)) {
      throw new Error("Direction must be 'left' or 'right'");
    }
  }

  compare(requests, direction = "right") {
    return [
      this.fcfs(requests),
      this.sstf(requests),
      this.scan(requests, direction),
      this.cscan(requests, direction),
      this.look(requests, direction),
      this.clook(requests, direction),
    ];
  }
}


class DiskSchedulingService {
  constructor(scheduler) {
    this.scheduler = scheduler;
    this.listeners = new Map();
  }

  on(eventName, listener) {
    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, []);
    }
    this.listeners.get(eventName).push(listener);
  }

  emit(eventName, payload) {
    const listeners = this.listeners.get(eventName) || [];
    for (const listener of listeners) {
      listener(payload);
    }
  }

  async schedule(requests, direction) {
    this.emit("requests.received", { count: requests.length });

    // Promise.resolve creates an asynchronous service boundary without
    // requiring an external package or a real disk device.
    const results = await Promise.resolve(
      this.scheduler.compare(requests, direction)
    );

    const best = [...results].sort((a, b) => a.movement - b.movement)[0];

    this.emit("schedule.completed", {
      algorithm: best.algorithm,
      movement: best.movement,
    });

    return results;
  }
}


function printResults(results) {
  console.log("\nAlgorithm comparison");
  console.log("-".repeat(70));

  const sorted = [...results].sort((a, b) => a.movement - b.movement);

  for (const result of sorted) {
    console.log(
      `${result.algorithm.padEnd(10)} ` +
      `movement=${String(result.movement).padStart(4)} ` +
      `average=${result.averageSeek.toFixed(2)} ` +
      `order=${result.order.join(" -> ")}`
    );
  }
}


async function main() {
  const scheduler = new DiskScheduler(200, 53);
  const service = new DiskSchedulingService(scheduler);

  service.on("requests.received", ({ count }) => {
    console.log(`Received ${count} disk requests.`);
  });

  service.on("schedule.completed", ({ algorithm, movement }) => {
    console.log(
      `Best movement for this workload: ${algorithm} (${movement} cylinders).`
    );
  });

  const requests = [98, 183, 37, 122, 14, 124, 65, 67];
  const direction = "right";

  console.log("Disk Scheduling Event-Driven Demonstration");
  console.log(`Head=${scheduler.initialHead}, disk=0..${scheduler.diskSize - 1}`);
  console.log(`Requests=${requests.join(", ")}`);
  console.log(`Direction=${direction}`);

  const results = await service.schedule(requests, direction);
  printResults(results);

  console.log("\nEdge-case validation");

  try {
    scheduler.fcfs([10, 250]);
  } catch (error) {
    console.log(`Invalid request rejected: ${error.message}`);
  }

  try {
    scheduler.look([10, 20], "up");
  } catch (error) {
    console.log(`Invalid direction rejected: ${error.message}`);
  }
}


main().catch((error) => {
  console.error(`Scheduling service failed: ${error.message}`);
  process.exitCode = 1;
});
