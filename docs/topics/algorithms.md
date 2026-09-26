# Algorithms

What experienced engineers forget before an algorithms interview, grouped by subtopic. Bounds follow [MIT 6.006](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/), [Princeton Algorithms](https://algs4.cs.princeton.edu/), and the [USACO Guide](https://usaco.guide/). For database indexes see [database.md](database.md); for rate limiting and load balancing see [system.md](system.md); for consensus see [distributed.md](distributed.md).

## Complexity and problem solving

### Time and space bounds

- State the **input size**, then worst-case time and **auxiliary space**; producing an output of size `k` already costs Ω(k).
- Nested loops aren't automatically O(n²): if two pointers each advance at most `n` times, total work is O(n).
- Recursion stack counts as space: balanced divide-and-conquer uses O(log n) frames, a linear chain O(n).

### Amortized analysis

- A dynamic array's occasional **O(n) resize** still gives **O(1) amortized** append, because capacity grows geometrically.
- Amortized is a guarantee over a sequence of operations; hash-table lookup is **expected** O(1), and collisions can make one operation O(n).

### Recurrence patterns

- **Binary search**: `T(n) = T(n/2) + O(1) = O(log n)`.
- **Merge sort**: `T(n) = 2T(n/2) + O(n) = O(n log n)`.
- Recursion without memoization can revisit states exponentially often; after memoizing, cost = **states × work per state**.

## Arrays and sequences

### Binary search boundaries

- Search for the **boundary** of a monotonic predicate: keep a known-false and a known-true index until they're adjacent.
- **Lower bound** = first element `>= x`; upper bound = first `> x`; their difference counts occurrences.
- Binary search on the answer needs a monotonic feasibility test: O(log R × cost(test)) over a range of size `R`.

### Two pointers and sliding windows

- On a sorted array, move the left or right pointer depending on whether the pair sum is too small or too large — each moves at most `n` times.
- A variable window needs a **monotonic condition** when expanding and shrinking; sum-based windows break with negative values.
- A fixed-size window adds the new element and removes the old one in O(1) per step.

### Prefix sums and difference arrays

- With `P[0]=0`, `P[i+1]=P[i]+a[i]`, the sum of `[l,r)` is **`P[r]-P[l]`**: O(n) setup, O(1) per query.
- For many range increments, mark `D[l]+=v`, `D[r]-=v`, then take one prefix sum.

### Monotonic stacks

- **Next greater/smaller element**, scanning left to right: the new value is the answer for every index it pops.
- Each index is pushed and popped once, so the scan is **O(n)**; pick strict vs non-strict comparison for duplicates.

### Monotonic deque

- **Sliding window maximum**: keep indices with decreasing values; pop smaller values from the back, drop the front once it leaves the window.
- Every index enters and leaves once — **O(n)** total instead of O(nk).

### Intervals

- **Merge overlapping intervals**: sort by start, extend the last merged interval while the next start ≤ its end — O(n log n).
- **Minimum meeting rooms**: sweep sorted start and end points (or a min-heap of end times); the maximum overlap is the answer.

### Cycle detection in sequences

- **Floyd's tortoise and hare**: a slow and a fast pointer meet inside a cycle — O(n) time, **O(1) space**.
- Restart one pointer from the head and advance both by one; they meet at the cycle's entry.

## Strings

### KMP prefix function

- **KMP** precomputes, for each pattern prefix, the longest proper prefix that is also a suffix, and reuses it after a mismatch instead of rescanning the text.
- Search takes **O(n+m)** time for text length `n` and pattern length `m`, with O(m) extra space.

### Rolling hash (Rabin-Karp)

- A **polynomial rolling hash** updates a window's hash in O(1) as it slides, so search is O(n + m) expected.
- Collisions happen: **verify each match** for exact results — two moduli only make collisions rarer; also finds duplicate substrings via binary search on length.

## Sorting and selection

### Comparison sorts

| Algorithm | Time | Extra space | Stable? | Useful distinction |
|---|---|---|---|---|
| Merge sort | O(n log n) worst | O(n) | yes | predictable bound |
| Quicksort | O(n log n) expected, O(n²) worst | O(log n) expected stack | no | randomized pivot; in-place partitioning |
| Heapsort | O(n log n) worst | O(1) | no | bounded extra space |

Standard array implementations; variants differ in stability and space.

### Sorting lower bound and counting sort

- Any **comparison sort** needs Ω(n log n) comparisons in the worst case — it must distinguish `n!` orders.
- **Counting sort** runs in O(n + k) for integer keys in a range of size `k`, with O(k) counts plus O(n) output for stable placement.

### Quickselect and top-k

- **Quickselect** partitions around a random pivot and recurses into one side: O(n) expected, O(n²) worst.
- A size-`k` **min-heap** keeps the largest `k` of `n` items in O(n log k) time and O(k) space.

## Data structures

### Heap invariants

- A binary heap is a **complete tree** in an array; the root is the min or max, siblings are unordered.
- Peek O(1); insert and remove-root O(log n); **bottom-up construction is O(n)**.

### Hash tables and collisions

- Expected O(1) lookup and update, no ordering; **collisions** are resolved by chaining or probing, and the table rehashes past a load threshold.
- Equal keys must hash equally; mutating a key's hashed fields after insertion makes it unfindable.

### Disjoint-set union

- **Union-find** tracks components with `find` (representative) and `union` (merge); no efficient deletion or path queries.
- **Path compression + union by size/rank** gives amortized O(α(n)) — effectively constant.

### Tries and prefix lookup

- A **trie** follows one edge per symbol: lookup is O(key length), independent of the number of keys.
- Prefix search is natural, but a node per prefix costs much more space than a hash map; compressed tries merge single-child paths.

### LRU cache

- **Hash map + doubly linked list**: the map finds a node in O(1), the list keeps recency — move to front on access, evict from the tail.
- Python: `OrderedDict.move_to_end` + `popitem(last=False)`; Java: `LinkedHashMap` in access order.

### Fenwick and segment trees

- A **Fenwick tree** (binary indexed tree) gives prefix sums with point updates, both O(log n), in one array.
- A **segment tree** answers any associative range query (min, max, sum) with O(log n) updates; **lazy propagation** adds range updates.

## Trees and graphs

### Tree traversal and BST ordering

- **Inorder** traversal of a BST yields sorted keys; preorder suits serialization, postorder bottom-up aggregation.
- An unbalanced BST degrades to **O(n)** height; AVL/red-black rotations keep operations O(log n).

### Graph representation and traversal

- An **adjacency list** takes O(V+E) space and supports BFS/DFS in O(V+E); a matrix takes O(V²) but tests an edge in O(1).
- **BFS** gives shortest paths by edge count; DFS exposes cycles, components, and finishing order.
- Mark a node visited when **enqueuing** it, not when dequeuing, to avoid duplicate BFS work.

### Topological ordering

- A topological order exists **only for a DAG**.
- **Kahn's algorithm** repeatedly removes zero-indegree vertices; fewer than `V` removals means a cycle.
- DFS alternative: reverse finishing order, detecting back edges. Both O(V+E).

### Shortest-path choices

| Edge weights | Algorithm | Time with adjacency lists | Caveat |
|---|---|---|---|
| all equal, positive | BFS | O(V+E) | counts edges |
| nonnegative | Dijkstra + binary heap | O((V+E) log V) | negative edges invalidate greedy settlement |
| negative allowed | Bellman-Ford | O(VE) | detects reachable negative cycles |
| DAG, any weights | topological relaxation | O(V+E) | needs acyclic graph |

### Minimum spanning tree

- An **MST** connects all vertices of an undirected graph with minimum total weight — not a shortest-path tree.
- **Kruskal** sorts edges and keeps those joining different union-find components; **Prim** grows one tree from a min-edge priority queue.

## Dynamic programming

### DP state and order

- Define a **state** holding everything future decisions need, a recurrence, base cases, and an evaluation order where dependencies are ready.
- Top-down **memoization** visits only reachable states; bottom-up tabulation fills them all. Cost = states × transitions.

### Knapsack and one-dimensional DP

- **0/1 knapsack**: iterate capacities **downward** per item so it isn't reused; upward iteration models unbounded reuse.
- O(nC) is **pseudopolynomial**: `C` is a number whose input length is only O(log C).

### Longest increasing subsequence

- The O(n log n) method keeps the **smallest tail** for each length and binary-searches where each value goes.
- For strictly increasing, replace the first tail `>= x`; the tails array gives the length, not the subsequence itself.

### Two-sequence DP: LCS and edit distance

- **LCS**: `dp[i][j] = dp[i-1][j-1] + 1` on a match, else `max(dp[i-1][j], dp[i][j-1])`.
- **Edit distance**: diagonal on a match, else `1 + min(insert, delete, replace)`.
- Both O(nm) time, reducible to **O(min(n, m)) space** with two rows.

### Bitmask DP

- Index DP by a subset encoded as bits: travelling salesman is `dp[mask][last]` in **O(2ⁿ · n²)** — feasible up to n ≈ 20.
- Iterate submasks of `mask` with `s = (s - 1) & mask`; over all masks that totals O(3ⁿ).

## Greedy, backtracking, and hardness

### Greedy proof pattern

- A greedy choice needs an **exchange argument** or a maintained invariant — locally best isn't enough.
- Maximum non-overlapping intervals: sort by **earliest finish time**; sorting by start or by length fails.

### Backtracking and pruning

- Backtracking walks a **decision tree**, undoing each choice after recursing; reject invalid partial solutions early.
- Prune only branches that can't produce an answer or beat the best score; enumerating all outputs stays exponential.

### Bit manipulation

- `x & (x − 1)` clears the lowest set bit, so `x > 0 && (x & (x − 1)) == 0` tests a power of two; **`x & −x`** isolates it.
- XOR of all elements cancels pairs — finds the single unpaired number in O(1) space.

### Recognizing NP-hard problems

- Traveling salesman, subset sum, knapsack, graph coloring, SAT, Hamiltonian path, and set cover are **NP-hard** in general.
- No polynomial algorithm is known (none exists unless P = NP); exact answers use exponential search with pruning, or pseudopolynomial DP when numbers are small (subset sum, knapsack only).
- Otherwise use heuristics or an **approximation** algorithm where a guarantee exists (greedy set cover: H(n) ≤ ln n + 1); general TSP and coloring have no good ratio unless P = NP.
