"use strict";

/*
 * File Systems in Node.js
 *
 * Demonstrates:
 * - paths and directory trees
 * - asynchronous and synchronous file operations
 * - metadata and permissions
 * - streaming I/O
 * - atomic replacement
 * - integrity checks
 * - recursive inventory
 * - safe path validation
 * - symbolic links
 *
 * Run with Node.js 18+.
 */

const fs = require("node:fs");
const fsp = require("node:fs/promises");
const path = require("node:path");
const crypto = require("node:crypto");
const os = require("node:os");
const { pipeline } = require("node:stream/promises");

function heading(title) {
    console.log(`\n${"=".repeat(72)}\n${title}\n${"=".repeat(72)}`);
}

async function createWorkspace() {
    return fsp.mkdtemp(path.join(os.tmpdir(), "filesystem-lab-"));
}

async function ensureParent(filePath) {
    await fsp.mkdir(path.dirname(filePath), { recursive: true });
}

async function demonstratePaths(root) {
    heading("Paths and directory structure");

    const report = path.join(root, "documents", "reports", "quarterly.txt");
    await ensureParent(report);
    await fsp.writeFile(report, "Revenue: 125000\nCost: 73000\n", "utf8");

    console.log("Root:", root);
    console.log("Absolute:", path.resolve(report));
    console.log("Directory:", path.dirname(report));
    console.log("Filename:", path.basename(report));
    console.log("Extension:", path.extname(report));

    const entries = await fsp.readdir(root, { recursive: true });
    for (const entry of entries) {
        console.log(entry);
    }
}

async function demonstrateOperations(root) {
    heading("File operations");

    const source = path.join(root, "operations", "source.txt");
    const copy = path.join(root, "operations", "backup.txt");
    const moved = path.join(root, "archive", "source-moved.txt");

    await ensureParent(source);
    await fsp.writeFile(source, "Line one\n", "utf8");
    await fsp.appendFile(source, "Line two\n", "utf8");

    console.log(await fsp.readFile(source, "utf8"));

    await fsp.copyFile(source, copy);
    await ensureParent(moved);
    await fsp.rename(source, moved);
    await fsp.rm(copy);

    console.log("Moved:", moved);
    console.log("Original exists:", await exists(source));
    console.log("Moved exists:", await exists(moved));
}

async function exists(target) {
    try {
        await fsp.access(target);
        return true;
    } catch {
        return false;
    }
}

function permissionString(mode) {
    const bits = [
        [0o400, "r"], [0o200, "w"], [0o100, "x"],
        [0o040, "r"], [0o020, "w"], [0o010, "x"],
        [0o004, "r"], [0o002, "w"], [0o001, "x"]
    ];

    return bits.map(([mask, letter]) => (mode & mask) ? letter : "-").join("");
}

async function demonstrateMetadataAndPermissions(root) {
    heading("Metadata and permissions");

    const target = path.join(root, "secure.txt");
    await fsp.writeFile(target, "Restricted data\n", "utf8");

    let info = await fsp.stat(target);

    console.log({
        size: info.size,
        isFile: info.isFile(),
        isDirectory: info.isDirectory(),
        modified: info.mtime.toISOString(),
        accessed: info.atime.toISOString(),
        created: info.birthtime.toISOString(),
        mode: permissionString(info.mode & 0o777)
    });

    // chmod expresses POSIX-style permission bits. Windows may expose
    // these bits differently depending on filesystem and runtime behavior.
    if (process.platform !== "win32") {
        await fsp.chmod(target, 0o640);
        info = await fsp.stat(target);
        console.log("After chmod 640:", permissionString(info.mode & 0o777));
    } else {
        console.log("POSIX chmod semantics are platform-dependent on Windows.");
    }
}

async function demonstrateStreaming(root) {
    heading("Streaming binary data");

    const source = path.join(root, "large-data.bin");
    const destination = path.join(root, "large-data-copy.bin");

    const writer = fs.createWriteStream(source);

    for (let i = 0; i < 1000; i++) {
        if (!writer.write(Buffer.alloc(1024, i % 256))) {
            await new Promise(resolve => writer.once("drain", resolve));
        }
    }

    await new Promise((resolve, reject) => {
        writer.end(resolve);
        writer.on("error", reject);
    });

    await pipeline(
        fs.createReadStream(source),
        fs.createWriteStream(destination)
    );

    const sourceHash = await sha256(source);
    const destinationHash = await sha256(destination);

    console.log("Bytes:", (await fsp.stat(source)).size);
    console.log("Hashes match:", sourceHash === destinationHash);
}

