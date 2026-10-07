# Go

What experienced Go engineers forget before an interview, grouped by subtopic.

## Concurrency

### Scheduler (GMP)

- Goroutines (G) run on OS threads (M) through logical processors (P); [`GOMAXPROCS`](https://pkg.go.dev/runtime#GOMAXPROCS) = number of Ps.
- Default = min(logical CPUs, affinity mask); since Go 1.25 also [capped by the cgroup CPU limit](https://go.dev/doc/go1.25#container-aware-gomaxprocs) (rounded up, floor 2) and updated when it changes — before that, containers needed [`automaxprocs`](https://github.com/uber-go/automaxprocs).
- Blocking syscall → the M is parked and the P moves to another M; network I/O goes through the netpoller and doesn't hold a thread.
- Each P has a local run queue (256 goroutines) plus a `runnext` slot; an idle P takes half of another P's queue ([work stealing](https://en.wikipedia.org/wiki/Work_stealing)), and every 61st schedule checks the global queue for fairness.
- Preemption is [asynchronous (signal-based)](https://go.dev/doc/go1.14#runtime) since Go 1.14, so tight loops no longer starve the scheduler.
- Goroutines start with a 2 KB stack that grows and is copied as needed — this is why launching hundreds of thousands is normal.

### Channel axioms

| Operation | nil channel | closed channel |
|---|---|---|
| send | blocks forever | panics |
| receive | blocks forever | buffered values first, then zero value, `ok == false` |
| close | panics | panics |

Only the sender should [close](https://go.dev/ref/spec#Close) a channel; [`for range ch`](https://go.dev/ref/spec#For_range) ends once it's closed and drained.

### select

- Picks randomly among [ready cases](https://go.dev/ref/spec#Select_statements) (avoids [starvation](https://en.wikipedia.org/wiki/Starvation_%28computer_science%29)); `default` makes it non-blocking.
- Setting a channel variable to `nil` disables its case — used to merge channels until all are closed.
- [`time.Timer`](https://pkg.go.dev/time#Timer)/[`time.Ticker`](https://pkg.go.dev/time#Ticker) channels are unbuffered since Go 1.23, fixing stale-value races with `Stop`/`Reset`, and an unreferenced timer is collectible without calling `Stop`; both [need a `go 1.23`+ line in `go.mod`](https://go.dev/doc/go1.23#timer-changes) until Go 1.27 [removed the `asynctimerchan` opt-out](https://go.dev/doc/go1.27#runtime).

### Sync primitives

- [`sync.Mutex`](https://pkg.go.dev/sync#Mutex) is not [reentrant](https://en.wikipedia.org/wiki/Reentrant_mutex) and must not be copied after first use (`go vet`'s [`copylocks`](https://pkg.go.dev/golang.org/x/tools/go/analysis/passes/copylock) catches this).
- [`sync.RWMutex`](https://pkg.go.dev/sync#RWMutex) blocks new readers once a writer is waiting, to avoid writer starvation.
- [`sync.Once`](https://pkg.go.dev/sync#Once) plus [`OnceFunc`](https://pkg.go.dev/sync#OnceFunc)/[`OnceValue`](https://pkg.go.dev/sync#OnceValue)/[`OnceValues`](https://pkg.go.dev/sync#OnceValues) (1.21) for once-only initialization.
- [`WaitGroup.Go(f)`](https://pkg.go.dev/sync#WaitGroup.Go) (1.25) starts a goroutine and handles `Add`/`Done` for you.

### Atomics, sync.Map, sync.Pool

- Typed atomics ([`atomic.Int64`](https://pkg.go.dev/sync/atomic#Int64), etc., 1.19) replace the old `atomic.AddInt64(&x, ...)` style.
- [`sync.Map`](https://pkg.go.dev/sync#Map) is optimized only for keys written once and read many times, or disjoint key sets per goroutine — a plain map + mutex is usually faster otherwise.
- [`sync.Pool`](https://pkg.go.dev/sync#Pool) items are moved to a [victim cache](https://go.dev/doc/go1.13#syncpkgsync) at each GC and freed at the next one (since Go 1.13), so an unused item survives about two GC cycles — never use it as a cache that must hold data.

### Memory model and races

- [Happens-before](https://go.dev/ref/mem) is established by channel send/receive, mutex lock/unlock, `sync.Once`, and atomics — not by program order across goroutines.
- A data race is less undefined than in C/C++, but multiword values (interfaces, slice headers, strings) can tear and corrupt memory.
- [`-race`](https://go.dev/doc/articles/race_detector) detects only races that actually execute during the run.
- Rule of thumb: channels to hand off ownership or coordinate, a mutex to protect shared state in place.

### context.Context

- Carries cancellation, deadlines, and request-scoped values across API and goroutine boundaries; canceling a parent cancels all children.
- [`WithCancelCause`](https://pkg.go.dev/context#WithCancelCause) (1.20) lets callers retrieve *why* a context was canceled via [`context.Cause(ctx)`](https://pkg.go.dev/context#Cause).
- [`AfterFunc`](https://pkg.go.dev/context#AfterFunc) and [`WithoutCancel`](https://pkg.go.dev/context#WithoutCancel) (1.21): run a function on cancellation, or derive a context that keeps values but drops the parent's cancellation.
- Pass as the first parameter, [never store in a struct](https://go.dev/blog/context-and-structs); use [`WithValue`](https://pkg.go.dev/context#WithValue) only for request-scoped data, not optional parameters.
- Every `WithCancel`/`WithTimeout`/`WithDeadline` returns a `cancel` func: call it (`defer cancel()`) or the child context and its timer live until the parent ends; `go vet` flags it ([`lostcancel`](https://pkg.go.dev/golang.org/x/tools/go/analysis/passes/lostcancel)).

### Patterns and goroutine leaks

- Worker pool, fan-in/fan-out, [pipeline](https://go.dev/blog/pipelines), and [semaphore](https://en.wikipedia.org/wiki/Semaphore_%28programming%29) (buffered channel `make(chan struct{}, n)`) are the standard shapes.
- [`errgroup.Group`](https://pkg.go.dev/golang.org/x/sync/errgroup#Group) (`golang.org/x/sync/errgroup`) runs goroutines, returns the first error, and can cap concurrency with `SetLimit`.
- A goroutine leak is a goroutine blocked forever — a send nobody receives, a receive on a channel that never closes, or a loop that ignores `ctx.Done()`. Detect with the [pprof goroutine profile](https://pkg.go.dev/runtime/pprof#Profile) or [`go.uber.org/goleak`](https://pkg.go.dev/go.uber.org/goleak).
- [`testing/synctest`](https://pkg.go.dev/testing/synctest) (1.25) runs concurrent code in a fake-clock "bubble" so time-dependent tests run instantly and deterministically.

## Memory management

### Escape analysis

- The compiler [decides stack vs heap](https://go.dev/doc/faq#stack_or_heap) by proving whether a value outlives the function ([escape analysis](https://en.wikipedia.org/wiki/Escape_analysis)); see the decisions with `go build -gcflags=-m`.
- Common causes: returning a pointer, storing a pointer in a heap object/global, boxing a value into an interface, closures capturing variables, and slices whose size isn't known at compile time.

### Garbage collector

- Concurrent, [tri-color mark-sweep](https://en.wikipedia.org/wiki/Tracing_garbage_collection#Tri-color_marking); non-generational and non-compacting; a [write barrier](https://en.wikipedia.org/wiki/Write_barrier#In_garbage_collection) keeps marking correct while the program runs.
- [`GOGC`](https://go.dev/doc/gc-guide#GOGC) (default 100) controls heap growth before the next cycle; [`GOMEMLIMIT`](https://go.dev/doc/gc-guide#Memory_limit) (1.19) sets a soft memory cap, useful in containers.
- [Green Tea GC](https://go.dev/blog/greenteagc) improves memory locality by scanning objects in larger, contiguous spans; introduced experimental (`GOEXPERIMENT=greenteagc`) in 1.25, it became the default collector in 1.26.

### Reducing allocations

- Preallocate slices and maps when the size is known (`make([]T, 0, n)`).
- Reuse buffers via [`sync.Pool`](https://pkg.go.dev/sync#Pool); build strings with [`strings.Builder`](https://pkg.go.dev/strings#Builder).
- Avoid needless `[]byte`↔`string` conversions — both copy, except where the compiler proves it safe (map lookups `m[string(b)]`).

### Struct layout and padding

- Fields are [aligned](https://en.wikipedia.org/wiki/Data_structure_alignment) to their type's alignment, so on 64-bit `struct{ a bool; b int64; c bool }` takes 24 bytes while `{b int64; a, c bool}` takes 16 — order fields largest first in hot, numerous structs.
- An empty struct (`struct{}`) is [zero bytes](https://go.dev/ref/spec#Size_and_alignment_guarantees) — used for sets (`map[K]struct{}`) and signal channels.

## Slices, maps, strings

### Slice mechanics

- A [slice header](https://go.dev/blog/slices-intro) is `{pointer, len, cap}`; copying the header still shares the backing array.
- [`append`](https://pkg.go.dev/builtin#append) grows in place while `len < cap`; otherwise it allocates roughly 2× under 256 elements, then a smoother ~1.25× for larger slices, and copies.
- Aliasing gotcha: `b := a[:2]; append(b, x)` can overwrite `a[2]` if capacity allows. Use the [full slice expression](https://go.dev/ref/spec#Slice_expressions) `a[lo:hi:max]` to cap capacity and force a fresh allocation on append.
- A small subslice of a huge array keeps the whole array alive for the GC — copy out the needed part if keeping it long-term.

### Maps

- [Hash table](https://en.wikipedia.org/wiki/Hash_table); implemented as [Swiss tables](https://go.dev/blog/swisstable) since Go 1.24 (faster, but iteration order was already randomized and remains so).
- Concurrent write (or write + read) is a race; the runtime detects it best-effort, and then it's a fatal, unrecoverable error, not a panic you can `recover`.
- Maps never shrink after deletions; [`clear(m)`](https://pkg.go.dev/builtin#clear) (1.21) empties one without reallocating the header.
- Map values aren't [addressable](https://go.dev/ref/spec#Address_operators): `&m[k]` and `m[k].field = x` don't compile for struct values.
- Reading a nil map returns zero values, but writing to a nil map panics — `make` it first (a nil slice, by contrast, works with `append`).

### Strings

- Immutable byte sequence, usually [UTF-8](https://en.wikipedia.org/wiki/UTF-8); `len(s)` counts bytes, `range s` decodes and yields [runes](https://go.dev/blog/strings) with byte offsets.
- Invalid UTF-8 encountered during `range` yields [`U+FFFD`](https://en.wikipedia.org/wiki/Specials_%28Unicode_block%29#Replacement_character).
- `string`↔`[]byte` conversions copy; substrings share the original's backing memory.

## Types and interfaces

### Interface internals

- An interface value is a [(type, value)](https://go.dev/doc/faq#nil_error) pair; it is `nil` only when both are nil — a nil `*T` stored in an `error` is not `== nil`.
- Comparing two interface values panics if both hold the same [non-comparable](https://go.dev/ref/spec#Comparison_operators) dynamic type (e.g. `[]int`); different dynamic types just compare unequal.
- [Compile-time satisfaction check](https://go.dev/doc/effective_go#blank_implements): `var _ io.Reader = (*MyReader)(nil)`.

### Method sets and embedding

- Pointer-receiver methods are only in the [method set](https://go.dev/ref/spec#Method_sets) of `*T`, so only `*T` satisfies an interface requiring them.
- [Embedding](https://go.dev/doc/effective_go#embedding) promotes fields/methods but is not inheritance: no polymorphism — a promoted method calling its own method calls its own version, never an outer "override." A same-named outer method shadows it.
- An embedded interface in a struct that's left unimplemented panics only when the missing method is actually called.

### Generics

- [Constraints](https://go.dev/ref/spec#Type_constraints) are interfaces defining a type set; `~int` accepts any type whose underlying type is `int`; [`comparable`](https://pkg.go.dev/builtin#comparable) allows `==`/map keys.
- Compiled via [GC-shape stenciling](https://github.com/golang/proposal/blob/master/design/generics-implementation-gcshape.md) — types with the same underlying shape share code, which can still be slower than hand-specialized code in hot paths.
- [Generic methods](https://go.dev/doc/go1.27#language) since Go 1.27: a method may declare its own type parameters, but interface methods can't, and a generic method can't satisfy an interface method. Still no specialization.

### Iterators and loop variables

- [Range-over-func](https://go.dev/blog/range-functions) iterators ([`iter.Seq`](https://pkg.go.dev/iter#Seq), [`iter.Seq2`](https://pkg.go.dev/iter#Seq2), 1.23) let `range` work over a function, powering the `slices`/`maps` iterator helpers.
- Since Go 1.22, [each iteration gets its own copy](https://go.dev/blog/loopvar-preview) of variables declared by the loop (`:=`) — the classic closure-capture bug needs `go 1.21` semantics or a reused outer variable (`for i = 0; ...`).

## Errors, defer, panic

### Error wrapping

- [`fmt.Errorf("...: %w", err)`](https://pkg.go.dev/fmt#Errorf) wraps; [`errors.Is`](https://pkg.go.dev/errors#Is) walks the chain comparing to a sentinel, [`errors.As`](https://pkg.go.dev/errors#As) extracts a concrete type. Never compare a wrapped error with `==`.
- [`errors.Join`](https://pkg.go.dev/errors#Join) (1.20) combines multiple errors into one that `Is`/`As` can still unwrap.

### defer and panic

- [`defer`](https://go.dev/ref/spec#Defer_statements) arguments are evaluated immediately, execution is LIFO; a deferred closure can modify named return values.
- `defer` inside a long-running loop accumulates — calls only run at function return, not at loop end.
- [`recover()`](https://go.dev/ref/spec#Handling_panics) only stops a panic when called directly inside a deferred function; an unrecovered panic in any goroutine kills the whole process.

## Standard library gotchas

### net/http clients and servers

- The default [`http.Client`](https://pkg.go.dev/net/http#Client) has no timeout — a hung server blocks the goroutine forever; always set `Timeout` or use a context.
- Always close `resp.Body` (and drain it) or the connection isn't reused and leaks.
- [`http.Server`](https://pkg.go.dev/net/http#Server) needs `ReadHeaderTimeout`/`ReadTimeout`/`WriteTimeout`, or slow clients ([Slowloris](https://en.wikipedia.org/wiki/Slowloris_%28cyber_attack%29)) hold connections open.
- [`ServeMux` patterns](https://go.dev/blog/routing-enhancements) since 1.22 take methods and wildcards: `mux.HandleFunc("GET /items/{id}", h)` with `r.PathValue("id")`.

### encoding/json gotchas

- Numbers decoded into `any` become float64, so integer IDs above [2⁵³](https://en.wikipedia.org/wiki/Double-precision_floating-point_format#Precision_limitations_on_integer_values) lose precision — use [`Decoder.UseNumber`](https://pkg.go.dev/encoding/json#Decoder.UseNumber) or a typed field.
- A nil slice or map encodes as `null`, an empty one as `[]` or `{}`.
- Unexported fields are silently skipped; unknown JSON fields are ignored unless [`DisallowUnknownFields`](https://pkg.go.dev/encoding/json#Decoder.DisallowUnknownFields); field-name matching is [case-insensitive](https://pkg.go.dev/encoding/json#Unmarshal).
- [`omitempty`](https://pkg.go.dev/encoding/json#Marshal) never omits a struct value (a zero `time.Time` included); `omitzero` (1.24) does.

## Modules and tooling

### Minimal version selection

- Go picks the minimum version satisfying every `require` ([MVS](https://go.dev/ref/mod#minimal-version-selection)), not the latest — builds are reproducible without a lock file.
- [`go.sum`](https://go.dev/ref/mod#go-sum-files) holds checksums verified against the public [checksum database](https://go.dev/ref/mod#checksum-database); it isn't a lock file.

### Module layout and workspaces

- [Major versions ≥ 2](https://go.dev/ref/mod#major-version-suffixes) change the import path (`example.com/lib/v2`).
- [`internal/`](https://pkg.go.dev/cmd/go#hdr-Internal_packages) packages are importable only from within the parent tree.
- [`go.work`](https://go.dev/ref/mod#workspaces) (1.18) builds several local modules together without [`replace`](https://go.dev/ref/mod#go-mod-file-replace) directives.

### Compatibility and GODEBUG

- Potentially breaking changes ship behind [`GODEBUG`](https://go.dev/doc/godebug) settings whose defaults follow the main module's [`go` line](https://go.dev/ref/mod#go-mod-file-go), so a toolchain upgrade alone keeps their old behavior (other runtime and performance changes still apply).
- Override per program with [`//go:debug`](https://go.dev/doc/godebug#default) directives or the `GODEBUG` environment variable.

## Testing and profiling

### Test tooling

- Benchmarks use [`b.Loop()`](https://pkg.go.dev/testing#B.Loop) (1.24), which replaced the manual `for i := 0; i < b.N; i++` idiom and avoids some compiler over-optimization pitfalls.
- [Fuzzing](https://go.dev/doc/security/fuzz/) (`func FuzzX`, 1.18) generates inputs from a seed corpus.

### Profiling

- [pprof](https://pkg.go.dev/runtime/pprof) profiles: CPU, heap (alloc vs inuse), goroutine, block, mutex — collected via test flags or [`net/http/pprof`](https://pkg.go.dev/net/http/pprof) in a running service.
- [`go tool trace`](https://pkg.go.dev/cmd/trace) shows scheduler and latency behavior over time, complementing pprof's aggregate view.
- Go 1.27 adds a [goroutine leak profile](https://go.dev/doc/go1.27#goroutineleak-profiles) that reports goroutines blocked on unreachable channels or locks.

### Profile-guided optimization

- [PGO](https://go.dev/doc/pgo) (GA in 1.21): commit a production CPU profile as `default.pgo` in the main package, and builds use it automatically.
- The compiler inlines hot calls and devirtualizes hot interface calls — typically 2–14% less CPU.
