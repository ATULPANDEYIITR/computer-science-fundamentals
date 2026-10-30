# Binary Search Trees: Insertion, Deletion, Searching, and Balancing

## Problem Domain

A binary search tree (BST) is a node-based data structure that stores keys according to an ordering rule. Each node has at most two children:

- The left subtree contains keys smaller than the node's key.
- The right subtree contains keys greater than the node's key.
- Each key appears once in the index. In these implementations, inserting an existing key updates its associated value.

This ordering makes it possible to search by following one path from the root rather than examining every record. The effectiveness of that path depends on the tree's shape.

The implementations use integer keys and string values to represent an infrastructure asset index. Keys represent unique asset identifiers. Values represent associated asset descriptions, such as `gateway`, `database`, and `scheduler`.

## Core Tree Concepts

### Node and Root

A node contains a key, an associated value, and references to its left and right children. The root is the entry point to the tree. An empty tree has no root.

A node may have:

| Node condition | Structure |
|---|---|
| Leaf | No children |
| Left-only node | One left child |
| Right-only node | One right child |
| Two-child node | Both left and right children |
| Root | The entry point, which may also be a leaf |

A leaf has no children. The root does not necessarily have the smallest or largest key.

### Binary Search Tree Ordering

Consider the keys:

`50, 30, 70, 20, 40, 60, 80`

One valid structure is:

                 50
               /    \
             30      70
            /  \    /  \
           20  40  60  80

The ordering rule applies recursively to entire subtrees, not just to direct children. Every key in the left subtree of `50` must be less than `50`. Every key in its right subtree must be greater than `50`.

### Traversal

Inorder traversal visits:

1. The left subtree.
2. The current node.
3. The right subtree.

For a valid BST, inorder traversal produces keys in ascending order. It is useful for ordered reporting, exporting records, and checking the tree's ordering invariant.

Preorder and postorder traversal are useful for other operations, such as copying a tree or processing children before their parent. The implementations primarily use inorder traversal because ordered retrieval is a central operation of an index.

### Height and Depth

Depth describes a node's distance from the root. The root has depth zero when measured in edges.

Height describes the longest downward path from a node to a leaf. In these programs, tree height is measured in node levels:

- An empty tree has height zero.
- A tree containing only a root has height one.
- A path of ten nodes has height ten.

Tree height determines the maximum number of nodes encountered along a search path.

## Fundamental Operations

### Searching

Searching starts at the root.

For a requested key:

- Return the associated value when the current node matches.
- Move to the left child when the requested key is smaller.
- Move to the right child when the requested key is larger.
- Report absence when the path reaches an empty child.

For a tree of height \(h\), search takes \(O(h)\) time.

A balanced tree has logarithmic height, producing approximately \(O(\log n)\) search time. An unbalanced tree can have height \(n\), producing \(O(n)\) search time.

The programs distinguish a missing record from a record containing an empty value. Values are validated as non-empty strings, so an absent result has an unambiguous representation.

### Insertion

Insertion follows the same search path until it finds an empty child position.

For example, inserting `65` into the earlier tree follows:

`50 → 70 → 60 → right child`

The new node becomes the right child of `60`.

The position is determined by the key's ordering. A duplicate key does not create a second node. It updates the existing value and leaves the node count unchanged.

Insertion takes \(O(h)\) time in an ordinary BST. The AVL implementation also performs balancing operations after insertion.

### Deletion

Deletion has three distinct structural cases.

**Leaf deletion**

A leaf has no children. Its parent reference is changed to null. When the leaf is the root, the root becomes null.

**Deletion with one child**

The deleted node is replaced by its only child. The replacement takes the deleted node's former position, preserving the remaining subtree.

**Deletion with two children**

The implementation finds the inorder successor, which is the smallest key in the deleted node's right subtree. It copies that successor's key and value into the target node, then physically removes the successor.

The successor has no left child, so its removal reduces to a leaf or one-child deletion.

