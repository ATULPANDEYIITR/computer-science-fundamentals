'use strict';

/*
 * Process Scheduling Laboratory
 *
 * This Node.js program models scheduling as an event-driven system.
 * It focuses on mechanisms that are particularly useful in JavaScript:
 *
 * - immutable process descriptions
 * - objects and Maps for scheduling state
 * - queue-based Round Robin behavior
 * - event-oriented preemption
 * - policy functions
 * - validation and structured results
 *
 * Algorithms:
 * FCFS, SJF, SRTF, non-preemptive Priority,
 * preemptive Priority, and Round Robin.
 */

class Process {
    constructor(id, arrival, burst, priority = 0) {
        if (typeof id !== 'string' || id.trim() === '') {
            throw new TypeError('Process ID must be a non-empty string.');
        }

        if (!Number.isInteger(arrival) || arrival < 0) {
            throw new RangeError('Arrival time must be a non-negative integer.');
        }

        if (!Number.isInteger(burst) || burst <= 0) {
            throw new RangeError('Burst time must be a positive integer.');
        }

        if (!Number.isInteger(priority)) {
            throw new TypeError('Priority must be an integer.');
        }

        this.id = id;
        this.arrival = arrival;
        this.burst = burst;
        this.priority = priority;
    }
}

function validateProcesses(processes) {
    if (!Array.isArray(processes) || processes.length === 0) {
        throw new Error('At least one process is required.');
    }

    const ids = new Set();

    for (const process of processes) {
        if (!(process instanceof Process)) {
            throw new TypeError('Every workload entry must be a Process.');
        }

        if (ids.has(process.id)) {
            throw new Error(`Duplicate process ID: ${process.id}`);
        }

        ids.add(process.id);
    }

    return [...processes].sort(
        (a, b) => a.arrival - b.arrival || a.id.localeCompare(b.id)
    );
}

function appendInterval(timeline, start, end, processId) {
    if (end <= start) {
        return;
    }

    const previous = timeline[timeline.length - 1];

    if (
        previous &&
        previous.end === start &&
        previous.processId === processId
    ) {
        previous.end = end;
        return;
    }

    timeline.push({ start, end, processId });
}

function createResult(
    algorithm,
    processes,
    completion,
    firstStart,
    timeline
) {
    let contextSwitches = 0;
    let previousProcess = null;

    for (const interval of timeline) {
        if (interval.processId === null) {
            previousProcess = null;
            continue;
        }

        if (
            previousProcess !== null &&
            previousProcess !== interval.processId
        ) {
            contextSwitches++;
        }

        previousProcess = interval.processId;
    }

    const rows = processes.map((process) => {
        const completionTime = completion.get(process.id);
        const turnaround = completionTime - process.arrival;
        const waiting = turnaround - process.burst;
        const response = firstStart.get(process.id) - process.arrival;

        return {
            id: process.id,
            arrival: process.arrival,
            burst: process.burst,
            priority: process.priority,
            completion: completionTime,
            turnaround,
            waiting,
            response
        };
    });

    const busyTime = processes.reduce(
        (sum, process) => sum + process.burst,
        0
    );

    const makespan = Math.max(...completion.values());

    return {
        algorithm,
        rows,
        timeline,
        contextSwitches,
        cpuUtilization: makespan === 0 ? 0 : (busyTime / makespan) * 100,
        throughput: processes.length / makespan
    };
}

function average(rows, field) {
    return rows.reduce((sum, row) => sum + row[field], 0) / rows.length;
}

function fcfs(processes) {
    const jobs = validateProcesses(processes);
    const completion = new Map();
    const firstStart = new Map();
    const timeline = [];

    let time = 0;

    for (const process of jobs) {
        if (time < process.arrival) {
            appendInterval(timeline, time, process.arrival, null);
            time = process.arrival;
        }

        if (!firstStart.has(process.id)) {
            firstStart.set(process.id, time);
        }

        const end = time + process.burst;

        appendInterval(timeline, time, end, process.id);
        completion.set(process.id, end);
        time = end;
    }

    return createResult(
        'FCFS',
        jobs,
        completion,
        firstStart,
        timeline
    );
}

