# Go Cheatsheet

The 10 most frequently asked Go interview topics, with short answers.

## 1. What are goroutines?

A goroutine is a **lightweight thread managed by the Go runtime**, started with `go f()`. It begins with a small stack (~2 KB) that grows and shrinks on demand, so running hundreds of thousands of them is normal. Creation and context switching are far cheaper than OS threads.

The runtime uses the **GMP scheduler**: G (goroutines) are multiplexed onto M (OS threads) via P (logical processors, count = `GOMAXPROCS`, defaults to CPU count). Each P has a local run queue; idle Ps steal work from others. Scheduling is preemptive (async preemption since Go 1.14). The `main` function doesn't wait for goroutines — use `sync.WaitGroup` or channels to synchronize.

## 2. What are channels? Buffered vs unbuffered?

Channels are typed conduits for passing values between goroutines — "**don't communicate by sharing memory; share memory by communicating**." An **unbuffered** channel (`make(chan T)`) blocks the sender until a receiver is ready, so it synchronizes both sides. A **buffered** channel (`make(chan T, n)`) blocks the sender only when the buffer is full and the receiver only when it's empty.

Key rules: only the **sender should close** a channel. Sending on a closed channel **panics**; receiving from a closed channel returns the zero value immediately (`v, ok := <-ch` gives `ok == false`). Sending or receiving on a **nil channel blocks forever**. `for v := range ch` loops until the channel is closed.

## 3. What does `select` do?

`select` waits on multiple channel operations and runs the first one that is ready. If several are ready, it picks one **at random** (to avoid starvation). A `default` case makes it non-blocking.

Common patterns: timeouts (`case <-time.After(d)`), cancellation (`case <-ctx.Done()`), and non-blocking send/receive. An empty `select {}` blocks forever. Setting a channel variable to `nil` disables its case — useful for merging channels until all are closed.

## 4. Arrays vs slices? How does `append` work?

An **array** has a fixed size that is part of its type (`[4]int` ≠ `[5]int`) and is a value — assigning or passing it copies all elements. A **slice** is a small header `{pointer, len, cap}` pointing into an underlying array. Copying a slice copies the header, so both **share the same backing array**.

`append` writes in place if `len < cap`; otherwise it allocates a new, larger array (roughly 2x for small slices, ~1.25x for large) and copies. Gotcha: after `b := a[:2]`, appending to `b` can overwrite `a[2]`. Always use the result (`s = append(s, x)`), and use `copy` or a full slice expression `a[:2:2]` to avoid aliasing.

## 5. How do maps work? Are they thread-safe?

A map is a **hash table** (reference type). Reading a missing key returns the zero value; use `v, ok := m[k]` to check presence. **Iteration order is randomized** on purpose. Writing to a **nil map panics** (reading is fine). Map elements aren't addressable, so `&m[k]` and `m[k].field = x` don't compile for struct values.

Maps are **not safe for concurrent use**: concurrent write + read/write causes a fatal "concurrent map writes" error. Protect with `sync.Mutex`/`sync.RWMutex`, or use `sync.Map` (optimized for keys written once and read many times, or disjoint key sets per goroutine).

## 6. How do interfaces work? What is the nil interface gotcha?

Interfaces are satisfied **implicitly** — any type with the required methods implements the interface, no `implements` keyword. Keep them small (`io.Reader`, `io.Writer`) and define them where they're consumed. `any` (`interface{}`) holds any value; use type assertions (`v, ok := x.(T)`) or type switches to get the concrete type back.

Internally an interface value is a pair **(type, value)**. It's `nil` only when **both** are nil. So a nil `*MyErr` returned as `error` is **not** `== nil`, because the type part is set. Return a literal `nil` instead of a typed nil pointer. Also: methods with **pointer receivers** are only in the method set of `*T`, so only `*T` (not `T`) satisfies an interface requiring them.

## 7. How does error handling work in Go?

Errors are ordinary values implementing `error` (`Error() string`), returned as the last result and checked explicitly with `if err != nil`. There are no exceptions. Create errors with `errors.New` or `fmt.Errorf`.

**Wrap** errors with context using `fmt.Errorf("read config: %w", err)`. Inspect chains with **`errors.Is`** (compare to a sentinel like `io.EOF`) and **`errors.As`** (extract a specific error type). Don't compare wrapped errors with `==`. `errors.Join` (Go 1.20) combines multiple errors.

## 8. What are `defer`, `panic`, and `recover`?

`defer` schedules a call to run when the surrounding function returns, in **LIFO order**. It's used for cleanup (`defer f.Close()`, `defer mu.Unlock()`). Arguments are **evaluated immediately** at the `defer` statement, not when it runs. Deferred closures can modify **named return values**. Avoid `defer` inside long loops — calls pile up until the function returns.

`panic` stops normal execution and unwinds the stack, running deferred calls. `recover()` stops the panic, but **only works when called directly inside a deferred function**. Use panics for truly unrecoverable bugs; use errors for expected failures. A panic in a goroutine that isn't recovered crashes the whole program.

## 9. What is `context.Context` used for?

`context` carries **cancellation signals, deadlines, and request-scoped values** across API boundaries and goroutines. Create with `context.WithCancel`, `WithTimeout`, `WithDeadline`, or `WithValue`, derived from `context.Background()`. Canceling a parent cancels all children. Goroutines watch `<-ctx.Done()` and read `ctx.Err()` for the reason.

Conventions: pass it as the **first parameter** named `ctx`; don't store it in structs; **always call the `cancel` func** (`defer cancel()`) to release resources; use `WithValue` only for request-scoped data (trace IDs, auth), not for optional parameters.

## 10. What sync primitives exist? How do you detect data races?

- `sync.Mutex` / `sync.RWMutex` — exclusive lock / many readers or one writer.
- `sync.WaitGroup` — wait for a group of goroutines (`Add` before starting, `Done` in each, `Wait`).
- `sync.Once` — run initialization exactly once.
- `sync/atomic` — lock-free counters and flags (`atomic.Int64`, etc.).
- `sync.Pool` — reuse temporary objects to reduce GC pressure.

A **data race** happens when two goroutines access the same memory concurrently and at least one writes. Detect it with the **race detector**: `go test -race` / `go run -race`. Don't copy values containing a mutex (pass pointers; `go vet` catches this). Common leak: a goroutine blocked forever on a channel nobody reads or closes.
