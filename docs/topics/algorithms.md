# Algorithms

What experienced engineers forget before an algorithms interview, grouped by subtopic. Bounds follow [MIT 6.006](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/), [Princeton Algorithms](https://algs4.cs.princeton.edu/), and the [USACO Guide](https://usaco.guide/). For database indexes see [postgresql.md](postgresql.md); for rate limiting and load balancing see [system.md](system.md); for consensus see [distributed.md](distributed.md).

## Complexity and problem solving

### Time and space bounds

- Producing an output of size `k` already costs [Ω(k)](https://en.wikipedia.org/wiki/Big_O_notation#Family_of_Bachmann–Landau_notations), whatever the algorithm.
- Nested loops aren't automatically O(n²): if two pointers each advance at most `n` times, total work is O(n).
- Recursion stack counts as space: balanced [divide-and-conquer](https://en.wikipedia.org/wiki/Divide-and-conquer_algorithm) uses O(log n) frames, a linear chain O(n).

### Input size and target complexity

At ~10⁸ simple operations per second, the constraints tell you which complexity to aim for:

| n up to | Target | Typical technique |
|---|---|---|
| 10–11 | O(n!) | permutations |
| 20 | O(2ⁿ) | subsets, bitmask DP |
| 500 | O(n³) | interval DP, [Floyd–Warshall](https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm) |
| 5,000 | O(n²) | pairwise DP |
| 10⁶ | O(n log n) | sorting, heaps, [binary search](https://en.wikipedia.org/wiki/Binary_search) |
| beyond | O(n) or O(log n) | linear scan, math |

### Amortized analysis

- A [dynamic array's](https://en.wikipedia.org/wiki/Dynamic_array#Geometric_expansion_and_amortized_cost) occasional O(n) resize still gives O(1) [amortized](https://en.wikipedia.org/wiki/Amortized_analysis) append, because capacity grows geometrically.
- Amortized is a guarantee over a sequence of operations; [hash-table](https://en.wikipedia.org/wiki/Hash_table) lookup is expected O(1), and collisions can make one operation O(n).

### Recurrence patterns

- [Master theorem](https://en.wikipedia.org/wiki/Master_theorem_%28analysis_of_algorithms%29) for `T(n) = aT(n/b) + f(n)`: compare `f(n)` with `n^(log_b a)` — polynomially smaller → Θ(n^(log_b a)); equal → Θ(n^(log_b a) · log n); polynomially larger (plus a regularity condition) → Θ(f(n)).
- [Merge sort](https://en.wikipedia.org/wiki/Merge_sort) (a = b = 2, f = n) is the equal case → O(n log n); [binary search](https://en.wikipedia.org/wiki/Binary_search) (a = 1, b = 2, f = 1) → O(log n).
- Recursion without [memoization](https://en.wikipedia.org/wiki/Memoization) can revisit states exponentially often; after memoizing, cost = states × work per state.

## Arrays and sequences

### Binary search boundaries

- Search for the boundary of a monotonic predicate: keep a known-false and a known-true index until they're adjacent.
- [Lower bound](https://en.cppreference.com/cpp/algorithm/lower_bound) = first element `>= x`; [upper bound](https://en.cppreference.com/cpp/algorithm/upper_bound) = first `> x`; their difference counts occurrences.
- [Binary search](https://en.wikipedia.org/wiki/Binary_search) on the answer needs a monotonic feasibility test: O(log R × cost(test)) over a range of size `R`.

### Two pointers and sliding windows

- On a sorted array, [move the left or right pointer](https://usaco.guide/silver/two-pointers) depending on whether the pair sum is too small or too large — each moves at most `n` times.
- A [variable window](https://usaco.guide/gold/sliding-window) needs a monotonic condition when expanding and shrinking; sum-based windows break with negative values.
- A fixed-size window adds the new element and removes the old one in O(1) per step.

### Prefix sums and difference arrays

- With `P[0]=0`, `P[i+1]=P[i]+a[i]`, the sum of `[l,r)` is `P[r]-P[l]`: O(n) setup, O(1) per query.
- For many range increments, mark `D[l]+=v`, `D[r]-=v`, then take one [prefix sum](https://en.wikipedia.org/wiki/Prefix_sum).

### Monotonic stacks

- Next greater/smaller element, scanning left to right: the new value is the answer for every index it pops.
- Each index is pushed and popped once, so the scan is O(n); pick strict vs non-strict comparison for duplicates.

### Monotonic deque

- [Sliding window maximum](https://usaco.guide/gold/sliding-window#sliding-window-maximum-in-mathcalon): keep indices with decreasing values; pop smaller values from the back, drop the front once it leaves the window.
- Every index enters and leaves once — O(n) total instead of O(nk).

### Maximum subarray (Kadane)

- [Scan once](https://en.wikipedia.org/wiki/Maximum_subarray_problem#Kadane's_algorithm): `cur = max(x, cur + x)`, `best = max(best, cur)` — O(n) time, O(1) space.
- Initialize both with the first element, not 0, so an all-negative array returns its largest value.
- Circular variant: `max(best, total − minimum subarray)`, unless every value is negative (then just `best`).

### Intervals

- Merge overlapping intervals: sort by start, extend the last merged interval while the next start ≤ its end — O(n log n).
- Minimum meeting rooms: [sweep](https://en.wikipedia.org/wiki/Sweep_line_algorithm) sorted start and end points (or a [min-heap](https://en.wikipedia.org/wiki/Binary_heap) of end times); the maximum overlap is the answer.

### Cycle detection in sequences

- [Floyd's tortoise and hare](https://en.wikipedia.org/wiki/Cycle_detection#Floyd's_tortoise_and_hare): a slow and a fast pointer meet inside a cycle — O(n) time, O(1) space.
- Restart one pointer from the head and advance both by one; they meet at the cycle's entry.

## Strings

### KMP prefix function

- [KMP](https://en.wikipedia.org/wiki/Knuth%E2%80%93Morris%E2%80%93Pratt_algorithm) precomputes, for each pattern prefix, the [longest proper prefix that is also a suffix](https://cp-algorithms.com/string/prefix-function.html), and reuses it after a mismatch instead of rescanning the text.
- Search takes O(n+m) time for text length `n` and pattern length `m`, with O(m) extra space.

### Rolling hash (Rabin-Karp)

- A [polynomial rolling hash](https://en.wikipedia.org/wiki/Rolling_hash#Polynomial_rolling_hash) updates a window's hash in O(1) as it slides, so search is O(n + m) expected.
- Collisions happen: verify each match for exact results — two moduli only make collisions rarer; also finds duplicate substrings via [binary search](https://en.wikipedia.org/wiki/Binary_search) on length.

## Sorting, selection, and sampling

### Comparison sorts

| Algorithm | Time | Extra space | [Stable?](https://en.wikipedia.org/wiki/Sorting_algorithm#Stability) | Useful distinction |
|---|---|---|---|---|
| [Merge sort](https://en.wikipedia.org/wiki/Merge_sort) | O(n log n) worst | O(n) | yes | predictable bound |
| [Quicksort](https://en.wikipedia.org/wiki/Quicksort) | O(n log n) expected, O(n²) worst | O(log n) expected stack | no | randomized pivot; in-place partitioning |
| [Heapsort](https://en.wikipedia.org/wiki/Heapsort) | O(n log n) worst | O(1) | no | bounded extra space |

Standard array implementations; variants differ in stability and space.

### Sorting lower bound and counting sort

- Any [comparison sort](https://en.wikipedia.org/wiki/Comparison_sort#Number_of_comparisons_required_to_sort_a_list) needs Ω(n log n) comparisons in the worst case — it must distinguish `n!` orders.
- [Counting sort](https://en.wikipedia.org/wiki/Counting_sort) runs in O(n + k) for integer keys in a range of size `k`, with O(k) counts plus O(n) output for stable placement.

### Quickselect and top-k

- [Quickselect](https://en.wikipedia.org/wiki/Quickselect) partitions around a random pivot and recurses into one side: O(n) expected, O(n²) worst.
- A size-`k` [min-heap](https://en.wikipedia.org/wiki/Binary_heap) keeps the largest `k` of `n` items in O(n log k) time and O(k) space.

### Random sampling and shuffling

- [Reservoir sampling](https://en.wikipedia.org/wiki/Reservoir_sampling) picks `k` items from a stream of unknown length: keep the first `k`, then replace a random slot with the i-th item with probability k/i — one pass, O(k) memory.
- [Fisher–Yates](https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle) shuffle: for `i` from `n−1` down to 1, swap `a[i]` with `a[rand(0..i)]` — O(n), every permutation equally likely.
- Swapping with `a[rand(0..n−1)]` at each step looks similar but is [biased](https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle#Naïve_method) (nⁿ outcomes can't split evenly over n! permutations).

## Data structures

### Heap invariants

- A [binary heap](https://en.wikipedia.org/wiki/Binary_heap) is a [complete tree](https://en.wikipedia.org/wiki/Binary_tree#Types_of_binary_trees) in an array; the root is the min or max, siblings are unordered.
- Peek O(1); insert and remove-root O(log n); [bottom-up construction is O(n)](https://en.wikipedia.org/wiki/Binary_heap#Building_a_heap_%28Heapify%29).

### Heap patterns

- [k-way merge](https://en.wikipedia.org/wiki/K-way_merge_algorithm): push the head of each of `k` sorted lists into a [min-heap](https://en.wikipedia.org/wiki/Binary_heap), pop and push the next from the same list — O(n log k).
- Running median with two heaps: a max-heap for the lower half, a min-heap for the upper, sizes differing by at most one — O(log n) per insert, O(1) median.
- Heaps can't delete arbitrary items cheaply: lazy deletion marks items removed and discards them when they reach the top.

### Hash tables and collisions

- Expected O(1) lookup and update, no ordering; collisions are resolved by [chaining](https://en.wikipedia.org/wiki/Hash_table#Separate_chaining) or [probing](https://en.wikipedia.org/wiki/Hash_table#Open_addressing), and the table rehashes past a [load threshold](https://en.wikipedia.org/wiki/Hash_table#Load_factor).
- Equal keys must hash equally; mutating a key's hashed fields after insertion makes it unfindable.

### Disjoint-set union

- [Union-find](https://en.wikipedia.org/wiki/Disjoint-set_data_structure) tracks components with `find` (representative) and `union` (merge); no efficient deletion or path queries.
- [Path compression](https://en.wikipedia.org/wiki/Disjoint-set_data_structure#Finding_set_representatives) + union by [size](https://en.wikipedia.org/wiki/Disjoint-set_data_structure#Union_by_size)/[rank](https://en.wikipedia.org/wiki/Disjoint-set_data_structure#Union_by_rank) gives [amortized](https://en.wikipedia.org/wiki/Amortized_analysis) O([α(n)](https://en.wikipedia.org/wiki/Ackermann_function#Inverse)) — effectively constant.

### Tries and prefix lookup

- A [trie](https://en.wikipedia.org/wiki/Trie) follows one edge per symbol: lookup is O(key length), independent of the number of keys.
- Prefix search is natural, but a node per prefix costs much more space than a hash map; [compressed tries](https://en.wikipedia.org/wiki/Radix_tree) merge single-child paths.

### LRU cache

- Hash map + [doubly linked list](https://en.wikipedia.org/wiki/Doubly_linked_list): the map finds a node in O(1), the list keeps [recency](https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_Recently_Used_%28LRU%29).
- Move a node to the front on every access and evict from the tail — both O(1).

### Fenwick and segment trees

- A [Fenwick tree](https://en.wikipedia.org/wiki/Fenwick_tree) (binary indexed tree) gives prefix sums with point updates, both O(log n), in one array.
- A [segment tree](https://cp-algorithms.com/data_structures/segment_tree.html) answers any associative range query (min, max, sum) with O(log n) updates; [lazy propagation](https://cp-algorithms.com/data_structures/segment_tree.html#range-updates-lazy-propagation) adds range updates.

## Trees and graphs

### Tree traversal and BST ordering

- [Inorder](https://en.wikipedia.org/wiki/Tree_traversal#In-order,_LNR) traversal of a [BST](https://en.wikipedia.org/wiki/Binary_search_tree) yields sorted keys; preorder suits serialization, postorder bottom-up aggregation.
- An unbalanced BST degrades to O(n) height; [AVL](https://en.wikipedia.org/wiki/AVL_tree)/[red-black](https://en.wikipedia.org/wiki/Red%E2%80%93black_tree) rotations keep operations O(log n).

### Graph representation and traversal

- An [adjacency list](https://en.wikipedia.org/wiki/Adjacency_list) takes O(V+E) space and supports [BFS](https://en.wikipedia.org/wiki/Breadth-first_search)/[DFS](https://en.wikipedia.org/wiki/Depth-first_search) in O(V+E); a [matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) takes O(V²) but tests an edge in O(1).
- BFS gives shortest paths by edge count; DFS exposes cycles, components, and finishing order.
- Mark a node visited when enqueuing it, not when dequeuing, to avoid duplicate BFS work.

### Topological ordering

- A [topological order](https://en.wikipedia.org/wiki/Topological_sorting) exists only for a [DAG](https://en.wikipedia.org/wiki/Directed_acyclic_graph).
- [Kahn's algorithm](https://en.wikipedia.org/wiki/Topological_sorting#Kahn's_algorithm) repeatedly removes zero-indegree vertices; fewer than `V` removals means a cycle.
- [DFS alternative](https://en.wikipedia.org/wiki/Topological_sorting#Depth-first_search): reverse finishing order, detecting back edges. Both O(V+E).

### Shortest-path choices

| Edge weights | Algorithm | Time with adjacency lists | Caveat |
|---|---|---|---|
| all equal, positive | [BFS](https://en.wikipedia.org/wiki/Breadth-first_search) | O(V+E) | counts edges |
| nonnegative | [Dijkstra](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm) + [binary heap](https://en.wikipedia.org/wiki/Binary_heap) | O((V+E) log V) | negative edges invalidate greedy settlement |
| negative allowed | [Bellman-Ford](https://en.wikipedia.org/wiki/Bellman%E2%80%93Ford_algorithm) | O(VE) | detects reachable negative cycles |
| [DAG](https://en.wikipedia.org/wiki/Directed_acyclic_graph), any weights | [topological relaxation](https://en.wikipedia.org/wiki/Topological_sorting#Application_to_shortest_path_finding) | O(V+E) | needs acyclic graph |

### Minimum spanning tree

- An [MST](https://en.wikipedia.org/wiki/Minimum_spanning_tree) connects all vertices of an undirected graph with minimum total weight — not a [shortest-path tree](https://en.wikipedia.org/wiki/Shortest-path_tree).
- [Kruskal](https://en.wikipedia.org/wiki/Kruskal%27s_algorithm) sorts edges and keeps those joining different [union-find](https://en.wikipedia.org/wiki/Disjoint-set_data_structure) components; [Prim](https://en.wikipedia.org/wiki/Prim%27s_algorithm) grows one tree from a min-edge priority queue.

## Dynamic programming

### DP state and order

- Define a state holding everything future decisions need, a [recurrence](https://en.wikipedia.org/wiki/Recurrence_relation), base cases, and an evaluation order where dependencies are ready.
- Top-down [memoization](https://en.wikipedia.org/wiki/Memoization) visits only reachable states; bottom-up tabulation fills them all. Cost = states × transitions.

### Knapsack and one-dimensional DP

- [0/1 knapsack](https://en.wikipedia.org/wiki/Knapsack_problem#0-1_knapsack_problem): iterate capacities downward per item so it isn't reused; upward iteration models unbounded reuse.
- O(nC) is [pseudopolynomial](https://en.wikipedia.org/wiki/Pseudo-polynomial_time): `C` is a number whose input length is only O(log C).

### Longest increasing subsequence

- The [O(n log n) method](https://en.wikipedia.org/wiki/Longest_increasing_subsequence#Efficient_algorithms) keeps the smallest tail for each length and binary-searches where each value goes.
- For strictly increasing, replace the first tail `>= x`; the tails array gives the length, not the subsequence itself.

### Two-sequence DP: LCS and edit distance

- [LCS](https://en.wikipedia.org/wiki/Longest_common_subsequence): `dp[i][j] = dp[i-1][j-1] + 1` on a match, else `max(dp[i-1][j], dp[i][j-1])`.
- [Edit distance](https://en.wikipedia.org/wiki/Levenshtein_distance): diagonal on a match, else `1 + min(insert, delete, replace)`.
- Both O(nm) time, reducible to O(min(n, m)) space with two rows.

### Bitmask DP

- Index DP by a subset encoded as bits: [travelling salesman](https://en.wikipedia.org/wiki/Held%E2%80%93Karp_algorithm) is `dp[mask][last]` in O(2ⁿ · n²) — feasible up to n ≈ 20.
- [Iterate submasks](https://cp-algorithms.com/algebra/all-submasks.html) of `mask` with `s = (s - 1) & mask`; over all masks that totals O(3ⁿ).

## Greedy, backtracking, and hardness

### Greedy proof pattern

- A [greedy choice](https://en.wikipedia.org/wiki/Greedy_algorithm) needs an exchange argument or a maintained invariant — locally best isn't enough.
- [Maximum non-overlapping intervals](https://en.wikipedia.org/wiki/Interval_scheduling): sort by earliest finish time; sorting by start or by length fails.

### Backtracking and pruning

- [Backtracking](https://en.wikipedia.org/wiki/Backtracking) walks a decision tree, undoing each choice after recursing; reject invalid partial solutions early.
- Prune only branches that can't produce an answer or [beat the best score](https://en.wikipedia.org/wiki/Branch_and_bound); enumerating all outputs stays exponential.

### Bit manipulation

- `x & (x − 1)` clears the lowest set bit, so `x > 0 && (x & (x − 1)) == 0` tests a power of two; `x & −x` isolates it.
- [XOR](https://en.wikipedia.org/wiki/Exclusive_or#Bitwise_operation) of all elements cancels pairs — finds the single unpaired number in O(1) space.

### Recognizing NP-hard problems

- [Traveling salesman](https://en.wikipedia.org/wiki/Travelling_salesman_problem), [subset sum](https://en.wikipedia.org/wiki/Subset_sum_problem), [knapsack](https://en.wikipedia.org/wiki/Knapsack_problem), [graph coloring](https://en.wikipedia.org/wiki/Graph_coloring), [SAT](https://en.wikipedia.org/wiki/Boolean_satisfiability_problem), [Hamiltonian path](https://en.wikipedia.org/wiki/Hamiltonian_path_problem), and [set cover](https://en.wikipedia.org/wiki/Set_cover_problem) are [NP-hard](https://en.wikipedia.org/wiki/NP-hardness) in general.
- No polynomial algorithm is known (none exists unless [P = NP](https://en.wikipedia.org/wiki/P_versus_NP_problem)); exact answers use exponential search with pruning, or [pseudopolynomial DP](https://en.wikipedia.org/wiki/Pseudo-polynomial_time) when numbers are small (subset sum, knapsack only).
- Otherwise use heuristics or an [approximation](https://en.wikipedia.org/wiki/Approximation_algorithm) algorithm where a guarantee exists ([greedy set cover](https://en.wikipedia.org/wiki/Set_cover_problem#Greedy_algorithm): [H(n)](https://en.wikipedia.org/wiki/Harmonic_number) ≤ ln n + 1); general TSP and coloring have no good ratio unless P = NP.
