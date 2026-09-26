# Python

What experienced Python engineers forget before an interview, grouped by subtopic.

## Runtime and the GIL

### The GIL

- CPython compiles to bytecode run by a stack-based VM; the **GIL** lets only one thread execute bytecode at a time, keeping refcounting safe without per-object locks.
- The GIL is released during blocking I/O and by some C extensions, so threads still help I/O-bound work; **CPU-bound** work needs processes or a GIL-releasing extension.
- A running thread is asked to drop the GIL every **5 ms** (`sys.getswitchinterval()`), which is why CPU-bound threads also slow I/O threads.
- The GIL doesn't make statements atomic — `x += 1` on a shared value is several bytecodes and still races; use a `Lock`.

### Free threading and subinterpreters

- The **free-threaded build** (no GIL) was experimental in 3.13 and is **officially supported since 3.14** (PEP 779); an incompatible C extension can force the GIL back on.
- **`concurrent.interpreters`** (3.14, PEP 734) runs several interpreters in one process, each with its own GIL, talking over cross-interpreter queues.

### Specializing interpreter and JIT

- **3.11** added the adaptive specializing interpreter, roughly **25%** faster on average: hot bytecodes are rewritten into type-specialized versions.
- 3.13 added an experimental copy-and-patch **JIT**; 3.14's official Windows and macOS builds include it, off by default (`PYTHON_JIT=1`).

## Memory management

### Refcounting and the cyclic GC

- **Reference counting** frees an object the instant its count hits zero; a **generational cyclic GC** periodically frees reference cycles counting can't.
- 3.14.0–3.14.4 shipped an incremental GC; **3.14.5 reverted it** over production memory growth.

### Object identity and caching

- CPython caches small ints (**-5 to 256**) and interns some strings, so `is` can return `True` for equal values by accident.
- Use `==` for values and **`is` only for singletons** like `None`.

### `__slots__`, weakrefs, finalizers

- **`__slots__`** replaces the per-instance `__dict__` with fixed storage — less memory per instance, no arbitrary new attributes.
- **`weakref`** holds a reference that doesn't keep the object alive — for caches and observers.
- **`__del__`** runs at refcount zero, or only at the next GC pass if the object is in a cycle (collectable since 3.4, PEP 442); use `with` for deterministic cleanup (`weakref.finalize` is a safer `__del__`, not more deterministic).

## Built-in data structures

### Time complexity

| Operation | list | dict / set | deque |
|---|---|---|---|
| index / lookup | O(1) | O(1) avg | O(n) |
| append / add | O(1) amortized | O(1) avg | O(1) both ends |
| insert/pop at front | **O(n)** | — | **O(1)** |
| `x in c` | **O(n)** | **O(1)** avg | O(n) |

- `list.sort()`/`sorted` is **Timsort**: stable, O(n log n), O(n) on nearly sorted data.
- `heapq` is a **min-heap** over a plain list; max-heap functions (`heappush_max`, `heappop_max`) exist **since 3.14**; before that, push negated keys.

### dict and set internals

- A dict is an **open-addressing** hash table plus a compact, insertion-ordered entries array — that layout is why order is preserved.
- Keys must be hashable; a mutable object whose hash changes after insertion becomes unfindable.

## Concurrency

### Threads vs processes vs asyncio

| Model | Best for | Cost |
|---|---|---|
| threads | I/O-bound, blocking libraries | GIL limits CPU parallelism |
| processes | CPU-bound | memory, pickling/IPC overhead |
| asyncio | many concurrent I/O waits | everything must be non-blocking |

### multiprocessing start methods

- **`fork`** copies the parent — fast, but can inherit inconsistent state (a lock held by another thread mid-acquire).
- `spawn` starts a fresh interpreter — slower, safest; **`forkserver`** forks children from a clean single-threaded server process.
- **`forkserver` is the Linux default since 3.14** (previously `fork`).

### asyncio event loop

- One thread runs the loop: it polls ready I/O (epoll/kqueue via `selectors` on Unix; IOCP proactor on Windows since 3.8), then runs ready callbacks; a coroutine only yields control at an **`await`** on something not yet ready.
- `asyncio.create_task` schedules a coroutine; calling a coroutine function without awaiting or scheduling it **does nothing**.
- Keep a reference to created tasks — the loop holds only weak references, so an unreferenced task can be **garbage-collected mid-run**.

### asyncio tasks and cancellation

