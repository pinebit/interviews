# Operating Systems

What experienced engineers forget about Linux and OS internals before an interview, grouped by subtopic. For containers (namespaces, cgroups) see [devops.md](devops.md); for TCP and DNS see [networking.md](networking.md).

## Processes and threads

### Processes vs threads

- A **process** has its own address space, file descriptors, and credentials; **threads** share the address space and descriptors of their process.
- On Linux both are **tasks** created by `clone()` with different sharing flags; the scheduler treats them alike.

### fork, exec, copy-on-write

- **`fork()`** duplicates the process lazily: pages are shared **copy-on-write** until one side writes.
- **`exec()`** replaces the program image, keeping the PID and open descriptors (unless `O_CLOEXEC`).
- Forking a multi-threaded process copies only the calling thread — locks held by others stay locked forever in the child.

### Zombies and orphans

- A **zombie** has exited but its parent hasn't called `wait()` — it holds only a PID table entry, but enough of them exhaust PIDs.
- An **orphan** is re-parented to PID 1 (or a subreaper), which must reap it — why containers need a proper init.

### Signals

- **`SIGTERM`** asks politely and can be handled; **`SIGKILL`** and `SIGSTOP` can't be caught or ignored.
- `SIGCHLD` tells a parent a child changed state; `SIGHUP` conventionally means reload config; `SIGPIPE` kills a process writing to a closed socket unless ignored.
- Signal handlers may call only **async-signal-safe** functions (not `malloc`, not `printf`).

### User mode, kernel mode, syscalls

- A **syscall** switches to kernel mode — a few hundred nanoseconds, much more with mitigations and cache effects; batching syscalls matters at high rates.
- The **vDSO** maps some calls (`clock_gettime`) into user space so they cost no mode switch.

## Scheduling

### Context switches

- A switch saves and restores registers and may change the address space; the direct cost is **~1–5 µs**, the indirect cost is cold **caches and TLB**.
- Thread switches within a process are cheaper — no page-table change.
- Thousands of runnable threads mostly add switching overhead; that's why event loops and green threads (goroutines) exist.

### Linux scheduler

- **EEVDF** replaced **CFS** as the default scheduler in **Linux 6.6** (2023): each task gets a fair share weighted by its `nice` value, with better latency for short-running tasks.
- Real-time policies (`SCHED_FIFO`, `SCHED_RR`) always run before normal tasks.

### CPU quotas and throttling

- A cgroup CPU limit is a **quota per 100 ms period**: a 1-CPU limit lets 4 threads use 25 ms each, then **throttles** the whole group for the rest of the period — latency spikes while average CPU looks low.
- Watch `nr_throttled` in `cpu.stat`; match thread-pool sizes (`GOMAXPROCS`, JVM) to the quota.

### Load average

- Counts tasks that are **running, runnable, or in uninterruptible sleep** (D state, usually disk or NFS I/O), averaged over 1, 5, 15 minutes.
- High load with idle CPUs means tasks are **blocked on I/O**, not CPU-bound; compare against the core count.

## Memory

### Virtual memory and the TLB

- Each process sees a private virtual address space mapped to physical frames in **4 KB pages** through page tables.
- The **TLB** caches translations; **huge pages** (2 MB, 1 GB) cut TLB misses for large heaps — transparent huge pages can also cause latency spikes during compaction, so databases often disable them.

### Page faults

- **Minor fault**: the page is in memory and just needs mapping (first touch, copy-on-write).
- **Major fault**: the page must be read from disk (swap or a memory-mapped file) — milliseconds each.

### Overcommit and the OOM killer

- `malloc` usually succeeds without backing memory; physical pages are allocated **on first touch** (overcommit).
- When memory runs out, the **OOM killer** kills the process with the highest `oom_score` (tuned by `oom_score_adj`); in a container, hitting the **cgroup limit** triggers an OOM kill inside that cgroup only.

### cgroup memory limits

- cgroup v2 **`memory.max`** is the hard limit: exceeding it OOM-kills inside the cgroup (a Kubernetes memory limit maps here).
- **`memory.high`** is a soft limit: above it the kernel throttles and reclaims aggressively instead of killing.
- Page cache counts toward the cgroup but is reclaimed first, so watch the **working set** (usage minus inactive file pages), which the kubelet uses for eviction.

### Swap

