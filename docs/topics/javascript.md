# JavaScript

What experienced JavaScript engineers forget before an interview, grouped by subtopic.

## Event loop

### Microtasks vs macrotasks

- One call stack; the event loop pulls queued callbacks on once the stack is empty. The **microtask queue** (Promise callbacks, `queueMicrotask`, `MutationObserver`) drains **completely** after each stack-emptying step, before the loop continues. The **macrotask queue** (`setTimeout`, I/O, UI events) runs **one task per iteration**, with microtasks drained again right after.
- This is why `Promise.resolve().then(cb)` always fires before `setTimeout(cb, 0)`, regardless of source order — a microtask that keeps scheduling more microtasks can starve rendering and macrotasks indefinitely.
- **Rendering** and `requestAnimationFrame` callbacks run after microtasks drain but before the next macrotask/paint — heavy microtask chains can delay a frame even though they "ran first."
- Node loop phases: **timers → pending callbacks → poll (I/O) → check (`setImmediate`) → close**. After each callback, the **`process.nextTick` queue** drains first, then promise microtasks.
- `setTimeout(f, 0)` vs `setImmediate(f)` order is **nondeterministic** in the main module, but inside an I/O callback `setImmediate` always runs first (check comes right after poll).

## Scope and closures

### Hoisting, TDZ, and closures

- `var`/`function` declarations are hoisted with their binding created upfront (a `var` reads as `undefined` before its line runs; a `function` declaration is fully callable before its line). `let`/`const` are hoisted too but sit in the **temporal dead zone** — `ReferenceError` on access from scope start until the declaration line executes.
- Classic loop bug: `for (var i = 0; i < 3; i++) setTimeout(() => console.log(i))` logs `3,3,3` — all closures share the one function-scoped `i`. `let` creates a fresh binding per iteration, fixing it without extra code.
- A closure keeps its entire enclosing scope's referenced variables alive — a common **memory leak** is a long-lived closure (event listener, timer) retaining a large object it barely uses.

## `this` and prototypes

### Binding rules

- `this` is determined by **how** a function is called, resolved in this precedence order: **`new`** (newly created object) > explicit **`call`/`apply`/`bind`** > implicit (`obj.method()` → `obj`) > default (`undefined` in strict mode, global object otherwise).
- **Arrow functions** have no own `this` — captured lexically at definition time, which is exactly why they're preferred for callbacks needing the outer `this`. Passing a method as a bare reference (`setTimeout(obj.method)`) loses its `this` binding — the call site is no longer `obj.method()`.
- **Prototype chain**: every object has an internal `[[Prototype]]` link; lookup walks it until found or `null`. `class` is sugar over this — methods land on `ClassName.prototype`, `extends` wires the chain — with real differences from old-style constructor functions: class bodies run in strict mode, class declarations have a **TDZ** (unlike function declarations), and a class is not callable without `new`.
- **Private `#fields`** are enforced by the engine, not just convention — accessing `obj.#field` from outside the class is a syntax error, not just `undefined`.

## Coercion and equality

### Equality algorithm and special values

- `==` coerces operands to a common type before comparing (`'' == 0` → `true`, `null == undefined` → `true`, but `null == 0` → `false`); `===` never coerces. Prefer `===`.
- `NaN !== NaN`; use `Number.isNaN` or `Object.is`. `Object.is(a, b)` behaves like `===` except it treats `NaN` as equal to itself and distinguishes `+0` from `-0` (`Object.is(0, -0)` is `false`, `0 === -0` is `true`).
- `typeof null === 'object'` — a long-standing quirk kept for backward compatibility, not a meaningful type check.
- Default `Array.sort()` is **lexicographic** (converts elements to strings) — sorting numbers requires an explicit comparator (`(a, b) => a - b`), or `[10, 2, 1].sort()` gives `[1, 10, 2]`.

## Async

### Promise combinators

| Combinator | Settles when | Use when |
|---|---|---|
| `Promise.all` | any rejects, or all fulfill | need every result, fail fast on error |
| `Promise.allSettled` | always, tagged fulfilled/rejected | need every outcome regardless of failure |
| `Promise.race` | first settles (either way) | first result or failure wins |
| `Promise.any` | first fulfillment, or all reject (`AggregateError`) | first success, ignore individual failures |

