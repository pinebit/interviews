# Rust

What experienced Rust engineers forget before an interview, grouped by subtopic.

## Ownership and borrowing

### Move semantics

- A non-`Copy` value has one owner; assignment or passing **moves** it, invalidating the old binding. `Copy` types (integers, etc.) duplicate instead.
- `Clone` is an explicit, possibly expensive deep copy; `Copy` is an implicit, cheap bitwise one — a type can only be `Copy` if all its fields are.
- Interior mutability breaks the "one mutable borrow" rule safely: **`Cell<T>`** (copy in/out, no references handed out), **`RefCell<T>`** (runtime-checked borrows, **panics** on a second conflicting borrow instead of failing at compile time), **`OnceCell`/`OnceLock`** (write-once, then freely shared), **`Mutex`** (thread-safe interior mutability).

### Borrow rules

- `&T` (shared, many allowed) vs `&mut T` (exclusive, one at a time) — never both live for overlapping uses.
- **Non-lexical lifetimes (NLL)**: a borrow's scope ends at its last use, not at the end of the block, so a shared borrow can finish before a later mutable borrow in the same function.
- **Reborrowing**: passing `&mut *r` (or just `r` where a `&mut` is expected) creates a shorter-lived borrow from an existing mutable reference without moving it — this is why you can call multiple `&mut self` methods in sequence without "using up" the original reference.

## Lifetimes

### Elision and `'static`

- Three elision rules: **(1)** each elided input lifetime gets its own parameter, **(2)** if there's exactly one input lifetime it's assigned to all elided output lifetimes, **(3)** for a method, `&self`'s lifetime is assigned to all elided outputs.
- **`'static`** as a *bound* (`T: 'static`) means "contains no non-static references," which **owned data satisfies** — it doesn't mean "lives forever." `&'static T` is the actual "lives for the whole program" reference.
- **HRTB** (`for<'a> Fn(&'a T)`) expresses "works for any lifetime," needed when a closure/trait must accept a reference whose lifetime isn't known until it's called.
- "Borrowed value does not live long enough" almost always means a temporary was dropped while still borrowed, or a struct is trying to outlive a reference it holds — check where the referent is actually owned.

## Traits and generics

### Dispatch

- **Static dispatch** (generics, monomorphization) — one specialized copy per concrete type, zero runtime cost, larger binary. **Dynamic dispatch** (`dyn Trait`) — a fat pointer (data + vtable), runtime cost, works with heterogeneous collections.
- **Dyn compatibility** (formerly called "object safety"): a trait can back a `dyn Trait` only if its methods don't return `Self` by value or take generic type parameters, roughly.
- The **orphan rule**: you can implement a trait for a type only if you own the trait or the type — prevents conflicting impls from different crates.
- **Blanket impls** (`impl<T: Display> MyTrait for T`) implement a trait for every type satisfying a bound.

### Associated types and newer generics

- **Associated types** (`Iterator::Item`) fix one type per implementation; **generic type parameters** allow many implementations for the same type (`From<A>`, `From<B>`) — pick associated types when there's exactly one sensible type per impl.
- `Sized` is an implicit bound on every type parameter; `?Sized` opts out, needed to accept unsized types like `str` or `dyn Trait` behind a reference.
- `impl Trait` in argument position is sugar for an anonymous generic; in return position it hides the concrete type while still being static dispatch (unlike `dyn Trait`).
- **GATs** (generic associated types, stable since 1.65) let an associated type itself be generic, e.g. over a lifetime — needed for a `LendingIterator`-style trait.
- **Async fn in traits** (stabilized for the basic case in 1.75) desugars to a method returning `impl Future`; dynamic dispatch over async trait methods still generally needs `async-trait` or manual boxing.

## Smart pointers and memory

### Ownership pointers

- **`Box<T>`** — single owner, heap allocation. **`Rc<T>`** — shared ownership, non-atomic refcount, single-threaded; pair with **`Weak<T>`** to break reference cycles (a cycle of only `Rc` leaks memory, since counts never reach zero). **`Arc<T>`** — same as `Rc` but atomic, for cross-thread sharing. **`Cow<T>`** — clone-on-write, avoids copying until mutation is actually needed.
- Drop order: **reverse declaration order** for local variables; struct fields drop in **declaration order** (the opposite of locals).
- **`mem::forget`** is safe in the type-safety sense — it leaks the value instead of running its destructor, but leaking memory is not undefined behavior in Rust.
- **`Pin<P>`** prevents a value from being moved in memory after being pinned — required for self-referential structures, which is exactly what async generator state machines are.

## Error handling

### `?` and error crates

- `?` on `Result` extracts `Ok` or returns early with `Err`, converting via `From` when the error types differ; `?` on `Option` extracts `Some` or returns `None`.
- **`thiserror`** — for libraries: derives `Error` on your own enum, preserving distinct variants for callers to match on. **`anyhow`** — for applications: one dynamic `anyhow::Error` type when callers just need to log/propagate, not match.
- `panic!` normally **unwinds** (runs destructors up the stack); building with `panic = "abort"` terminates immediately without unwinding — smaller binaries, faster panics, no `catch_unwind` recovery.
- **`catch_unwind`** can catch an unwinding panic at a boundary (e.g. FFI, a thread pool worker) but must not be used for routine control flow, and can't catch anything under `panic = "abort"`.

## Concurrency

### Send/Sync and primitives

- **`Send`**: ownership can move to another thread. **`Sync`**: `&T` can be shared across threads (equivalent to `&T: Send`). `Rc<T>` is neither; `RefCell<T>` is `Send` but not `Sync` (its runtime borrow-check isn't atomic); a `MutexGuard` is not `Send` (it must be dropped on the thread that acquired it, since the OS lock is thread-owned on some platforms).
- **Mutex poisoning**: if a thread panics while holding the lock, the `Mutex` is marked poisoned and later `.lock()` calls return an `Err` by default, surfacing that shared state may be inconsistent.
- **Scoped threads** (`std::thread::scope`, stable since **1.63**) let spawned threads borrow local data without `'static` + `Arc`, since the scope guarantees they finish before it exits.
- Channels: `std::sync::mpsc` (multi-producer, single-consumer, `channel()` unbounded vs `sync_channel(n)` bounded) or **crossbeam** for multi-producer multi-consumer and more channel types.
- Atomics and memory orderings: **Relaxed** (no ordering guarantee, just atomicity), **Acquire/Release** (pairs to establish happens-before between a release-store and an acquire-load), **SeqCst** (a single global total order, strongest and most expensive).