The inorder successor is used because replacing a node with it preserves the BST ordering rule.

Deletion takes \(O(h)\) time in an ordinary BST. A balanced tree performs additional height updates and rotations to preserve its balance.

## Balanced and Unbalanced Trees

### Unbalanced Binary Search Tree

A basic BST does not automatically control its height.

Inserting ascending keys creates a structure such as:

    1
     \
      2
       \
        3
         \
          4
           \
            5

This structure behaves like a linked list. Each additional search may traverse almost every existing node.

For \(n\) sequentially inserted keys:

- The height becomes \(n\).
- Searching for the last key takes \(O(n)\) time.
- Insertion of the next largest key takes \(O(n)\) time.
- Building the tree by sequential insertion takes \(O(n^2)\) time.

An unbalanced BST can still be appropriate when the data is small, insertion order is not problematic, and simplicity is a priority.

### AVL Tree

An AVL tree is a self-balancing BST. It maintains a balance condition at every node:

\[
|h(\text{left}) - h(\text{right})| \leq 1
\]

The difference between the two subtree heights is called the balance factor:

\[
BF = h(\text{left}) - h(\text{right})
\]

After insertion or deletion, the tree updates node heights and restores the balance condition using rotations.

AVL trees provide logarithmic height, so searching, insertion, and deletion take \(O(\log n)\) time.

### AVL Rotation Cases

| Case | Imbalance | Correction |
|---|---|---|
| LL | Left subtree's left branch is too high | Right rotation |
| RR | Right subtree's right branch is too high | Left rotation |
| LR | Left subtree's right branch is too high | Left rotation on child, then right rotation |
| RL | Right subtree's left branch is too high | Right rotation on child, then left rotation |

A rotation changes local parent-child relationships while preserving the relative inorder ordering of the keys.

For a right rotation:

                 z                  y
                / \                / \
               y   C      →       A   z
              / \                    / \
             A   B                  B   C

The middle subtree `B` becomes the left subtree of `z`. No key needs to be moved outside this local structure.

### Comparison of Tree Types

| Property | Ordinary BST | AVL tree |
|---|---|---|
| Ordering rule | BST ordering | BST ordering |
| Automatic balancing | No | Yes |
| Maximum height | \(O(n)\) | \(O(\log n)\) |
| Search | \(O(h)\) | \(O(\log n)\) |
| Insertion | \(O(h)\) | \(O(\log n)\) |
| Deletion | \(O(h)\) | \(O(\log n)\) |
| Rotations | None | Required when imbalanced |
| Implementation complexity | Lower | Higher |
| Additional maintenance | Minimal | Height and balance updates |

The performance of an ordinary BST depends heavily on insertion order. The AVL tree spends additional processing time maintaining height information to avoid long search paths.

## Extended Ordered-Index Operations

### Range Queries

A range query returns records whose keys fall between two supplied bounds.

For a range from `35` to `70`, the expected result is an ascending sequence of matching keys. Nodes outside the interval can be skipped using BST ordering.

The implementation uses an iterative traversal. Its work depends on the number of visited nodes and the shape of the tree. A balanced tree can efficiently narrow the search region, while an unbalanced tree may require substantial traversal.

The PostgreSQL implementation demonstrates an additional distinction: its range function uses the composite primary-key index on the authoritative records table rather than performing a tree-node traversal.

### K-th Smallest Key

The k-th smallest operation uses inorder traversal and a one-based position.

For example, the first position returns the smallest key. A position outside the range from `1` to the node count raises an error.

The implementations use an iterative traversal. This takes \(O(n)\) time in the worst case. A production index that frequently requests order statistics could maintain subtree sizes in each node, allowing the search to follow a single path in \(O(h)\) time.

### Invariant Validation

A valid BST must satisfy more than a local parent-child comparison.

Validation checks that:

