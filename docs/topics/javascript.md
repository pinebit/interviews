# JavaScript Cheatsheet

The 20 most frequently asked JavaScript interview topics, with short answers.

## 1. How does the event loop work? What's the difference between the microtask and macrotask queue?

JavaScript is **single-threaded**: one call stack, plus a runtime-managed **event loop** that pulls queued callbacks onto the stack once it's empty. The **microtask queue** (Promise callbacks, `queueMicrotask`, `MutationObserver`) is drained **completely** after each stack-emptying step, before the loop moves on. The **macrotask queue** (`setTimeout`, `setInterval`, I/O, UI events) runs **one task per loop iteration**, with microtasks drained again after it.

This is why `Promise.resolve().then(cb)` always runs before a `setTimeout(cb, 0)`, regardless of order written. A microtask that keeps scheduling more microtasks can **starve** rendering and macrotasks indefinitely.

## 2. What are closures, and what's the classic loop-variable bug?

A **closure** is a function bundled with references to variables from its enclosing scope, which persist even after that outer function has returned. This enables patterns like private state, memoization, and factory functions returning configured functions.

The classic bug: `for (var i = 0; i < 3; i++) setTimeout(() => console.log(i))` logs `3, 3, 3` because `var` is function-scoped — all three closures share the same `i`, which finishes the loop before any timeout fires. `let` fixes it by creating a **new binding per iteration** (block-scoped), so each closure captures its own `i`.

## 3. What is prototypal inheritance? How does `class` relate to it?

Every object has an internal **`[[Prototype]]`** link (accessed via `Object.getPrototypeOf` or the non-standard `__proto__`) to another object; property lookup walks this **prototype chain** until found or it reaches `null`. `Object.create(proto)` creates an object with a specific prototype directly.

**`class`** syntax (ES6+) is **sugar over prototypes** — methods defined in a class body are added to `ClassName.prototype`, and `extends` sets up the prototype chain between constructor functions. There's no separate "class" mechanism at runtime; it's the same prototype system with cleaner syntax and some added rigor (e.g. must `new`, temporal dead zone before `super()`).

## 4. How does `this` get determined? What do `call`, `apply`, `bind`, and arrow functions do?

`this` is determined by **how a function is called**, not where it's defined: as a method (`obj.method()`) it's `obj`; as a plain function call it's `undefined` in strict mode (the global object otherwise); with `new` it's the newly created object; explicitly with `call`/`apply`/`bind` it's whatever's passed.

**Arrow functions** have no own `this` — they capture it **lexically** from the enclosing scope at definition time, which is why they're preferred for callbacks that need the outer `this` (e.g. inside a class method's inner callback). `call(thisArg, ...args)` and `apply(thisArg, argsArray)` invoke immediately with a given `this`; `bind(thisArg)` returns a new function permanently bound, callable later.

## 5. What's the difference between `==` and `===`? What is type coercion?

**`===`** (strict equality) compares value **and type**, no conversion. **`==`** (loose equality) **coerces** operands to a common type before comparing, following a specific, often surprising algorithm (`'' == 0` is `true`, `null == undefined` is `true` but `null == 0` is `false`). Prefer `===` almost always to avoid coercion surprises.

**Truthy/falsy**: only `false, 0, -0, 0n, '', null, undefined, NaN` are falsy — everything else, including `[]` and `{}`, is truthy. `Object.is(a, b)` is like `===` but treats `NaN` as equal to itself and distinguishes `+0`/`-0`.

## 6. What is hoisting? What is the temporal dead zone?

**Hoisting**: declarations are processed before code executes. `var` declarations and `function` declarations are hoisted with their binding created upfront — a `var` is accessible (as `undefined`) before its line runs; a `function` declaration is fully usable before its line.

`let`/`const` are also hoisted as bindings, but stay in the **temporal dead zone (TDZ)** — inaccessible (`ReferenceError` on access) from the start of their scope until their declaration line actually executes. This is why `let`/`const` catch use-before-declare bugs that `var` silently allows.

## 7. How do promises work, and what's the difference between `Promise.all`, `allSettled`, `race`, and `any`?

A **`Promise`** represents an eventual value with three states: pending, fulfilled, rejected — once settled, it's immutable. `.then`/`.catch`/`.finally` register callbacks; `async`/`await` is syntax sugar that makes promise chains read like synchronous code, with `try`/`catch` catching rejections.

