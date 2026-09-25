# Python

What experienced Python engineers forget before an interview, grouped by subtopic.

## Runtime and the GIL

### The GIL

- CPython compiles to bytecode run by a stack-based VM; the **GIL** lets only one thread execute bytecode at a time, keeping refcounting safe without per-object locks.
- The GIL is released during blocking I/O and by some C extensions, so threads still help **I/O-bound** work; **CPU-bound** work needs processes or a GIL-releasing extension.

### Free threading and subinterpreters

- The **free-threaded build** (no GIL) was experimental in 3.13 and is **officially supported since 3.14** (PEP 779); an incompatible C extension can force the GIL back on.
- **`concurrent.interpreters`** (**3.14**, PEP 734) runs several interpreters in one process, each with its own GIL, talking over cross-interpreter queues.

## Memory management

### Refcounting and the cyclic GC

- **Reference counting** frees an object the instant its count hits zero; a **generational cyclic GC** periodically frees reference cycles counting can't.
- 3.14.0–3.14.4 shipped an incremental GC; **3.14.5 reverted it** over production memory growth.

### Object identity and caching

- CPython caches small ints (**-5 to 256**) and interns some strings, so `is` can return `True` for equal values by accident — use `==` for values, `is` only for singletons like `None`.

### `__slots__`, weakrefs, finalizers

- **`__slots__`** replaces the per-instance `__dict__` with fixed storage — less memory per instance, no arbitrary new attributes.
- **`weakref`** holds a reference that doesn't keep the object alive — for caches and observers.
- **`__del__`** runs at refcount zero, or only at the next GC pass if the object is in a cycle (collectable **since 3.4**, PEP 442); use `with` or `weakref.finalize` for deterministic cleanup.

## Concurrency

### Threads vs processes vs asyncio

| Model | Best for | Cost |
|---|---|---|
| threads | I/O-bound, blocking libraries | GIL limits CPU parallelism |
| processes | CPU-bound | memory, pickling/IPC overhead |
| asyncio | many concurrent I/O waits | everything must be non-blocking |

### multiprocessing start methods

- **`fork`** copies the parent — fast, but can inherit inconsistent state (a lock held by another thread mid-acquire).
- **`spawn`** starts a fresh interpreter — slower, safest; **`forkserver`** forks children from a clean single-threaded server process.
- **`forkserver` is the Linux default since 3.14** (previously `fork`).

### asyncio tasks and cancellation

- **`TaskGroup`** (**3.11**) is structured concurrency: one failure cancels the siblings and waits for them; `gather` doesn't cancel the others by default.
- A blocking call in a coroutine (`time.sleep`, sync file I/O) **stalls the whole event loop** — use async libraries or **`asyncio.to_thread`**.
- Cancellation raises **`CancelledError`** at the next `await`; cleanup in `finally` must re-raise it, never swallow it.

## Gotchas

### Mutable default arguments

- Defaults are evaluated **once, at definition time** — `def f(x, cache=[])` shares one list across calls; default to `None` and create the object inside.

### Late-binding closures

- A closure captures the *variable*, not its value — `[lambda: i for i in range(3)]` all return `2`; bind early with `lambda i=i: i`.

### Scope and `UnboundLocalError`

- **LEGB** lookup: Local, Enclosing, Global, Built-in.
- Assigning to a name anywhere in a function makes it local for the **whole** body, so reading it before the assignment raises `UnboundLocalError`; use `nonlocal`/`global`.

### Copies and aliasing

- `[[0] * 3] * 3` builds three references to the **same** inner list — mutating one row mutates all.
- `copy.copy()` copies only the outer object; `copy.deepcopy()` recurses and handles cycles via a memo dict.

### Mutation during iteration

- Removing items from a list inside `for` skips elements; resizing a dict raises `RuntimeError: dictionary changed size during iteration` — iterate over a copy.
- Dict insertion order is guaranteed **since 3.7**.

### Import mechanics

- Loaded modules are cached in **`sys.modules`**, so top-level code runs once per process.
- A **circular import** hands one module a partially initialized module missing the name it needs — import inside the function, break the cycle, or guard type-only imports with `TYPE_CHECKING`.

## Object model

### MRO and `super()`

- Multiple inheritance resolves via **C3 linearization** (the **MRO**); `super()` follows the computed MRO, not the direct parent, so every class in a mixin chain must call `super().__init__()`.

### Descriptors

- An object with `__get__`/`__set__`/`__delete__` on a class attribute is a **descriptor**; `property`, bound methods, `classmethod`, and `staticmethod` are all built on it.
- **Data descriptors** (define `__set__`) beat the instance `__dict__`; non-data descriptors (only `__get__`, e.g. functions) lose to it.

### Class creation hooks

- **`__new__`** creates the instance, `__init__` only initializes it — override `__new__` for immutable subclasses or instance caching.
- **Metaclasses** customize class *creation*; **`__init_subclass__`** covers most "react when a subclass is defined" needs without one.

### Equality and hashing

- Defining **`__eq__`** without `__hash__` sets `__hash__ = None`, making instances unhashable.
- `@dataclass(frozen=True)` makes instances immutable and hashable; `slots=True` (**3.10**) adds `__slots__`.

## Functions and iteration

### Generators

- Generators are lazy and **exhausted after one pass**; `yield from` delegates to a sub-generator.
- `gen.send(v)` resumes a generator and makes `v` the value of the paused `yield` expression.

### Decorators

- Wrap with **`functools.wraps(func)`** or the wrapper loses `__name__`, `__doc__`, and signature.
- A decorator with arguments needs an extra layer: `@deco(arg)` calls `deco(arg)`, which must return the real decorator.

### Context managers and exceptions

- **`__exit__` returning `True` suppresses** the exception; `contextlib.contextmanager` turns a one-`yield` generator into a context manager.
- `try ... else` runs only when no exception was raised; **`except*`** (**3.11**) handles exception groups, e.g. from a `TaskGroup`.

## Typing

### Gradual typing and protocols

- Type hints are **not enforced at runtime** — they're for `mypy`/`pyright`.
- **`typing.Protocol`** gives **structural** typing: a class matches by having the methods, unlike ABCs, which need subclassing or registration.
- **`TypedDict`** types a dict's known keys without making it a class.

### Generics and annotation evaluation

- **PEP 695** syntax (`class Box[T]: ...`, `type Alias = ...`, **3.12**) replaces manual `TypeVar` declarations with scoped type parameters.
- Annotations are **evaluated lazily since 3.14** (**PEP 649**), making `from __future__ import annotations` largely unnecessary.

## Tooling

### Packaging and tests

- `pyproject.toml` is the standard manifest; **`uv`** resolves, installs, and manages Python versions far faster than pip, with a lock file.
- **`pytest`** fixture **scope** (`function`, `class`, `module`, `session`) sets how often it's rebuilt — a `session` fixture holding mutable state leaks between tests.

### Profiling

- **`cProfile`** gives function-level call counts and cumulative time; **`py-spy`** samples a running process without code changes, safe in production.