- Every left-subtree key is smaller than all applicable ancestor keys.
- Every right-subtree key is greater than all applicable ancestor keys.
- Each node is reached only once.
- The actual number of nodes equals the recorded node count.
- In an AVL tree, stored heights match calculated heights.
- In an AVL tree, every node satisfies the balance condition.

The Python and JavaScript validators use iterative traversal to avoid recursion-depth problems when checking a highly skewed ordinary BST. The C++ validator uses explicit bounds and ownership-safe pointers. The Java implementation also detects repeated node references during validation.

The AVL validation additionally calculates subtree heights and checks the stored metadata against the actual structure.

## Python Implementation

The Python file provides two independently usable index classes:

- `BinarySearchTree` implements an unbalanced BST.
- `AvlTree` implements a self-balancing AVL tree.

Both inherit the common operations from `IndexBase`.

### Data Representation

The `Node` dataclass stores:

- `key`: the unique integer identifier.
- `value`: the associated description.
- `left` and `right`: child references.
- `height`: maintained by the AVL implementation.

Using a dataclass provides a direct representation of a tree node without introducing unrelated data structures.

### Ordinary BST Mechanics

Insertion uses an iterative loop. It walks down the tree and attaches a new node at the first available child position.

Deletion also uses iterative traversal. For a two-child deletion, the implementation locates the successor and physically removes that successor after copying its data.

These iterative methods are deliberate: sorted input can produce a tree with thousands of levels, and recursive traversal of such a structure can exceed Python's recursion limit.

### AVL Mechanics

The AVL implementation uses recursive insertion and deletion because its height remains logarithmic when invariants are maintained.

The `_refresh` method calculates a node's height from its children. `_balance_factor` measures the height difference. `_rotate_left` and `_rotate_right` change local links, and `_rebalance` selects the required rotation pattern.

The implementation updates the node count only when a new key is inserted or an existing key is deleted. Updating a value does not change the count.

### Tests and Workload

The script checks:

- Successful and unsuccessful searches.
- Duplicate-key value updates.
- Leaf deletion.
- One-child deletion.
- Two-child deletion.
- Ordered traversal.
- Range retrieval.
- K-th smallest retrieval.
- Tree invariant validation.
- Height differences for sorted insertion.

The 1,000-record sorted-insertion workload exposes the difference between a plain BST and an AVL tree. The ordinary BST becomes a chain with height 1,000. The AVL tree remains logarithmic in height.

The script uses only the Python standard library.

## JavaScript Implementation

The JavaScript file uses Node.js standard-library facilities and combines ordered indexing with an asynchronous service boundary.

### Index Classes

`BinarySearchTree` implements iterative insertion and deletion. `AvlTree` uses recursive operations and rotation-based balancing.

`IndexBase` shares searching, range retrieval, inorder traversal, height measurement, k-th smallest retrieval, and invariant checking.

The node representation uses ordinary objects. The AVL implementation stores a height on every node and refreshes it after structural changes.

### Event-Driven Service

`TreeIndexService` extends Node.js `EventEmitter`.

Its responsibilities include:

- Validating keys and values before accepting operations.
- Serializing modifications through a Promise queue.
- Emitting `inserted`, `updated`, and `deleted` events.
- Waiting for earlier writes before performing a search or report.
- Returning explicit results for missing records.

The serialized write queue prevents concurrent asynchronous callers from making decisions based on partially ordered mutations.

A rejected write does not permanently block the queue. The queue's internal continuation handles a previous rejection while the original caller still receives the operation's failure.

### Domain Events

An insertion emits an event containing its type, key, value, and timestamp. Repeated insertion of an existing key emits an update event rather than an insertion event.

Deletion of a missing key returns a `not-found` result and does not emit a successful deletion event.

The event mechanism is independent of the balancing algorithm. The same service can operate with an ordinary BST or an AVL index.

### Runtime and Security

The implementation requires Node.js and uses the built-in `events` module. No npm packages are needed.

