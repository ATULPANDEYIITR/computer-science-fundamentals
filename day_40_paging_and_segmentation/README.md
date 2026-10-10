# Paging and Segmentation: Address Translation and Memory Protection

## Scope

This learning artifact models two classical memory-management mechanisms and their interaction:

- **Segmentation** treats a logical address as a segment selector plus an offset. The segment descriptor supplies a base, a limit, and access permissions.
- **Paging** divides a linear virtual address space into fixed-size pages and maps those pages to physical frames through page-table entries.
- **Address translation** connects these stages. In the combined model, a logical reference is first checked against a segment, converted into a linear address, split into a page number and offset, and then resolved through a TLB or page table.
- **Memory protection** can be enforced at more than one stage. A segment can reject an access before paging occurs, while a page-table entry can independently reject an otherwise valid linear address.

The six deliverables deliberately approach the same subject from different technical perspectives rather than translating one implementation into five programming languages.

## Address spaces and terminology

A **logical address** belongs to a segmented view of memory. It can be represented as:

`segment : offset`

The segment descriptor supplies a base and limit. The offset is valid only when it falls within that limit.

A **linear address** is the address produced after segmentation. In a simplified segmented model:

`linear_address = segment_base + offset`

Paging then divides the linear address into:

`page_number + page_offset`

For a 16-bit virtual address with an 8-bit page offset, the upper 8 bits identify the virtual page and the lower 8 bits identify the byte within that page.

A **physical address** is formed after the page number has been mapped to a physical frame:

`physical_address = frame_number × page_size + page_offset`

The page offset does not change during ordinary paging translation. Only the page/frame component changes.

## Segmentation

Segmentation is useful when memory needs to be described in logical regions such as code, data, or stack areas.

A segment descriptor in the implementations contains:

| Attribute | Purpose |
|---|---|
| Base | Starting linear address of the segment |
| Limit | Largest permitted offset |
| Read permission | Allows data to be read |
| Write permission | Allows modification |
| Execute permission | Allows instruction execution |

The important protection property is that the segment limit is checked before the linear address is accepted. An offset outside the segment produces a segment fault rather than a page-table lookup.

The Python and Java implementations use separate segment descriptors for executable code and writable data. The C++ case study uses the same distinction while exposing the translation stages directly. The JavaScript implementation places the segment check inside an event-driven translation service.

The segment-level rule is conceptually:

`0 <= offset <= limit`

A valid offset can still fail later. Passing the segment check does not guarantee that a corresponding page exists.

## Paging

Paging removes the requirement that a virtual region occupy physically contiguous memory.

The page table maps a virtual page to a physical frame. A simplified page-table entry contains:

- frame number
- present bit
- readable bit
- writable bit
- executable bit
- user-accessibility information
- accessed state
- dirty state

The Python implementation makes these fields executable through `PageTableEntry`. The C++ program stores them in a case-study memory subsystem. Java uses an immutable `record` and creates updated entries when accessed or dirty state changes.

A missing mapping produces a **page fault**. A present mapping with insufficient permissions produces a **protection fault**.

These failures are deliberately separated because they represent different operating-system decisions:

- A page fault means the requested page is not currently available through the page table.
- A protection fault means the mapping exists but the requested operation is not permitted.

## Address translation

The combined translation path used throughout the artifacts is:

`logical address`
→ `segment validation`
→ `linear address`
→ `page number + offset`
→ `TLB lookup`
→ `page-table lookup if necessary`
→ `physical frame + offset`
→ `physical address`

This ordering matters.

A segment limit violation cannot be repaired by adding a page-table entry because the logical address is invalid before paging is reached.

A valid segment reference can still generate a page fault if its linear address belongs to an unmapped page.

A valid segment and mapped page can still generate a protection fault when, for example, a write is attempted against a read-only page.

## TLB behavior

The Translation Lookaside Buffer is a cache of recent page-to-frame translations.

Without a TLB, every memory reference may require a page-table lookup before the physical memory access. With a TLB hit, the cached frame can be used directly.

The Python implementation uses a small FIFO TLB and reports hit/miss statistics. The JavaScript version adds event-driven processing around translation requests. The C++ and Java implementations use bounded TLB structures to make replacement behavior explicit.

A TLB does not replace the page table as the authoritative mapping. It caches translation information. When a mapping changes, the corresponding cached entry must be invalidated or otherwise made consistent with the new mapping.

## Page-table protection versus segmentation protection

These mechanisms are related but not interchangeable.

A segment describes a logical region and its bounds. A page table describes how portions of the resulting linear address space are physically mapped.

Consider a writable data segment whose linear range contains a read-only page. A reference can satisfy the segment's write permission but still fail when the page-table permission is evaluated.

Conversely, a page can be writable while a particular segment that reaches that page is read-only. The segment can therefore reject a write before the page permission is considered.

