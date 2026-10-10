'use strict';

/*
 * Paging and Segmentation
 *
 * This Node.js program models a memory-management subsystem using an
 * event-driven design. It focuses on the JavaScript-specific value of
 * representing address-translation requests as events and processing them
 * asynchronously.
 *
 * No external packages are required.
 */

const PAGE_SIZE = 256;
const VIRTUAL_SIZE = 65536;
const PHYSICAL_SIZE = 65536;

class MemoryFault extends Error {}
class PageFault extends MemoryFault {}
class ProtectionFault extends MemoryFault {}
class SegmentFault extends MemoryFault {}

const Access = Object.freeze({
    READ: 'read',
    WRITE: 'write',
    EXECUTE: 'execute'
});

class PageTableEntry {
    constructor(frame, permissions) {
        this.frame = frame;
        this.present = true;
        this.readable = permissions.readable ?? false;
        this.writable = permissions.writable ?? false;
        this.executable = permissions.executable ?? false;
        this.user = permissions.user ?? true;
        this.accessed = false;
        this.dirty = false;
    }

    permits(access) {
        return {
            [Access.READ]: this.readable,
            [Access.WRITE]: this.writable,
            [Access.EXECUTE]: this.executable
        }[access] === true;
    }
}

class SegmentDescriptor {
    constructor(name, base, limit, permissions) {
        this.name = name;
        this.base = base;
        this.limit = limit;
        this.readable = permissions.readable ?? false;
        this.writable = permissions.writable ?? false;
        this.executable = permissions.executable ?? false;
    }

    permits(access) {
        return {
            [Access.READ]: this.readable,
            [Access.WRITE]: this.writable,
            [Access.EXECUTE]: this.executable
        }[access] === true;
    }
}

class TLB {
    constructor(capacity = 4) {
        this.capacity = capacity;
        this.entries = new Map();
        this.hits = 0;
        this.misses = 0;
    }

    lookup(page) {
        if (this.entries.has(page)) {
            this.hits++;
            return this.entries.get(page);
        }

        this.misses++;
        return undefined;
    }

    insert(page, frame) {
        if (this.entries.has(page)) {
            this.entries.set(page, frame);
            return;
        }

        if (this.entries.size >= this.capacity) {
            const oldest = this.entries.keys().next().value;
            this.entries.delete(oldest);
        }

        this.entries.set(page, frame);
    }

    invalidate(page) {
        if (page === undefined) {
            this.entries.clear();
        } else {
            this.entries.delete(page);
        }
    }
}

class PagedMemory {
    constructor(tlbCapacity = 4) {
        this.pageTable = new Map();
        this.physicalMemory = new Uint8Array(PHYSICAL_SIZE);
        this.tlb = new TLB(tlbCapacity);
        this.nextFrame = 0;
        this.listeners = new Map();
    }

    on(event, listener) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(listener);
    }

    emit(event, payload) {
        for (const listener of this.listeners.get(event) ?? []) {
            listener(payload);
        }
    }

    mapPage(page, permissions, requestedFrame = undefined) {
        if (!Number.isInteger(page) || page < 0 || page >= 256) {
            throw new RangeError('Invalid virtual page');
        }

        const frame = requestedFrame ?? this.nextFrame++;
        if (frame < 0 || frame >= 256) {
            throw new RangeError('Invalid physical frame');
        }

        this.pageTable.set(
            page,
            new PageTableEntry(frame, permissions)
        );
        this.tlb.invalidate(page);
    }

    checkAddress(address) {
        if (!Number.isInteger(address) || address < 0 || address >= VIRTUAL_SIZE) {
            throw new MemoryFault('Virtual address is outside the address space');
        }
    }

    translate(address, access) {
        this.checkAddress(address);

        const page = address >>> 8;
        const offset = address & 0xff;

        let frame = this.tlb.lookup(page);
        let tlbHit = frame !== undefined;

        let entry = this.pageTable.get(page);

        if (frame === undefined) {
            if (!entry || !entry.present) {
                this.emit('pageFault', { page, address });
                throw new PageFault(`Page ${page} is not present`);
            }

            frame = entry.frame;
            this.tlb.insert(page, frame);
        } else if (!entry || !entry.present) {
            this.tlb.invalidate(page);
            throw new PageFault('TLB referenced a stale mapping');
        }

        if (!entry.permits(access)) {
            this.emit('protectionFault', { page, address, access });
            throw new ProtectionFault(
                `${access} access denied for virtual page ${page}`
            );
        }

        entry.accessed = true;
        if (access === Access.WRITE) {
            entry.dirty = true;
        }

        return {
            virtualAddress: address,
            page,
            offset,
            frame,
            physicalAddress: frame * PAGE_SIZE + offset,
            tlbHit
        };
    }

    read(address, length = 1) {
        if (!Number.isInteger(length) || length < 0) {
            throw new RangeError('Read length must be non-negative');
        }

        const result = [];
        for (let i = 0; i < length; i++) {
            const translation = this.translate(address + i, Access.READ);
            result.push(this.physicalMemory[translation.physicalAddress]);
        }
        return Uint8Array.from(result);
    }

    write(address, values) {
        const bytes = values instanceof Uint8Array
            ? values
            : Uint8Array.from(values);

        for (let i = 0; i < bytes.length; i++) {
            const translation = this.translate(address + i, Access.WRITE);
            this.physicalMemory[translation.physicalAddress] = bytes[i];
        }
    }
}

