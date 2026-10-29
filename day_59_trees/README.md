# Trees: Terminology, Binary Trees, and Tree Traversal

## Scope

This project implements tree data structures from three complementary programming perspectives and models persistent tree state in PostgreSQL.

The central relationship is:

`Tree → Nodes → Parent/Child Relationships → Tree Shape → Traversal → Search`

The implementations distinguish an ordinary binary tree from a binary search tree. A binary tree restricts each node to at most two children. A binary search tree adds an ordering invariant:

`left subtree values < node value < right subtree values`

The ordering rule is what makes efficient directed search possible.

## Core Terminology

| Term | Meaning |
|---|---|
| Tree | A hierarchical, acyclic data structure composed of nodes and edges |
| Node | A single element containing a value and references to child nodes |
| Root | The unique top node of a tree |
| Parent | A node directly connected above another node |
| Child | A node directly connected below another node |
| Sibling | Nodes sharing the same parent |
| Leaf | A node with no children |
| Internal node | A node with at least one child |
| Edge | The relationship connecting two nodes |
| Depth | Number of edges from the root to a node |
| Height | Maximum number of levels represented by the implementation |
| Subtree | A node together with its descendants |
| Binary tree | A tree in which each node has at most two children |
| Binary search tree | A binary tree maintaining an ordered-key invariant |
| Traversal | Systematic visitation of tree nodes |
| Balanced tree | A tree whose shape prevents excessive height |
| Skewed tree | A tree whose shape approaches a linked list |

The source implementations use height as the number of levels. Therefore an empty tree has height `0` and a single-node tree has height `1`.

## Binary Tree Structure

A binary node has two possible child positions:

