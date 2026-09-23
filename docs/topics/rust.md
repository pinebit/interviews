# Rust Cheatsheet

The 20 most frequently asked Rust interview topics, with short answers.

## 1. What is ownership in Rust?

**Ownership** determines who is responsible for a value. A value has one owner at a time; assigning or passing a non-`Copy` value moves ownership, so the old binding cannot use it. When the owner goes out of scope, Rust drops the value and its owned resources.

Borrowing lets code use a value without moving it. Types such as integers are **`Copy`**, so assigning them duplicates the value instead. Ownership and borrowing make memory safety possible without a tracing garbage collector.

## 2. How do borrowing and references work?

A reference **borrows** a value without owning it: `&T` permits shared reads, while `&mut T` permits exclusive mutation. While a mutable borrow is active, no other borrow may access that value; multiple shared borrows are allowed when there is no active mutable borrow.

The borrow checker also ensures a reference never outlives its referent. Borrow scopes usually end at their last use, so a shared borrow can finish before a later mutable borrow in the same block.

## 3. What are lifetimes, and when do you write them?

A **lifetime** is the region where a reference is valid. Rust usually infers it, but a function returning a reference may need an annotation such as `'a` to express how the output relates to its input references.

Annotations **describe relationships**; they do not extend how long a value lives. If an output could refer to either of two inputs, its validity cannot exceed the shorter relevant input lifetime.

## 4. What are traits, and how do generics use them?

A **trait** defines shared behavior through methods and associated items. A type implements a trait explicitly; a generic bound such as `T: Display` lets a function accept any implementing type and call that behavior.

Generics normally use **static dispatch** through monomorphization. A trait object such as `&dyn Display` uses **dynamic dispatch** through a vtable when runtime polymorphism is needed; it must satisfy object-safety rules.

## 5. How do `Option` and `Result` represent absence and errors?

**`Option<T>`** is `Some(T)` or `None` and makes an absent value explicit. **`Result<T, E>`** is `Ok(T)` or `Err(E)` and carries a recoverable error. Handle variants with `match`, `if let`, or combinators rather than assuming success.

Use `Option` when absence is expected and needs no explanation; use `Result` when callers need a reason for failure. Rust has no general null reference for ordinary references, but raw pointers can be null.

## 6. How does Rust handle recoverable errors versus panics?

Return **`Result<T, E>`** for failures a caller can handle, adding context or converting error types at API boundaries. **`panic!`** signals an unrecoverable condition or violated invariant and is not a substitute for routine error handling.

A panic normally unwinds the current thread's stack and runs destructors, but builds configured with **`panic = "abort"`** terminate without unwinding. Code should not rely on panics for ordinary control flow.

## 7. What does the `?` operator do?

For a **`Result`**, `?` extracts `Ok(value)` or returns early with `Err(error)`, converting the error with `From` when required. For an **`Option`**, it extracts `Some(value)` or returns `None`.

The enclosing function or block must have a compatible return type. `?` propagates failure; it does not log it or add context by itself.

## 8. What is the difference between `String` and `&str`?

**`String`** owns growable UTF-8 text, usually stored on the heap. **`&str`** is a borrowed view of UTF-8 bytes; a string literal has type `&'static str`, while a slice can also refer into a `String`.

Accept `&str` when a function only reads text so callers can pass either form without transferring ownership. String lengths and slice offsets count **bytes**, not characters; direct integer indexing is disallowed because UTF-8 characters have variable length.

## 9. How do `struct` and `enum` differ?

A **`struct`** groups fields that exist together, such as a user's name and email. An **`enum`** represents one of several variants, each of which may carry different data; `Option` and `Result` are standard examples.

Use `match` to handle variants. Exhaustive matching makes the compiler flag code that misses a case when an enum changes.

## 10. How does Rust provide memory management without garbage collection?

Rust uses **ownership and scope** to release resources when their owner is dropped; it does not run a tracing garbage collector. Stack values and owned heap allocations are cleaned up through the same ownership rules, with no required GC pause.

This does not guarantee every allocation is reclaimed: `Rc` or `Arc` reference cycles can leak memory. Use **`Weak`** for links that should not keep an object alive.