function sjf(processes) {
    const jobs = validateProcesses(processes);
    const remaining = [...jobs];
    const completion = new Map();
    const firstStart = new Map();
    const timeline = [];

    let time = 0;

    while (remaining.length > 0) {
        const available = remaining.filter(
            (process) => process.arrival <= time
        );

        if (available.length === 0) {
            const nextArrival = Math.min(
                ...remaining.map((process) => process.arrival)
            );

            appendInterval(timeline, time, nextArrival, null);
            time = nextArrival;
            continue;
        }

        available.sort(
            (a, b) =>
                a.burst - b.burst ||
                a.arrival - b.arrival ||
                a.id.localeCompare(b.id)
        );

        const process = available[0];
        const index = remaining.indexOf(process);

        remaining.splice(index, 1);

        firstStart.set(process.id, time);

        const end = time + process.burst;
        appendInterval(timeline, time, end, process.id);

        completion.set(process.id, end);
        time = end;
    }

    return createResult(
        'SJF',
        jobs,
        completion,
        firstStart,
        timeline
    );
}

function srtf(processes) {
    const jobs = validateProcesses(processes);
    const remaining = new Map(
        jobs.map((process) => [process.id, process.burst])
    );

    const completion = new Map();
    const firstStart = new Map();
    const timeline = [];

    let time = 0;
    let completed = 0;

    while (completed < jobs.length) {
        const available = jobs.filter(
            (process) =>
                process.arrival <= time &&
                remaining.get(process.id) > 0
        );

        if (available.length === 0) {
            const future = jobs.filter(
                (process) =>
                    remaining.get(process.id) > 0 &&
                    process.arrival > time
            );

            const nextArrival = Math.min(
                ...future.map((process) => process.arrival)
            );

            appendInterval(timeline, time, nextArrival, null);
            time = nextArrival;
            continue;
        }

        available.sort(
            (a, b) =>
                remaining.get(a.id) - remaining.get(b.id) ||
                a.arrival - b.arrival ||
                a.id.localeCompare(b.id)
        );

        const process = available[0];

        if (!firstStart.has(process.id)) {
            firstStart.set(process.id, time);
        }

        const futureArrivals = jobs
            .filter(
                (candidate) =>
                    candidate.arrival > time &&
                    remaining.get(candidate.id) > 0
            )
            .map((candidate) => candidate.arrival);

        const nextArrival =
            futureArrivals.length > 0
                ? Math.min(...futureArrivals)
                : Infinity;

        const currentRemaining = remaining.get(process.id);
        const finishTime = time + currentRemaining;
        const runUntil = Math.min(finishTime, nextArrival);

        const elapsed = runUntil - time;

        appendInterval(timeline, time, runUntil, process.id);

        remaining.set(
            process.id,
            currentRemaining - elapsed
        );

        time = runUntil;

        if (remaining.get(process.id) === 0) {
            completion.set(process.id, time);
            completed++;
        }
    }

    return createResult(
        'SRTF',
        jobs,
        completion,
        firstStart,
        timeline
    );
}

function priorityNonPreemptive(processes) {
    const jobs = validateProcesses(processes);
    const remaining = [...jobs];
    const completion = new Map();
    const firstStart = new Map();
    const timeline = [];

    let time = 0;

    while (remaining.length > 0) {
        const available = remaining.filter(
            (process) => process.arrival <= time
        );

        if (available.length === 0) {
            const nextArrival = Math.min(
                ...remaining.map((process) => process.arrival)
            );

            appendInterval(timeline, time, nextArrival, null);
            time = nextArrival;
            continue;
        }

        available.sort(
            (a, b) =>
                a.priority - b.priority ||
                a.arrival - b.arrival ||
                a.id.localeCompare(b.id)
        );

        const process = available[0];
        remaining.splice(remaining.indexOf(process), 1);

        firstStart.set(process.id, time);

        const end = time + process.burst;

        appendInterval(timeline, time, end, process.id);
        completion.set(process.id, end);

        time = end;
    }

    return createResult(
        'Priority (Non-Preemptive)',
        jobs,
        completion,
        firstStart,
        timeline
    );
}

