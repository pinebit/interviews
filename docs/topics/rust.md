# Rust

What experienced Rust engineers forget before an interview, grouped by subtopic.

## Ownership and borrowing

### Move semantics and Copy

- A non-`Copy` value has one owner; assignment or passing [moves](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html#variables-and-data-interacting-with-move) it, invalidating the old binding.
- [`Copy`](https://doc.rust-lang.org/std/marker/trait.Copy.html) is an implicit bitwise copy, allowed only if every field is `Copy` and there's no `Drop`; [`Clone`](https://doc.rust-lang.org/std/clone/trait.Clone.html) is explicit and possibly expensive.

### Borrow rules and NLL

- Many `&T` or one `&mut T` at a time — never both for overlapping uses ([borrowing rules](https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html#the-rules-of-references)).
- [Non-lexical lifetimes](https://blog.rust-lang.org/2022/08/05/nll-by-default/): a borrow ends at its last use, not at the end of the block.
- Reborrowing (`&mut *r`, implicit when passing `r`) makes a shorter borrow, so you can call several `&mut self` methods in a row.

### Interior mutability

| Type | Checked | Thread-safe | Note |
|---|---|---|---|
| [`Cell<T>`](https://doc.rust-lang.org/std/cell/struct.Cell.html) | none needed | no | copy/replace in and out; no references through `&Cell` |
| [`RefCell<T>`](https://doc.rust-lang.org/std/cell/struct.RefCell.html) | runtime | no | a conflicting borrow panics |
| [`OnceCell`](https://doc.rust-lang.org/std/cell/struct.OnceCell.html)/[`OnceLock`](https://doc.rust-lang.org/std/sync/struct.OnceLock.html) | write once | `OnceLock` yes | lazy initialization |
| [`Mutex`](https://doc.rust-lang.org/std/sync/struct.Mutex.html)/[`RwLock`](https://doc.rust-lang.org/std/sync/struct.RwLock.html) | runtime (lock) | yes | can be poisoned |

## Lifetimes

### Elision rules

- [Rule 1](https://doc.rust-lang.org/reference/lifetime-elision.html#lifetime-elision-in-functions): each elided input reference gets its own lifetime.
- Rule 2: exactly one input lifetime → it's used for all outputs.
- Rule 3: in methods, `&self`'s lifetime goes to all outputs.

### `'static` and HRTBs

- [`T: 'static`](https://doc.rust-lang.org/rust-by-example/scope/lifetime/static_lifetime.html#trait-bound) means "holds no non-static borrows" — `String`, `Vec<u8>` satisfy it, `Box<&'a str>` doesn't; it doesn't mean "lives forever". `&'static T` is the forever reference.
- [HRTB](https://doc.rust-lang.org/nomicon/hrtb.html) (`for<'a> Fn(&'a T)`) says "works for every lifetime", needed when the reference is only created inside the callee.

### "Does not live long enough"

- Usually a [temporary](https://doc.rust-lang.org/reference/destructors.html#temporary-scopes) dropped at the end of the statement while still borrowed — bind it to a variable first.
- Or a struct outliving a reference it holds — find where the referent is actually owned, or store owned data instead.

## Traits and generics

### Static vs dynamic dispatch

- Generics are [monomorphized](https://doc.rust-lang.org/book/ch10-01-syntax.html#performance-of-code-using-generics): one copy per type, zero-cost calls, bigger binary.
- [`dyn Trait`](https://doc.rust-lang.org/reference/types/trait-object.html) is unsized; `&dyn`/`Box<dyn>` is a fat pointer (data + vtable): one copy, an indirect call, heterogeneous collections.
- [Dyn compatibility](https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility) (formerly "object safety"): roughly, no methods returning `Self` by value and no generic methods.

### Coherence: orphan rule and blanket impls

- [Orphan rule](https://doc.rust-lang.org/reference/items/implementations.html#orphan-rules): implement a trait only if your crate owns the trait or the type — prevents conflicting impls across crates.
- [Blanket impls](https://doc.rust-lang.org/book/ch10-02-traits.html#using-trait-bounds-to-conditionally-implement-methods) (`impl<T: Display> MyTrait for T`) cover every type meeting a bound.

### Associated types vs type parameters

- [Associated types](https://doc.rust-lang.org/reference/items/associated-items.html#associated-types) (`Iterator::Item`) fix one type per impl; type parameters allow many impls for one type (`From<A>`, `From<B>`).
- [GATs](https://blog.rust-lang.org/2022/10/28/gats-stabilization/) (1.65) let an associated type be generic, e.g. over a lifetime — the basis of lending iterators.

### `Sized` and `impl Trait`

- Every type parameter is implicitly [`Sized`](https://doc.rust-lang.org/std/marker/trait.Sized.html); `?Sized` accepts `str`, `[T]`, or `dyn Trait` behind a pointer.
- [`impl Trait`](https://doc.rust-lang.org/reference/types/impl-trait.html) in argument position is an anonymous generic; in return position it hides the concrete type but stays static dispatch.

### Eq, Ord, and Hash

- [`PartialEq`](https://doc.rust-lang.org/std/cmp/trait.PartialEq.html)/[`PartialOrd`](https://doc.rust-lang.org/std/cmp/trait.PartialOrd.html) allow incomparable values (NaN ≠ NaN); [`Eq`](https://doc.rust-lang.org/std/cmp/trait.Eq.html) promises an equivalence relation (`a == a`), [`Ord`](https://doc.rust-lang.org/std/cmp/trait.Ord.html) a total order.
- `f64` implements none of `Eq`, `Ord`, or `Hash`, so it can't key a `HashMap` or `BTreeMap` or use `.sort()`; use [`sort_by(f64::total_cmp)`](https://doc.rust-lang.org/std/primitive.f64.html#method.total_cmp) or an ordered wrapper.
- [`Hash` must agree with `Eq`](https://doc.rust-lang.org/std/hash/trait.Hash.html#hash-and-eq) (`a == b` ⇒ equal hashes), or map lookups silently fail.
- [Derived `PartialOrd`/`Ord`](https://doc.rust-lang.org/std/cmp/trait.PartialOrd.html#derivable) compare fields in declaration order; enums by discriminant (variant order unless set explicitly), then fields.

### Async functions in traits

- [Async fn in traits](https://blog.rust-lang.org/2023/12/21/async-fn-rpit-in-traits/) (1.75) desugars to a method returning `impl Future`.
- Callers can't require that future to be `Send` without help (the [`trait-variant`](https://docs.rs/trait-variant) crate), and `dyn` dispatch still needs boxing or [`async-trait`](https://docs.rs/async-trait).

## Closures, iterators, strings

### Fn, FnMut, FnOnce

| Trait | Captured state | Callable |
|---|---|---|
| [`Fn`](https://doc.rust-lang.org/std/ops/trait.Fn.html) | borrowed immutably | many times, via `&self` (concurrently only if `Sync`) |
| [`FnMut`](https://doc.rust-lang.org/std/ops/trait.FnMut.html) | borrowed mutably | many times, via `&mut self` |
| [`FnOnce`](https://doc.rust-lang.org/std/ops/trait.FnOnce.html) | moved out / consumed | once |

- Every `Fn` is also `FnMut` and `FnOnce`; take the loosest bound your code allows (`FnOnce` if you call it once), so callers can pass more kinds of closures.
- [`move`](https://doc.rust-lang.org/reference/expressions/closure-expr.html#closure-expressions) changes how variables are captured (by value), not which trait is implemented — a `move` closure that only reads is still `Fn`.
- [Async closures](https://blog.rust-lang.org/2025/02/20/Rust-1.85.0/#async-closures) (`async || { ... }`, 1.85) can borrow from their captures across `.await`, which `|| async { ... }` couldn't; bound them with [`AsyncFn`](https://doc.rust-lang.org/std/ops/trait.AsyncFn.html)/`AsyncFnMut`/`AsyncFnOnce`.

### Iterators

- [Iterator](https://doc.rust-lang.org/std/iter/index.html) adapters (`map`, `filter`, …) are [lazy](https://doc.rust-lang.org/std/iter/index.html#laziness): nothing runs until a consumer (`collect`, `sum`, `for`).
- They compile to the same code as a hand-written loop — a [zero-cost abstraction](https://doc.rust-lang.org/book/ch13-04-performance.html).

### String vs &str

- [No indexing by integer](https://doc.rust-lang.org/book/ch08-02-strings.html#indexing-into-strings) (`s[0]` doesn't compile) because characters are variable-width; slicing at a non-char boundary panics.
- [`len()`](https://doc.rust-lang.org/std/primitive.str.html#method.len) counts bytes; [`chars()`](https://doc.rust-lang.org/std/primitive.str.html#method.chars) yields [Unicode scalar values](https://www.unicode.org/glossary/#unicode_scalar_value), which still aren't user-perceived characters ([grapheme clusters](https://www.unicode.org/reports/tr29/)).

## Smart pointers and memory

### Box, Rc, Arc, Cow

- [`Box<T>`](https://doc.rust-lang.org/std/boxed/struct.Box.html): single owner on the heap. [`Rc<T>`](https://doc.rust-lang.org/std/rc/struct.Rc.html): shared, non-atomic count, one thread. [`Arc<T>`](https://doc.rust-lang.org/std/sync/struct.Arc.html): atomic count, cross-thread.
- An `Rc`/`Arc` cycle leaks; break it with [`rc::Weak`](https://doc.rust-lang.org/std/rc/struct.Weak.html) or [`sync::Weak`](https://doc.rust-lang.org/std/sync/struct.Weak.html).
- [`Cow<T>`](https://doc.rust-lang.org/std/borrow/enum.Cow.html) borrows until a mutation forces an owned copy.

### RAII, drop order, leaking

- [RAII](https://doc.rust-lang.org/rust-by-example/scope/raii.html): resources (files, locks, sockets) are released in [`Drop`](https://doc.rust-lang.org/std/ops/trait.Drop.html) when the owner goes out of scope — no `finally` needed.
- [Locals drop in reverse declaration order](https://doc.rust-lang.org/reference/destructors.html); struct fields drop in declaration order.
- [`mem::forget`](https://doc.rust-lang.org/std/mem/fn.forget.html) is safe: [leaking memory](https://doc.rust-lang.org/nomicon/leaking.html) isn't undefined behavior in Rust.

### Deref coercion, AsRef, Borrow

- [Deref coercion](https://doc.rust-lang.org/std/ops/trait.Deref.html#deref-coercion) converts `&String` → `&str`, `&Vec<T>` → `&[T]`, `&Box<T>` → `&T` automatically at calls and method lookups.
- [`AsRef<T>`](https://doc.rust-lang.org/std/convert/trait.AsRef.html) is a cheap reference conversion for flexible parameters: `fn open<P: AsRef<Path>>(p: P)`.
- [`Borrow<T>`](https://doc.rust-lang.org/std/borrow/trait.Borrow.html) also promises identical `Eq`/`Hash`/`Ord`, which is why `HashMap<String, V>::get` accepts a `&str`.

### Layout and niche optimization

- [Niche optimization](https://doc.rust-lang.org/std/option/index.html#representation): `Option<&T>`, `Option<Box<T>>`, and `Option<NonZeroU32>` are the same size as the inner type — the forbidden null or zero value encodes `None`.
- The default [`repr(Rust)`](https://doc.rust-lang.org/reference/type-layout.html#the-rust-representation) may reorder fields to cut padding; [`repr(C)`](https://doc.rust-lang.org/reference/type-layout.html#the-c-representation) fixes C field order for FFI.
- `&str`, `&[T]`, and `&dyn Trait` are two words (pointer + length or vtable); an enum is its largest variant plus a tag, unless a niche absorbs the tag.

### Pin and Unpin

- [`Pin<P>`](https://doc.rust-lang.org/std/pin/index.html) stops the pointee from moving only if it's `!Unpin`; most types are [`Unpin`](https://doc.rust-lang.org/std/marker/trait.Unpin.html) and move freely.
- Async state machines are `!Unpin` because they can be self-referential — that's why futures are polled through `Pin<&mut Self>`.

## Error handling

### `?` and error crates

- [`?`](https://doc.rust-lang.org/reference/expressions/operator-expr.html#the-try-propagation-expression) returns early with `Err`, converting via [`From`](https://doc.rust-lang.org/std/convert/trait.From.html); on `Option` it returns `None`.
- [`thiserror`](https://docs.rs/thiserror) for libraries (typed enums callers can match); [`anyhow`](https://docs.rs/anyhow) for applications (one dynamic error with context).

### Integer overflow and casts

- [Overflow](https://doc.rust-lang.org/reference/expressions/operator-expr.html#overflow) panics in debug builds and wraps in release (unless [`overflow-checks = true`](https://doc.rust-lang.org/cargo/reference/profiles.html#overflow-checks)), so state intent with [`checked_*`](https://doc.rust-lang.org/std/primitive.i32.html#method.checked_add), `wrapping_*`, `saturating_*`, or `overflowing_*`.
- [`as` between integers](https://doc.rust-lang.org/reference/expressions/operator-expr.html#numeric-cast) truncates or reinterprets silently (`300_i32 as u8 == 44`, `-1_i32 as u32 == u32::MAX`); [`try_from`](https://doc.rust-lang.org/std/convert/trait.TryFrom.html) fails instead.
- `as` from float to integer [saturates](https://blog.rust-lang.org/2020/07/16/Rust-1.45.0/#fixing-unsoundness-in-casts) (since 1.45), and NaN becomes 0.

### Panics and unwinding

- `panic!` [unwinds](https://doc.rust-lang.org/nomicon/unwinding.html) by default, running destructors; [`panic = "abort"`](https://doc.rust-lang.org/cargo/reference/profiles.html#panic) exits immediately — smaller binary, no recovery.
- [`catch_unwind`](https://doc.rust-lang.org/std/panic/fn.catch_unwind.html) stops an unwinding panic at a boundary (FFI, worker pool) — never for control flow, and useless under `abort`.

## Concurrency

### Send and Sync

- [`Send`](https://doc.rust-lang.org/std/marker/trait.Send.html): ownership can move to another thread. [`Sync`](https://doc.rust-lang.org/std/marker/trait.Sync.html): `&T` can be shared (`T: Sync` ⇔ `&T: Send`).
- `Rc` is neither; `RefCell<T>` is `Send` if `T: Send`, never `Sync`; [`MutexGuard`](https://doc.rust-lang.org/std/sync/struct.MutexGuard.html) is not `Send` — it must be released on the locking thread.

### Mutex poisoning and scoped threads

- A panic while holding a `Mutex` [poisons](https://doc.rust-lang.org/std/sync/struct.Mutex.html#poisoning) it; later `lock()` calls return `Err` so callers can decide whether the data is still valid.
- [`thread::scope`](https://doc.rust-lang.org/std/thread/fn.scope.html) (1.63) lets threads borrow local data without `'static` or `Arc`, since they must finish before the scope ends.

### Channels

- [`std::sync::mpsc`](https://doc.rust-lang.org/std/sync/mpsc/index.html): multi-producer single-consumer; `channel()` is unbounded, `sync_channel(n)` bounded.
- [crossbeam](https://docs.rs/crossbeam-channel) adds multi-consumer channels and `select!`.

### Atomics and memory ordering

- [`Relaxed`](https://doc.rust-lang.org/std/sync/atomic/enum.Ordering.html): atomicity only. `Release` store + an `Acquire` load that reads its value: happens-before between the two threads. `SeqCst`: one global order, strongest and slowest.
- x86 is [strongly ordered](https://en.wikipedia.org/wiki/Memory_ordering#In_symmetric_multiprocessing_%28SMP%29_microprocessor_systems), so a too-weak ordering often works there and fails only on ARM.

## Async

### Futures and executors

- [Futures](https://doc.rust-lang.org/std/future/trait.Future.html) are lazy — nothing runs until an executor (e.g. [Tokio](https://tokio.rs/)) polls them.
- Holding a non-`Send` guard across `.await` makes the future non-`Send`, so it can't be spawned on a multi-threaded runtime.
- [`tokio::spawn`](https://docs.rs/tokio/latest/tokio/task/fn.spawn.html) needs a `Send + 'static` future: move owned data or `Arc` clones in, not references.
- Tokio's default runtime is multi-threaded with [work stealing](https://en.wikipedia.org/wiki/Work_stealing); `current_thread` plus a [`LocalSet`](https://docs.rs/tokio/latest/tokio/task/struct.LocalSet.html) runs non-`Send` futures; [`JoinSet`](https://docs.rs/tokio/latest/tokio/task/struct.JoinSet.html) spawns and awaits a group of tasks.

### Blocking and locks in async code

- A blocking call inside async code stalls the worker thread and every task on it — move it to [`spawn_blocking`](https://docs.rs/tokio/latest/tokio/task/fn.spawn_blocking.html).
- A `std::sync::Mutex` is fine in async code if it's never held across `.await` (and it's faster).
- Use [`tokio::sync::Mutex`](https://docs.rs/tokio/latest/tokio/sync/struct.Mutex.html#which-kind-of-mutex-should-you-use) only when the guard must live across an `.await`.

### Cancellation is drop

- Dropping a [future](https://doc.rust-lang.org/std/future/trait.Future.html) cancels it at its current `.await`, with no signal and no chance to run async cleanup.
- Dropping a Tokio [`JoinHandle`](https://docs.rs/tokio/latest/tokio/task/struct.JoinHandle.html) detaches the spawned task instead — cancel with `abort()`.
- [Cancel safety](https://docs.rs/tokio/latest/tokio/macro.select.html#cancellation-safety): in `select!`, a losing branch is dropped mid-await — `read_line` into a buffer can lose data, `recv()` on a channel can't.

## Unsafe and FFI

### What `unsafe` allows

- [Five extra powers](https://doc.rust-lang.org/book/ch20-01-unsafe-rust.html#unsafe-superpowers): dereference raw pointers, call unsafe functions, implement unsafe traits, access mutable statics, read union fields.
- It does not turn off the borrow checker for references.

### Undefined behavior and Miri

- Common [UB](https://doc.rust-lang.org/reference/behavior-considered-undefined.html): two live `&mut` to the same data, invalid values (a `bool` that isn't 0/1), data races on non-atomic memory.
- [Miri](https://github.com/rust-lang/miri) interprets [MIR](https://rustc-dev-guide.rust-lang.org/mir/index.html) and catches much UB that "works" in normal builds.

## Macros and Cargo

### Macro kinds and hygiene

- [`macro_rules!`](https://doc.rust-lang.org/reference/macros-by-example.html) pattern-matches token trees; [procedural macros](https://doc.rust-lang.org/reference/procedural-macros.html) (derive, attribute, function-like) run code on a `TokenStream` at compile time.
- [Hygiene](https://doc.rust-lang.org/reference/macros-by-example.html#hygiene): `macro_rules!` locals and labels don't collide with the caller's (mixed-site); items and proc-macro output are unhygienic.

### Features and workspaces

- [Features are additive](https://doc.rust-lang.org/cargo/reference/features.html#feature-unification) — unioned across the dependency graph — so a feature must never remove functionality.
- A [workspace](https://doc.rust-lang.org/cargo/reference/workspaces.html) shares one `Cargo.lock` and `target/` across crates.

### Lock files and editions

- Commit `Cargo.lock` for binaries; [since 2023](https://blog.rust-lang.org/2023/08/29/committing-lockfiles/), Cargo's guidance is to commit it for libraries too, as a CI baseline (dependents ignore it).
- [Editions](https://doc.rust-lang.org/edition-guide/editions/index.html) are opt-in, per-crate language changes; crates on different editions link together freely.
- [Edition 2024](https://doc.rust-lang.org/edition-guide/rust-2024/index.html) enables [let chains](https://blog.rust-lang.org/2025/06/26/Rust-1.88.0/#let-chains) (`if let Some(x) = a && x > 0`, 1.88) and makes `impl Trait` in return position [capture all in-scope lifetimes](https://doc.rust-lang.org/edition-guide/rust-2024/rpit-lifetime-capture.html) by default.