- **`TaskGroup`** (3.11) is structured concurrency: one failure cancels the siblings and waits for them; `gather` doesn't cancel the others by default.
- A blocking call in a coroutine (`time.sleep`, sync file I/O) **stalls the whole event loop** — use async libraries or `asyncio.to_thread`.
- Cancellation raises **`CancelledError`** at the next `await`; `finally` cleanup propagates it automatically, but an `except` that catches it must re-raise.

## Gotchas

### Mutable default arguments

- Defaults are evaluated **once, at definition time** — `def f(x, cache=[])` shares one list across calls; default to `None` and create the object inside.
- Dataclasses reject unhashable defaults (`list`, `dict`, `set`) — use **`field(default_factory=list)`**.

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

- Multiple inheritance resolves via **C3 linearization** (the MRO, `Cls.__mro__`).
- **`super()`** follows the instance's MRO, not the direct parent, so every class in a mixin chain must call `super().__init__()`.

### Descriptors

- An object with `__get__`/`__set__`/`__delete__` on a class attribute is a **descriptor**; `property`, bound methods, `classmethod`, and `staticmethod` are all built on it.
- **Data descriptors** (define `__set__` or `__delete__`) beat the instance `__dict__`; non-data descriptors (only `__get__`, e.g. functions) lose to it.

### Class creation hooks

- **`__new__`** creates the instance, `__init__` only initializes it — override `__new__` for immutable subclasses or instance caching.
- **Metaclasses** customize class *creation*; **`__init_subclass__`** covers most "react when a subclass is defined" needs without one.

### Equality and hashing

- Defining **`__eq__`** without `__hash__` sets `__hash__ = None`, making instances unhashable.
- `@dataclass(frozen=True)` blocks field reassignment (shallow — a list field stays mutable) and generates `__hash__`, which raises `TypeError` on an unhashable field; `slots=True` (**3.10**) adds `__slots__`.

## Functions and iteration

### Generators

- Generators are lazy and **exhausted after one pass**; `yield from` delegates to a sub-generator.
- `gen.send(v)` resumes a generator and makes `v` the value of the paused `yield` expression.

### Decorators

- Wrap with **`functools.wraps(func)`** or the wrapper loses `__name__`, `__doc__`, and signature.
- A decorator with arguments needs an extra layer: `@deco(arg)` calls `deco(arg)`, which must return the real decorator.

### functools.cache pitfalls

- **`@cache`** (3.9) is `lru_cache(maxsize=None)` — unbounded, so it grows forever on unbounded inputs; switch to `lru_cache(maxsize=N)` to bound it.
- On a method it keys on `self` and **keeps every instance alive**; use `cached_property` or a per-instance cache.
- Arguments must be hashable, and a returned mutable object is shared by every caller.

### Context managers and exceptions

- **`__exit__` returning `True` suppresses** the exception; `contextlib.contextmanager` turns a one-`yield` generator into a context manager.
- `try ... else` runs only when no exception was raised; **`except*`** (**3.11**) handles exception groups, e.g. from a `TaskGroup`.

## Recent language features

### Structural pattern matching

- `match` (**3.10**) destructures by shape: `case {"type": "click", "x": x}`, `case Point(x=0)`.
- A bare name in a `case` **binds**, it doesn't compare — `case RED:` matches everything; use dotted names (`Color.RED`) for constants.

### Template strings

- **t-strings** (`t"Hello {name}"`, **3.14**, PEP 750) produce a `Template` object with static parts and interpolated values kept separate.
- A library receiving it can escape values safely (SQL, HTML), unlike an f-string that arrives already joined.

## Typing

### Gradual typing and protocols

- Type hints are **not enforced at runtime** — they're for `mypy`/`pyright`.
- **`typing.Protocol`** gives structural typing: a class matches by having the methods, unlike ABCs, which need subclassing or registration.
- **`TypedDict`** types a dict's known keys without making it a class.

### Generics and annotation evaluation

- **PEP 695** syntax (`class Box[T]: ...`, `type Alias = ...`, 3.12) replaces manual `TypeVar` declarations with scoped type parameters.
- Annotations are **evaluated lazily since 3.14** (**PEP 649**), making `from __future__ import annotations` largely unnecessary.

## Tooling

### Packaging and tests

- `pyproject.toml` is the standard manifest; **`uv`** resolves, installs, and manages Python versions far faster than pip, with a lock file.
- **`pytest`** fixture **scope** (`function`, `class`, `module`, `session`) sets how often it's rebuilt — a `session` fixture holding mutable state leaks between tests.

### Profiling

- **`cProfile`** gives function-level call counts and cumulative time; **`py-spy`** samples a running process without code changes, safe in production.
- **`tracemalloc`** snapshots allocations by line to find memory growth.