function sha256(filePath) {
    return new Promise((resolve, reject) => {
        const hash = crypto.createHash("sha256");

        const stream = fs.createReadStream(filePath);
        stream.on("data", chunk => hash.update(chunk));
        stream.on("end", () => resolve(hash.digest("hex")));
        stream.on("error", reject);
    });
}

async function walk(root) {
    const result = [];

    async function visit(current) {
        const entries = await fsp.readdir(current, { withFileTypes: true });

        for (const entry of entries) {
            const full = path.join(current, entry.name);
            result.push(full);

            if (entry.isDirectory()) {
                await visit(full);
            }
        }
    }

    await visit(root);
    return result;
}

async function demonstrateInventory(root) {
    heading("Filesystem inventory");

    const entries = await walk(root);

    for (const fullPath of entries) {
        const info = await fsp.stat(fullPath);
        const relative = path.relative(root, fullPath);

        console.log(
            `${relative} | ${info.size} bytes | ` +
            `${info.isDirectory() ? "directory" : "file"} | ` +
            `${permissionString(info.mode & 0o777)}`
        );
    }
}

function assertInside(root, candidate) {
    const resolvedRoot = path.resolve(root);
    const resolvedCandidate = path.resolve(candidate);
    const relative = path.relative(resolvedRoot, resolvedCandidate);

    if (
        relative === "" ||
        relative.startsWith(`..${path.sep}`) ||
        path.isAbsolute(relative)
    ) {
        throw new Error(`Unsafe path outside approved root: ${candidate}`);
    }

    return resolvedCandidate;
}

async function demonstrateSafeDeletion(root) {
    heading("Safe recursive deletion");

    const backup = path.join(root, "backup");
    await fsp.mkdir(path.join(backup, "data"), { recursive: true });
    await fsp.writeFile(path.join(backup, "data", "records.txt"), "1,42\n");

    const validated = assertInside(root, backup);
    await fsp.rm(validated, { recursive: true, force: true });

    console.log("Validated deletion:", !(await exists(backup)));
}

async function demonstrateAtomicUpdate(root) {
    heading("Atomic-style configuration update");

    const destination = path.join(root, "config.json");
    const temporary = `${destination}.${process.pid}.tmp`;

    const configuration = {
        environment: "production",
        auditLogging: true,
        maxConnections: 40
    };

    await fsp.writeFile(
        temporary,
        JSON.stringify(configuration, null, 2),
        "utf8"
    );

    // rename replaces the destination on supported filesystems when the
    // destination already exists, avoiding a partially written final file.
    await fsp.rename(temporary, destination);

    console.log(await fsp.readFile(destination, "utf8"));
}

async function demonstrateSymlink(root) {
    heading("Symbolic links");

    const target = path.join(root, "target.txt");
    const link = path.join(root, "reference.txt");

    await fsp.writeFile(target, "Referenced content\n", "utf8");

    try {
        await fsp.symlink(
            path.basename(target),
            link,
            process.platform === "win32" ? "file" : undefined
        );

        const linkInfo = await fsp.lstat(link);
        console.log("Is symbolic link:", linkInfo.isSymbolicLink());
        console.log("Resolved target:", await fsp.realpath(link));
    } catch (error) {
        console.log("Symbolic link creation unavailable:", error.code);
    }
}

async function demonstrateFailures(root) {
    heading("Failure handling");

    const missing = path.join(root, "missing.txt");

    try {
        await fsp.readFile(missing, "utf8");
    } catch (error) {
        if (error.code === "ENOENT") {
            console.log("ENOENT handled: file does not exist.");
        } else {
            throw error;
        }
    }

    const directory = path.join(root, "directory");
    await fsp.mkdir(directory);

    try {
        await fsp.readFile(directory, "utf8");
    } catch (error) {
        console.log("Directory read failure:", error.code);
    }
}

async function main() {
    const root = await createWorkspace();
    console.log("Temporary workspace:", root);

    try {
        await demonstratePaths(root);
        await demonstrateOperations(root);
        await demonstrateMetadataAndPermissions(root);
        await demonstrateStreaming(root);
        await demonstrateInventory(root);
        await demonstrateSafeDeletion(root);
        await demonstrateAtomicUpdate(root);
        await demonstrateSymlink(root);
        await demonstrateFailures(root);
    } finally {
        await fsp.rm(root, { recursive: true, force: true });
        console.log("\nTemporary workspace removed.");
    }
}

main().catch(error => {
    console.error("Filesystem laboratory failed:", error);
    process.exitCode = 1;
});