- Swap moves anonymous pages to disk under pressure: fewer OOM kills, but touching them costs **major faults**.
- `vm.swappiness` biases reclaim between page cache and anonymous memory; latency-sensitive servers usually run with little or no swap.

### NUMA

- On multi-socket servers each socket has local memory; reaching another node's memory costs **1.5–2×** the latency.
- Linux allocates on the node of the thread that **first touches** a page, so a thread moved to another socket reads remotely.
- Pin latency-critical processes and their memory with `numactl`; `numastat` shows remote allocations.

### Page cache and "free" memory

- Unused RAM caches file data (**page cache**), so low `free` is normal — check **`available`** in `free -m`.
- `write()` returns once data is in the page cache; dirty pages are flushed later unless you call **`fsync`**.

### RSS, VSZ, and shared memory

- VSZ counts all mapped virtual memory (mostly irrelevant); **RSS** counts resident pages but double-counts shared ones; **PSS** splits shared pages proportionally.
- Default thread stack size is typically **8 MB** of virtual memory (`ulimit -s`), mostly untouched.

## Files and I/O

### File descriptors and inodes

- Everything open — files, sockets, pipes — is a file descriptor; the soft limit is often **1024** (`ulimit -n`), causing "too many open files" on busy servers.
- A filename points to an inode; deleting an open file frees its space only when the **last descriptor closes** — why `df` and `du` can disagree.
- **Hard links** are extra names for the same inode (same filesystem only); symlinks store a path and can dangle.

### I/O multiplexing: select, poll, epoll

- `select`/`poll` pass the whole descriptor set on every call — O(n) per wait; `select` is capped at 1024 descriptors.
- **`epoll`** registers descriptors once and returns only ready ones — O(ready); the basis of Nginx, Node's libuv, and Go's netpoller (kqueue on BSD/macOS).
- **Level-triggered** keeps reporting while data remains; **edge-triggered** reports once per change, so you must read until `EAGAIN`.

### io_uring

- **io_uring** (Linux 5.1+) submits and completes I/O through rings shared with the kernel — true async file and network I/O with few syscalls.
- Its large kernel attack surface means many container runtimes and hardened hosts **block it via seccomp**.

### Durability and fsync

- Data is durable only after **`fsync`** (or `fdatasync`); a new file also needs its **directory** fsynced.
- After an fsync error, Linux may drop the dirty pages and a retry can falsely succeed — since 2018's "fsyncgate", **PostgreSQL panics** on fsync failure instead of retrying.

### Zero-copy I/O

- **`sendfile`**/`splice` move file data to a socket inside the kernel, skipping user-space copies — how static file servers and Kafka reach high throughput.
- **`mmap`** maps a file into memory; reads become page faults served from the page cache.

## Synchronization

### Mutexes, spinlocks, futexes

- A **spinlock** busy-waits — only for very short critical sections, never while sleeping.
- A mutex sleeps when contended; Linux implements it on **futexes**, which stay entirely in user space until there's contention.
- A semaphore counts permits (connection limits); a **condition variable** waits for a predicate and must be re-checked in a loop (spurious wakeups).

### Deadlock conditions

- All four **Coffman conditions** must hold: mutual exclusion, hold and wait, no preemption, **circular wait**.
- Break one — usually circular wait, with a global **lock ordering** — or use `trylock` with timeouts.

### Priority inversion

- A low-priority task holds a lock needed by a high-priority task while a medium-priority task starves it (Mars Pathfinder, 1997).
- **Priority inheritance** temporarily boosts the lock holder.

### False sharing

- Cores transfer memory in **64-byte cache lines**; two threads writing different variables on the same line keep invalidating each other's caches.
- Pad or align hot per-thread counters to separate lines.

## Performance analysis

### Linux observability tools

- `top`/`htop` (CPU per process), `vmstat 1` (run queue, swap, context switches), `iostat -x 1` (disk utilization, await), `pidstat` (per-process CPU and I/O).
- **`perf`** samples stacks with low overhead → flame graphs; **eBPF** tools (`bpftrace`, bcc) trace kernel events in production safely.
- **`strace`** shows every syscall but slows the process heavily (ptrace) — avoid on hot production paths.

### CPU time breakdown

- us (user code), sy (kernel), **wa** (idle waiting for I/O), **st** (stolen by the hypervisor — noisy neighbors on VMs).
- High sy points at syscall-heavy code or lock contention; high **st** means you need a bigger or dedicated instance, not code changes.
