# Operating Systems

What experienced engineers forget about Linux and OS internals before an interview, grouped by subtopic. For containers (namespaces, cgroups) see [devops.md](devops.md); for TCP and DNS see [networking.md](networking.md).

## Processes and threads

### fork, exec, copy-on-write

- [`fork()`](https://man7.org/linux/man-pages/man2/fork.2.html) duplicates the process lazily: pages are shared [copy-on-write](https://en.wikipedia.org/wiki/Copy-on-write) until one side writes.
- [`exec()`](https://man7.org/linux/man-pages/man2/execve.2.html) replaces the program image, keeping the PID and open descriptors (unless [`O_CLOEXEC`](https://man7.org/linux/man-pages/man2/open.2.html)).
- Forking a multi-threaded process copies only the calling thread — locks held by others stay locked forever in the child.
- On Linux, processes and threads are both tasks created by [`clone()`](https://man7.org/linux/man-pages/man2/clone.2.html) with different sharing flags; the scheduler treats them alike.

### Process states

| State | Meaning |
|---|---|
| R | [running or runnable](https://man7.org/linux/man-pages/man1/ps.1.html#PROCESS_STATE_CODES) (on a run queue) |
| S | interruptible sleep: waiting for an event; signals wake it |
| D | uninterruptible sleep, usually disk or NFS I/O; even `SIGKILL` waits, and it counts toward [load average](https://en.wikipedia.org/wiki/Load_%28computing%29#Linux_as_an_example) |
| Z | [zombie](https://en.wikipedia.org/wiki/Zombie_process): exited, not yet reaped by its parent |
| T | stopped (`SIGSTOP`, a debugger) |

### Zombies and orphans

- A [zombie](https://en.wikipedia.org/wiki/Zombie_process) has exited but its parent hasn't called [`wait()`](https://man7.org/linux/man-pages/man2/wait.2.html) — it holds only a PID table entry, but enough of them exhaust PIDs.
- An [orphan](https://en.wikipedia.org/wiki/Orphan_process) is re-parented to PID 1 (or a [subreaper](https://man7.org/linux/man-pages/man2/PR_SET_CHILD_SUBREAPER.2const.html)), which must reap it — why containers need a [proper init](https://github.com/krallin/tini).

### Signals

- [`SIGTERM`](https://man7.org/linux/man-pages/man7/signal.7.html) asks politely and can be handled; `SIGKILL` and `SIGSTOP` can't be caught or ignored.
- `SIGCHLD` tells a parent a child changed state; `SIGHUP` conventionally means reload config; `SIGPIPE` kills a process writing to a closed socket unless ignored.
- Signal handlers may call only [async-signal-safe](https://man7.org/linux/man-pages/man7/signal-safety.7.html) functions (not `malloc`, not `printf`).

### User mode, kernel mode, syscalls

- A [syscall](https://en.wikipedia.org/wiki/System_call) switches to kernel mode — a few hundred nanoseconds, much more with [mitigations](https://docs.kernel.org/admin-guide/hw-vuln/index.html) and cache effects; batching syscalls matters at high rates.
- The [vDSO](https://man7.org/linux/man-pages/man7/vdso.7.html) maps some calls (`clock_gettime`) into user space so they cost no mode switch.

## Scheduling

### Context switches

- A switch saves and restores registers and may change the address space; the direct cost is ~1–5 µs, the indirect cost is cold caches and [TLB](https://en.wikipedia.org/wiki/Translation_lookaside_buffer).
- Thread switches within a process are cheaper — no page-table change.
- Thousands of runnable threads mostly add switching overhead; that's why event loops and [green threads](https://en.wikipedia.org/wiki/Green_thread) ([goroutines](golang.md)) exist.

### Linux scheduler

- [EEVDF](https://docs.kernel.org/scheduler/sched-eevdf.html) replaced [CFS](https://docs.kernel.org/scheduler/sched-design-CFS.html) as the default scheduler in [Linux 6.6](https://kernelnewbies.org/Linux_6.6#New_task_scheduler:_EEVDF) (2023): each task gets a fair share weighted by its [`nice`](https://man7.org/linux/man-pages/man7/sched.7.html) value, with better latency for short-running tasks.
- [Real-time policies](https://man7.org/linux/man-pages/man7/sched.7.html) (`SCHED_FIFO`, `SCHED_RR`) always run before normal tasks.

### CPU quotas and throttling

- A cgroup CPU limit is a quota per period ([`cpu.max`](https://docs.kernel.org/admin-guide/cgroup-v2.html#cpu-interface-files), default 100 ms): a 1-CPU limit lets 4 threads use 25 ms each, then throttles the whole group for the rest of the period — latency spikes while average CPU looks low.
- Watch `nr_throttled` in `cpu.stat`; match thread-pool sizes ([`GOMAXPROCS`](https://pkg.go.dev/runtime#GOMAXPROCS), JVM) to the quota.

### Load average

- Counts tasks that are running, runnable, or in [uninterruptible sleep](https://man7.org/linux/man-pages/man1/ps.1.html#PROCESS_STATE_CODES) (D state, usually disk or NFS I/O), [averaged over 1, 5, 15 minutes](https://en.wikipedia.org/wiki/Load_%28computing%29#Linux_as_an_example).
- High load with idle CPUs means tasks are blocked on I/O, not CPU-bound; compare against the core count.

## Memory

### Virtual memory and the TLB

- Each process sees a private [virtual address space](https://en.wikipedia.org/wiki/Virtual_memory) mapped to physical frames in pages (4 KB on x86-64; arm64 can use 16 or 64 KB) through [page tables](https://en.wikipedia.org/wiki/Page_table).
- The [TLB](https://en.wikipedia.org/wiki/Translation_lookaside_buffer) caches translations; [huge pages](https://docs.kernel.org/admin-guide/mm/hugetlbpage.html) (2 MB, 1 GB) cut TLB misses for large heaps — [transparent huge pages](https://docs.kernel.org/admin-guide/mm/transhuge.html) can also cause latency spikes during compaction, so databases often disable them.

### Page faults

- [Minor fault](https://en.wikipedia.org/wiki/Page_fault#Minor_page_fault): served without disk I/O — map a cached page, allocate on first touch, or [copy-on-write](https://en.wikipedia.org/wiki/Copy-on-write).
- [Major fault](https://en.wikipedia.org/wiki/Page_fault#Major_page_fault): the page must be read from disk (swap or a memory-mapped file) — tens of microseconds on NVMe, milliseconds on spinning disks.

### Overcommit and the OOM killer

- `malloc` usually succeeds without backing memory ([overcommit](https://docs.kernel.org/mm/overcommit-accounting.html)); physical pages are allocated on [first touch](https://docs.kernel.org/admin-guide/mm/concepts.html#anonymous-memory).
- When memory runs out, the [OOM killer](https://docs.kernel.org/admin-guide/mm/concepts.html#oom-killer) kills the process with the highest [`oom_score`](https://man7.org/linux/man-pages/man5/proc_pid_oom_score.5.html) (tuned by [`oom_score_adj`](https://man7.org/linux/man-pages/man5/proc_pid_oom_score_adj.5.html)); in a container, a [cgroup limit](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files) that reclaim can't satisfy triggers an OOM kill inside that cgroup only.

### cgroup memory limits

- cgroup v2 [`memory.max`](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files) is the hard limit: at it the kernel reclaims, and OOM-kills inside the cgroup only if reclaim fails (a [Kubernetes memory limit](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) maps here).
- [`memory.high`](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files) is a soft limit: above it the kernel throttles and reclaims aggressively instead of killing.
- [Page cache](https://en.wikipedia.org/wiki/Page_cache) counts toward the cgroup but is usually reclaimed first, so watch the working set (usage minus inactive file pages), which the [kubelet uses for eviction](https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/).

### Swap

- [Swap](https://en.wikipedia.org/wiki/Memory_paging#Swap_files_and_partitions) moves anonymous pages to disk under pressure: fewer OOM kills, but touching them costs [major faults](https://en.wikipedia.org/wiki/Page_fault#Major_page_fault).
- [`vm.swappiness`](https://docs.kernel.org/admin-guide/sysctl/vm.html#swappiness) biases reclaim between [page cache](https://en.wikipedia.org/wiki/Page_cache) and anonymous memory; latency-sensitive servers usually run with little or no swap.

### NUMA

- On multi-socket servers each socket has [local memory](https://en.wikipedia.org/wiki/Non-uniform_memory_access); reaching another node's memory costs 1.5–2× the latency.
- Linux allocates on the node of the thread that first touches a page, so a thread moved to another socket reads remotely.
- Pin latency-critical processes and their memory with [`numactl`](https://man7.org/linux/man-pages/man8/numactl.8.html); [`numastat`](https://man7.org/linux/man-pages/man8/numastat.8.html) shows remote allocations.

### Page cache and "free" memory

- Unused RAM caches file data ([page cache](https://en.wikipedia.org/wiki/Page_cache)), so low `free` is normal — check `available` in [`free -m`](https://man7.org/linux/man-pages/man1/free.1.html).
- [`write()`](https://man7.org/linux/man-pages/man2/write.2.html) returns once data is in the page cache; dirty pages are flushed later unless you call [`fsync`](https://man7.org/linux/man-pages/man2/fsync.2.html).

### RSS, VSZ, and shared memory

- [VSZ](https://man7.org/linux/man-pages/man1/ps.1.html) counts all mapped virtual memory (mostly irrelevant); [RSS](https://en.wikipedia.org/wiki/Resident_set_size) counts resident pages but double-counts shared ones; [PSS](https://en.wikipedia.org/wiki/Proportional_set_size) splits shared pages proportionally.
- Default thread stack size is typically 8 MB of virtual memory (`ulimit -s`), mostly untouched.

## Files and I/O

### File descriptors and inodes

- Everything open — files, sockets, pipes — is a [file descriptor](https://en.wikipedia.org/wiki/File_descriptor); the [soft limit](https://man7.org/linux/man-pages/man2/getrlimit.2.html) is often 1024 (`ulimit -n`), causing "too many open files" on busy servers.
- A filename points to an [inode](https://en.wikipedia.org/wiki/Inode); deleting a file frees its space only when no [hard links](https://en.wikipedia.org/wiki/Hard_link), open descriptors, or mappings remain — why `df` and `du` can disagree.
- Hard links are extra names for the same inode (same filesystem only); [symlinks](https://en.wikipedia.org/wiki/Symbolic_link) store a path and can dangle.

### I/O multiplexing: select, poll, epoll

- [`select`](https://man7.org/linux/man-pages/man2/select.2.html)/[`poll`](https://man7.org/linux/man-pages/man2/poll.2.html) pass the whole descriptor set on every call — O(n) per wait; `select` is capped at 1024 descriptors.
- [`epoll`](https://man7.org/linux/man-pages/man7/epoll.7.html) registers descriptors once and returns only ready ones — O(ready); the basis of Nginx, Node's [libuv](https://docs.libuv.org/en/v1.x/design.html), and Go's [netpoller](golang.md) ([kqueue](https://man.freebsd.org/cgi/man.cgi?kqueue) on BSD/macOS).
- [Level-triggered](https://man7.org/linux/man-pages/man7/epoll.7.html) keeps reporting while data remains; edge-triggered reports once per change, so you must read until `EAGAIN`.

### io_uring

- [io_uring](https://man7.org/linux/man-pages/man7/io_uring.7.html) ([Linux 5.1+](https://kernelnewbies.org/Linux_5.1)) submits and completes I/O through rings shared with the kernel — true async file and network I/O with few syscalls.
- Its large kernel attack surface means many container runtimes and hardened hosts [block it via seccomp](https://docs.docker.com/engine/security/seccomp/).

### Durability and fsync

- Data is durable only after [`fsync`](https://man7.org/linux/man-pages/man2/fsync.2.html) (or `fdatasync`); a new file also needs its directory fsynced.
- After an fsync error, Linux may drop the dirty pages and a retry can falsely succeed — since 2018's "[fsyncgate](https://wiki.postgresql.org/wiki/Fsync_Errors)", [PostgreSQL panics](https://www.postgresql.org/docs/current/runtime-config-error-handling.html#GUC-DATA-SYNC-RETRY) on fsync failure instead of retrying.

### Atomic file replace

- Write a temp file in the same directory → [`fsync`](https://man7.org/linux/man-pages/man2/fsync.2.html) it → [`rename()`](https://man7.org/linux/man-pages/man2/rename.2.html) it over the target → `fsync` the directory.
- `rename` within one filesystem is [atomic](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html) on POSIX: readers see the old or the new file, never a torn mix.
- Skipping the first `fsync` can leave an [empty file after a crash](https://lwn.net/Articles/322823/) (the rename persisted before the data).

### Zero-copy I/O

- [`sendfile`](https://man7.org/linux/man-pages/man2/sendfile.2.html) (or [`splice`](https://man7.org/linux/man-pages/man2/splice.2.html) through a pipe) moves file data to a socket inside the kernel, skipping user-space copies — how static file servers and [Kafka](https://kafka.apache.org/43/design/design/#efficiency) reach high throughput.
- [`mmap`](https://man7.org/linux/man-pages/man2/mmap.2.html) maps a file into memory; reads become page faults served from the [page cache](https://en.wikipedia.org/wiki/Page_cache).

## Synchronization

### Mutexes, spinlocks, futexes

- A [spinlock](https://en.wikipedia.org/wiki/Spinlock) busy-waits — only for very short critical sections, never while sleeping.
- A [mutex](https://man7.org/linux/man-pages/man3/pthread_mutex_lock.3p.html) sleeps when contended; Linux implements it on [futexes](https://man7.org/linux/man-pages/man7/futex.7.html), which stay entirely in user space until there's contention.
- A [semaphore](https://en.wikipedia.org/wiki/Semaphore_%28programming%29) counts permits (connection limits); a [condition variable](https://en.wikipedia.org/wiki/Monitor_%28synchronization%29#Condition_variables) waits for a predicate and must be re-checked in a loop ([spurious wakeups](https://en.wikipedia.org/wiki/Spurious_wakeup)).

### Deadlock conditions

- All four [Coffman conditions](https://en.wikipedia.org/wiki/Deadlock_%28computer_science%29#Conditions) must hold: mutual exclusion, hold and wait, no preemption, circular wait.
- Break one — usually circular wait, with a global lock ordering — or use [`trylock`](https://man7.org/linux/man-pages/man3/pthread_mutex_lock.3p.html) with timeouts.

### Atomics, CAS, and the ABA problem

- [Compare-and-swap](https://en.wikipedia.org/wiki/Compare-and-swap) writes only if the value still equals the expected one; retry loops build lock-free stacks, counters, and mutex fast paths.
- [ABA](https://en.wikipedia.org/wiki/ABA_problem): the value goes A → B → A between the read and the CAS, so a stale CAS succeeds (a popped stack node freed and reused); fix with version-tagged pointers or safe reclamation ([hazard pointers](https://en.wikipedia.org/wiki/Hazard_pointer), epochs).
- Under heavy contention, CAS loops bounce the cache line between cores and can be slower than a mutex.
- x86 is strongly ordered ([TSO](https://www.cl.cam.ac.uk/~pes20/weakmemory/cacm.pdf)), ARM weakly ordered, so code that works on x86 can break on ARM without the right memory orderings ([rust.md](rust.md)).

### False sharing

- Cores transfer memory in [cache lines](https://en.wikipedia.org/wiki/CPU_cache#Cache_entries) (64 bytes on x86-64, 128 on Apple M-series); two threads writing different variables on the same line [keep invalidating each other's caches](https://en.wikipedia.org/wiki/False_sharing).
- Pad or align hot per-thread counters to separate lines.

## Performance analysis

### Linux observability tools

- [`perf`](https://perfwiki.github.io/main/) samples stacks with low overhead → [flame graphs](https://www.brendangregg.com/flamegraphs.html); [eBPF](https://ebpf.io/what-is-ebpf/) tools ([`bpftrace`](https://github.com/bpftrace/bpftrace), [bcc](https://github.com/iovisor/bcc)) trace kernel events in production safely.
- [`strace`](https://strace.io/) shows every syscall but slows the process heavily ([ptrace](https://man7.org/linux/man-pages/man2/ptrace.2.html)) — avoid on hot production paths.

### Memory hierarchy latencies

| Level | Latency |
|---|---|
| L1 cache | ~1 ns |
| L2 cache | ~4 ns |
| L3 cache | ~10–40 ns |
| DRAM | ~100 ns |
| NVMe SSD read | ~10–100 µs |

Sequential access and contiguous layouts (arrays over linked lists, [struct-of-arrays](https://en.wikipedia.org/wiki/AoS_and_SoA)) win through [prefetching](https://en.wikipedia.org/wiki/Cache_prefetching) and full cache-line use.

### CPU time breakdown

- `us` (user code), `sy` (kernel), `wa` (idle waiting for I/O), `st` ([stolen by the hypervisor](https://man7.org/linux/man-pages/man1/top.1.html) — noisy neighbors on VMs).
- High `sy` points at syscall-heavy code or lock contention; high `st` means you need a bigger or dedicated instance, not code changes.