**`Promise.all`** rejects as soon as any input rejects (fails fast), resolving with all values only if every promise succeeds. **`allSettled`** always resolves, with each result tagged `fulfilled`/`rejected` — use when you need every outcome regardless of failures. **`race`** settles with whichever input settles first (fulfilled or rejected). **`any`** resolves with the first **fulfillment**, only rejecting if all inputs reject.

## 8. What is the difference between `null` and `undefined`?

**`undefined`** means a variable has been declared but not assigned, a function parameter wasn't passed, or a property doesn't exist. **`null`** is an explicit, intentional "no value," assigned deliberately by code. `typeof undefined === 'undefined'`, but `typeof null === 'object'` (a long-standing language quirk kept for backward compatibility).

`??` (nullish coalescing) treats them the same — falls back only when the left side is `null` or `undefined`, unlike `||` which also falls back on any falsy value (`0`, `''`, etc.).

## 9. How do `var`, `let`, and `const` differ in scoping?

**`var`** is **function-scoped** (or global), ignores block boundaries, and allows redeclaration. **`let`** and **`const`** are **block-scoped** — confined to the nearest `{}`, and cannot be redeclared in the same scope. **`const`** additionally forbids reassignment of the **binding** — but if it holds an object/array, the contents remain mutable (`const arr = []; arr.push(1)` is fine).

Modern style defaults to `const`, using `let` only when reassignment is needed, and avoids `var` entirely to sidestep hoisting and scoping surprises.

## 10. What is event delegation, and how does event bubbling/capturing work?

DOM events **propagate** in three phases: **capturing** (root down to target), **target**, then **bubbling** (target back up to root) — `addEventListener`'s third argument (`{capture: true}`) chooses which phase to listen on; the default is bubbling. `stopPropagation()` halts further propagation; `preventDefault()` stops the browser's default action (e.g. a link navigating) without stopping propagation.

**Event delegation** attaches one listener to a common ancestor instead of many listeners on individual children, relying on bubbling and `event.target` to identify which child was actually interacted with — more memory-efficient and automatically covers dynamically added children.

## 11. What are the differences between `map`, `forEach`, `filter`, and `reduce`?

**`forEach`** runs a callback per element for side effects, returns `undefined` — can't be chained or broken out of early (no equivalent to `break`). **`map`** returns a **new array** of the same length with each element transformed. **`filter`** returns a new array containing only elements where the callback returns truthy.

**`reduce(fn, initial)`** folds the array into a single accumulated value, calling `fn(acc, item, index, array)` for each element — the most general of the four; `map` and `filter` can both be implemented in terms of `reduce`. Omitting the initial value uses the first element as the seed and starts from index 1, which throws on an empty array.

## 12. What are `Symbol`, `WeakMap`, and `WeakSet` used for?

**`Symbol()`** creates a guaranteed-unique value, commonly used as an object property key to avoid name collisions (e.g. well-known symbols like `Symbol.iterator` define custom iteration behavior for `for...of`). Symbol-keyed properties are excluded from `JSON.stringify`, `for...in`, and `Object.keys`.