class SegmentedPager {
    constructor(pager) {
        this.pager = pager;
        this.segments = new Map();
    }

    defineSegment(name, base, limit, permissions) {
        if (base < 0 || limit < 0 || base + limit >= VIRTUAL_SIZE) {
            throw new RangeError('Segment exceeds linear address space');
        }

        this.segments.set(
            name,
            new SegmentDescriptor(name, base, limit, permissions)
        );
    }

    translate(segmentName, offset, access) {
        const segment = this.segments.get(segmentName);

        if (!segment) {
            throw new SegmentFault(`Unknown segment: ${segmentName}`);
        }

        if (!Number.isInteger(offset) || offset < 0 || offset > segment.limit) {
            throw new SegmentFault(
                `Offset ${offset} exceeds ${segmentName} segment limit`
            );
        }

        if (!segment.permits(access)) {
            throw new ProtectionFault(
                `${access} access denied by segment ${segmentName}`
            );
        }

        const linearAddress = segment.base + offset;
        const result = this.pager.translate(linearAddress, access);
        return { ...result, segment: segmentName };
    }
}

class TranslationService {
    constructor(segmentedPager) {
        this.memory = segmentedPager;
        this.queue = [];
        this.processing = false;
    }

    submit(request) {
        return new Promise((resolve, reject) => {
            this.queue.push({ request, resolve, reject });
            this.process();
        });
    }

    async process() {
        if (this.processing) {
            return;
        }

        this.processing = true;

        while (this.queue.length > 0) {
            const item = this.queue.shift();

            try {
                // Promise.resolve creates an asynchronous boundary that models
                // a request entering an event-driven memory-management service.
                await Promise.resolve();
                const result = this.memory.translate(
                    item.request.segment,
                    item.request.offset,
                    item.request.access
                );
                item.resolve(result);
            } catch (error) {
                item.reject(error);
            }
        }

        this.processing = false;
    }
}

function formatTranslation(t) {
    return [
        `${t.segment}:${t.offset.toString(16)}`,
        `linear=0x${t.virtualAddress.toString(16).padStart(4, '0')}`,
        `physical=0x${t.physicalAddress.toString(16).padStart(4, '0')}`,
        t.tlbHit ? 'TLB hit' : 'page-table lookup'
    ].join(' | ');
}

async function main() {
    const pager = new PagedMemory(2);

    pager.on('pageFault', event => {
        console.log(`EVENT pageFault page=${event.page}`);
    });

    pager.on('protectionFault', event => {
        console.log(
            `EVENT protectionFault page=${event.page} access=${event.access}`
        );
    });

    const memory = new SegmentedPager(pager);

    memory.defineSegment('code', 0x1000, 0x01ff, {
        readable: true,
        writable: false,
        executable: true
    });

    memory.defineSegment('data', 0x3000, 0x01ff, {
        readable: true,
        writable: true,
        executable: false
    });

    pager.mapPage(0x10, {
        readable: true,
        writable: false,
        executable: true
    }, 4);

    pager.mapPage(0x11, {
        readable: true,
        writable: false,
        executable: true
    }, 5);

    pager.mapPage(0x30, {
        readable: true,
        writable: true,
        executable: false
    }, 8);

    const service = new TranslationService(memory);

    console.log('=== Event-driven address translation ===');

    const executable = await service.submit({
        segment: 'code',
        offset: 0x20,
        access: Access.EXECUTE
    });
    console.log(formatTranslation(executable));

    const writable = await service.submit({
        segment: 'data',
        offset: 0x40,
        access: Access.WRITE
    });
    console.log(formatTranslation(writable));

    try {
        await service.submit({
            segment: 'code',
            offset: 0x20,
            access: Access.WRITE
        });
    } catch (error) {
        console.log(`Rejected write: ${error.message}`);
    }

    try {
        await service.submit({
            segment: 'data',
            offset: 0x300,
            access: Access.READ
        });
    } catch (error) {
        console.log(`Rejected segment access: ${error.message}`);
    }

    try {
        await service.submit({
            segment: 'data',
            offset: 0x180,
            access: Access.READ
        });
    } catch (error) {
        console.log(`Page translation failure: ${error.message}`);
    }

    console.log(
        `TLB statistics: hits=${pager.tlb.hits}, misses=${pager.tlb.misses}`
    );

    console.log('=== Page-table state ===');
    for (const [page, entry] of pager.pageTable) {
        console.log(
            `page=${page} frame=${entry.frame} ` +
            `accessed=${entry.accessed} dirty=${entry.dirty}`
        );
    }
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
