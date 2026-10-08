# Python

What experienced Python engineers forget before an interview, grouped by subtopic.

## Runtime and the GIL

### The GIL

- CPython compiles to [bytecode](https://docs.python.org/3/glossary.html#term-bytecode) run by a stack-based VM; the [GIL](https://docs.python.org/3/glossary.html#term-global-interpreter-lock) lets only one thread execute bytecode at a time, keeping refcounting safe without per-object locks.
- The GIL is released during blocking I/O and by some C extensions, so threads still help I/O-bound work; CPU-bound work needs processes or a GIL-releasing extension.
- A running thread is asked to drop the GIL every 5 ms ([`sys.getswitchinterval()`](https://docs.python.org/3/library/sys.html#sys.getswitchinterval)), which is why CPU-bound threads also slow I/O threads.
- The GIL doesn't make statements atomic — `x += 1` on a shared value is several bytecodes and still races; use a [`Lock`](https://docs.python.org/3/library/threading.html#lock-objects).

### Free threading and subinterpreters

- The [free-threaded build](https://docs.python.org/3/howto/free-threading-python.html) (no GIL) was experimental in 3.13 and is officially supported since 3.14 ([PEP 779](https://peps.python.org/pep-0779/)); an incompatible C extension can force the GIL back on.
- [`concurrent.interpreters`](https://docs.python.org/3/library/concurrent.interpreters.html) (3.14, [PEP 734](https://peps.python.org/pep-0734/)) runs several interpreters in one process, each with its own GIL, talking over cross-interpreter queues.

### Specializing interpreter

- 3.11 added the [adaptive specializing interpreter](https://peps.python.org/pep-0659/), roughly [25% faster](https://docs.python.org/3/whatsnew/3.11.html#faster-cpython) on average.
- Hot bytecodes are rewritten in place into type-specialized versions, which fall back when the observed types change.

## Memory management

### Refcounting and the cyclic GC

- [Reference counting](https://docs.python.org/3/glossary.html#term-reference-count) frees an object the instant its count hits zero (the free-threaded build can delay it).
- A generational [cyclic GC](https://docs.python.org/3/library/gc.html) periodically finds and frees reference cycles, which counting alone can't.

### Object identity and caching

- CPython [caches small ints](https://docs.python.org/3/c-api/long.html#c.PyLong_FromLong) (-5 to 256) and [interns](https://docs.python.org/3/library/sys.html#sys.intern) some strings, so `is` can return `True` for equal values by accident.
- Use `==` for values and [`is` only for singletons](https://peps.python.org/pep-0008/#programming-recommendations) like `None`.

### `__slots__`, weakrefs, finalizers

- [`__slots__`](https://docs.python.org/3/reference/datamodel.html#slots) replaces the per-instance `__dict__` with fixed storage — less memory per instance, no arbitrary new attributes.
- [`weakref`](https://docs.python.org/3/library/weakref.html) holds a reference that doesn't keep the object alive — for caches and observers.
- [`__del__`](https://docs.python.org/3/reference/datamodel.html#object.__del__) runs at refcount zero, or only at the next GC pass if the object is in a cycle (collectable since 3.4, [PEP 442](https://peps.python.org/pep-0442/)); use `with` for deterministic cleanup ([`weakref.finalize`](https://docs.python.org/3/library/weakref.html#weakref.finalize) is a safer `__del__`, not more deterministic).

## Built-in data structures

### Time complexity

| Operation | list | dict / set | deque |
|---|---|---|---|
| index / lookup | O(1) | O(1) avg | O(n) |
| append / add | O(1) amortized | O(1) avg | O(1) both ends |
| insert/pop at front | O(n) | — | O(1) |
| `x in c` | O(n) | O(1) avg | O(n) |

- [`list.sort()`](https://docs.python.org/3/library/stdtypes.html#list.sort)/`sorted` is [Timsort](https://en.wikipedia.org/wiki/Timsort): stable, O(n log n), O(n) on nearly sorted data.
- [`heapq`](https://docs.python.org/3/library/heapq.html) is a min-heap over a plain list; max-heap functions ([`heappush_max`](https://docs.python.org/3/library/heapq.html#heapq.heappush_max), `heappop_max`) exist since 3.14; before that, push negated keys.

### dict and set internals

- A dict is an [open-addressing](https://en.wikipedia.org/wiki/Open_addressing) hash table plus a [compact, insertion-ordered entries array](https://docs.python.org/3/whatsnew/3.6.html#new-dict-implementation) — that layout is why order is preserved.
- Keys must be [hashable](https://docs.python.org/3/glossary.html#term-hashable); a mutable object whose hash changes after insertion becomes unfindable.

## Concurrency

### Threads vs processes vs asyncio

| Model | Best for | Cost |
|---|---|---|
| [threads](https://docs.python.org/3/library/threading.html) | I/O-bound, blocking libraries | GIL limits CPU parallelism |
| [processes](https://docs.python.org/3/library/multiprocessing.html) | CPU-bound | memory, pickling/IPC overhead |
| [asyncio](https://docs.python.org/3/library/asyncio.html) | many concurrent I/O waits | everything must be non-blocking |

### multiprocessing start methods

- [`fork`](https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods) copies the parent — fast, but can inherit inconsistent state (a lock held by another thread mid-acquire).
- `spawn` starts a fresh interpreter — slower, safest; `forkserver` forks children from a clean single-threaded server process.
- `forkserver` is the [Linux default since 3.14](https://docs.python.org/3/whatsnew/3.14.html#whatsnew314-multiprocessing-start-method) (previously `fork`); macOS defaults to `spawn` since 3.8, Windows always has.
- With `spawn`/`forkserver`, children re-import the main module, so [guard entry code](https://docs.python.org/3/library/multiprocessing.html#the-spawn-and-forkserver-start-methods) with `if __name__ == "__main__":`; the target, arguments, and results must [pickle](https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled) (no lambdas, local functions, or open file objects).

### asyncio event loop

- One thread runs the [loop](https://docs.python.org/3/library/asyncio-eventloop.html): it polls ready I/O ([epoll](https://en.wikipedia.org/wiki/Epoll)/[kqueue](https://en.wikipedia.org/wiki/Kqueue) via [`selectors`](https://docs.python.org/3/library/selectors.html) on Unix; [IOCP proactor](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.ProactorEventLoop) on Windows since 3.8), then runs ready callbacks; a coroutine only yields control at an `await` on something not yet ready.
- [`asyncio.create_task`](https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task) schedules a coroutine; calling a coroutine function without awaiting or scheduling it does nothing.
- Keep a reference to created tasks — the loop holds only weak references, so an unreferenced task can be garbage-collected mid-run.

### asyncio tasks and cancellation

- [`TaskGroup`](https://docs.python.org/3/library/asyncio-task.html#task-groups) (3.11) is [structured concurrency](https://en.wikipedia.org/wiki/Structured_concurrency): one failure cancels the siblings and waits for them; [`gather`](https://docs.python.org/3/library/asyncio-task.html#asyncio.gather) doesn't cancel the others by default.
- A blocking call in a coroutine (`time.sleep`, sync file I/O) stalls the whole event loop — use async libraries or [`asyncio.to_thread`](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread).
- [Cancellation](https://docs.python.org/3/library/asyncio-task.html#task-cancellation) raises [`CancelledError`](https://docs.python.org/3/library/asyncio-exceptions.html#asyncio.CancelledError) at the next `await`; `finally` cleanup propagates it automatically, but an `except` that catches it must re-raise.

## Gotchas

### Default arguments and late binding

- [Defaults are evaluated once](https://docs.python.org/3/reference/compound_stmts.html#function-definitions), at definition time — `def f(x, cache=[])` shares one list across calls; default to `None` and create the object inside.
- Dataclasses reject unhashable defaults (`list`, `dict`, `set`) — use [`field(default_factory=list)`](https://docs.python.org/3/library/dataclasses.html#mutable-default-values).
- A closure [captures the variable, not its value](https://docs.python.org/3/faq/programming.html#why-do-lambdas-defined-in-a-loop-with-different-values-all-return-the-same-result) — `[lambda: i for i in range(3)]` all return `2`; a default binds early: `lambda i=i: i`.

### Scope and `UnboundLocalError`

- [LEGB](https://docs.python.org/3/reference/executionmodel.html#resolution-of-names) lookup: Local, Enclosing, Global, Built-in.
- Assigning to a name anywhere in a function makes it local for the whole body, so reading it before the assignment raises [`UnboundLocalError`](https://docs.python.org/3/faq/programming.html#why-am-i-getting-an-unboundlocalerror-when-the-variable-has-a-value); use [`nonlocal`](https://docs.python.org/3/reference/simple_stmts.html#the-nonlocal-statement)/[`global`](https://docs.python.org/3/reference/simple_stmts.html#the-global-statement).

### Numeric gotchas

- [`//` and `%` floor toward −∞](https://docs.python.org/3/reference/expressions.html#binary-arithmetic-operations): `-7 // 2 == -4` and `-7 % 2 == 1`; C, Go, Rust, and JavaScript truncate toward zero (`-7 % 2 == -1`).
- [`round()`](https://docs.python.org/3/library/functions.html#round) rounds [half to even](https://en.wikipedia.org/wiki/Rounding#Rounding_half_to_even): `round(2.5) == 2`, `round(3.5) == 4`; `round(2.675, 2) == 2.67` because the float is slightly below 2.675.
- `int` never overflows (arbitrary precision); `float` is an [IEEE 754 double](https://docs.python.org/3/tutorial/floatingpoint.html), so use [`decimal.Decimal`](https://docs.python.org/3/library/decimal.html) built from strings for money.

### Recursion depth

- The default limit is 1000 frames ([`sys.getrecursionlimit()`](https://docs.python.org/3/library/sys.html#sys.getrecursionlimit)); going deeper raises [`RecursionError`](https://docs.python.org/3/library/exceptions.html#RecursionError).
- There's no [tail-call optimization](https://en.wikipedia.org/wiki/Tail_call), so deep DFS or memoized recursion on large inputs needs an explicit stack.
- [`sys.setrecursionlimit`](https://docs.python.org/3/library/sys.html#sys.setrecursionlimit) helps for moderate depths; for depths around 10⁵ and beyond, rewrite iteratively.

### Copies and aliasing

- `[[0] * 3] * 3` builds [three references to the same inner list](https://docs.python.org/3/faq/programming.html#how-do-i-create-a-multidimensional-list) — mutating one row mutates all.
- [`copy.copy()`](https://docs.python.org/3/library/copy.html) copies only the outer object; `copy.deepcopy()` recurses and handles cycles via a memo dict.

### Mutation during iteration

- Removing items from a list inside `for` skips elements.
- Resizing a dict while iterating raises `RuntimeError: dictionary changed size during iteration` — iterate over a copy ([dict views](https://docs.python.org/3/library/stdtypes.html#dictionary-view-objects)).

### Import mechanics

- Loaded modules are cached in [`sys.modules`](https://docs.python.org/3/reference/import.html#the-module-cache), so top-level code runs once per process.
- A [circular import](https://docs.python.org/3/faq/programming.html#what-are-the-best-practices-for-using-import-in-a-module) hands one module a partially initialized module missing the name it needs — import inside the function, break the cycle, or guard type-only imports with [`TYPE_CHECKING`](https://docs.python.org/3/library/typing.html#typing.TYPE_CHECKING).

## Object model

### MRO and `super()`

- Multiple inheritance resolves via [C3 linearization](https://docs.python.org/3/howto/mro.html) (the MRO, [`Cls.__mro__`](https://docs.python.org/3/reference/datamodel.html#type.__mro__)).
- [`super()`](https://docs.python.org/3/library/functions.html#super) follows the instance's MRO, not the direct parent, so every class in a mixin chain must call `super().__init__()`.

### Shared class attributes

- A mutable [class attribute](https://docs.python.org/3/tutorial/classes.html#class-and-instance-variables) (`items = []` in the class body) is shared by every instance.
- `self.items.append(x)` mutates the shared list; `self.items = [...]` creates an instance attribute that shadows it.
- Create per-instance state in `__init__`; dataclasses force [`field(default_factory=list)`](https://docs.python.org/3/library/dataclasses.html#dataclasses.field) for this reason.

### Descriptors

- An object with `__get__`/`__set__`/`__delete__` on a class attribute is a [descriptor](https://docs.python.org/3/howto/descriptor.html); `property`, bound methods, `classmethod`, and `staticmethod` are all built on it.
- [Data descriptors](https://docs.python.org/3/howto/descriptor.html#descriptor-protocol) (define `__set__` or `__delete__`) beat the instance `__dict__`; non-data descriptors (only `__get__`, e.g. functions) lose to it.

### Class creation hooks

- [`__new__`](https://docs.python.org/3/reference/datamodel.html#object.__new__) creates the instance, `__init__` only initializes it — override `__new__` for immutable subclasses or instance caching.
- [Metaclasses](https://docs.python.org/3/reference/datamodel.html#metaclasses) customize class creation; [`__init_subclass__`](https://docs.python.org/3/reference/datamodel.html#object.__init_subclass__) covers most "react when a subclass is defined" needs without one.

### Equality and hashing

- Defining [`__eq__` without `__hash__`](https://docs.python.org/3/reference/datamodel.html#object.__hash__) sets `__hash__ = None`, making instances unhashable.
- [`@dataclass(frozen=True)`](https://docs.python.org/3/library/dataclasses.html#frozen-instances) blocks field reassignment (shallow — a list field stays mutable) and generates `__hash__`, which raises `TypeError` on an unhashable field; [`slots=True`](https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass) (3.10) adds `__slots__`.

## Functions and iteration

### Generators

- [Generators](https://docs.python.org/3/glossary.html#term-generator) are lazy and exhausted after one pass; [`yield from`](https://docs.python.org/3/reference/expressions.html#yield-expressions) delegates to a sub-generator.
- [`gen.send(v)`](https://docs.python.org/3/reference/expressions.html#generator.send) resumes a generator and makes `v` the value of the paused `yield` expression.

### Decorators

- Wrap with [`functools.wraps(func)`](https://docs.python.org/3/library/functools.html#functools.wraps) or the wrapper loses `__name__`, `__doc__`, and signature.
- A [decorator](https://docs.python.org/3/glossary.html#term-decorator) with arguments needs an extra layer: `@deco(arg)` calls `deco(arg)`, which must return the real decorator.

### functools.cache pitfalls

- [`@cache`](https://docs.python.org/3/library/functools.html#functools.cache) (3.9) is `lru_cache(maxsize=None)` — unbounded, so it grows forever on unbounded inputs; switch to [`lru_cache(maxsize=N)`](https://docs.python.org/3/library/functools.html#functools.lru_cache) to bound it.
- On a method it keys on `self` and [keeps every instance alive](https://docs.python.org/3/faq/programming.html#how-do-i-cache-method-calls); use [`cached_property`](https://docs.python.org/3/library/functools.html#functools.cached_property) or a per-instance cache.
- Arguments must be hashable, and a returned mutable object is shared by every caller.

### Context managers and exceptions

- [`__exit__`](https://docs.python.org/3/reference/datamodel.html#object.__exit__) returning `True` suppresses the exception; [`contextlib.contextmanager`](https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager) turns a one-`yield` generator into a context manager.
- [`try ... else`](https://docs.python.org/3/reference/compound_stmts.html#the-try-statement) runs only when no exception was raised; [`except*`](https://docs.python.org/3/reference/compound_stmts.html#except-star) (3.11) handles [exception groups](https://docs.python.org/3/library/exceptions.html#exception-groups), e.g. from a `TaskGroup`.

## Typing and recent features

### Gradual typing and protocols

- [Type hints](https://docs.python.org/3/library/typing.html) are not enforced at runtime — they're for [`mypy`](https://mypy.readthedocs.io/)/[`pyright`](https://github.com/microsoft/pyright).
- [`typing.Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol) gives structural typing: a class matches by having the methods, unlike [ABCs](https://docs.python.org/3/library/abc.html), which need subclassing or registration.
- [`TypedDict`](https://docs.python.org/3/library/typing.html#typing.TypedDict) types a dict's known keys without making it a class.

### Generics and annotation evaluation

- [PEP 695](https://peps.python.org/pep-0695/) syntax (`class Box[T]: ...`, `type Alias = ...`, 3.12) replaces manual [`TypeVar`](https://docs.python.org/3/library/typing.html#typing.TypeVar) declarations with scoped type parameters.
- Annotations are [evaluated lazily since 3.14](https://docs.python.org/3/whatsnew/3.14.html#pep-649-pep-749-deferred-evaluation-of-annotations) ([PEP 649](https://peps.python.org/pep-0649/)), making `from __future__ import annotations` largely unnecessary.

### Structural pattern matching

- [`match`](https://docs.python.org/3/reference/compound_stmts.html#the-match-statement) (3.10) destructures by shape: `case {"type": "click", "x": x}`, `case Point(x=0)`.
- A bare name in a `case` [binds, it doesn't compare](https://docs.python.org/3/reference/compound_stmts.html#capture-patterns) — `case RED:` matches everything; use [dotted names](https://docs.python.org/3/reference/compound_stmts.html#value-patterns) (`Color.RED`) for constants.

### Template strings

- [t-strings](https://docs.python.org/3/library/string.templatelib.html) (`t"Hello {name}"`, 3.14, [PEP 750](https://peps.python.org/pep-0750/)) produce a `Template` object with static parts and interpolated values kept separate.
- A library receiving it can escape values safely (SQL, HTML), unlike an [f-string](https://docs.python.org/3/reference/lexical_analysis.html#f-strings) that arrives already joined.

## Tooling

### Packaging and tests

- [`pyproject.toml`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) is the standard manifest; [`uv`](https://docs.astral.sh/uv/) resolves, installs, and manages Python versions far faster than pip, with a lock file.
- [`pytest` fixture scope](https://docs.pytest.org/en/stable/how-to/fixtures.html#scope-sharing-fixtures-across-classes-modules-packages-or-session) (`function`, `class`, `module`, `session`) sets how often it's rebuilt — a `session` fixture holding mutable state leaks between tests.

### Profiling

- [`cProfile`](https://docs.python.org/3/library/profile.html) gives function-level call counts and cumulative time; [`py-spy`](https://github.com/benfred/py-spy) samples a running process without code changes, safe in production.
- [`tracemalloc`](https://docs.python.org/3/library/tracemalloc.html) snapshots allocations by line to find memory growth.