Input checks reject unsafe integer keys, empty values, and oversized values. The service serializes writes but is not a durable database. Process termination loses its in-memory records and event history.

## C++17 Implementation

The C++ program models the ordered index using explicit ownership and a shared polymorphic interface.

### Memory Ownership

`Node` stores its child links as `std::unique_ptr<Node>`.

A unique pointer gives each child subtree one owning reference. When a node is deleted or replaced, ownership is moved instead of copied.

This avoids manual memory deallocation and prevents two parent nodes from accidentally owning the same child.

`TreeIndex` defines the common search and traversal operations. `BinarySearchTree` and `AvlTree` implement insertion, deletion, and their own invariant validation.

### Ordinary BST Deletion

The ordinary BST uses a pointer to the owning `unique_ptr` during insertion and deletion.

For a two-child deletion, it finds the inorder successor through the right subtree. It copies the successor's key and value, then moves the successor's right child into its former location.

For zero-child and one-child deletion, ownership of the remaining child is moved directly into the deleted node's position.

This makes the code independent of raw parent pointers.

### AVL Ownership and Rotations

AVL rotations move unique pointers between nodes. The original root and pivot are transferred into their new ownership positions.

Height refreshes occur after changing the links. The rebalance operation examines the balance factor and chooses a single or double rotation.

The recursive operations have logarithmic depth under the AVL invariant.

### Validation and Reporting

The common interface includes:

- Search.
- Inorder traversal.
- Range retrieval.
- K-th smallest retrieval.
- Height measurement.
- Node count.
- Structural validation.

The ordinary BST validator uses explicit lower and upper bounds. The AVL validator also checks stored heights and balance factors.

The program reports both index structures and exercises a sorted insertion sequence. It uses standard C++17 headers and does not require external libraries.

## Java 17 Implementation

The Java program models an enterprise asset catalog with an active ordered index and a separate lifecycle record map.

### Domain Model

`Asset` is an immutable record containing:

- A positive asset identifier.
- A name.
- A category.
- An `AssetStatus`.

The status is either `ACTIVE` or `RETIRED`.

The `TreeIndex` interface defines operations required by the catalog. `AbstractTreeIndex` implements common ordered queries and validation. `UnbalancedBstIndex` and `AvlIndex` provide the two structural strategies.

### Catalog Lifecycle

`AssetCatalogService` separates asset lifecycle rules from tree mechanics.

Registration rejects duplicate identifiers and requires new assets to be active. Retiring an asset removes it from the active search index and updates its stored lifecycle state.

Retired assets remain in the catalog's record map, but they are no longer returned by active-index searches.

The active index and the record map have distinct responsibilities:

| Component | Responsibility |
|---|---|
| Record map | Retains the catalog's lifecycle records |
| Tree index | Locates currently active assets by identifier |
| `AssetStatus` | Defines permitted lifecycle states |
| `AssetCatalogService` | Applies registration and retirement rules |

### Explicit Structural Policies

Both implementations satisfy the same `TreeIndex` contract.

The ordinary BST uses iterative operations and does not maintain balance metadata. The AVL index updates heights and restores the balance condition through rotations.

The catalog service does not need to know which tree is selected. It depends on the interface rather than a particular tree implementation.

### Failure Handling

The service rejects duplicate registration, unknown retirement identifiers, and repeated retirement. It also detects an inconsistent state in which an active asset cannot be removed from the search index.

The immutable `Asset` record makes lifecycle updates explicit: retirement creates a new record with the new state rather than mutating an existing asset object.

### Performance

The enterprise example inserts and retires a small group of infrastructure assets, then compares the height of the two implementations using 1,000 sorted keys.

The common range and k-th smallest operations use ordered traversal. They are useful for modest catalog queries. More frequent order-statistic queries would justify storing subtree-size metadata.

The Java implementation requires only Java 17 or later.

## PostgreSQL Implementation

The SQL file provides a persistent relational representation of two different tree strategies.

