# JavaScript

What experienced JavaScript engineers forget before an interview, grouped by subtopic.

## Event loop

### Microtasks vs macrotasks

- The [microtask queue](https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide) (promise reactions, [`queueMicrotask`](https://developer.mozilla.org/en-US/docs/Web/API/Window/queueMicrotask), [`MutationObserver`](https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver)) drains completely whenever the call stack empties.
- The [task (macrotask) queue](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops) ([`setTimeout`](https://developer.mozilla.org/en-US/docs/Web/API/Window/setTimeout), I/O, UI events) runs one task per loop iteration, then microtasks drain again.
- So `Promise.resolve().then(f)` always beats `setTimeout(f, 0)`; a microtask that keeps queuing microtasks starves rendering and tasks.

### Rendering in the loop

- [`requestAnimationFrame`](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame) callbacks, style, layout, and paint run between tasks, at most once per frame (~16.7 ms at 60 Hz), after microtasks drain.
- A [long task](https://developer.mozilla.org/en-US/docs/Glossary/Long_task) or microtask chain delays the next frame — this is what [INP](https://web.dev/articles/inp) measures (see [frontend.md](frontend.md)).

## Scope and closures

### Hoisting and the TDZ

- `var` is [hoisted](https://developer.mozilla.org/en-US/docs/Glossary/Hoisting) and reads as `undefined` before its line; a `function` declaration is callable before its line.
- `let`/`const`/`class` are hoisted but sit in the [temporal dead zone](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let#temporal_dead_zone_tdz) — access before the declaration throws `ReferenceError`.

### Closures in loops

- `for (var i = 0; i < 3; i++) setTimeout(() => console.log(i))` logs `3,3,3` — one function-scoped `i` shared by every [closure](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures#creating_closures_in_loops_a_common_mistake).
- `let` creates a [fresh binding per iteration](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/for#lexical_declarations_in_the_initialization_block), printing `0,1,2`.

## `this` and prototypes

### `this` binding rules

- Precedence: `new` > explicit [`call`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/call)/[`apply`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/apply)/[`bind`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/bind) > implicit (`obj.method()`) > default (`undefined` in [strict mode](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode), global otherwise).
- [Arrow functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions) have no own [`this`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this); they capture it lexically.
- Passing `obj.method` as a bare callback (`setTimeout(obj.method)`) loses `this`.

### Prototypes and classes

- Property lookup walks the [`[[Prototype]]` chain](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Inheritance_and_the_prototype_chain) until found or `null`; `class` methods live on `C.prototype`.
- Unlike constructor functions, [classes](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes) run in strict mode, have a TDZ, and throw if called without `new`.
- [`#private` fields](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes/Private_elements) are engine-enforced: `obj.#x` outside the class is a syntax error.

## Coercion and equality

### `==`, `===`, `Object.is`

- [`==` coerces](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Equality_comparisons_and_sameness#loose_equality_using): `'' == 0` and `null == undefined` are `true`, but `null == 0` is `false`; `===` never coerces.
- `NaN !== NaN`; [`Object.is`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/is) treats `NaN` as equal to itself and distinguishes `+0` from `-0`.

### Type-check quirks

- [`typeof null === 'object'`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/typeof#typeof_null) — a historical bug kept for compatibility.
- Default [`Array.prototype.sort()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort) compares as strings: `[10, 2, 1].sort()` → `[1, 10, 2]`; pass `(a, b) => a - b`.

## Numbers

### IEEE 754 doubles

- Every `number` is a [64-bit double](https://en.wikipedia.org/wiki/Double-precision_floating-point_format): `0.1 + 0.2 !== 0.3`; compare with a tolerance or use integers (cents).
- Integers are exact only up to [`Number.MAX_SAFE_INTEGER`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER) = 2⁵³ − 1; IDs beyond that ([Snowflake](https://en.wikipedia.org/wiki/Snowflake_ID), tweet IDs) must travel as strings or [`BigInt`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/BigInt).
- Bitwise operators on numbers [truncate to 32-bit](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number#fixed-width_number_conversion) signed integers (`>>>` returns unsigned); on `BigInt` they are arbitrary-precision.
- [`Math.sumPrecise(iterable)`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/sumPrecise) (ES2026) adds floats without accumulating rounding error, unlike a naive `reduce`.

### Typed arrays

- [Typed arrays](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Typed_arrays) are fixed-type views over an [`ArrayBuffer`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/ArrayBuffer) — unboxed numeric storage; several views can share one buffer.
- [`SharedArrayBuffer`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer) + [`Atomics`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Atomics) share memory between workers.

## Async

### Promise combinators

| Combinator | Settles when | Use when |
|---|---|---|
| [`Promise.all`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/all) | any rejects, or all fulfill | need every result, fail fast |
| [`Promise.allSettled`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled) | all settle (input rejections don't reject it), tagged fulfilled/rejected | need every outcome |
| [`Promise.race`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/race) | first settles (either way) | timeouts, first response wins |
| [`Promise.any`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/any) | first fulfills, or all reject ([`AggregateError`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/AggregateError)) | first success wins |

### async/await ordering

- The [`new Promise` executor](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/Promise) runs synchronously; only the `.then` callbacks are deferred.
- Code after [`await`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/await) always resumes as a microtask, even when the awaited value is already resolved or isn't a promise.
- Inside `try`, `return promise` skips the `catch` when it rejects; write `return await promise`.
- An [`async` function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function) always returns a new promise, so a `throw` inside it becomes a rejection, not a synchronous exception.

### Sequential vs parallel await

- `for (const x of xs) await f(x)` runs serially: each call starts after the previous settles; start all calls first, then `await Promise.all([...])` so they overlap.
- An unhandled rejection doesn't throw synchronously; Node [crashes the process on it by default](https://nodejs.org/api/cli.html#--unhandled-rejectionsmode) since Node 15.

### Cancellation and async iteration

- [`AbortController`](https://developer.mozilla.org/en-US/docs/Web/API/AbortController) cancels `fetch` and other abortable APIs via a shared [`AbortSignal`](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal); [`AbortSignal.timeout(ms)`](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static) builds a deadline.
- [`for await...of`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/for-await...of) consumes async generators and any object with [`Symbol.asyncIterator`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/asyncIterator).

### fetch semantics

- [`fetch`](https://developer.mozilla.org/en-US/docs/Web/API/Window/fetch) rejects only when the request can't be made (network error, CORS, invalid URL or options, abort); HTTP 4xx/5xx resolve with [`res.ok`](https://developer.mozilla.org/en-US/docs/Web/API/Response/ok) `=== false`, so check it.
- The body is a stream and can be read once; call [`res.clone()`](https://developer.mozilla.org/en-US/docs/Web/API/Response/clone) before reading it twice.
- There is no default timeout: pass `signal: AbortSignal.timeout(ms)`.
- Cookies go only to the same origin by default ([`credentials: 'same-origin'`](https://developer.mozilla.org/en-US/docs/Web/API/RequestInit#credentials)); cross-origin requests need `'include'` plus [CORS credential headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS#requests_with_credentials).

## Modules

### CommonJS vs ESM

- [CommonJS](https://nodejs.org/api/modules.html) `require` loads synchronously at runtime and can be called conditionally; a destructured import is a snapshot, not a live binding.
- [ESM](https://nodejs.org/api/esm.html) is statically analyzed — enabling [tree shaking](https://developer.mozilla.org/en-US/docs/Glossary/Tree_shaking) and [live bindings](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/import#imported_values_can_only_be_modified_by_the_exporter) — loads asynchronously, and allows [top-level `await`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/await#top_level_await).

### Node interop and the dual-package hazard

- [`require(esm)`](https://nodejs.org/api/modules.html#loading-ecmascript-modules-using-require) works for synchronous ES modules (no top-level `await`) without a flag since Node 22.12 / 20.19.
- [Dual-package hazard](https://nodejs.org/api/packages.html#dual-commonjses-module-packages): a package shipping CJS and ESM builds can load twice under different identities, breaking `instanceof` and singletons.

## Memory

### Garbage collection and leaks

- V8's collector is [generational](https://v8.dev/blog/trash-talk): a fast scavenger for the young generation (most objects die young), mark-compact for the old generation.
- Common leaks: [detached DOM nodes](https://developer.chrome.com/docs/devtools/memory-problems#discover_detached_dom_tree_memory_leaks_with_heap_snapshots) still referenced from JS, forgotten listeners and timers, unbounded caches.
- A [closure](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures) keeps its referenced outer variables alive, so a long-lived listener can retain a large object it barely uses.

### Hidden classes and inline caches

- V8 gives objects created with the same properties in the same order a shared [hidden class](https://v8.dev/docs/hidden-classes) (shape); adding a property transitions to a new one.
- Each property-access site [caches the shapes](https://mathiasbynens.be/notes/shapes-ics) it has seen: monomorphic (one) is fastest, polymorphic up to 4, then megamorphic (a generic slow lookup).
- Initialize every field in the constructor in a fixed order; `delete` on a hot object can drop it into slow [dictionary mode](https://v8.dev/blog/fast-properties).
- Arrays track [element kinds](https://v8.dev/blog/elements-kinds) too: mixing integers, doubles, and holes (`new Array(n)`) downgrades them for good — except that `Array.prototype.fill` can repack a holey array (since February 2025).

### Weak references

- [`WeakMap`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/WeakMap)/[`WeakSet`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/WeakSet) keys don't keep objects alive — good for per-object metadata and caches.
- [`WeakRef`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/WeakRef) weakly holds one object; [`FinalizationRegistry`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/FinalizationRegistry) callbacks may run late or never — cleanup hints only, never correctness.

### Deep cloning

- [`structuredClone`](https://developer.mozilla.org/en-US/docs/Web/API/Window/structuredClone) handles cycles, `Map`, `Set`, `Date`, and typed arrays, but not functions or DOM nodes.
- `JSON.parse(JSON.stringify(x))` ([`JSON.stringify`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/stringify)) drops `undefined`/functions/symbols, turns `Date` into a string, throws on `BigInt` and cycles.

## Metaprogramming and iteration

### Proxy and Reflect

- A [`Proxy`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Proxy) intercepts operations (get, set, has, delete, apply) on a target — the basis of [Vue's reactivity](https://vuejs.org/guide/extras/reactivity-in-depth.html) and MobX.
- [`Reflect`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Reflect) exposes the default behavior of each trap, so handlers can forward with `Reflect.get(target, key, receiver)`.

### Iterators and generators

- An object is [iterable](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Iteration_protocols) if it has `[Symbol.iterator]()` returning `{ next() → { value, done } }`; `for...of`, spread, and destructuring use it.
- [Generators](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/function*) (`function*`) are lazy, pause at `yield`, and can receive values via `next(v)`; async generators power `for await`.
- [Iterator helpers](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Iterator#iterator_helper_objects) (`.map`, `.filter`, `.take`, `.drop` on iterators, ES2025) are lazy, unlike the array methods.

## Node.js runtime

### Node event loop phases

- [Phases](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick#phases-overview): timers → pending callbacks → poll (I/O) → check (`setImmediate`) → close.
- Since Node 20 ([libuv 1.45](https://github.com/libuv/libuv/releases/tag/v1.45.0)), timers run after poll in each iteration instead of before it (plus once when the loop starts); this can shift timer vs `setImmediate` ordering.
- After each callback, the [`process.nextTick`](https://nodejs.org/api/process.html#processnexttickcallback-args) queue drains first, then promise microtasks.
- `setTimeout(f, 0)` vs [`setImmediate(f)`](https://nodejs.org/api/timers.html#setimmediatecallback-args) order is [nondeterministic](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick#setimmediate-vs-settimeout) in the main module; inside an I/O callback `setImmediate` always runs first.

### libuv thread pool

- Network sockets use [epoll](https://en.wikipedia.org/wiki/Epoll)/[kqueue](https://en.wikipedia.org/wiki/Kqueue), but `fs`, [`dns.lookup`](https://nodejs.org/api/dns.html#dnslookuphostname-options-callback), async `crypto` (`pbkdf2`, `scrypt`), and `zlib` run on the libuv [thread pool](https://docs.libuv.org/en/v1.x/threadpool.html).
- The pool has 4 threads by default ([`UV_THREADPOOL_SIZE`](https://nodejs.org/api/cli.html#uv_threadpool_sizesize)), so a few slow DNS lookups or hashes can stall all file I/O.

### Stream backpressure

- [`write()` returns `false`](https://nodejs.org/api/stream.html#writablewritechunk-encoding-callback) once the buffer passes [`highWaterMark`](https://nodejs.org/api/stream.html#buffering); stop writing until the [`'drain'`](https://nodejs.org/api/stream.html#event-drain) event.
- [`stream.pipeline()`](https://nodejs.org/api/stream.html#streampipelinesource-transforms-destination-callback) handles [backpressure](https://nodejs.org/en/learn/modules/backpressuring-in-streams), errors, and cleanup of every stream in the chain — `.pipe()` doesn't forward errors.

### Worker threads and cluster

- [`worker_threads`](https://nodejs.org/api/worker_threads.html): threads in one process with separate V8 isolates, for CPU-bound JS; share memory through `SharedArrayBuffer`.
- [`cluster`](https://nodejs.org/api/cluster.html): forks processes sharing one server port to use all cores — in containers, usually replaced by more replicas.

### AsyncLocalStorage

- [`AsyncLocalStorage`](https://nodejs.org/api/async_context.html#class-asynclocalstorage) carries request-scoped context (request ID, trace, user) through every async call without passing it as an argument.
- The basis of Node APM tracing (e.g. [OpenTelemetry](https://opentelemetry.io/docs/languages/js/)) and per-request logging.

## DOM events

### Propagation and delegation

- [Phases](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting/Event_bubbling): capture (root → target) → target → bubble (target → root); [`{capture: true}`](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener#capture) listens during capture.
- [Event delegation](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting/Event_bubbling#event_delegation): one listener on an ancestor plus [`event.target`](https://developer.mozilla.org/en-US/docs/Web/API/Event/target) covers many children, including ones added later.

### Listener performance

- [`passive: true`](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener#passive) promises not to call `preventDefault()`, so scrolling starts without waiting for the handler.
- [Debounce](https://developer.mozilla.org/en-US/docs/Glossary/Debounce) fires once after a pause (search-as-you-type); [throttle](https://developer.mozilla.org/en-US/docs/Glossary/Throttle) fires at most once per interval (scroll, resize).

## Recent language additions

### Temporal

- [`Temporal`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Temporal) ([Stage 4](https://github.com/tc39/proposals/blob/main/finished-proposals.md) in March 2026, ES2027) replaces `Date` with immutable values and separate types for instants, dates, times, and zoned date-times.
- Time zones are explicit ([`ZonedDateTime`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Temporal/ZonedDateTime)) and arithmetic is calendar-safe, unlike [`Date`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date)'s mutable, local-time-by-default API.

### Explicit resource management

- [`using`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/using) / [`await using`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/await_using) (ES2027; [TypeScript since 5.2](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-2.html#using-declarations-and-explicit-resource-management)) call [`[Symbol.dispose]()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/dispose) / [`[Symbol.asyncDispose]()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/asyncDispose) when the block exits, even on throw — no `try/finally`.
- [`DisposableStack`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/DisposableStack) collects several resources and disposes them in reverse order.