`             root`
`            /    \`
`        left      right`
`        /  \      /   \`
`      ...  ...  ...   ...`

The positions are meaningful even when one or both children are absent.

An ordinary binary tree does not require values to be ordered. The Python and JavaScript examples construct ordinary binary trees from level-order input so that missing children can be represented explicitly.

## Binary Search Tree Structure

The binary search tree adds a domain invariant:

`              50`
`             /  \`
`           30    70`
`          / \    / \`
`        20  40  60  80`
`                  \`
`                  65`

For every node:

- Values in the left subtree are smaller.
- Values in the right subtree are larger.
- Duplicate keys are rejected by the implementations.

This invariant allows search to discard half of a correctly balanced tree at each level.

A badly shaped tree can instead become:

`10`
`  \`
`   20`
`     \`
`      30`
`        \`
`         40`

The same BST operations then degrade from logarithmic behavior toward linear behavior.

## Tree Traversals

### Preorder

Preorder visits:

`Root → Left → Right`

For the sample BST, the sequence begins with the root:

`50, 30, 20, 40, 70, 60, 65, 80`

Preorder is useful when the parent should be processed before descendants.

### Inorder

Inorder visits:

`Left → Root → Right`

For a valid BST, inorder traversal produces sorted values:

`20, 30, 40, 50, 60, 65, 70, 80`

This makes inorder traversal useful for ordered extraction and structural validation.

### Postorder

Postorder visits:

`Left → Right → Root`

Children are processed before their parent. This is useful for operations such as dependency-aware deletion or bottom-up aggregation.

### Level Order

Level-order traversal visits nodes breadth-first:

`Root → depth 1 → depth 2 → ...`

It uses a queue and exposes the tree by levels. It is also useful for calculating height without recursive depth accumulation.

## Traversal Mechanics

The implementations intentionally use explicit stacks and queues for several traversals.

| Traversal | Main structure | Time | Auxiliary space |
|---|---|---:|---:|
| Preorder | Stack | `O(n)` | `O(h)` |
| Inorder | Stack | `O(n)` | `O(h)` |
| Postorder | Stack with state | `O(n)` | `O(h)` |
| Level order | Queue | `O(n)` | `O(w)` |

`n` is the number of nodes, `h` is tree height, and `w` is maximum width.

Iterative traversal avoids dependence on the programming language's call-stack limit. This matters for highly skewed trees.

## Python Implementation

The Python source provides two related models.

`BinaryTree` supports:

- Level-order construction.
- Preorder traversal.
- Inorder traversal.
- Postorder traversal.
- Level-order traversal.
- Membership testing.
- Height calculation.
- Leaf counting.

`BinarySearchTree` extends the model with:

- Ordered insertion.
- Duplicate detection.
- Directed search.
- Minimum-value lookup.
- Maximum-value lookup.
- Full BST invariant validation.

Python `dataclass` is used for node representation. `Enum` provides explicit traversal types. `deque` supplies efficient queue operations for breadth-first traversal.

The implementation also includes assertions covering:

- Empty trees.
- Normal traversal sequences.
- Search success and failure.
- Minimum and maximum values.
- Height.
- Leaf counts.
- Duplicate insertion failure.
- BST validity.

The implementation does not require external packages.

## JavaScript Implementation

The JavaScript source uses Node.js standard-library facilities and focuses on event-driven processing.

`TreeNode` validates numeric keys and restricts them to safe integers. This avoids JavaScript number-precision problems for integer keys beyond the safe-integer range.

`BinaryTree` provides iterative traversal methods.

`BinarySearchTree` adds:

- Ordered insertion.
- Directed search.
- BST validation.
- Range queries.

`TreeEventBus` demonstrates an event-driven approach. Tree insertions publish events to registered listeners, separating mutation from audit behavior.

`processTreeOperations` provides asynchronous operation handling using Promises. The operation model supports search and range requests while preserving validation and explicit failure behavior.

The JavaScript implementation therefore treats the tree not only as a data structure but also as an event-producing application component.

## C++17 Implementation

The C++ program models ownership and resource management explicitly.

`TreeNode` stores raw child pointers because the example is designed to demonstrate a tree with explicit ownership. `BinaryTree` owns its nodes and releases them through a destructor.

Copying is disabled:

`BinaryTree(const BinaryTree&) = delete`

This prevents accidental shallow copies and double deletion.

The C++ implementation provides:

- Preorder.
- Inorder.
- Postorder.
- Level-order traversal.
- Height.
- BST insertion.
- BST search.
- BST validation.
- Range queries.
- Exception handling.

`RepositoryTreeIndex` uses a BST as a conceptual integer index for commit identifiers. This connects the abstract tree structure to a practical indexing scenario without changing the underlying tree semantics.

The range query prunes branches that cannot contain values in the requested interval and sorts the resulting values before returning them.

## Java 17 Implementation

The Java source models tree behavior as an enterprise-style service.

The domain uses:

- `enum` for traversal and node state.
- `record` for immutable value-oriented data.
- An explicit `TreePolicy` interface.
- A concrete non-negative-key policy.
- A custom duplicate-key exception.
- A service object controlling mutation and queries.
- Event listeners for insertion auditing.
- Immutable traversal results.

`BinarySearchTreeService` owns the mutable tree state and keeps mutation rules private.

The `validate()` operation checks the full BST invariant using lower and upper bounds. This is stronger than merely checking each node against its immediate parent because it detects violations deeper inside a subtree.

`TreeMetrics` packages height, node count, and structural validity into an immutable record.

This design separates:

`Policy → Mutation → Validation → Query → Metrics`

rather than treating the tree as a collection of unrelated methods.

## PostgreSQL Implementation

The PostgreSQL source represents tree state relationally.

The primary entities are:

- `trees`
- `tree_nodes`
- `traversal_runs`
- `traversal_results`

The `tree_nodes` table stores:

- Node value.
- Parent node.
- Left child.
- Right child.
- Node kind.
- Depth.
- Owning tree.

Foreign keys enforce that referenced nodes belong to the same tree.

The partial unique index `one_root_per_tree` prevents multiple root nodes within a tree.

The unique `(tree_id, value)` index prevents duplicate values for the modeled BST.

The parent, left-child, and right-child relationships are checked by a deferred constraint trigger. Deferred validation is useful when several related rows must be created or connected within one transaction.

## PostgreSQL Tree Workflow

The database exposes `bst_insert(tree_id, value)` as a stored function.

Its workflow is:

`Find root`
`→ compare value`
`→ select left or right child`
`→ lock current node`
`→ continue until an empty child position`
`→ insert node`
`→ connect parent`
`→ return node identifier`

The operation rejects:

- Unknown trees.
- Non-BST trees.
- Duplicate values.
- Invalid relationships.

The insertion is executed inside a transaction in the sample workflow.

## Recursive Queries

PostgreSQL recursive CTEs represent hierarchical relationships naturally.

The path query starts at root nodes and recursively follows child relationships:

`Root`
`↓`
`Child`
`↓`
`Grandchild`
`↓`
`...`

Each result includes a path array, allowing structural inspection of the hierarchy.

The database also provides reports for:

- Tree height.
- Leaf counts.
- Nodes grouped by depth.
- Structural relationships.
- BST ordering violations.
- Leaf eligibility.
- Indexed value lookup.

`EXPLAIN (ANALYZE, BUFFERS)` is included for the value lookup so the effect of the tree-value index can be inspected.

## Validation and Failure Handling

The implementations deliberately reject invalid states rather than silently accepting them.

Important failure conditions include:

| Condition | Handling |
|---|---|
| Duplicate BST value | Exception or database error |
| Invalid numeric key | Validation failure |
| Invalid range | Exception |
| Search for missing key | Normal `false` result |
| Empty tree traversal | Empty collection |
| Invalid BST ordering | Validation returns false |
| Invalid relational child | PostgreSQL constraint failure |
| Missing parent node | PostgreSQL trigger failure |
| Multiple roots | Partial unique-index violation |

These checks preserve the difference between an empty result and an invalid operation.

## Binary Tree Versus Binary Search Tree

The two structures must not be conflated.

| Property | Binary Tree | Binary Search Tree |
|---|---|---|
| Maximum children | 2 | 2 |
| Value ordering | Not required | Required |
| Directed search | Not generally possible | Yes |
| Inorder sorted output | Not guaranteed | Guaranteed when valid |
| Duplicate policy | Application-dependent | Restricted by this project |
| Shape controls performance | Yes | Yes, especially strongly |

A binary tree is defined primarily by structure. A BST is defined by structure plus an ordering invariant.

## Practical Performance

For a tree with `n` nodes:

- Any complete traversal requires `O(n)` time.
- BST search requires `O(h)`.
- BST insertion requires `O(h)`.
- Level-order traversal requires `O(w)` auxiliary queue space.
- DFS traversal generally requires `O(h)` auxiliary space.

For balanced trees:

`h ≈ log2(n)`

For a skewed tree:

`h ≈ n`

Consequently, an unbalanced BST does not provide a guaranteed logarithmic search time.

The examples intentionally use an ordinary BST so that this performance dependency remains visible. Production systems requiring predictable worst-case performance should use a balanced search structure such as an AVL tree or red-black tree, or rely on a database/index implementation designed for the required workload.

## Security and Robustness

Tree implementations can fail through malformed or adversarial input even when the data structure itself is simple.

The implementations address several risks:

- Input keys are validated.
- JavaScript keys are restricted to safe integers.
- Duplicate mutations are rejected.
- Recursive algorithms are minimized where deep input could exhaust call-stack limits.
- C++ ownership is controlled and copying is disabled.
- Java mutable state is encapsulated inside a service.
- PostgreSQL relationships are protected by foreign keys and triggers.
- Database mutations use transactions.
- SQL values are passed as function parameters rather than constructed through dynamic SQL.
- Structural validation detects inconsistent BST relationships.

A production service should also impose maximum tree depth or node-count limits when trees are built from untrusted external input.

## Conceptual Relationship

The complete model can be viewed as:

`Node`
`  ↓`
`Parent / Child Relationships`
`  ↓`
`Tree Shape`
`  ↓`
`Traversal`
`  ↓`
`Search and Aggregation`
`  ↓`
`Validation`
`  ↓`
`Persistent Representation`

The same structural concepts appear in all five implementations, while each language emphasizes a different engineering concern: Python emphasizes concise data modeling, JavaScript emphasizes events and asynchronous processing, C++ emphasizes ownership and resource safety, Java emphasizes domain services and explicit policies, and PostgreSQL emphasizes relational integrity and transactional hierarchy management.
