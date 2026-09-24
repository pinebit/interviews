# Python

What experienced Python engineers forget before an interview, grouped by subtopic.

## Runtime and the GIL

### Bytecode and the GIL

- CPython compiles to bytecode run by a stack-based VM; the **GIL** lets only one thread execute Python bytecode at a time, keeping refcounting thread-safe without per-object locking.
- The GIL is released during blocking I/O and by some C extensions, so `threading` still helps **I/O-bound** work; for **CPU-bound** work use `multiprocessing` (separate processes, separate GILs) or a GIL-releasing C extension.
- The **free-threaded build** (no GIL) was experimental in **3.13** and became **officially supported (PEP 779)** in **3.14** — third-party C-extension packages may still be incompatible and force the GIL back on.
- **`concurrent.interpreters`** (**3.14**, PEP 734) runs multiple interpreters in one process, each with its own GIL, communicating over cross-interpreter queues — true parallelism without separate OS processes.

## Memory management

### Refcounting and GC

- **Reference counting** is the primary mechanism — an object is freed the instant its count hits zero; a **generational cyclic GC** runs periodically to catch reference cycles counting alone can't free.
- CPython caches small ints (**-5 to 256**) and some string literals (**interning**) — this is why `is` can accidentally return `True` for equal small values; never rely on it for general values.
- **`__slots__`** replaces the per-instance `__dict__` with fixed storage, cutting memory for classes with many instances (and disabling arbitrary new attributes).
- **`weakref`** holds a reference that doesn't keep the object alive, used for caches and observer patterns; **`__del__`** runs at collection time (not deterministically, and never for objects the GC can't reach due to a cycle involving `__del__` in old Python — though the cyclic GC handles finalizers correctly since 3.4).

## Concurrency

### Threads, processes, asyncio

