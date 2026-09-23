# Python Cheatsheet

The 20 most frequently asked Python interview topics, with short answers.

## 1. What is the GIL, and how does it affect concurrency?

The **Global Interpreter Lock** allows only one thread to execute Python bytecode at a time in CPython, even on multi-core machines. It exists to keep reference counting (CPython's memory management) thread-safe without fine-grained locking.

`threading` still helps for **I/O-bound** work, because the GIL is released during blocking I/O and some C-extension calls. For **CPU-bound** work, use `multiprocessing` (separate processes, separate GILs) or a C extension that releases the GIL. Python 3.13 introduced an experimental **free-threaded build** (`--disable-gil`) that removes it entirely.

## 2. How does Python's memory management work?

CPython uses **reference counting** as the primary mechanism: each object tracks how many references point to it, and it's freed immediately when the count hits zero. A **cyclic garbage collector** runs periodically to catch reference cycles (e.g. two objects referencing each other) that counting alone can't free.

`gc` module controls this collector (`gc.disable()`, `gc.collect()`). `sys.getrefcount(obj)` inspects the count. Small integers and interned strings are cached and reused. `__slots__` on a class avoids the per-instance `__dict__`, cutting memory for classes with many instances.

## 3. What are generators, and how do they differ from lists?

A **generator** produces values lazily, one at a time, via `yield`, instead of building a full list in memory. Each call to `next()` resumes the function where it left off, retaining local state. This makes them ideal for large or infinite sequences.

`(x**2 for x in range(n))` is a generator expression, versus `[x**2 for x in range(n)]` which is a list comprehension built eagerly. Generators are **exhausted after one pass**; you can't restart them. `yield from` delegates to a sub-generator, useful for composing pipelines.

## 4. What is the difference between `is` and `==`?

**`==`** compares values via `__eq__`; **`is`** compares identity — whether two names point to the **same object** in memory (`id(a) == id(b)`). Use `is` for `None`, `True`, `False`, and sentinel comparisons; use `==` for value equality.

Gotcha: CPython caches small integers (-5 to 256) and some string literals, so `a is b` can be `True` for equal small ints by implementation accident — never rely on that for general values.

## 5. How do mutable default arguments cause bugs?

A default argument value is evaluated **once**, at function definition time, not on each call. If the default is mutable (`def f(x, cache=[])`), every call without an explicit argument shares and mutates the **same object**, causing state to leak across calls.

Fix: use `None` as the sentinel default and create the mutable object inside the function body: `def f(x, cache=None): cache = [] if cache is None else cache`.

## 6. What are decorators, and how do you write one that preserves metadata?

A **decorator** is a function that wraps another function or class to add behavior without modifying its source: `@decorator` above a `def` is sugar for `func = decorator(func)`. Common uses: logging, timing, caching (`functools.lru_cache`), access control, registration.

A decorator that wraps with an inner function should use **`functools.wraps(func)`** on the wrapper, or the wrapped function loses its `__name__`, `__doc__`, and signature for introspection and debugging tools.

## 7. What is the difference between `*args` and `**kwargs`?

**`*args`** collects extra positional arguments into a tuple; **`**kwargs`** collects extra keyword arguments into a dict. They let a function accept a variable number of arguments and are commonly used to forward calls in wrappers/decorators (`func(*args, **kwargs)`).

Since PEP 570 (3.8), `/` in a signature marks preceding parameters as **positional-only**, and `*` marks following ones as **keyword-only** — useful for stable public APIs.

## 8. How does Python's scoping and closures work (`LEGB`)?

Name resolution follows **LEGB**: Local, Enclosing, Global, Built-in — the interpreter searches each scope in that order. A function reading an outer variable creates a **closure**; the variable is looked up by reference, not copied at definition time (the same loop-variable-capture gotcha as other languages).

Assigning to a name inside a function makes it **local** by default, even if a global of the same name exists — this raises `UnboundLocalError` if read before assignment. Use `global` or `nonlocal` to explicitly bind to an outer scope for assignment.

## 9. What are context managers, and how does `with` work?

A **context manager** implements `__enter__`/`__exit__` (or is built via `@contextlib.contextmanager` around a generator with one `yield`). `with obj:` calls `__enter__` on entry and guarantees `__exit__` runs on exit, even if an exception occurs — used for files, locks, DB transactions, and temporary state changes.

`__exit__` receives exception info and can suppress the exception by returning `True`. Multiple managers can be combined: `with open(a) as f1, open(b) as f2:`.

## 10. What's the difference between deep copy and shallow copy?

**`copy.copy()`** (shallow) creates a new outer object but keeps references to the same nested/child objects. **`copy.deepcopy()`** recursively copies every nested object, producing a fully independent structure. Mutating a nested list after a shallow copy affects both copies.

Simple immutable containers (tuples of ints, etc.) don't need deep copying. Deep copy can be slow and must handle cycles (it does, via a memo dict) — prefer shallow copy or restructuring data when performance matters.

## 11. How does exception handling work, and what's the `else`/`finally` for?

`try`/`except` catches exceptions; catch the **most specific type first** since Python checks `except` clauses in order. `else` runs only if the `try` block **didn't** raise, useful to separate "code that might fail" from "code that runs after success." `finally` always runs, for cleanup regardless of outcome.

Use `raise NewError(...) from original_err` to chain exceptions and preserve the original traceback context. Avoid bare `except:` — it also catches `KeyboardInterrupt`/`SystemExit`; use `except Exception:` instead.

## 12. What is duck typing, and how do Protocols relate to it?

**Duck typing**: an object's suitability is determined by whether it has the needed methods/attributes at runtime, not by its declared type ("if it walks like a duck..."). This underlies Python's dynamic typing and things like iterables, context managers, and callables.

`typing.Protocol` (3.8+) formalizes this for static type checkers: a class satisfies a Protocol by having matching methods, with **no explicit inheritance required** (structural typing), unlike ABCs which require explicit subclassing or registration.

## 13. How do `async`/`await` and the event loop work?

**`async def`** defines a coroutine; `await` suspends it until the awaited coroutine/future completes, yielding control back to the **event loop** (`asyncio`), which runs other ready coroutines in the meantime — single-threaded concurrency via cooperative multitasking, good for I/O-bound work.

`asyncio.gather()` runs coroutines concurrently and collects results. A blocking call (e.g. `time.sleep`, sync file I/O) inside a coroutine **blocks the whole event loop** — use `asyncio.sleep`, async libraries, or `run_in_executor` for blocking work.

## 14. What's the difference between `@staticmethod`, `@classmethod`, and instance methods?

An **instance method** takes `self`, operates on an instance. A **`@classmethod`** takes `cls` instead, operates on the class itself — commonly used for alternative constructors (`Point.from_tuple(...)`) and is inherited correctly by subclasses (unlike hardcoding the class name). A **`@staticmethod`** takes neither — it's just a regular function namespaced inside the class for organization.

## 15. How does Python resolve method calls with multiple inheritance (MRO)?

Python uses the **C3 linearization algorithm** to compute the **Method Resolution Order** — a deterministic, consistent ordering of a class and its ancestors. `ClassName.__mro__` or `.mro()` shows the order; `super()` follows this order, not just the immediate parent, which lets **cooperative multiple inheritance** (mixins) work correctly.

This matters for mixin-based design: each class's `__init__` should call `super().__init__(...)` so the whole chain initializes properly.

## 16. What is the difference between a module and a package? How does `import` work?

A **module** is a single `.py` file. A **package** is a directory containing an `__init__.py` (or, since 3.3, a namespace package without one) plus modules/subpackages. `import` searches `sys.path`, caches loaded modules in `sys.modules` (so a module's top-level code runs only once), and circular imports fail when two modules need each other's names before either finishes loading.

Use `from __future__ import annotations` or `TYPE_CHECKING` guards to break circular imports needed only for type hints.

## 17. What are Python's built-in data structures, and when do you use each?

**`list`** — ordered, mutable, O(1) append/index, O(n) search/insert-at-front. **`tuple`** — ordered, immutable, hashable if elements are, usable as dict keys. **`dict`** — hash map, insertion-ordered since 3.7, O(1) average lookup. **`set`**/`frozenset` — unordered unique elements, O(1) average membership test, set algebra (`|`, `&`, `-`).

`collections` module extras: `defaultdict` (auto-initializing values), `Counter` (frequency counting), `deque` (O(1) append/pop from both ends, unlike `list`'s O(n) from the front), `OrderedDict` (rarely needed now that dicts preserve order).

## 18. How do type hints work, and are they enforced at runtime?

Type hints (`def f(x: int) -> str:`) are **not enforced at runtime** by the interpreter — they're metadata checked by static tools like `mypy` or `pyright`. This is **gradual typing**: you can annotate incrementally, and unannotated code is still valid.

`typing` provides generics (`list[int]`, `dict[str, int]` natively since 3.9), `Optional[T]`/`T | None`, `Union`, `Callable`, and `TypeVar` for generic functions/classes. `dataclasses` (`@dataclass`) auto-generates `__init__`, `__repr__`, `__eq__` from annotated fields.

## 19. What is the difference between a virtual environment and a package manager?

A **virtual environment** (`venv`, `virtualenv`) isolates a project's installed packages and interpreter from the system Python, avoiding version conflicts between projects. A **package manager** (`pip`, or higher-level tools like `poetry`/`uv`) installs, resolves, and locks dependency versions, typically into an active virtual environment.

`requirements.txt` lists dependencies (often unpinned or loosely pinned); a **lock file** (`poetry.lock`, `uv.lock`) pins exact resolved versions for reproducible installs. `pip freeze` captures the current environment's exact versions.

## 20. How do you profile and test Python code?

The standard `unittest` module or (far more common in practice) **`pytest`** covers testing: fixtures, parametrization (`@pytest.mark.parametrize`), and plugins for coverage (`pytest-cov`) and mocking (`unittest.mock`/`pytest-mock`). `mock.patch` replaces objects/functions for the duration of a test.

For performance: **`cProfile`** gives function-level call counts and cumulative time (`python -m cProfile -s cumtime script.py`); `timeit` benchmarks small snippets accurately by controlling for setup overhead; `line_profiler` shows per-line timing for a chosen function. Always profile before optimizing.
