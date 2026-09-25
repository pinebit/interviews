# JavaScript

What experienced JavaScript engineers forget before an interview, grouped by subtopic.

## Event loop

### Microtasks vs macrotasks

- The **microtask queue** (promise reactions, `queueMicrotask`, `MutationObserver`) drains **completely** whenever the call stack empties.
- The task (macrotask) queue (`setTimeout`, I/O, UI events) runs **one task per loop iteration**, then microtasks drain again.
- So `Promise.resolve().then(f)` always beats `setTimeout(f, 0)`; a microtask that keeps queuing microtasks starves rendering and tasks.

### Rendering in the loop

- **`requestAnimationFrame`** callbacks, style, layout, and paint run between tasks, at most once per frame (~16.7 ms at 60 Hz), after microtasks drain.
- A long task or microtask chain delays the next frame — this is what INP measures (see [frontend.md](frontend.md)).

## Scope and closures

### Hoisting and the TDZ

- `var` is hoisted and reads as `undefined` before its line; a `function` declaration is callable before its line.
- `let`/`const`/`class` are hoisted but sit in the **temporal dead zone** — access before the declaration throws `ReferenceError`.

### Closures in loops

- `for (var i = 0; i < 3; i++) setTimeout(() => console.log(i))` logs `3,3,3` — one function-scoped `i`.
- `let` creates a **fresh binding per iteration**, printing `0,1,2`.

## `this` and prototypes

### `this` binding rules

- Precedence: **`new`** > explicit `call`/`apply`/`bind` > implicit (`obj.method()`) > default (`undefined` in strict mode, global otherwise).
- **Arrow functions** have no own `this`; they capture it lexically.
- Passing `obj.method` as a bare callback (`setTimeout(obj.method)`) loses `this`.

### Prototypes and classes

- Property lookup walks the **`[[Prototype]]` chain** until found or `null`; `class` methods live on `C.prototype`.
- Unlike constructor functions, classes run in strict mode, have a **TDZ**, and throw if called without `new`.
- **`#private` fields** are engine-enforced: `obj.#x` outside the class is a syntax error.

## Coercion and equality

### `==`, `===`, `Object.is`

- `==` coerces: `'' == 0` and `null == undefined` are `true`, but `null == 0` is `false`; `===` never coerces.
- `NaN !== NaN`; **`Object.is`** treats `NaN` as equal to itself and distinguishes `+0` from `-0`.

### Type-check quirks

- `typeof null === 'object'` — a historical bug kept for compatibility.
- Default `Array.prototype.sort()` compares **as strings**: `[10, 2, 1].sort()` → `[1, 10, 2]`; pass `(a, b) => a - b`.

## Numbers

### IEEE 754 doubles

- Every `number` is a 64-bit double: `0.1 + 0.2 !== 0.3`; compare with a tolerance or use integers (cents).
- Integers are exact only up to **`Number.MAX_SAFE_INTEGER` = 2⁵³ − 1**; IDs beyond that (Snowflake, tweet IDs) must travel as strings or `BigInt`.
- Bitwise operators convert to **32-bit** signed integers.
- `Math.sumPrecise(iterable)` (ES2026) adds floats without accumulating rounding error, unlike a naive `reduce`.

### Typed arrays

- **Typed arrays** are fixed-type views over an `ArrayBuffer` — unboxed numeric storage; several views can share one buffer.
- `SharedArrayBuffer` + `Atomics` share memory between workers.

## Async

### Promise combinators

| Combinator | Settles when | Use when |
|---|---|---|
| `Promise.all` | any rejects, or all fulfill | need every result, fail fast |
| `Promise.allSettled` | always, tagged fulfilled/rejected | need every outcome |
| `Promise.race` | first settles (either way) | timeouts, first response wins |
| `Promise.any` | first fulfills, or all reject (`AggregateError`) | first success wins |

### Sequential vs parallel await

- `await` inside a loop runs **serially**; start the operations first, then `await Promise.all([...])` so their times overlap.
- An unhandled rejection doesn't throw synchronously; Node **crashes the process on it by default since Node 15**.

### Cancellation and async iteration

- **`AbortController`** cancels `fetch` and other abortable APIs via a shared `AbortSignal`; `AbortSignal.timeout(ms)` builds a deadline.
- **`for await...of`** consumes async generators and any object with `Symbol.asyncIterator`.

### Promise helpers

- **`Promise.withResolvers()`** (ES2024) returns `{ promise, resolve, reject }`.
- **`Promise.try()`** (ES2025) runs a function and turns both its result and a synchronous throw into a promise.

## Modules

### CommonJS vs ESM

- CommonJS `require` loads **synchronously** at runtime and can be called conditionally; a destructured import is a snapshot, not a live binding.
- ESM is statically analyzed — enabling tree shaking and **live bindings** — loads asynchronously, and allows **top-level `await`**.

### Node interop and the dual-package hazard