This layered model is useful because different protection rules operate at different abstraction levels.

## Python implementation

The Python program is an executable memory-management laboratory.

`PagedMemory` owns the physical byte array, page table, and TLB. Its `translate()` method performs the central paging operation. The method separates virtual-page extraction, TLB lookup, page-table resolution, permission checking, accessed-state tracking, dirty-state tracking, and physical-address construction.

The `SegmentedMemory` class adds the logical-address layer. It verifies the segment name, validates the offset against the segment limit, checks segment permissions, creates the linear address, and delegates to `PagedMemory`.

The program also demonstrates a cross-page write. This matters because a multi-byte operation can span two pages. The implementation translates each byte independently, making the page boundary visible rather than incorrectly assuming that one page mapping covers the complete operation.

The TLB demonstration intentionally uses a small capacity so that FIFO replacement becomes observable. The page-table examples also expose accessed and dirty state, which are relevant to page-replacement and write-back decisions.

The Python implementation uses only the standard library and can be executed directly with Python 3.

## JavaScript implementation

The JavaScript implementation models translation as an event-driven service.

`PagedMemory` owns page mappings and physical memory. `SegmentedPager` adds segment validation. `TranslationService` provides an asynchronous request queue, so callers submit logical memory references and receive a Promise containing the translation result.

This design demonstrates a useful distinction between the memory-management algorithm and the surrounding execution model. Address translation itself remains deterministic, while requests can be processed through an asynchronous event-driven interface.

The JavaScript program emits `pageFault` and `protectionFault` events. This makes failure states observable without coupling the core translation routine to one particular logging mechanism.

JavaScript's `Map`, `Uint8Array`, Promises, and event-listener pattern are used because they directly support the simulated memory system rather than serving as unrelated language demonstrations.

## C++ case study

The C++ program represents a compact operating-system memory subsystem.

`AddressSpace` owns page mappings, segment descriptors, physical memory, and a TLB. Its `translate()` method performs the full logical-to-physical path.

The case study separates four failure classes:

- `SegmentFault` handles nonexistent segments and offsets beyond a segment limit.
- `ProtectionFault` handles disallowed operations.
- `PageFault` handles absent page mappings.
- Successful translation produces a physical address while recording accessed and dirty state.

The C++ design uses `std::unordered_map` for page and segment lookup and a bounded FIFO structure for the TLB. The use of exceptions makes protection and mapping failures explicit control-flow outcomes rather than hidden return values.

The program also reports the difference between a TLB hit and a page-table lookup. This reflects an important architectural distinction: the TLB accelerates translation but does not change the logical meaning of the page table.

## Java enterprise-oriented model

The Java implementation uses explicit domain types to model a service-oriented memory subsystem.

`SegmentDescriptor`, `PageTableEntry`, `LogicalAddress`, and `Translation` represent distinct domain concepts rather than treating memory addresses as unstructured integers.

The `PermissionPolicy` interface separates policy evaluation from translation mechanics. `StandardPermissionPolicy` provides the normal behavior, while the service remains responsible for address validation and state transitions.

Java records are particularly useful for the immutable description of translation state. When a page becomes accessed or dirty, the implementation creates an updated page-table entry instead of mutating a record.

The TLB is deliberately encapsulated behind its own type. This keeps cache replacement behavior separate from the authoritative page-table model.

The enterprise-oriented structure is useful for showing how memory-management rules can be represented as domain services rather than as a collection of unrelated conditionals.

## SQL data model

The PostgreSQL script represents memory management as a relational domain.

`process` identifies an address space.

`segment` stores logical memory regions, their bases and limits, and their segment-level permissions.

`physical_frame` represents physical memory frames and their allocation state.

`page_mapping` represents page-table entries. The unique constraint on `(process_id, virtual_page)` prevents two authoritative mappings for the same virtual page within one process.

`memory_access` records translation attempts and their outcomes. It distinguishes successful accesses from segment faults, page faults, and protection faults.

`status_check` provides an operational audit mechanism for memory-management consistency checks.

The schema uses check constraints to prevent contradictory permission states such as a page that is both writable and executable in this simplified model. PostgreSQL foreign keys preserve relationships between processes, segments, mappings, and physical frames.

## Database-level address translation

The SQL examples calculate a linear address from a segment base and offset:

`linear_address = base_address + segment_offset`

They then derive the page number and page offset using division and modulo by the page size.

The page mapping query joins the calculated virtual page against `page_mapping` and calculates:

`physical_address = frame_id × page_size + page_offset`

This is deliberately implemented with SQL expressions because relational systems can evaluate address-space metadata, audit mappings, and detect invalid configurations without requiring every check to occur in application code.

## Integrity and transactions

Database constraints are particularly useful for structural rules.

