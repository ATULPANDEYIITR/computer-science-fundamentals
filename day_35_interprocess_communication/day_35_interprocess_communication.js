'use strict';

/*
 * Interprocess Communication in Node.js
 *
 * This program deliberately uses different IPC models rather than presenting
 * one mechanism repeatedly:
 *
 *   - child_process IPC: discrete messages between a parent and child.
 *   - OS pipe streams: stdout is a byte stream and therefore requires framing
 *     when the application needs distinct messages.
 *   - Worker threads + SharedArrayBuffer: shared memory with Atomics.
 *   - Unix domain sockets: bidirectional local stream communication.
 *
 * Run with:
 *   node ipc-laboratory.js
 */

const {
  fork,
  spawn,
  Worker,
  isMainThread,
  parentPort,
  workerData,
} = require('node:worker_threads');

const net = require('node:net');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');

const FRAME_LIMIT = 1024 * 1024;

function section(title) {
  console.log(`\n=== ${title} ===`);
}

function sleep(milliseconds) {
  return new Promise(resolve => setTimeout(resolve, milliseconds));
}

/*
 * Child-process message IPC
 *
 * fork() creates a separate Node.js process and establishes an IPC channel.
 * Messages are discrete application objects, so the receiver does not need
 * to reconstruct message boundaries from a stream.
 */
async function demonstrateProcessMessages() {
  section('PROCESS IPC: discrete messages');

  const child = fork(__filename, ['--message-worker'], {
    stdio: ['inherit', 'inherit', 'inherit', 'ipc'],
  });

  const responses = new Map();

  const responsePromise = new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('message worker timed out'));
    }, 5000);

    child.on('message', message => {
      if (message.type === 'response') {
        responses.set(message.requestId, message);

        if (responses.size === 3) {
          clearTimeout(timeout);
          resolve();
        }
      }
    });

    child.on('error', reject);
  });

  const requests = [
    { requestId: 'r-101', operation: 'hash', value: 'interprocess-data' },
    { requestId: 'r-102', operation: 'hash', value: 'shared-boundary' },
    { requestId: 'r-103', operation: 'invalid', value: 'test' },
  ];

  for (const request of requests) {
    child.send({
      type: 'request',
      ...request,
    });
  }

  await responsePromise;

  for (const request of requests) {
    console.log(request.requestId, '->', responses.get(request.requestId));
  }

  child.send({ type: 'shutdown' });

  await new Promise((resolve, reject) => {
    child.once('exit', resolve);
    child.once('error', reject);
  });
}

/*
 * Stream IPC through stdout
 *
 * stdout behaves as a byte stream. A logical line may arrive in pieces, and
 * several lines can arrive in one chunk. The parser below uses newline
 * delimiters to establish application-level message boundaries.
 */
async function demonstratePipeStream() {
  section('PIPE STREAM: framing a byte stream');

  const child = spawn(process.execPath, [__filename, '--pipe-worker'], {
    stdio: ['pipe', 'pipe', 'inherit'],
  });

  const request = JSON.stringify({
    command: 'transform',
    payload: 'pipe messages require framing',
  }) + '\n';

  const response = new Promise((resolve, reject) => {
    let buffer = '';

    child.stdout.setEncoding('utf8');

    child.stdout.on('data', chunk => {
      buffer += chunk;

      let newlineIndex;
      while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
        const line = buffer.slice(0, newlineIndex);
        buffer = buffer.slice(newlineIndex + 1);

        try {
          resolve(JSON.parse(line));
        } catch (error) {
          reject(new Error(`invalid framed JSON: ${error.message}`));
        }
      }
    });

    child.once('error', reject);
  });

  child.stdin.write(request);
  child.stdin.end();

  console.log('pipe response:', await response);

  await new Promise(resolve => child.once('exit', resolve));
}

/*
 * Shared memory using SharedArrayBuffer
 *
 * Worker threads have shared process memory facilities through
 * SharedArrayBuffer. Atomics.add() makes the update indivisible with respect
 * to other participating workers.
 *
 * This is deliberately different from message passing: workers can directly
 * access the same bytes rather than sending a copy of the data.
 */
function runSharedWorker(sharedBuffer, index, increment) {
  return new Promise((resolve, reject) => {
    const worker = new Worker(__filename, {
      workerData: {
        buffer: sharedBuffer,
        index,
        increment,
      },
    });

    worker.once('message', resolve);
    worker.once('error', reject);
  });
}

async function demonstrateSharedMemory() {
  section('SHARED MEMORY: SharedArrayBuffer and Atomics');

  const sharedBuffer = new SharedArrayBuffer(Int32Array.BYTES_PER_ELEMENT * 4);
  const counters = new Int32Array(sharedBuffer);

  counters.set([100, 200, 300, 400]);

  const workers = [];

  for (let workerIndex = 0; workerIndex < 4; workerIndex += 1) {
    workers.push(
      runSharedWorker(
        sharedBuffer,
        workerIndex,
        (workerIndex + 1) * 10
      )
    );
  }

  const results = await Promise.all(workers);

  console.log('worker updates:', results);
  console.log('final shared counters:', [...counters]);
}

/*
 * Length-prefixed socket protocol
 *
 * A Unix stream socket has no message boundaries. Prefixing each JSON payload
 * with a four-byte unsigned length makes the protocol deterministic and also
 * permits a maximum frame size check before allocation.
 */