- **`require(esm)`** works for synchronous ES modules (no top-level `await`) without a flag **since Node 22.12 / 20.19**.
- **Dual-package hazard**: a package shipping CJS and ESM builds can load twice under different identities, breaking `instanceof` and singletons.

## Memory

### Garbage collection and leaks

- V8's collector is **generational**: a fast scavenger for the young generation (most objects die young), mark-compact for the old generation.
- Common leaks: **detached DOM nodes** still referenced from JS, forgotten listeners and timers, unbounded caches.
- A closure keeps its referenced outer variables alive, so a long-lived listener can retain a large object it barely uses.

### Weak references

- **`WeakMap`/`WeakSet`** keys don't keep objects alive — good for per-object metadata and caches.
- **`WeakRef`** weakly holds one object; **`FinalizationRegistry`** callbacks may run late or never — cleanup hints only, never correctness.

### Deep cloning

- **`structuredClone`** handles cycles, `Map`, `Set`, `Date`, and typed arrays, but not functions or DOM nodes.
- `JSON.parse(JSON.stringify(x))` drops `undefined`/functions/symbols, turns `Date` into a string, throws on `BigInt` and cycles.

## Metaprogramming and iteration

### Proxy and Reflect

- A **`Proxy`** intercepts operations (get, set, has, delete, apply) on a target — the basis of Vue's reactivity and MobX.
- **`Reflect`** exposes the default behavior of each trap, so handlers can forward with `Reflect.get(target, key, receiver)`.

### Iterators and generators

- An object is iterable if it has **`[Symbol.iterator]()`** returning `{ next() → { value, done } }`; `for...of`, spread, and destructuring use it.
- Generators (`function*`) are lazy, pause at `yield`, and can receive values via `next(v)`; async generators power `for await`.

## Node.js runtime

### Node event loop phases

- Phases: **timers → pending callbacks → poll (I/O) → check (`setImmediate`) → close**.
- After each callback, the `process.nextTick` queue drains first, then promise microtasks.
- `setTimeout(f, 0)` vs `setImmediate(f)` order is **nondeterministic** in the main module; inside an I/O callback `setImmediate` always runs first.

### libuv thread pool

- Network sockets use epoll/kqueue, but **`fs`**, `dns.lookup`, async `crypto` (`pbkdf2`, `scrypt`), and `zlib` run on the libuv **thread pool**.
- The pool has **4 threads** by default (`UV_THREADPOOL_SIZE`), so a few slow DNS lookups or hashes can stall all file I/O.

### Stream backpressure

- **`write()` returns `false`** once the buffer passes `highWaterMark`; stop writing until the `'drain'` event.
- **`stream.pipeline()`** handles backpressure, errors, and cleanup of every stream in the chain — `.pipe()` doesn't forward errors.

### Workers, cluster, child processes

- **`worker_threads`**: threads in one process with separate V8 isolates, for CPU-bound JS; share memory through `SharedArrayBuffer`.
- **`cluster`**: forks processes sharing one server port to use all cores — in containers, usually replaced by more replicas.
- `child_process`: runs other programs (`spawn` streams output, `exec` buffers it).

### AsyncLocalStorage

- **`AsyncLocalStorage`** carries request-scoped context (request ID, trace, user) through every async call without passing it as an argument.
- The basis of Node APM tracing and per-request logging.

## DOM events

### Propagation and delegation

- Phases: **capture** (root → target) → target → **bubble** (target → root); `{capture: true}` listens during capture.
- **Event delegation**: one listener on an ancestor plus `event.target` covers many children, including ones added later.

### Listener performance

- **`passive: true`** promises not to call `preventDefault()`, so scrolling starts without waiting for the handler.
- **Debounce** fires once after a pause (search-as-you-type); **throttle** fires at most once per interval (scroll, resize).

## Recent language additions

### Array and object helpers

- **`toSorted`, `toReversed`, `toSpliced`, `with`** (ES2023) return a new array instead of mutating.
- **`Object.groupBy`/`Map.groupBy`** (ES2024) group an iterable by a callback's key.

### Temporal

- **`Temporal`** (Stage 4 in March 2026, **ES2026**) replaces `Date`: immutable values, explicit time zones (`ZonedDateTime`), calendar-safe arithmetic, separate types for dates, times, and instants.
- Shipped in Firefox 139 and Chrome 144; Safari has it only in Technology Preview, so it isn't Baseline yet.

### Explicit resource management

- **`using`** / `await using` (ES2026; TypeScript since 5.2) call **`[Symbol.dispose]()`** / `[Symbol.asyncDispose]()` when the block exits, even on throw — no `try/finally`.
- **`DisposableStack`** collects several resources and disposes them in reverse order.

### Sets and iterators

- **Set methods** (`union`, `intersection`, `difference`, `isSubsetOf`, …) arrived in **ES2025**.
- **Iterator helpers** (`.map`, `.filter`, `.take`, `.drop` on iterators, ES2025) are lazy, unlike the array methods.
