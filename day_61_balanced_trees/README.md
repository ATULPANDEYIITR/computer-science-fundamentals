# Balanced Trees: AVL Trees and Red-Black Trees

## Scope

This project explores balanced binary search trees, focusing on AVL trees and Red-Black trees. It demonstrates how self-balancing mechanisms maintain efficient search, insertion, and deletion operations.

The implementations cover tree structures, rotations, balancing rules, traversal, validation, and performance analysis across Python, JavaScript, C++17, Java 17, and PostgreSQL.

## Core Concepts

A balanced binary search tree maintains an ordering property while controlling its height.

For every node:

- Values in the left subtree are smaller than the node's value.
- Values in the right subtree are greater than the node's value.
- Both subtrees must satisfy the binary search tree property.

A balanced tree prevents the structure from becoming unnecessarily skewed.

| Operation | Average Time Complexity | Worst-Case Time Complexity |
|---|---:|---:|
| Search | O(log n) | O(log n) |
| Insertion | O(log n) | O(log n) |
| Deletion | O(log n) | O(log n) |
| Traversal | O(n) | O(n) |

## AVL Trees

An AVL tree is a self-balancing binary search tree in which the height difference between the left and right subtrees of every node is at most one.

The balance factor is calculated as:

`Balance Factor = Height(Left Subtree) - Height(Right Subtree)`

Valid balance factors are:

- `-1`
- `0`
- `1`

When an insertion or deletion causes an imbalance, the tree performs rotations.

### AVL Rotations

| Rotation | Condition | Correction |
|---|---|---|
| LL | Left subtree of left child becomes heavy | Right rotation |
| RR | Right subtree of right child becomes heavy | Left rotation |
| LR | Right subtree of left child becomes heavy | Left rotation followed by right rotation |
| RL | Left subtree of right child becomes heavy | Right rotation followed by left rotation |

## Red-Black Trees

A Red-Black tree is a self-balancing binary search tree that assigns a color to each node.

Each node is either red or black.

### Red-Black Tree Properties

1. Every node is either red or black.
2. The root is black.
3. All NIL leaves are black.
4. A red node cannot have a red parent or red child.
5. Every path from a node to its descendant NIL leaves contains the same number of black nodes.

These properties maintain logarithmic tree height.

Red-Black trees use recoloring and rotations to restore balance after insertion and deletion.

## AVL Trees vs Red-Black Trees

| Feature | AVL Tree | Red-Black Tree |
|---|---|---|
| Balancing method | Height-based | Color-based |
| Balance control | Strict | Relatively flexible |
| Search performance | Often faster | May require more comparisons |
| Insertion | May require rotations | Uses recoloring and rotations |
| Deletion | May require repeated rebalancing | Uses recoloring and rotations |
| Height | More strictly controlled | Less strictly controlled |
| Typical use | Search-intensive workloads | Frequent insertion and deletion |

## Implementation Structure

The project provides five independent implementations.

| Language | Implementation Focus |
|---|---|
| Python | Object-oriented tree structures, insertion, deletion, rotations, and validation |
| JavaScript | Node-based tree operations and dynamic data handling |
| C++17 | Pointer-based tree structures and memory management |
| Java 17 | Object-oriented tree models and balancing operations |
| PostgreSQL | Relational representation of tree nodes and structural validation |

Each implementation demonstrates the same fundamental concepts while following the conventions of its programming language.

## PostgreSQL Data Model

The PostgreSQL implementation represents tree nodes using relational records.

A node contains:

- Unique node identifier
- Stored value
- Parent node reference
- Left child reference
- Right child reference
- Node color or balance information
- Tree type

The relational model supports structural inspection, parent-child relationships, and validation queries.

Database constraints help maintain record integrity, while application-level operations handle tree balancing.

## Validation and Testing

The implementations should validate:

- Binary search tree ordering.
- Correct parent-child relationships.
- AVL balance factors.
- Red-Black tree color properties.
- Root conditions.
- Duplicate-value handling.
- Empty-tree operations.
- Insertion and deletion edge cases.
- Correct traversal output.

Testing should include sorted input, reverse-sorted input, random input, duplicate values, and repeated insertion and deletion.

## Performance Analysis

Balanced trees provide predictable logarithmic search, insertion, and deletion operations.

The AVL tree maintains tighter height constraints, making it suitable for workloads with frequent searches.

The Red-Black tree offers more flexible balancing, making it useful when insertions and deletions occur frequently.

Both structures avoid the linear-height behavior that can occur in an ordinary binary search tree.

## Practical Applications

Balanced trees are useful in:

- Database indexing concepts
- In-memory ordered collections
- Dictionary and map implementations
- Scheduling systems
- Search-intensive applications
- Dynamic data management
- Symbol tables
- Ordered sets

## Learning Outcomes

After completing this project, learners should be able to:

1. Explain binary search tree ordering.
2. Understand why tree height affects performance.
3. Calculate AVL balance factors.
4. Implement LL, RR, LR, and RL rotations.
5. Explain Red-Black tree properties.
6. Understand recoloring and rotation operations.
7. Compare AVL and Red-Black balancing strategies.
8. Implement insertion, deletion, and search.
9. Validate balanced tree invariants.
10. Analyze time and space complexity.

## Engineering Principles

The project emphasizes:

- Correctness of tree invariants.
- Consistent handling of edge cases.
- Separation of structural operations and balancing logic.
- Clear implementation of rotations.
- Predictable operation complexity.
- Reusable and testable code.
- Language-specific implementation practices.

## Conclusion

AVL trees and Red-Black trees demonstrate two important approaches to maintaining balanced binary search trees.

AVL trees prioritize stricter height balancing, while Red-Black trees use color-based rules to provide flexible balancing.

Understanding both structures builds a foundation for advanced data structures, database indexing, algorithm design, and efficient data management.
