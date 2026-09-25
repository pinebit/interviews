# Rust

What experienced Rust engineers forget before an interview, grouped by subtopic.

## Ownership and borrowing

### Move semantics and Copy

- A non-`Copy` value has one owner; assignment or passing **moves** it, invalidating the old binding.
- **`Copy`** is an implicit bitwise copy, allowed only if every field is `Copy` and there's no `Drop`; **`Clone`** is explicit and possibly expensive.

### Borrow rules and NLL

- Many `&T` **or** one `&mut T` at a time — never both for overlapping uses.
- **Non-lexical lifetimes**: a borrow ends at its **last use**, not at the end of the block.
- **Reborrowing** (`&mut *r`, implicit when passing `r`) makes a shorter borrow, so you can call several `&mut self` methods in a row.

### Interior mutability

| Type | Checked | Thread-safe | Note |
|---|---|---|---|
| `Cell<T>` | none needed | no | copy/replace in and out, never hands out references |
| `RefCell<T>` | runtime | no | a conflicting borrow **panics** |
| `OnceCell`/`OnceLock` | write once | `OnceLock` yes | lazy initialization |
| `Mutex`/`RwLock` | runtime (lock) | yes | can be poisoned |

## Lifetimes

### Elision rules

- **(1)** Each elided input reference gets its own lifetime; **(2)** exactly one input lifetime → it's used for all outputs; **(3)** in methods, `&self`'s lifetime goes to all outputs.

### `'static` and HRTBs

- **`T: 'static`** means "holds no non-static borrows" — **owned data satisfies it**; it doesn't mean "lives forever". `&'static T` is the forever reference.
- **HRTB** (`for<'a> Fn(&'a T)`) says "works for every lifetime", needed when the reference is only created inside the callee.

### "Does not live long enough"

- Usually a temporary dropped while still borrowed, or a struct outliving a reference it holds — find where the referent is actually owned.

## Traits and generics

### Static vs dynamic dispatch

- **Generics** are monomorphized: one copy per type, zero-cost calls, bigger binary.
- **`dyn Trait`** is a fat pointer (data + vtable): one copy, an indirect call, heterogeneous collections.
- **Dyn compatibility** (formerly "object safety"): roughly, no methods returning `Self` by value and no generic methods.

### Coherence: orphan rule and blanket impls

- **Orphan rule**: implement a trait only if your crate owns the trait or the type — prevents conflicting impls across crates.
- **Blanket impls** (`impl<T: Display> MyTrait for T`) cover every type meeting a bound.

### Associated types vs type parameters

- **Associated types** (`Iterator::Item`) fix one type per impl; **type parameters** allow many impls for one type (`From<A>`, `From<B>`).
- **GATs** (**1.65**) let an associated type be generic, e.g. over a lifetime — the basis of lending iterators.

### `Sized` and `impl Trait`

- Every type parameter is implicitly `Sized`; **`?Sized`** accepts `str`, `[T]`, or `dyn Trait` behind a pointer.
- `impl Trait` in argument position is an anonymous generic; in return position it hides the concrete type but stays static dispatch.

### Async functions in traits

- **Async fn in traits** (**1.75**) desugars to a method returning `impl Future`; `dyn` dispatch over them still needs boxing or the `async-trait` crate.

## Smart pointers and memory

### Box, Rc, Arc, Cow

- **`Box<T>`**: single owner on the heap. **`Rc<T>`**: shared, non-atomic count, one thread. **`Arc<T>`**: atomic count, cross-thread.
- An `Rc`/`Arc` cycle **leaks**; break it with **`Weak<T>`**.
- **`Cow<T>`** borrows until a mutation forces an owned copy.

### Drop order and leaking

- Locals drop in **reverse declaration order**; struct fields drop in **declaration order**.
- **`mem::forget`** is safe: leaking memory isn't undefined behavior in Rust.

### Pin and Unpin

- **`Pin<P>`** stops the pointee from moving **only if it's `!Unpin`**; most types are `Unpin` and move freely.
- Async state machines are `!Unpin` because they can be self-referential — that's why futures are polled through `Pin<&mut Self>`.

## Error handling

### `?` and error crates

- `?` returns early with `Err`, converting via **`From`**; on `Option` it returns `None`.
- **`thiserror`** for libraries (typed enums callers can match); **`anyhow`** for applications (one dynamic error with context).

### Panics and unwinding

- `panic!` **unwinds** by default, running destructors; `panic = "abort"` exits immediately — smaller binary, no recovery.
- **`catch_unwind`** stops an unwinding panic at a boundary (FFI, worker pool) — never for control flow, and useless under `abort`.

## Concurrency

### Send and Sync

- **`Send`**: ownership can move to another thread. **`Sync`**: `&T` can be shared (`T: Sync` ⇔ `&T: Send`).
- `Rc` is neither; `RefCell` is `Send` but not `Sync`; **`MutexGuard` is not `Send`** — it must be released on the locking thread.

### Mutex poisoning and scoped threads

- A panic while holding a `Mutex` **poisons** it; later `lock()` calls return `Err` so callers can decide whether the data is still valid.
- **`thread::scope`** (**1.63**) lets threads borrow local data without `'static` or `Arc`, since they must finish before the scope ends.

### Channels

- `std::sync::mpsc`: multi-producer single-consumer; `channel()` is unbounded, `sync_channel(n)` bounded.
- **crossbeam** adds multi-consumer channels and `select!`.

### Atomics and memory ordering

- **Relaxed**: atomicity only. **Release** store + **Acquire** load: happens-before between the two threads. **SeqCst**: one global order, strongest and slowest.

## Async

### Futures and executors

- Futures are **lazy** — nothing runs until an executor (e.g. **Tokio**) polls them.
- Holding a non-`Send` guard across `.await` makes the future non-`Send`, so it can't be spawned on a multi-threaded runtime.

### Blocking in async code

- A blocking call inside async code stalls the worker thread and every task on it — move it to **`spawn_blocking`**.

### Cancellation is drop

- Dropping a future cancels it at its current `.await`, with no signal — **cancel safety** in `select!` means losing a branch mid-await leaves no half-done state.

## Unsafe and FFI

### What `unsafe` allows

- Five extra powers: dereference raw pointers, call unsafe functions, implement unsafe traits, access mutable statics, read union fields.
- It does **not** turn off the borrow checker for references.

### Undefined behavior and Miri

- Common UB: two live `&mut` to the same data, invalid values (a `bool` that isn't 0/1), data races on non-atomic memory.
- **Miri** interprets MIR and catches much UB that "works" in normal builds.

## Macros and Cargo

### Macro kinds and hygiene

- **`macro_rules!`** pattern-matches token trees; **procedural macros** (derive, attribute, function-like) run code on a `TokenStream` at compile time.
- **Hygiene**: identifiers created inside a macro don't collide with the caller's, unlike C textual macros.

### Features and workspaces

- **Features are additive** — unioned across the dependency graph — so a feature must never remove functionality.
- A **workspace** shares one `Cargo.lock` and `target/` across crates.

### Lock files and editions

- Commit **`Cargo.lock`** for binaries; since 2023, Cargo's guidance is to commit it for libraries too, as a CI baseline (dependents ignore it).
- **Editions** are opt-in, per-crate language changes; **edition 2024** is available **since Rust 1.85**.