It uses the `bst_lab` schema and separates authoritative records from their search structures.

### Relational Model

| Table | Purpose |
|---|---|
| `tree_catalog` | Identifies an index and its strategy |
| `tree_item` | Stores authoritative keyed records and payloads |
| `tree_node` | Stores parent, left-child, and right-child relationships |
| `tree_event` | Records item insertion and deletion events |

A `tree_catalog` row identifies either an ordinary `BST` or a `REBUILT_BALANCED` structure.

Each `tree_item` has a composite primary key consisting of the tree identifier and record key. This permits the same key to exist in separate trees without ambiguity.

`tree_node` contains the structural relationships. Its composite foreign keys ensure that a node can refer only to records and nodes in the same tree.

### Why the Model Separates Records and Nodes

`tree_item` is the authoritative data. It stores the actual payload associated with each key.

`tree_node` is a derived index structure. It determines how searches move from the root to the matching record.

This separation allows the structure to be rebuilt without losing the underlying records. It also makes the PostgreSQL balanced strategy explicit.

### Ordinary BST Insertion

`insert_item` first inserts the authoritative record and then calls `bst_attach` for an ordinary BST.

`bst_attach` begins at the root and follows left or right references based on key ordering. When it finds an empty child position, it inserts the new node and updates the parent's corresponding child reference.

The catalog's node count increases after the structural insertion.

The composite foreign keys are deferrable because parent-child links can be temporarily inconsistent while a multi-step structural operation is being completed. They are checked at transaction end.

### Ordinary BST Deletion

`bst_delete_node` handles the three standard deletion cases.

The helper `bst_transplant` replaces a node in its parent's child reference or updates the root when the removed node is the root.

For a two-child deletion, the function finds the minimum key in the right subtree, relocates the successor, and reconnects the affected child and parent links.

After the structural operation succeeds, `delete_item` removes the corresponding authoritative record.

### Balanced-by-Rebuild Strategy

The PostgreSQL implementation uses a distinct `REBUILT_BALANCED` strategy.

Instead of implementing AVL rotations in PL/pgSQL, it reconstructs the entire tree from the sorted authoritative keys after each insertion or deletion.

`rebuild_balanced_tree`:

1. Reads all keys for the selected tree in ascending order.
2. Clears the old derived structure.
3. Selects the middle key as the root.
4. Recursively constructs the left and right subtrees.
5. Updates parent and child references.
6. Replaces the catalog root and node count.

Selecting the middle key recursively produces a balanced structure for a collection of unique ordered keys.

This strategy is intentionally different from AVL balancing. It is simple to inspect and verify, but has a higher write cost.

For \(n\) records, rebuilding requires \(O(n)\) work to obtain the ordered key collection and construct the node structure. Rebuilding after every insertion can therefore produce \(O(n^2)\) cumulative work across a sequence of \(n\) insertions.

The Python, JavaScript, C++17, and Java 17 AVL implementations instead maintain balance incrementally through rotations.

### Database Integrity

The SQL schema uses:

- Primary keys to prevent duplicate records and nodes.
- Foreign keys to maintain tree membership and parent-child references.
- Check constraints to reject self-referencing links.
- Composite references to prevent cross-tree connections.
- A catalog root reference to require an existing root node.
- A non-negative node-count constraint.
- Payload validation to reject empty descriptions.
- Transactions to keep record changes and tree changes together.

The audit trigger writes an event when an authoritative item is inserted or deleted. It does not treat every internal node movement as a separate business record change.

### Search and Reporting

`search_item` follows the tree structure from the root. It returns the payload for a matching key or null when the key is absent.

`range_items` retrieves an ordered range using the authoritative table's composite primary key.

The `tree_metrics` view uses a recursive CTE to walk from each root. It calculates:

- Reachable node count.
- Maximum depth.
- Agreement between reachable nodes and catalog node count.
- Key-ordering validity.