## 11. What is `Drop`, and when does it run?

The **`Drop`** trait customizes cleanup when an owned value leaves scope, such as releasing a lock guard or file-backed resource. Fields are dropped automatically after the type's `drop` method runs; most types need no manual `Drop` implementation.

Use `std::mem::drop(value)` to release something early by moving it into `drop`. A value's destructor may not run if the process aborts, the value is deliberately forgotten, or a reference cycle keeps it alive.

## 12. What do `Send` and `Sync` mean?

**`Send`** means ownership of a value can safely move to another thread. **`Sync`** means `&T` can safely be shared across threads; equivalently, `&T` is `Send`. The compiler derives these marker traits for many types from their fields.

`Rc<T>` is neither `Send` nor `Sync`. Manually implementing either trait is **unsafe** because the implementer must uphold its concurrency guarantees.

## 13. How do threads safely share mutable state?

**`Mutex<T>`** gives one thread at a time mutable access through a lock guard. Wrap it in **`Arc<Mutex<T>>`** when multiple threads need shared ownership of the same mutex; each thread gets an `Arc` clone, not a copy of `T`.

The guard unlocks when dropped. Keep critical sections short, handle lock poisoning where relevant, and choose message passing instead when transferring ownership better fits the work.

## 14. What is the difference between `Rc` and `Arc`?

Both provide **shared ownership** through reference counts. **`Rc<T>`** uses non-atomic counts for one thread; **`Arc<T>`** uses atomic counts so owners can be shared across threads when `T` has the required thread-safety traits.

`Arc` makes reference-count updates thread-safe; it does **not** make mutation of `T` safe. Use `Arc<Mutex<T>>`, another synchronization type, or immutable data when threads must access the same contents.

## 15. What does “fearless concurrency” mean in Rust?

Rust's **ownership rules** and `Send`/`Sync` bounds reject many data races at compile time. Threads can own separate values, transfer values through channels, or share state behind synchronization primitives.

These guarantees do not prevent deadlocks, logic races, or every bug in unsafe code. The phrase describes the confidence gained from compiler-checked memory and thread safety, not freedom from all concurrency errors.

## 16. What are channels in Rust?

A **channel** transfers values from senders to a receiver, often moving ownership instead of sharing mutable state. The standard library's `std::sync::mpsc` supports multiple producers and one consumer; cloning a sender lets several threads send.

`channel()` is unbounded, while `sync_channel(n)` adds a capacity limit and blocks senders when full. Receiving reports disconnection after all senders are dropped, which gives the consumer a natural exit signal.

## 17. What is a closure, and how does it capture variables?

A **closure** is an anonymous function that can use variables from its surrounding scope. It captures each value by shared borrow, mutable borrow, or ownership according to how the closure uses it; its capabilities are described by `Fn`, `FnMut`, and `FnOnce`.

`move` makes captures occur by value, useful when sending a closure to a thread. It may **copy** a `Copy` value rather than moving it, so `move` does not always consume the original binding.

## 18. What is `unsafe` Rust, and when is it needed?

An **`unsafe` block** permits operations the compiler cannot prove safe, such as dereferencing raw pointers, calling unsafe functions, accessing mutable statics, or using foreign interfaces. It is common at FFI and low-level abstraction boundaries.

`unsafe` does **not** turn off the borrow checker. The programmer must uphold the operation's documented invariants; keep unsafe blocks small and expose a safe API only when those invariants are enforced.

## 19. What is Cargo?

**Cargo** is Rust's package manager and build tool. `Cargo.toml` declares a package and its dependencies; `Cargo.lock` records resolved versions for reproducible builds.

Common commands are `cargo build`, `cargo run`, `cargo test`, and `cargo doc`. A **crate** is a compilation unit, while a package can contain a library crate, binary crates, or both.

## 20. How do macros differ from functions?

A **function** receives typed values at runtime and has a fixed signature. A **macro** operates on Rust syntax during compilation, allowing forms such as `println!` with variable arguments or `vec!` with repeated elements.

**Declarative macros** match syntax patterns; **procedural macros** transform token streams, powering derives and attributes. Prefer functions for ordinary behavior and macros when syntax-level generation is needed.