A foreign key prevents a page mapping from referring to an unknown physical frame.

A unique constraint prevents duplicate mappings for the same process and virtual page.

A check constraint prevents negative addresses and invalid permission combinations.

The transaction in the SQL script updates accessed and dirty state together with an access record. The transaction boundary prevents the audit operation from being partially committed if a later statement fails.

This does not attempt to turn PostgreSQL into a hardware MMU. The database is modeling the domain and enforcing persistent consistency, while the Python, JavaScript, C++, and Java programs model runtime translation behavior.

## Memory protection

Protection operates at several distinct levels in these artifacts.

**Segment protection** controls access to a logical region. A code segment may allow execution but reject writes.

**Page protection** controls access to an individual mapped page. A page-table entry can be readable but not writable.

**Presence** controls whether a page currently has a usable mapping.

**User accessibility** can distinguish mappings intended for user processes from privileged mappings in a more complete operating-system design.

A protection system should avoid relying on only one layer. If an application assumes that a data segment is writable but the page table denies writes, the page-level protection remains authoritative at the paging stage.

## Common failure modes

A frequent translation error is treating the virtual address as a physical address. Paging requires separating the virtual page number from the page offset.

Another error is changing the page offset during translation. The offset identifies the position inside the page and is preserved when the page is mapped to a frame.

A segment-bound violation is different from a page fault. The first means the logical reference violates the segment descriptor. The second means the resulting linear page has no usable mapping.

A TLB entry can become stale after a mapping changes. The implementations explicitly invalidate affected TLB entries when mappings are changed.

A permission check performed only at the segment level is insufficient when page-level permissions can be more restrictive.

## Multi-level page tables

The Python implementation includes the index calculation for a two-level page table.

For a 32-bit address with a 12-bit page offset and a 10-bit second-level index, the remaining upper bits form the first-level index.

The conceptual path becomes:

`virtual address`
→ `first-level index`
→ `page-table-page selection`
→ `second-level index`
→ `page-table entry`
→ `physical frame`
→ `offset`

Multi-level tables reduce the need to allocate page-table storage for completely unused portions of a large sparse address space. The trade-off is additional translation work when the required entries are not cached.

## Large pages and page-size trade-offs

The examples use small page sizes because small offsets make address translation easy to inspect.

Larger pages reduce the number of page-table entries required for a given memory range and can improve TLB reach because each cached translation covers more memory. They also increase internal fragmentation and can cause more data to be moved or mapped than an application actually needs.

A real operating system can therefore support multiple page sizes for different workloads. The correct choice depends on working-set size, allocation patterns, TLB behavior, fragmentation, and hardware support.

## Performance considerations

The main performance-sensitive structure is the TLB.

A TLB hit avoids the normal page-table lookup path. A TLB miss requires resolving the page mapping before the physical address can be produced.

Page-table organization also affects translation cost. A single-level table provides straightforward lookup but can consume substantial memory for sparse address spaces. Multi-level tables save space at the cost of additional traversal.

The examples intentionally keep the structures small so their behavior remains visible. They are models, not cycle-accurate simulations of a particular processor.

## Security considerations

Memory protection is a security boundary as well as a correctness mechanism.

A writable executable page is dangerous in many software designs because it weakens the distinction between data and code. The examples therefore reject writable-plus-executable combinations in their simplified policy model.

A stale TLB mapping can also become a security problem if a process continues to access a physical frame after its virtual mapping has changed. Real systems therefore require precise rules for invalidating or synchronizing translation caches.

Segment and page permissions should be treated as enforcement mechanisms rather than documentation. A permission mentioned only in application code does not protect the underlying address space.

## Relationship among the mechanisms

The four central concepts answer different questions:

| Mechanism | Question answered |
|---|---|
| Segmentation | Is this logical offset valid within the selected memory region? |
| Page table | Which physical frame backs this linear page? |
| Address translation | What physical address corresponds to the requested logical/virtual address? |
| Memory protection | Is the requested operation permitted at each enforcement stage? |

The complete path is therefore not a collection of interchangeable terms. Segmentation defines logical regions, paging provides fixed-size physical mapping, translation connects virtual references to physical locations, and protection constrains what operations are legal during that process.

## Practical boundary conditions

The implementations deliberately exercise:

- A valid code execution through a segment and executable page.
- A writable data access through a writable segment and page.
- A write against a read-only code region.
- An offset beyond a segment limit.
- A missing page mapping.
- TLB hits after previous translations.
- TLB replacement when capacity is exceeded.
- Accessed and dirty page state.
- Cross-page memory operations.
- Database-level uniqueness and referential-integrity enforcement.

These cases are important because successful translation is only one possible outcome. A realistic memory-management system must also define what happens when an address, mapping, permission, or cached translation is invalid.