## Async

### Futures and executors

- Futures are **lazy** — nothing happens until polled; an executor (e.g. **Tokio**) drives polling to completion.
- Holding a non-`Send` guard (like a `MutexGuard` or `RefCell` borrow) across an `.await` point makes the enclosing future non-`Send`, which breaks spawning it onto a multithreaded executor — drop the guard before awaiting.
- **Blocking** inside an async function (a synchronous, CPU- or I/O-blocking call) stalls the executor thread and every task scheduled on it — move blocking work to `spawn_blocking`.
- **Cancellation is drop**: dropping a future stops it wherever it's currently suspended, with no explicit cancellation signal — "cancel safety" in `select!` means a branch must leave state consistent even if dropped mid-await.

## Unsafe and FFI

### The unsafe superpowers

- Five things `unsafe` unlocks: dereference a raw pointer, call an unsafe function, implement an unsafe trait, access/modify a mutable static, access a union field.
- `unsafe` does **not** disable the borrow checker — ordinary safety rules for references still apply inside the block; it only allows the five operations above.
- Common UB sources: aliasing `&mut` references (two live mutable references to the same data), constructing an invalid value (e.g. a `bool` that isn't 0 or 1), and data races on non-atomic memory.
- **Miri** interprets Rust MIR and detects many forms of UB (invalid memory access, some aliasing violations) that compile and "work" under a normal build.

## Macros and Cargo

### Macro kinds

- **Declarative macros** (`macro_rules!`) pattern-match on token trees; **procedural macros** (derive, attribute, function-like) run arbitrary code on a `TokenStream` at compile time, powering `#[derive(...)]`.
- **Hygiene**: identifiers introduced by a macro don't accidentally capture or collide with identifiers at the call site, unlike naive C-style textual macros.

### Cargo workflow

- **Features** are additive (unioned across the dependency graph) — a feature should never remove functionality, or different crates enabling different feature sets would produce different builds from the same `Cargo.lock`.
- **Workspaces** share one `Cargo.lock` and target directory across multiple crates.
- **`Cargo.lock`**: committed for binaries (reproducible builds), typically not committed for libraries (so downstream crates resolve versions themselves).
- **Editions**: opt-in, per-crate language changes without breaking existing code; **edition 2024** is available **since Rust 1.85**.
