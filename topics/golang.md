# Go Cheatsheet

The 20 most frequently asked Go interview topics, with short answers.

## 1. What are goroutines?

A goroutine is a **lightweight thread managed by the Go runtime**, started with `go f()`. It begins with a small stack (~2 KB) that grows and shrinks on demand, so running hundreds of thousands of them is normal. Creation and context switching are far cheaper than OS threads.

The runtime uses the **GMP scheduler**: G (goroutines) are multiplexed onto M (OS threads) via P (logical processors, count = `GOMAXPROCS`, defaults to CPU count). Each P has a local run queue; idle Ps steal work from others. When a goroutine blocks on a syscall, its M is detached and the P moves to another thread, so other goroutines keep running. Scheduling is preemptive (async preemption since Go 1.14).

The `main` function doesn't wait for goroutines — when `main` returns, the program exits. Use `sync.WaitGroup`, channels, or `errgroup` to wait for them to finish.

## 2. What are channels? Buffered vs unbuffered?

Channels are typed conduits for passing values between goroutines — "**don't communicate by sharing memory; share memory by communicating**." An **unbuffered** channel (`make(chan T)`) blocks the sender until a receiver is ready, so it synchronizes both sides. A **buffered** channel (`make(chan T, n)`) blocks the sender only when the buffer is full and the receiver only when it's empty.

Key rules: only the **sender should close** a channel. Sending on a closed channel **panics**; receiving from a closed channel returns the zero value immediately (`v, ok := <-ch` gives `ok == false`). Sending or receiving on a **nil channel blocks forever**. `for v := range ch` loops until the channel is closed.

## 3. How do interfaces work? What is the nil interface gotcha?

Interfaces are satisfied **implicitly** — any type with the required methods implements the interface, no `implements` keyword. Keep them small (`io.Reader`, `io.Writer`) and define them where they're consumed ("accept interfaces, return structs"). `any` (`interface{}`) holds any value; use type assertions (`v, ok := x.(T)`) or type switches to get the concrete type back.

Internally an interface value is a pair **(type, value)**. It's `nil` only when **both** are nil. So a nil `*MyErr` returned as `error` is **not** `== nil`, because the type part is set. Return a literal `nil` instead of a typed nil pointer.

Methods with **pointer receivers** are only in the method set of `*T`, so only `*T` (not `T`) satisfies an interface requiring them. A compile-time check that a type implements an interface: `var _ io.Reader = (*MyReader)(nil)`.

## 4. Arrays vs slices? How does `append` work?

An **array** has a fixed size that is part of its type (`[4]int` ≠ `[5]int`) and is a value — assigning or passing it copies all elements. A **slice** is a small header `{pointer, len, cap}` pointing into an underlying array. Copying a slice copies the header, so both **share the same backing array**.

`append` writes in place if `len < cap`; otherwise it allocates a new, larger array (roughly 2x for small slices, ~1.25x for large) and copies. Gotcha: after `b := a[:2]`, appending to `b` can overwrite `a[2]`. Always use the result (`s = append(s, x)`), and use `copy` or a full slice expression `a[:2:2]` to avoid aliasing.

A small slice of a huge array keeps the **whole array alive** for the garbage collector — copy the needed part if you keep it long-term. Preallocate with `make([]T, 0, n)` when the size is known.

## 5. How do maps work? Are they thread-safe?

A map is a **hash table** (reference type; since Go 1.24 implemented as Swiss tables). Reading a missing key returns the zero value; use `v, ok := m[k]` to check presence. **Iteration order is randomized** on purpose. Writing to a **nil map panics** (reading is fine). Map elements aren't addressable, so `&m[k]` and `m[k].field = x` don't compile for struct values.

Maps are **not safe for concurrent use**: concurrent write + read/write causes a fatal "concurrent map writes" error. Protect with `sync.Mutex`/`sync.RWMutex`, or use `sync.Map` (optimized for keys written once and read many times, or disjoint key sets per goroutine).

## 6. What does `select` do?

`select` waits on multiple channel operations and runs the first one that is ready. If several are ready, it picks one **at random** (to avoid starvation). A `default` case makes it non-blocking.

Common patterns: timeouts (`case <-time.After(d)`), cancellation (`case <-ctx.Done()`), and non-blocking send/receive. An empty `select {}` blocks forever. Setting a channel variable to `nil` disables its case — useful for merging channels until all are closed.

## 7. What sync primitives exist? How do you detect data races?

