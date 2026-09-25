# JavaScript

What experienced JavaScript engineers forget before an interview, grouped by subtopic.

## Event loop

### Microtasks vs macrotasks

- The **microtask queue** (promise reactions, `queueMicrotask`, `MutationObserver`) drains **completely** whenever the call stack empties.
- The **task (macrotask) queue** (`setTimeout`, I/O, UI events) runs **one task per loop iteration**, then microtasks drain again.
- So `Promise.resolve().then(f)` always beats `setTimeout(f, 0)`; a microtask that keeps queuing microtasks starves rendering and tasks.

### Rendering in the loop

- **`requestAnimationFrame`** callbacks, style, layout, and paint run between tasks, at most once per frame (~16.7 ms at 60 Hz), after microtasks drain.
- A long task or microtask chain delays the next frame — this is what INP measures (see [frontend.md](frontend.md)).

### Node event loop phases

- Phases: **timers → pending callbacks → poll (I/O) → check (`setImmediate`) → close**.
- After each callback, the **`process.nextTick` queue** drains first, then promise microtasks.
- `setTimeout(f, 0)` vs `setImmediate(f)` order is **nondeterministic** in the main module; inside an I/O callback `setImmediate` always runs first.

## Scope and closures

### Hoisting and the TDZ

- `var` is hoisted and reads as `undefined` before its line; a `function` declaration is callable before its line.
- `let`/`const`/`class` are hoisted but sit in the **temporal dead zone** — access before the declaration throws `ReferenceError`.

### Closures in loops

- `for (var i = 0; i < 3; i++) setTimeout(() => console.log(i))` logs `3,3,3` — one function-scoped `i`.
- `let` creates a **fresh binding per iteration**, printing `0,1,2`.

### Closure memory leaks

- A closure keeps its referenced outer variables alive; a long-lived listener or timer can retain a large object it barely uses.

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

- **CommonJS** `require` loads **synchronously** at runtime and can be called conditionally; a destructured import is a snapshot, not a live binding.
- **ESM** is statically analyzed — enabling tree shaking and **live bindings** — loads asynchronously, and allows **top-level `await`**.

### Node interop and the dual-package hazard

- **`require(esm)`** works for synchronous ES modules (no top-level `await`) without a flag **since Node 22.12 / 20.19**.
- **Dual-package hazard**: a package shipping CJS and ESM builds can load twice under different identities, breaking `instanceof` and singletons.

## Memory and data

### V8 garbage collection

- V8's collector is **generational**: a fast scavenger for the young generation (most objects die young), and mark-compact for objects promoted to the old generation.

### Common leaks

- Detached DOM nodes still referenced from JS, forgotten listeners and timers, and closures capturing more than they use.

### Weak references

- **`WeakMap`/`WeakSet`** keys don't keep objects alive — good for per-object metadata and caches.
- **`WeakRef`** weakly holds one object; **`FinalizationRegistry`** callbacks may run late or never — cleanup hints only, never correctness.

### Deep cloning

- **`structuredClone`** handles cycles, `Map`, `Set`, `Date`, and typed arrays, but not functions or DOM nodes.
- `JSON.parse(JSON.stringify(x))` drops `undefined`/functions/symbols, turns `Date` into a string, throws on `BigInt` and cycles.

### Typed arrays

- **Typed arrays** are fixed-type views over an `ArrayBuffer` — unboxed numeric storage; several views can share one buffer.

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

### Sets and iterators

- **Set methods** (`union`, `intersection`, `difference`, `isSubsetOf`, …) and **iterator helpers** (`.map`, `.filter`, `.take`, `.drop` on iterators) arrived in **ES2025**.
