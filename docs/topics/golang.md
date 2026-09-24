# Go

What experienced Go engineers forget before an interview, grouped by subtopic.

## Concurrency

### Scheduler (GMP)

- Goroutines (G) run on OS threads (M) through logical processors (P); **`GOMAXPROCS`** = number of Ps, defaults to CPU count.
- **Since Go 1.25**, the default `GOMAXPROCS` considers cgroup CPU limits (`GODEBUG=containermaxprocs`) and updates periodically as they change (`GODEBUG=updatemaxprocs`); before 1.25, Go ignored cgroup limits entirely, which is why third-party libraries like `automaxprocs` existed.
- Blocking syscall → the M is parked and the P moves to another M; network I/O goes through the **netpoller** and doesn't hold a thread.
- Preemption is asynchronous (signal-based) **since Go 1.14**, so tight loops no longer starve the scheduler.
- Goroutines start with a **2 KB** stack that grows and is copied as needed — this is why launching hundreds of thousands is normal.

### Channel axioms

| Operation | nil channel | closed channel |
|---|---|---|
| send | blocks forever | **panics** |
| receive | blocks forever | zero value, `ok == false` |
| close | panics | **panics** |

Only the sender should close a channel; `for range ch` ends when it closes.

### select

- Picks **randomly** among ready cases (avoids starvation); `default` makes it non-blocking.
- Setting a channel variable to `nil` disables its case — used to merge channels until all are closed.
- `time.Timer`/`time.Ticker` channels are **unbuffered since Go 1.23**, fixing stale-value races with `Stop`/`Reset`; **since Go 1.23** an unreferenced timer is also collectible even without calling `Stop`.

### Sync primitives