- `sync.Mutex` / `sync.RWMutex` — exclusive lock / many readers or one writer.
- `sync.WaitGroup` — wait for a group of goroutines (`Add` before starting, `Done` in each, `Wait`; or `wg.Go(f)` since Go 1.25).
- `sync.Once` — run initialization exactly once.
- `sync/atomic` — lock-free counters and flags (`atomic.Int64`, etc.).
- `sync.Pool` — reuse temporary objects to reduce GC pressure.

A **data race** happens when two goroutines access the same memory concurrently and at least one writes. Detect it with the **race detector**: `go test -race` / `go run -race`. Don't copy values containing a mutex (pass pointers; `go vet` catches this). Rule of thumb for **channels vs mutex**: use channels to pass ownership of data or coordinate work, a mutex to protect shared state.

## 8. What is `context.Context` used for?

`context` carries **cancellation signals, deadlines, and request-scoped values** across API boundaries and goroutines. Create with `context.WithCancel`, `WithTimeout`, `WithDeadline`, or `WithValue`, derived from `context.Background()`. Canceling a parent cancels all children. Goroutines watch `<-ctx.Done()` and read `ctx.Err()` for the reason.

Conventions: pass it as the **first parameter** named `ctx`; don't store it in structs; **always call the `cancel` func** (`defer cancel()`) to release resources; use `WithValue` only for request-scoped data (trace IDs, auth), not for optional parameters.

## 9. How does error handling work in Go?

Errors are ordinary values implementing `error` (`Error() string`), returned as the last result and checked explicitly with `if err != nil`. There are no exceptions. Create errors with `errors.New` or `fmt.Errorf`.

**Wrap** errors with context using `fmt.Errorf("read config: %w", err)`. Inspect chains with **`errors.Is`** (compare to a sentinel like `io.EOF`) and **`errors.As`** (extract a specific error type). Don't compare wrapped errors with `==`. `errors.Join` (Go 1.20) combines multiple errors.

## 10. What are `defer`, `panic`, and `recover`?

`defer` schedules a call to run when the surrounding function returns, in **LIFO order**. It's used for cleanup (`defer f.Close()`, `defer mu.Unlock()`). Arguments are **evaluated immediately** at the `defer` statement, not when it runs. Deferred closures can modify **named return values**. Avoid `defer` inside long loops — calls pile up until the function returns.

`panic` stops normal execution and unwinds the stack, running deferred calls. `recover()` stops the panic, but **only works when called directly inside a deferred function**. Use panics for truly unrecoverable bugs; use errors for expected failures. A panic in a goroutine that isn't recovered crashes the whole program.

## 11. `make` vs `new`? What are zero values?

**`new(T)`** allocates a zeroed `T` and returns a `*T`. **`make`** is only for slices, maps, and channels: it initializes their internal structure and returns the value itself (`T`, not a pointer). `new` is rarely used in practice — `&T{}` does the same for structs.

Every variable starts at its **zero value**: `0`, `""`, `false`, and `nil` for pointers, slices, maps, channels, functions, and interfaces. Good Go types make the zero value useful: a nil slice works with `len` and `append`, a zero `sync.Mutex` is ready to use, a zero `bytes.Buffer` is an empty buffer. The exception to remember: a nil map panics on write.

## 12. Value vs pointer receivers? Is Go pass-by-value?

Go is **always pass-by-value**: function arguments and receivers are copies. Slices, maps, channels, and interfaces *feel* like references because their copied value contains a pointer to shared data — but reassigning the parameter itself (e.g. `s = append(s, x)` that reallocates) isn't visible to the caller.

Use a **pointer receiver** when the method mutates the receiver, when the struct is large (avoid copies), or when it contains a `sync.Mutex` or similar that must not be copied. Use a **value receiver** for small, immutable types. Be **consistent**: if any method needs a pointer receiver, use pointers for all methods of that type.

## 13. What concurrency patterns are common? How do goroutines leak?

- **Worker pool** — N goroutines reading jobs from a shared channel, which limits concurrency.
- **Pipeline** — stages connected by channels, each stage a goroutine.
- **Fan-out / fan-in** — spread work across workers, merge results into one channel.
- **Semaphore** — a buffered channel `make(chan struct{}, n)` limits concurrent operations.
- **`errgroup`** (`golang.org/x/sync/errgroup`) — run goroutines, return the first error, cancel the rest via context.

A **goroutine leak** is a goroutine blocked forever — usually on a send nobody receives, a receive on a channel nobody closes, or a loop that never checks `ctx.Done()`. Leaked goroutines hold memory and never get collected. Prevent by giving every goroutine a clear exit path (cancellation or channel close). Detect with the pprof goroutine profile or `go.uber.org/goleak` in tests.

