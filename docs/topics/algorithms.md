# Algorithms

What experienced engineers forget before an algorithms interview, grouped by subtopic. Bounds follow [MIT 6.006](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/), [Princeton Algorithms](https://algs4.cs.princeton.edu/), and the [USACO Guide](https://usaco.guide/). For database indexes see [database.md](database.md); for rate limiting and load balancing see [system.md](system.md); for consensus see [distributed.md](distributed.md).

## Complexity and problem solving

### Time and space bounds

- State the **input size**, then the worst-case time and **auxiliary space**; an output of size `k` already costs Ω(k) time to produce.
- Nested loops are not automatically O(n²): if two pointers each advance at most `n` times, total work is O(n).
- A recursive algorithm's stack counts toward auxiliary space; balanced divide-and-conquer recursion uses O(log n) stack frames, a linear chain uses O(n).

### Amortized analysis

- A dynamic array's occasional **O(n) resize** does not make every append O(n): geometric growth yields **O(1) amortized** append over a sequence of operations.
- Amortized is a guarantee over that sequence; hash-table lookup is usually **expected O(1)** under hashing assumptions, but collisions can make one operation O(n).

### Recurrence patterns

- **Binary search** halves one subproblem: `T(n) = T(n/2) + O(1) = O(log n)`.
- **Merge sort** solves two halves then merges in linear time: `T(n) = 2T(n/2) + O(n) = O(n log n)`.
- A branching recursion without memoization can revisit the same states exponentially often; count distinct **states × work per state** after memoizing.

## Arrays and search

### Binary search boundaries

- Search for a **boundary** in a monotonic predicate; maintain a known false side and a known true side until adjacent.
- **Lower bound** finds the first element `>= x`; **upper bound** finds the first `> x`. Their difference counts occurrences in a sorted array.
- Binary search on an answer needs a monotonic feasibility test; complexity is `O(log R × cost(test))` over an integer range of size `R`.

### Two pointers and sliding windows

- On a sorted array, move the left or right pointer according to whether a pair's sum is too small or too large; each pointer moves at most `n` times.
- A variable sliding window works when expanding and shrinking preserve a useful **monotonic condition**; the usual sum-based window fails with negative values.
- A fixed-size window adds the new element and removes the old one in O(1) per step.

### Prefix sums and difference arrays

- With `P[0]=0` and `P[i+1]=P[i]+a[i]`, half-open range sum `[l,r)` is **`P[r]-P[l]`**: O(n) setup, O(1) per query.
- For many range increments, mark `D[l]+=v`, `D[r]-=v`, then take a prefix sum once; each update is O(1).

### Monotonic stacks

- For a **next greater/smaller element**, pop indices that the new value makes obsolete; the remaining top is the nearest qualifying candidate.
- Each index is pushed and popped at most once, so the whole scan is **O(n)**; choose strict versus non-strict comparison deliberately for duplicates.

### KMP prefix function

- **KMP** preprocesses a pattern's longest proper prefix that is also a suffix, then reuses matches after a mismatch instead of restarting the text scan.
- Pattern search takes **O(n+m)** time for text length `n` and pattern length `m`, with O(m) preprocessing space.

## Sorting and selection

### Comparison sorts

| Algorithm | Time | Extra space | Stable? | Useful distinction |
|---|---|---|---|---|
| Merge sort | O(n log n) worst | O(n) | yes | predictable bound |
| Quicksort | O(n log n) expected, O(n²) worst | O(log n) expected stack | no | randomized pivot; in-place partitioning |
| Heapsort | O(n log n) worst | O(1) | no | bounded extra space |

These are properties of the standard array implementations; stability and space can differ in variants.

### Sorting lower bound and counting sort

- Any **comparison sort** needs Ω(n log n) comparisons in the worst case for arbitrary distinct keys: it must distinguish `n!` possible orders.
- **Counting sort** uses O(n + k) time for integer keys in a range of size `k`; counts need O(k) space, while stable placement also needs O(n) output space.

### Quickselect and top-k

- **Quickselect** partitions around a randomized pivot and recurses into one side: O(n) expected, O(n²) worst with poor pivots.
- A size-`k` **min-heap** tracks the largest `k` of `n` items in O(n log k) time and O(k) space; sorting all items costs O(n log n).

## Data structures

### Heap invariants

- A binary heap is a **complete tree** stored in an array; the root is the minimum or maximum, but siblings are not sorted.
- Peek is O(1); insert and remove-root are O(log n); **bottom-up heap construction is O(n)**.

### Hash tables and collisions

- Hash maps trade ordering for expected O(1) lookup/update; **collisions** require chaining or probing, and resizable tables rehash at a chosen load threshold.
- Equal keys must have equal hashes; mutable keys break lookup if fields used by the hash change after insertion.

### Disjoint-set union

- **Union-find** tracks connected components with `find` (representative) and `union` (merge); it does not support efficient deletion or path queries.
- **Path compression + union by size/rank** gives amortized O(α(n)) per operation, effectively constant at practical sizes.

### Tries and prefix lookup

- A **trie** follows one edge per symbol: lookup is O(length of key), independent of the number of stored keys under a bounded alphabet.
- Prefix search is natural, but storing a node/edge per prefix can cost much more space than a hash map; compressed tries merge single-child paths.

## Trees and graphs

### Tree traversal and BST ordering

- **Inorder** traversal of a binary search tree yields sorted keys; preorder suits serialization, postorder suits bottom-up aggregation.
- An unbalanced BST can degrade to **O(n)** height; AVL/red-black rotations keep search, insert, and delete O(log n).

### Graph representation and traversal

- An **adjacency list** uses O(V+E) space and supports BFS/DFS in O(V+E); a matrix uses O(V²) space but tests an edge in O(1).
- **BFS** finds minimum-edge paths in an unweighted graph; **DFS** exposes cycles, connected components, and finishing order. Mark a node when enqueuing it to avoid duplicate BFS work.

### Topological ordering

- A **topological order exists only for a DAG**; edges point from earlier to later vertices.
- Kahn's algorithm repeatedly removes zero-indegree vertices; fewer than `V` removals means a cycle. DFS can instead reverse finishing order, while detecting back edges. Both take O(V+E).

### Shortest-path choices

| Edge weights | Algorithm | Time with adjacency lists | Caveat |
|---|---|---|---|
| all equal | BFS | O(V+E) | counts edges |
| nonnegative | Dijkstra + binary heap | O((V+E) log V) | negative edges invalidate greedy settlement |
| negative allowed | Bellman-Ford | O(VE) | detects reachable negative cycles |
| DAG, any weights | topological relaxation | O(V+E) | needs acyclic graph |


### Minimum spanning tree

- An **MST** minimizes total edge weight while connecting all vertices of an undirected, connected graph; it is not a shortest-path tree.
- **Kruskal** sorts edges and accepts those joining different union-find components; **Prim** grows one tree using a minimum-edge priority queue.

## Dynamic programming and search

### DP state and order

- Define a **state** containing everything future decisions need, a recurrence, base cases, and an evaluation order where dependencies are ready.
- **Memoization** explores reachable states top-down; tabulation fills them bottom-up. Complexity is number of states × transitions per state.

### Knapsack and one-dimensional DP

- For **0/1 knapsack**, process capacities downward for each item so it cannot be reused in the same iteration; upward iteration models **unbounded** reuse.
- O(nC) time is **pseudopolynomial**: `C` is a numeric capacity, whose encoded input length is only O(log C).

### Longest increasing subsequence

- The O(n log n) method stores the **smallest possible tail** for each subsequence length and binary-searches where each new value belongs.
- Use first tail `>= x` for **strictly increasing** subsequences; the tails array alone gives the length, not necessarily an actual subsequence.

### Greedy proof pattern

- A greedy choice needs an **exchange argument** or a maintained invariant; choosing the locally best-looking option is not enough.
- For maximum number of non-overlapping intervals, sort by **earliest finish time** and take the next compatible interval; sorting by start time or shortest duration can fail.

### Backtracking and pruning

- Backtracking explores a **decision tree**, undoing each choice after recursion; track state that lets you reject invalid partial solutions early.
- Exponential worst-case search may still be necessary to enumerate exponentially many outputs; prune only when a branch cannot yield a required answer or improve the best score.