- **Unhandled rejections** surface as a process/window-level event; a rejected promise with no `.catch`/`try-catch` doesn't crash synchronously but is a real bug source in long-running processes.
- Sequential `await` in a loop runs **serially** — start independent operations first, then `await Promise.all([...])`, or their times needlessly sum instead of overlapping.
- **`AbortController`** cancels a fetch or other abortable operation via a shared `AbortSignal`; **async iterators** (`for await...of`) consume async generators or any object with `Symbol.asyncIterator`.
- **`Promise.withResolvers()`** (ES2024) returns `{ promise, resolve, reject }` without the old `let resolve; new Promise(r => resolve = r)` workaround; **`Promise.try()`** (ES2025) runs a function and normalizes both its return value and any synchronous throw into a promise.

## Modules

### CJS vs ESM

- **CommonJS** (`require`/`module.exports`) resolves and executes **synchronously** at runtime, supports requiring conditionally anywhere in code. **ESM** (`import`/`export`) is statically analyzed at parse time — enabling tree-shaking and **live bindings** (an imported name reflects the exporter's current value, not a copied snapshot) — and loads asynchronously, with **top-level `await`** supported directly in a module.
- **`require(esm)`**: Node can `require()` a synchronous ES module (no top-level await) directly **since Node 22+**, easing the two systems' interop.
- **Dual-package hazard**: a package shipping both a CJS and an ESM build can end up loaded twice under different identities (two separate module instances, breaking `instanceof` checks and shared singletons) if consumers mix `require` and `import` on it.

## Memory and data

### GC and leaks

- V8 uses a **generational** collector: young objects are collected frequently and cheaply (most die young — "the generational hypothesis"), promoted to an older generation if they survive, which is collected less often.
- Common leaks: detached DOM nodes still referenced from JS after removal, forgotten event listeners/timers holding closures alive, and closures capturing more than they need.
- **`WeakMap`/`WeakSet`** hold keys/values weakly, so entries are collectible once nothing else references them — good for caches/metadata keyed by objects without preventing their collection. **`WeakRef`** holds a weak reference to a single object; **`FinalizationRegistry`** runs a callback after an object is collected (not guaranteed to run promptly, or at all — never rely on it for correctness, only cleanup hints).
- **`structuredClone(obj)`** deep-clones including cycles and many built-in types (`Map`, `Set`, `Date`, typed arrays); `JSON.parse(JSON.stringify(obj))` drops functions/`undefined`/`Symbol`, turns `Date` into a string, throws on `BigInt`, and can't handle cycles at all.
- **Typed arrays** (`Uint8Array`, etc.) are fixed-type views over a raw `ArrayBuffer` — fast, homogeneous numeric storage without per-element boxing, unlike a regular `Array`. Multiple views can share one buffer, reading/writing the same memory with different type interpretations.

## DOM events

### Propagation and performance

- Three phases: **capturing** (root → target) → **target** → **bubbling** (target → root); `addEventListener`'s `{capture: true}` picks the phase, default is bubbling.
- **Event delegation**: one listener on a common ancestor plus `event.target` identifies the actual child — cheaper than per-child listeners and automatically covers dynamically added children.
- **`passive: true`** listeners promise not to call `preventDefault()`, letting the browser start scrolling immediately instead of waiting to see if the handler cancels it — meaningful for scroll/touch performance.
- **Debounce** (wait for a pause, fire once after) vs **throttle** (fire at most once per interval, regardless of call frequency) — debounce for search-as-you-type, throttle for scroll/resize handlers.

## Recent language additions

### Recent built-ins

- Non-mutating array methods **`toSorted`, `toReversed`, `toSpliced`, `with`** (ES2023) return a new array instead of mutating in place, mirroring the mutating originals (`sort`, `reverse`, `splice`) without the shared-reference footguns.
- **`Object.groupBy`** (ES2024) groups an iterable's items into a plain object keyed by a callback's return value, replacing a common manual `reduce` pattern.
- **Set methods** (`union`, `intersection`, `difference`, `symmetricDifference`, `isSubsetOf`, `isSupersetOf`, `isDisjointFrom`) and **iterator helpers** (`.map`, `.filter`, `.take`, `.drop` directly on iterators) shipped as part of the **ES2025** set of additions, closing long-standing gaps versus array methods.