- `sync.Mutex` is **not reentrant** and must not be copied after first use (`go vet`'s `copylocks` catches this).
- `sync.RWMutex` blocks new readers once a writer is waiting, to avoid writer starvation.
- `sync.Once` plus `OnceFunc`/`OnceValue`/`OnceValues` (**1.21**) for once-only initialization.
- `WaitGroup.Go(f)` (**1.25**) starts a goroutine and handles `Add`/`Done` for you.

### More sync primitives

- Typed atomics (`atomic.Int64`, etc., **1.19**) replace the old `atomic.AddInt64(&x, ...)` style.
- `sync.Map` is optimized only for keys written once and read many times, or disjoint key sets per goroutine — a plain map + mutex is usually faster otherwise.
- `sync.Pool` contents can be dropped on **any** GC cycle, not just after two, and are cleared entirely under memory pressure.

### Memory model and races

- Happens-before is established by channel send/receive, mutex lock/unlock, `sync.Once`, and atomics — not by program order across goroutines.
- A data race is a bug the Go memory model does not fully define the outcome of — not as unconstrained as C/C++ UB, but a multiword value (an interface, a slice header) can still tear and corrupt. Detect with `go test -race` / `go run -race`; it only catches races that actually execute during the run.
- Rule of thumb: channels to hand off ownership or coordinate, a mutex to protect shared state in place.

### context.Context

- Carries cancellation, deadlines, and request-scoped values across API and goroutine boundaries; canceling a parent cancels all children.
- `WithCancelCause` (**1.20**) lets callers retrieve *why* a context was canceled via `context.Cause(ctx)`.
- `AfterFunc` and `WithoutCancel` (**1.21**): run a function on cancellation, or derive a context that keeps values but drops the parent's cancellation.
- Pass as the **first parameter**, never store in a struct; use `WithValue` only for request-scoped data, not optional parameters.

### Patterns and goroutine leaks

- Worker pool, fan-in/fan-out, pipeline, and semaphore (buffered channel `make(chan struct{}, n)`) are the standard shapes.
- `errgroup.Group` (`golang.org/x/sync/errgroup`) runs goroutines, returns the first error, and can cap concurrency with `SetLimit`.
- A **goroutine leak** is a goroutine blocked forever — a send nobody receives, a receive on a channel that never closes, or a loop that ignores `ctx.Done()`. Detect with the pprof goroutine profile or `go.uber.org/goleak`.
- `testing/synctest` (**1.25**) runs concurrent code in a fake-clock "bubble" so time-dependent tests run instantly and deterministically.

## Memory management

### Escape analysis

- The compiler decides stack vs heap by proving whether a value outlives the function; see the decisions with `go build -gcflags=-m`.
- Common causes: returning a pointer, storing a pointer in a heap object/global, boxing a value into an interface, closures capturing variables, and slices whose size isn't known at compile time.

### Garbage collector

- Concurrent, tri-color mark-sweep; **non-generational** and **non-compacting**; a write barrier keeps marking correct while the program runs.
- **`GOGC`** (default 100) controls heap growth before the next cycle; **`GOMEMLIMIT`** (**1.19**) sets a soft memory cap, useful in containers.
- **Green Tea GC** improves memory locality by scanning objects in larger, contiguous spans; introduced experimental (`GOEXPERIMENT=greenteagc`) in **1.25**, it became the default collector in **1.26**.

### Reducing allocations

- Preallocate slices/maps with a known capacity, reuse buffers via `sync.Pool`, avoid unnecessary `[]byte`↔`string` conversions (both copy), build strings with `strings.Builder`.

## Slices, maps, strings

### Slice mechanics

- A slice header is `{pointer, len, cap}`; copying the header still shares the backing array.
- `append` grows in place while `len < cap`; otherwise it allocates roughly **2×** under 256 elements, then a smoother ~1.25× for larger slices, and copies.
- Aliasing gotcha: `b := a[:2]; append(b, x)` can overwrite `a[2]` if capacity allows. Use the full slice expression `a[lo:hi:max]` to cap capacity and force a fresh allocation on append.
- A small subslice of a huge array keeps the **whole array** alive for the GC — copy out the needed part if keeping it long-term.

### Maps

- Hash table; implemented as **Swiss tables since Go 1.24** (faster, but iteration order was already randomized and remains so).
- Concurrent write (or write + read) is a **fatal, unrecoverable** error, not a panic you can `recover`.
- Maps never shrink after deletions; `clear(m)` (**1.21**) empties one without reallocating the header.
- Map values aren't addressable: `&m[k]` and `m[k].field = x` don't compile for struct values.

### Strings

- Immutable byte sequence, usually UTF-8; `len(s)` counts **bytes**, `range s` decodes and yields **runes** with byte offsets.
- Invalid UTF-8 encountered during `range` yields `U+FFFD`.
- `string`↔`[]byte` conversions copy; substrings share the original's backing memory.

## Types and interfaces

### Interface internals

- An interface value is a **(type, value)** pair; it is `nil` only when both are nil — a nil `*T` stored in an `error` is **not** `== nil`.
- Comparing two interface values **panics** if their dynamic type is not comparable (e.g. holds a slice).
- Compile-time satisfaction check: `var _ io.Reader = (*MyReader)(nil)`.

### Method sets and embedding

- Pointer-receiver methods are only in the method set of `*T`, so only `*T` satisfies an interface requiring them.
- Embedding promotes fields/methods but is **not** inheritance: no polymorphism — a promoted method calling its own method calls its own version, never an outer "override." A same-named outer method shadows it.
- An embedded interface in a struct that's left unimplemented panics only when the missing method is actually called.

### Generics

- Constraints are interfaces defining a **type set**; `~int` accepts any type whose underlying type is `int`; `comparable` allows `==`/map keys.
- Compiled via **GC-shape stenciling** — types with the same underlying shape share code, which can still be slower than hand-specialized code in hot paths.
- No type parameters on methods, and no specialization.

### Iterators and loop variables

- **Range-over-func** iterators (`iter.Seq`, `iter.Seq2`, **1.23**) let `range` work over a function, powering the `slices`/`maps` iterator helpers.
- **Since Go 1.22**, each loop iteration gets its own variable — the classic closure-capture-in-loop bug requires `go 1.21` or earlier semantics to reproduce.

## Errors, defer, panic

### Error wrapping

- `fmt.Errorf("...: %w", err)` wraps; `errors.Is` walks the chain comparing to a sentinel, `errors.As` extracts a concrete type. Never compare a wrapped error with `==`.
- `errors.Join` (**1.20**) combines multiple errors into one that `Is`/`As` can still unwrap.

### defer and panic

- `defer` arguments are evaluated **immediately**, execution is **LIFO**; a deferred closure can modify named return values.
- `defer` inside a long-running loop accumulates — calls only run at function return, not at loop end.
- `recover()` only stops a panic when called **directly inside a deferred function**; an unrecovered panic in any goroutine kills the whole process.

## Testing and profiling

### Test tooling

- Table-driven tests with `t.Run` subtests, `t.Parallel()`, `t.Cleanup()`.
- Benchmarks use `b.Loop()` (**1.24**), which replaced the manual `for i := 0; i < b.N; i++` idiom and avoids some compiler over-optimization pitfalls.
- Fuzzing (`func FuzzX`, **1.18**) generates inputs from a seed corpus.

### Profiling

- **pprof** profiles: CPU, heap (alloc vs inuse), goroutine, block, mutex — collected via test flags or `net/http/pprof` in a running service.
- `go tool trace` shows scheduler and latency behavior over time, complementing pprof's aggregate view.