function priorityPreemptive(processes) {
    const jobs = validateProcesses(processes);
    const remaining = new Map(
        jobs.map((process) => [process.id, process.burst])
    );

    const completion = new Map();
    const firstStart = new Map();
    const timeline = [];

    let time = 0;
    let completed = 0;

    while (completed < jobs.length) {
        const available = jobs.filter(
            (process) =>
                process.arrival <= time &&
                remaining.get(process.id) > 0
        );

        if (available.length === 0) {
            const future = jobs.filter(
                (process) =>
                    remaining.get(process.id) > 0 &&
                    process.arrival > time
            );

            const nextArrival = Math.min(
                ...future.map((process) => process.arrival)
            );

            appendInterval(timeline, time, nextArrival, null);
            time = nextArrival;
            continue;
        }

        available.sort(
            (a, b) =>
                a.priority - b.priority ||
                a.arrival - b.arrival ||
                a.id.localeCompare(b.id)
        );

        const process = available[0];

        if (!firstStart.has(process.id)) {
            firstStart.set(process.id, time);
        }

        const futureArrivals = jobs
            .filter(
                (candidate) =>
                    candidate.arrival > time &&
                    remaining.get(candidate.id) > 0
            )
            .map((candidate) => candidate.arrival);

        const nextArrival =
            futureArrivals.length > 0
                ? Math.min(...futureArrivals)
                : Infinity;

        const currentRemaining = remaining.get(process.id);
        const finishTime = time + currentRemaining;
        const runUntil = Math.min(finishTime, nextArrival);
        const elapsed = runUntil - time;

        appendInterval(timeline, time, runUntil, process.id);

        remaining.set(
            process.id,
            currentRemaining - elapsed
        );

        time = runUntil;

        if (remaining.get(process.id) === 0) {
            completion.set(process.id, time);
            completed++;
        }
    }

    return createResult(
        'Priority (Preemptive)',
        jobs,
        completion,
        firstStart,
        timeline
    );
}

function roundRobin(processes, quantum) {
    if (!Number.isInteger(quantum) || quantum <= 0) {
        throw new RangeError(
            'Round Robin quantum must be a positive integer.'
        );
    }

    const jobs = validateProcesses(processes);

    const remaining = new Map(
        jobs.map((process) => [process.id, process.burst])
    );

    const completion = new Map();
    const firstStart = new Map();
    const timeline = [];

    const queue = [];
    let index = 0;
    let time = 0;
    let completed = 0;

    while (completed < jobs.length) {
        while (
            index < jobs.length &&
            jobs[index].arrival <= time
        ) {
            queue.push(jobs[index]);
            index++;
        }

        if (queue.length === 0) {
            const nextArrival = jobs[index].arrival;

            appendInterval(timeline, time, nextArrival, null);
            time = nextArrival;
            continue;
        }

        const process = queue.shift();

        if (remaining.get(process.id) <= 0) {
            continue;
        }

        if (!firstStart.has(process.id)) {
            firstStart.set(process.id, time);
        }

        const runTime = Math.min(
            quantum,
            remaining.get(process.id)
        );

        const end = time + runTime;

        appendInterval(timeline, time, end, process.id);

        while (
            index < jobs.length &&
            jobs[index].arrival <= end
        ) {
            queue.push(jobs[index]);
            index++;
        }

        remaining.set(
            process.id,
            remaining.get(process.id) - runTime
        );

        time = end;

        if (remaining.get(process.id) === 0) {
            completion.set(process.id, time);
            completed++;
        } else {
            queue.push(process);
        }
    }

    return createResult(
        `Round Robin (q=${quantum})`,
        jobs,
        completion,
        firstStart,
        timeline
    );
}