The report uses a path array to prevent a malformed cyclic structure from causing an infinite recursive traversal.

The sample queries also demonstrate record aggregation, tree comparisons, event history, and deletion of an absent key.

## Complexity Analysis

Let \(n\) represent the number of nodes and \(h\) represent tree height.

| Operation | Ordinary BST | AVL |
|---|---:|---:|
| Search | \(O(h)\) | \(O(\log n)\) |
| Insertion | \(O(h)\) | \(O(\log n)\) |
| Deletion | \(O(h)\) | \(O(\log n)\) |
| Inorder traversal | \(O(n)\) | \(O(n)\) |
| Height calculation | \(O(n)\) | \(O(n)\) |
| Range query | Depends on visited nodes | Depends on visited nodes |
| K-th smallest in these implementations | \(O(n)\) | \(O(n)\) |
| Storage | \(O(n)\) | \(O(n)\) |

For an ordinary BST, a favorable shape may have logarithmic height, but no such guarantee exists. A degenerate tree has height \(n\).

An AVL tree maintains logarithmic height through its balance invariant. This provides a predictable upper bound for search, insertion, and deletion.

The PostgreSQL rebuild strategy has a different operational profile. It produces balanced search structures, but reconstructing the entire structure after a mutation is more expensive than the incremental AVL updates.

## Edge Cases and Limitations

The implementations address several common correctness problems:

**Duplicate keys**

Keys are unique within a tree. A repeated insertion updates the value rather than creating an additional node.

**Missing keys**

Searching for an absent key returns an explicit absent result. Deleting a missing key does not change the tree.

**Empty trees**

An empty tree has no root, zero nodes, and height zero. Traversal returns an empty collection.

**Single-node trees**

Deleting the root of a single-node tree produces an empty tree.

**Two-child deletion**

The inorder successor preserves BST ordering when the target node is removed.

**Sorted input**

A plain BST can become a linear chain. An AVL tree prevents this structural degradation through rotations.

**Invalid ranges and positions**

Lower range bounds cannot exceed upper bounds. The k-th smallest operation uses a one-based position and rejects positions outside the current node count.

**Recursion depth**

The ordinary BST insertion and deletion implementations are iterative in Python, JavaScript, C++17, and Java. The AVL implementations use recursive balancing because their height is logarithmic.

**Persistence**

The in-memory language implementations lose their records when the process exits. The PostgreSQL implementation persists the authoritative records and the corresponding tree structures.

**Concurrency**

The JavaScript service serializes writes within a single Node.js process. The PostgreSQL functions lock the catalog row during mutations so concurrent changes to one tree are coordinated. The in-memory examples do not provide distributed synchronization.

**Large data volumes**

A pointer-based BST or AVL tree has per-node allocation and pointer-traversal costs. For large persistent datasets, database-native indexes may be preferable to implementing a tree structure in application code.

## Relationship Between the Five Implementations

The implementations share one domain rule: a key determines the ordered path through the tree. They differ in how they maintain the structure and where they place operational responsibilities.

| Implementation | Primary engineering focus | Balancing approach |
|---|---|---|
| Python | Reusable index classes, validation, and comparison | Incremental AVL rotations |
| JavaScript | Event-driven indexing and serialized asynchronous writes | Incremental AVL rotations |
| C++17 | Ownership, memory safety, and pointer-based structural updates | Incremental AVL rotations |
| Java 17 | Enterprise asset lifecycle and interface-based index selection | Incremental AVL rotations |
| PostgreSQL | Relational integrity, transactions, auditing, and persistent tree structures | Ordinary BST or balanced reconstruction |

The distinction between the two tree strategies is fundamental. A plain BST preserves key ordering but does not control height. An AVL tree preserves the same ordering while also maintaining a strict balance condition. The PostgreSQL rebuild strategy reaches a balanced shape by reconstructing it from sorted keys, rather than by applying AVL rotations after each mutation.