**`WeakMap`**/**`WeakSet`** hold their keys (`WeakMap`) or values (`WeakSet`) **weakly** — objects, or (since ES2023) non-registered `Symbol`s, not garbage-collection roots — so entries can be garbage-collected once no other reference exists, preventing memory leaks in caches/metadata keyed by objects. Unlike `Map`/`Set`, they're not iterable and have no `.size`, since their contents can vanish at any time.

## 13. What is the module system — CommonJS vs ES Modules?

**CommonJS** (`require`/`module.exports`), Node's original system, loads and executes **synchronously**, resolving `require` calls at runtime — supports conditional/dynamic requires anywhere in code. **ES Modules** (`import`/`export`), the language standard, are **statically analyzed** at parse time (enabling tree-shaking and `import`/`export` bindings that stay **live references**, not copied values) and load asynchronously.

Node supports both: `.mjs`/`"type": "module"` in `package.json` for ESM, `.cjs`/default for CommonJS. Dynamic `import('./mod.js')` returns a promise and works in both systems for lazy/conditional loading.

## 14. What is destructuring, and what do the spread and rest operators do?

**Destructuring** unpacks values from arrays/objects into distinct variables: `const {a, b: renamed, ...rest} = obj`, `const [first, , third] = arr`, both supporting default values (`{a = 5} = obj`) for `undefined` fields.

The `...` syntax is **spread** when expanding an iterable/object into individual elements (`[...arr1, ...arr2]`, `{...obj, extra: 1}` — a common shallow-clone/merge idiom) and **rest** when collecting remaining elements into an array/object (`function f(first, ...rest)`, `const [a, ...others] = arr`) — same syntax, opposite direction, determined by context.

## 15. How does `async`/`await` error handling and concurrency work?

`await` pauses the **`async` function** (not the whole program) until the awaited promise settles; a rejection becomes a thrown exception catchable with a normal `try`/`catch`. An `async` function always returns a **promise**, wrapping its return value or thrown error automatically.

Sequential `await`s in a loop run **serially** — each waits for the previous to finish. To run independent async operations concurrently, start them all first (without awaiting) and then `await Promise.all([...])`, or the total time needlessly sums instead of overlapping.

## 16. What's the difference between deep and shallow copying/comparison in JS?

Assignment of objects/arrays copies the **reference**, not the value — both variables point to the same object, so mutating one is visible through the other. A **shallow copy** (`{...obj}`, `Object.assign({}, obj)`, `arr.slice()`) copies top-level properties, but nested objects/arrays are still shared references.

A true **deep copy** needs `structuredClone(obj)` (modern, handles most types including cycles) or a recursive/library solution (`JSON.parse(JSON.stringify(obj))` works for simple JSON-safe data but drops functions, `undefined`, `Date` becomes a string, and can't handle cycles).

## 17. What is debouncing vs throttling?

**Debouncing** delays invoking a function until a burst of calls has **stopped** for a given interval — each new call resets the timer, so only the last call in a rapid sequence actually fires (e.g. search-as-you-type: wait until the user pauses typing).

**Throttling** guarantees a function runs **at most once per interval**, regardless of how many times it's called — extra calls within the window are dropped or deferred, not accumulated (e.g. scroll/resize handlers, rate-limiting a fixed cadence of updates).

## 18. How does `JSON.stringify`/`parse` handle edge cases?

`JSON.stringify` **silently drops** `undefined` values, functions, and `Symbol` properties from objects (converts them to `null` inside arrays instead of dropping, since array positions must be preserved); it throws on circular references and on `BigInt`. `Date` objects serialize via their `toJSON()` (ISO string), so parsing back gives a plain string, not a `Date`, unless you supply a custom **reviver** function.

A **replacer** function/array (2nd argument to `stringify`) filters or transforms values during serialization; a **reviver** function (2nd argument to `parse`) transforms values during deserialization — both useful for handling types JSON doesn't natively support.

## 19. What are typed arrays and `ArrayBuffer` used for?

An **`ArrayBuffer`** is a raw binary buffer, fixed-length by default (or growable up to a max size if created as `resizable`); a **typed array** (`Uint8Array`, `Float64Array`, etc.) is a view over that buffer interpreting its bytes as a specific numeric type, giving fast, fixed-size, homogeneous numeric storage — unlike a regular `Array`, which is a flexible, sparse, object-like structure with per-element boxing overhead.

Used for binary data: file/network I/O, WebGL, audio/image processing, and `Buffer` in Node (which extends `Uint8Array`). Multiple typed array **views** can share one `ArrayBuffer`, reading/writing the same underlying memory with different type interpretations.

## 20. How do you test and profile JavaScript code?

Common test runners (Jest, Vitest, Mocha) provide `describe`/`it`/`test` blocks, assertions, mocking (`jest.fn()`, `vi.fn()`), and snapshot testing. **Unit tests** isolate a function/module (mocking dependencies); **integration tests** exercise several modules together; end-to-end tools (Playwright, Cypress) drive a real browser.

For performance: browser DevTools' **Performance** panel records a CPU/paint timeline; `console.time`/`timeEnd` gives quick manual timing; Node's `--prof` and `node --inspect` support CPU profiling via Chrome DevTools. Always measure before optimizing — intuition about JS hot paths is often wrong due to JIT behavior.