- Choose by workload: threads for I/O-bound (limited by the GIL for CPU work), processes for CPU-bound (real parallelism, higher memory/IPC cost), asyncio for high-concurrency I/O with low overhead per task.
- **`multiprocessing` start methods**: `fork` (copies the parent process, fast but can inherit inconsistent state — e.g. locks held mid-acquire), `spawn` (fresh interpreter, slower, safest), `forkserver` (a forked-once server process forks children on demand, avoiding fork's thread-safety pitfalls). **`forkserver` became the default on Linux in Python 3.14** (previously `fork`).
- **asyncio**: `async def` defines a coroutine; `await` suspends it, yielding control to the event loop. **`asyncio.gather()`** runs several concurrently; **`TaskGroup`** (**3.11**) is the structured-concurrency alternative — it cancels siblings on any unhandled exception and waits for cleanup, which `gather` doesn't do by default.
- A blocking call inside a coroutine (`time.sleep`, sync file I/O) **stalls the whole event loop** — use `asyncio.sleep`, async libraries, or **`asyncio.to_thread`**.
- Task cancellation raises `CancelledError` inside the coroutine at its next suspension point — code doing cleanup in `finally` must not swallow it silently.

## Gotchas

### Classic traps

- **Mutable default arguments** are evaluated **once at definition time** — `def f(x, cache=[])` shares one list across all calls; use `None` as sentinel and create the mutable object inside the body.
- **Late-binding closures in loops**: a closure captures the *variable*, not its value at definition time — `[lambda: i for i in range(3)]` all return `2`. Fix by defaulting the parameter (`lambda i=i: i`).
- **`LEGB`** scope resolution (Local, Enclosing, Global, Built-in); assigning to a name inside a function makes it local for the *whole* function body, even before the assignment line — reading it earlier raises `UnboundLocalError`. Use `nonlocal`/`global` to bind outward explicitly.
- **Shallow vs deep copy**: `copy.copy()` copies the outer object only — `[[0]*3]*3` builds three references to the *same* inner list, so mutating one row mutates all three; `copy.deepcopy()` recurses (and handles cycles via a memo dict).
- **Mutating a collection while iterating it** (e.g. removing items from a list/dict in a `for` loop) skips elements or raises `RuntimeError: dictionary changed size during iteration` — iterate over a copy instead.
- **Dict insertion order** is guaranteed **since 3.7** (an implementation detail in 3.6) — safe to rely on now.

### Import mechanics

- `import` searches `sys.path` and caches every loaded module in **`sys.modules`**, so a module's top-level code runs only once per process even if imported from many places.
- **Circular imports** fail when two modules each need a name from the other before either has finished executing its top-level code — the importing module gets a partially-initialized module object missing the name it wants. Fix by importing inside a function (deferring the lookup until call time), restructuring to remove the cycle, or guarding a type-only circular import with `TYPE_CHECKING`.

## Object model

### MRO and descriptors

- Multiple inheritance resolves via **C3 linearization** (the **MRO**); `super()` follows the *computed* MRO, not just the immediate parent, which is what makes cooperative multiple inheritance (mixins) work — every class in the chain should call `super().__init__(...)`.
- **Descriptors** (`__get__`/`__set__`/`__delete__` on a class attribute) implement `property`, bound methods, `classmethod`, and `staticmethod` under the hood — understanding them explains why methods "just work" as callables on an instance.
- **`__new__`** creates the instance (called before `__init__`, which only initializes it) — override `__new__` for immutable types or singleton/caching patterns.
- **Metaclasses** (`type` subclasses) customize class *creation*; **`__init_subclass__`** is the lighter-weight hook for most "do something when a subclass is defined" needs, without a full metaclass.
- Defining **`__eq__`** without `__hash__` sets `__hash__` to `None`, making instances unhashable — Python does this because mutable equality and hashing by identity would otherwise silently violate the hash contract.
- **`dataclasses`**: `@dataclass(frozen=True)` makes instances immutable (raises on attribute assignment); `slots=True` (**3.10**) combines dataclasses with `__slots__` for memory savings.

## Functions and iteration

### Generators and decorators

- Generators (`yield`) produce values lazily and are **exhausted after one pass**; `yield from` delegates to a sub-generator. `gen.send(value)` resumes a generator and injects a value as the result of the paused `yield` expression — the basis of old-style coroutines.
- A decorator wrapping with an inner function should use **`functools.wraps(func)`**, or the wrapper loses `__name__`/`__doc__`/signature for introspection.
- Decorators taking their own arguments need an extra call layer: `@decorator(arg)` requires `decorator(arg)` to return the actual decorator function.
- **Context managers**: `__exit__` receives exception info and **returning `True` suppresses** the exception — a common source of silently swallowed errors when copy-pasted without checking the return value. `contextlib.contextmanager` wraps a generator with exactly one `yield` into a context manager.
- **Exceptions**: `else` on `try` runs only if no exception was raised (separates "might fail" from "runs after success"); exception groups and `except*` (**3.11**) let one `try` handle multiple concurrent exceptions raised together (e.g. from a `TaskGroup`).

## Typing

### Static typing in a dynamic language

- Type hints are **not enforced at runtime** — they're metadata for `mypy`/`pyright`; this is **gradual typing**, adoptable incrementally.
- **`typing.Protocol`** (3.8+) gives **structural** typing — a class satisfies it by having matching methods, no inheritance required, unlike ABCs which need explicit subclassing or registration.
- **`TypeVar`** vs **PEP 695 generic syntax** (`class Box[T]: ...`, **3.12**) — the new syntax is scoped to the class/function automatically, replacing manual `TypeVar` declarations.
- **`TypedDict`** types a dict's known keys/value-types without making it a real class.
- Annotation evaluation is **deferred by default since Python 3.14** (**PEP 649**) — annotations are computed lazily on demand instead of eagerly at definition time, making `from __future__ import annotations` largely unnecessary going forward.

## Tooling

### Environment and profiling

- `pyproject.toml` is the standard project/dependency manifest; **`uv`** resolves and installs dependencies (and manages Python versions) much faster than pip-based workflows, with a lock file for reproducible installs.
- **`pytest`** fixtures have **scope** (`function`, `class`, `module`, `session`) controlling how often they're re-created — a common bug is a `session`-scoped fixture holding mutable state that leaks between tests.
- Profiling: **`cProfile`** for function-level call counts/cumulative time; **`py-spy`** attaches to a running process without code changes (useful in production); always profile before optimizing.