## 14. How does the garbage collector work?

Go uses a **concurrent, tri-color mark-and-sweep** collector. It is **non-generational** and **non-moving**. Marking runs alongside your code (write barriers keep it correct), with only very short stop-the-world pauses (typically well under 1 ms). The trade-off: Go optimizes for **low latency**, and pays with some CPU overhead and throughput.

Tuning: **`GOGC`** (default 100) starts a new cycle when the heap grows 100% over the live heap after the last collection — higher means less GC CPU but more memory. **`GOMEMLIMIT`** (Go 1.19) sets a soft memory limit, useful in containers. The best optimization is **allocating less**: reuse buffers, preallocate slices, use `sync.Pool`, avoid unneeded pointers. Go 1.25 added an experimental "Green Tea" collector with better memory locality.

## 15. Stack vs heap: what is escape analysis?

The compiler decides where each variable lives. If it can prove a value isn't used after the function returns, it goes on the **stack** (free to allocate and release). Otherwise it **escapes to the heap** and must be garbage-collected. Unlike C, returning a pointer to a local variable is perfectly safe — the compiler moves it to the heap.

Common causes of escape: returning a pointer, storing a pointer in a heap object or global, passing a value into an interface (e.g. `fmt.Println(x)`), closures capturing variables, and slices whose size isn't known at compile time. See the decisions with **`go build -gcflags=-m`**. Reduce escapes in hot paths to cut GC pressure.

## 16. How do generics work?

Since Go 1.18, functions and types can have **type parameters**: `func Map[T, U any](s []T, f func(T) U) []U`. A **constraint** is an interface that limits the allowed types: `any`, `comparable` (supports `==`, usable as map keys), or a type set like `interface{ ~int | ~float64 }`, where **`~int`** also accepts types whose underlying type is `int`. `cmp.Ordered` covers types supporting `<`.

Limits: methods can't have their own type parameters, and there is no specialization. Use generics for containers and algorithms that work the same for many types (the standard `slices` and `maps` packages, Go 1.21), not as a replacement for interfaces when behavior differs per type.

## 17. What is struct embedding? Does Go have inheritance?

Go has **no inheritance** — it uses **composition**. Embedding a type in a struct (`type Logger struct{ *log.Logger }`) **promotes** its fields and methods, so you can call them directly on the outer type. That also means the outer type satisfies interfaces through the promoted methods.

It's not inheritance: there is no polymorphism through the embedded type. If the embedded type calls one of its own methods, it calls its own version, not an "override" defined on the outer type. An outer method with the same name **shadows** the embedded one. Embedding an interface in a struct is a common trick for partial implementations and test mocks.

## 18. How do strings, bytes, and runes work?

A string is an **immutable sequence of bytes**, usually UTF-8. `len(s)` returns **bytes, not characters**, and `s[i]` returns a byte. A **rune** (`int32`) is a Unicode code point. `for i, r := range s` decodes UTF-8 and yields runes with their byte offsets; use `utf8.RuneCountInString` to count characters.

Converting between `string` and `[]byte` **copies** the data. Substrings share memory with the original. Build strings in loops with **`strings.Builder`** — `s += x` allocates a new string every time.

## 19. What is the loop variable capture bug?

Before **Go 1.22**, a `for` loop had a single variable reused across all iterations. Closures and goroutines that captured it (`go func() { use(v) }()`) often all saw the last value. The old fix was shadowing it: `v := v`.

Since Go 1.22, **each iteration gets its own variable**, so the bug is gone for modules declaring `go 1.22` or later. Interviewers still ask it to check you understand closures capture **variables, not values**. Related newer features: `for i := range 10` (range over int, 1.22) and range-over-function iterators (1.23).

## 20. How do you test and profile Go code?

The standard `testing` package covers most needs: **table-driven tests** with `t.Run` subtests, `t.Parallel()` for concurrent tests, **benchmarks** (`func BenchmarkX(b *testing.B)`, run with `go test -bench`, `b.Loop()` since Go 1.24), and built-in **fuzzing** (`func FuzzX`, Go 1.18). Use `httptest` for HTTP handlers, `-race` for races, and `-cover` for coverage. Mock through small interfaces, not frameworks.

For performance, use **pprof**: CPU, heap, goroutine, block, and mutex profiles, collected from tests (`-cpuprofile`) or live services (`net/http/pprof`), viewed with `go tool pprof`. `go tool trace` shows scheduler behavior and latency. Always profile before optimizing.