function encodeFrame(message) {
  const payload = Buffer.from(JSON.stringify(message), 'utf8');

  if (payload.length > FRAME_LIMIT) {
    throw new Error('message exceeds protocol frame limit');
  }

  const header = Buffer.allocUnsafe(4);
  header.writeUInt32BE(payload.length, 0);

  return Buffer.concat([header, payload]);
}

class FrameDecoder {
  constructor(onMessage) {
    this.buffer = Buffer.alloc(0);
    this.onMessage = onMessage;
  }

  push(chunk) {
    this.buffer = Buffer.concat([this.buffer, chunk]);

    while (this.buffer.length >= 4) {
      const payloadLength = this.buffer.readUInt32BE(0);

      if (payloadLength > FRAME_LIMIT) {
        throw new Error('peer supplied an oversized frame');
      }

      const totalLength = 4 + payloadLength;

      if (this.buffer.length < totalLength) {
        return;
      }

      const payload = this.buffer.subarray(4, totalLength);
      this.buffer = this.buffer.subarray(totalLength);

      this.onMessage(JSON.parse(payload.toString('utf8')));
    }
  }
}

async function demonstrateUnixSocket() {
  section('SOCKET: Unix domain stream');

  const socketPath = path.join(
    os.tmpdir(),
    `ipc-lab-${process.pid}-${crypto.randomUUID()}.sock`
  );

  const server = net.createServer(socket => {
    const decoder = new FrameDecoder(message => {
      if (message.command === 'health') {
        socket.write(encodeFrame({
          status: 'ok',
          pid: process.pid,
          transport: 'unix-domain-stream',
        }));
      } else if (message.command === 'shutdown') {
        socket.write(encodeFrame({ status: 'stopped' }));
        socket.end();
      } else {
        socket.write(encodeFrame({
          status: 'error',
          reason: 'unsupported command',
        }));
      }
    });

    socket.on('data', chunk => {
      try {
        decoder.push(chunk);
      } catch (error) {
        socket.destroy(error);
      }
    });
  });

  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(socketPath, () => {
      try {
        fs.chmodSync(socketPath, 0o600);
      } catch (error) {
        reject(error);
        return;
      }
      resolve();
    });
  });

  const response = new Promise((resolve, reject) => {
    const socket = net.createConnection(socketPath);
    const decoder = new FrameDecoder(message => {
      console.log('socket response:', message);

      if (message.status === 'ok') {
        socket.write(encodeFrame({ command: 'shutdown' }));
      } else if (message.status === 'stopped') {
        socket.end();
        resolve();
      }
    });

    socket.on('data', chunk => {
      try {
        decoder.push(chunk);
      } catch (error) {
        reject(error);
      }
    });

    socket.once('error', reject);

    socket.once('connect', () => {
      socket.write(encodeFrame({ command: 'health' }));
    });
  });

  await response;

  await new Promise(resolve => server.close(resolve));

  try {
    fs.unlinkSync(socketPath);
  } catch (error) {
    if (error.code !== 'ENOENT') {
      throw error;
    }
  }
}

async function main() {
  await demonstrateProcessMessages();
  await demonstratePipeStream();
  await demonstrateSharedMemory();
  await demonstrateUnixSocket();

  console.log('\nIPC laboratory completed.');
}

/*
 * Child-process modes are intentionally kept in this same executable so the
 * file remains self-contained and does not require additional source files.
 */
if (!isMainThread && workerData) {
  const shared = new Int32Array(workerData.buffer);
  const oldValue = Atomics.add(
    shared,
    workerData.index,
    workerData.increment
  );

  parentPort.postMessage({
    index: workerData.index,
    previous: oldValue,
    current: oldValue + workerData.increment,
  });
} else if (process.argv[2] === '--message-worker') {
  process.on('message', message => {
    if (message.type === 'shutdown') {
      process.disconnect();
      return;
    }

    if (message.type !== 'request') {
      process.send({
        type: 'response',
        requestId: 'unknown',
        status: 'error',
        reason: 'invalid message type',
      });
      return;
    }

    if (message.operation === 'hash') {
      const digest = crypto
        .createHash('sha256')
        .update(String(message.value), 'utf8')
        .digest('hex');

      process.send({
        type: 'response',
        requestId: message.requestId,
        status: 'ok',
        digest,
      });
    } else {
      process.send({
        type: 'response',
        requestId: message.requestId,
        status: 'error',
        reason: 'unsupported operation',
      });
    }
  });
} else if (process.argv[2] === '--pipe-worker') {
  let input = '';

  process.stdin.setEncoding('utf8');

  process.stdin.on('data', chunk => {
    input += chunk;

    let newlineIndex;
    while ((newlineIndex = input.indexOf('\n')) !== -1) {
      const line = input.slice(0, newlineIndex);
      input = input.slice(newlineIndex + 1);

      try {
        const request = JSON.parse(line);

        if (request.command !== 'transform') {
          process.stdout.write(JSON.stringify({
            status: 'error',
            reason: 'unsupported command',
          }) + '\n');
          continue;
        }

        process.stdout.write(JSON.stringify({
          status: 'ok',
          transformed: String(request.payload).toUpperCase(),
        }) + '\n');
      } catch (error) {
        process.stdout.write(JSON.stringify({
          status: 'error',
          reason: 'invalid JSON request',
        }) + '\n');
      }
    }
  });
} else {
  main().catch(error => {
    console.error('IPC laboratory failed:', error);
    process.exitCode = 1;
  });
}