function printResult(result) {
    console.log(`\n${result.algorithm}`);
    console.log('-'.repeat(82));

    console.log(
        'Timeline:',
        result.timeline
            .map(
                ({ start, end, processId }) =>
                    `[${start},${end}) ${processId ?? 'IDLE'}`
            )
            .join(' | ')
    );

    console.table(result.rows);

    console.log(
        `Average waiting time : ${average(result.rows, 'waiting').toFixed(2)}`
    );
    console.log(
        `Average turnaround   : ${average(result.rows, 'turnaround').toFixed(2)}`
    );
    console.log(
        `Average response     : ${average(result.rows, 'response').toFixed(2)}`
    );
    console.log(
        `CPU utilization      : ${result.cpuUtilization.toFixed(2)}%`
    );
    console.log(
        `Throughput           : ${result.throughput.toFixed(4)} processes/unit`
    );
    console.log(
        `Context switches     : ${result.contextSwitches}`
    );
}

function compare(results) {
    console.log('\nScheduling comparison');
    console.log('-'.repeat(100));

    console.table(
        results.map((result) => ({
            Algorithm: result.algorithm,
            AvgWaiting: Number(
                average(result.rows, 'waiting').toFixed(2)
            ),
            AvgTurnaround: Number(
                average(result.rows, 'turnaround').toFixed(2)
            ),
            AvgResponse: Number(
                average(result.rows, 'response').toFixed(2)
            ),
            CPUUtilization: Number(
                result.cpuUtilization.toFixed(2)
            ),
            Throughput: Number(
                result.throughput.toFixed(4)
            ),
            ContextSwitches: result.contextSwitches
        }))
    );
}

function demonstrateEventDrivenPreemption() {
    /*
     * The workload deliberately introduces a short job after a long
     * job has started. SRTF must reconsider the CPU choice at arrival.
     */
    const workload = [
        new Process('COMPILER', 0, 10, 4),
        new Process('REQUEST', 2, 2, 2),
        new Process('CACHE', 4, 3, 1)
    ];

    console.log('\nEvent-driven preemption');
    printResult(sjf(workload));
    printResult(srtf(workload));
}

function demonstrateQueueSemantics() {
    /*
     * Round Robin uses FIFO queue behavior. Newly arrived work is
     * appended while a running process remains at the CPU.
     */
    const workload = [
        new Process('UI', 0, 5, 2),
        new Process('WORKER-A', 0, 4, 2),
        new Process('WORKER-B', 1, 3, 2)
    ];

    printResult(roundRobin(workload, 2));
}

function demonstrateValidation() {
    console.log('\nValidation');

    const cases = [
        () => new Process('', 0, 3),
        () => new Process('NEGATIVE', -1, 3),
        () => new Process('ZERO-BURST', 0, 0),
        () => roundRobin(
            [new Process('P1', 0, 3)],
            0
        )
    ];

    for (const test of cases) {
        try {
            test();
        } catch (error) {
            console.log(`${error.name}: ${error.message}`);
        }
    }
}

function main() {
    const workload = [
        new Process('P1', 0, 8, 2),
        new Process('P2', 1, 4, 1),
        new Process('P3', 2, 2, 3),
        new Process('P4', 3, 6, 2),
        new Process('P5', 5, 3, 1)
    ];

    console.log('PROCESS SCHEDULING LABORATORY');
    console.log('='.repeat(82));

    console.table(
        workload.map((process) => ({
            PID: process.id,
            Arrival: process.arrival,
            Burst: process.burst,
            Priority: process.priority
        }))
    );

    const results = [
        fcfs(workload),
        sjf(workload),
        srtf(workload),
        priorityNonPreemptive(workload),
        priorityPreemptive(workload),
        roundRobin(workload, 3)
    ];

    for (const result of results) {
        printResult(result);
    }

    compare(results);
    demonstrateEventDrivenPreemption();
    demonstrateQueueSemantics();
    demonstrateValidation();
}

main();
