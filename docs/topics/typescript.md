# TypeScript

What experienced TypeScript engineers forget before an interview, grouped by subtopic.

## Type system semantics

### Structural typing

- Compatibility is by **shape**, not declared name — a class or object satisfies an interface just by having the right members, no `implements` required. Contrast with nominal typing (Java, C#).
- **Excess property checks** apply only to **fresh object literals** assigned directly (`const p: Point = { x: 1, y: 2, z: 3 }` errors) — the same literal passed through a variable first (`const o = {...}; const p: Point = o`) bypasses the check entirely.
- **`any`** opts out of checking entirely; **`unknown`** is the type-safe counterpart — assignable to it from anything, but must be narrowed before use; **`never`** is the type of a value that can't occur, useful for exhaustiveness checks.

### interface vs type, bivariance

- `interface` supports **declaration merging** (reopening the name adds members); `type` can alias unions, tuples, and mapped/conditional types that `interface` can't express.
- **Method parameters are bivariant** (unsound but pragmatic for override compatibility) while **standalone function-typed properties are checked contravariantly**; `strictFunctionTypes` makes function-typed properties strict, but method shorthand syntax (`foo(x: T): void` vs `foo: (x: T) => void`) is deliberately exempted and stays bivariant, for compatibility with common override patterns.

## Narrowing

### Mechanisms

- `typeof`, `instanceof`, `in`, equality checks, and truthiness all narrow within a branch via **control flow analysis** — the narrowed type applies only where it's provably true.
- **Discriminated unions**: a shared literal tag field lets `switch (x.kind)` narrow automatically per case — one of the most useful patterns for safely modeling variants.
- A **type predicate** (`x is Fish`) or **`asserts`** function lets you encapsulate custom narrowing logic the compiler can't infer on its own.
- **Exhaustiveness** via `never`: assigning the presumed-unreachable branch to a `never`-typed variable causes a compile error if a new union member isn't handled.
- **Inferred type predicates** (**5.5**): a function whose body already narrows and returns a boolean gets an automatically inferred `x is T` return type, no manual annotation needed.

## Type-level programming

### Conditional and mapped types

- Conditional types (`T extends U ? X : Y`) are distributive over naked type parameters — `Cond<A | B>` becomes `Cond<A> | Cond<B>`; wrapping in `[T]` (`[T] extends [U] ? X : Y`) disables distribution when the union should be treated as one unit.
- `infer` inside a conditional extracts a sub-type, powering `ReturnType<T>`/`Parameters<T>`.
- Mapped types transform each property (`{ [K in keyof T]: T[K] }`); the `as` clause remaps keys, and `+`/`-` modifiers add or strip `readonly`/`?` per property.
- Template literal types build string-literal unions structurally (`` `on${Capitalize<Event>}` ``).

### Recent inference features

- **`satisfies`** (**4.9**) checks a value against a type without widening the value's own inferred type.
- **`const` type parameters** (**5.0**) infer the most specific literal type for a generic argument without the caller writing `as const`.
- **`NoInfer<T>`** (**5.4**) blocks a type parameter position from participating in inference, useful to stop a default value from widening the inferred type.

## Compilation and tooling

### Type erasure and speed

- Type annotations, interfaces, generics, and type-only imports are erased — most type-level constructs add **zero runtime footprint**. Numeric `enum`s and legacy decorators are exceptions that emit real runtime code.
- `tsc` does full type checking (and can emit JS, relatively slowly); esbuild/swc/Babel's TS preset do **transpile-only**, stripping types file-by-file without cross-file checking — much faster, but they'll happily emit JS from type-invalid code since they never build a full type graph. Enable **`isolatedModules`** to catch constructs (like non-`const` re-exported type-only names) that transpile-only tools can't handle correctly.
- **`verbatimModuleSyntax`** requires explicit `import type`/`export type` for type-only imports/exports, so a transpiler knows unambiguously what to elide without doing type analysis.
- **`erasableSyntaxOnly`** (**5.8**) forbids TypeScript syntax that can't be *erased* without emitting runtime code (enum bodies, parameter properties, namespaces with runtime code) — this is the flag that guarantees a file is compatible with Node.js's native **`--experimental-strip-types`**/type-stripping support.
- **`moduleResolution: bundler`** matches how modern bundlers resolve imports (no file-extension requirements); **`nodenext`** matches Node's own ESM/CJS resolution rules exactly, including required extensions in ESM.
- The native, Go-ported compiler (**TypeScript 7**, project name `tsgo` during preview) replaced the JS-based `tsc` as the standard compiler, giving large multiples of speedup on type-checking and project builds.

## Strictness flags

### The strict family

- **`strict: true`** enables the full family: `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, `strictPropertyInitialization`, and others — treat it as the floor for new projects.
- **`strictNullChecks`**: without it, `null`/`undefined` are assignable to everything (historically "the billion dollar mistake"); with it, only where explicitly allowed (`T | null`).
- **`noUncheckedIndexedAccess`**: an indexed access (`arr[i]`, `record[key]`) returns `T | undefined` instead of just `T` — catches the common bug of assuming an index/key is always present.
- **`exactOptionalPropertyTypes`**: distinguishes "property is absent" from "property is present but `undefined`" for optional properties — without it, `{ x?: number }` silently allows explicitly assigning `x: undefined`.

## Declarations and runtime features

### Enums and declaration merging

- Numeric `enum`s compile to a **bidirectional** runtime object (value→name and name→value) — real emitted code, unlike most TS constructs. **`const enum`** inlines values at compile time instead, but can't be referenced across an `isolatedModules` boundary from an *ambient* declaration — many teams prefer string literal unions or `as const` objects instead, for zero runtime cost and predictable cross-module behavior.
- **Declaration merging**: multiple `interface Foo` blocks merge members; a `namespace` can merge with a same-named function/class. **`.d.ts`** files hold only declarations, describing plain-JS libraries or shipping types separately from compiled output; **`declare global`** and **module augmentation** (`declare module 'express' { interface Request {...} }`) extend third-party or global types without touching their source.
- Decorators: the **standard** (stage-3 ECMAScript) form, stabilized in **5.0**, has a simpler runtime shape and drops parameter decorators; **`experimentalDecorators`** is the older, metadata-heavy stage-2 implementation still used by some frameworks — the two are incompatible, so check which a given codebase targets.

## Typing patterns

### Overloads and readonly arrays

- **Overload signatures** give a function multiple valid call shapes, followed by one implementation signature (a superset, invisible to callers) — reach for this only when a generic function or a discriminated-union parameter can't express the same precision more simply.
- **Readonly arrays** (`ReadonlyArray<T>`, `readonly T[]`) block mutating methods (`push`, `splice`) at compile time; **`as const`** on a literal narrows to the most specific literal type and makes nested properties `readonly` recursively — both are erased at compile time, enforcing nothing at runtime.
- Typed event handlers and generic component props (React) use the specific DOM/event generic (`React.ChangeEvent<HTMLInputElement>`) to get correctly typed fields without casts, and infer a component's type parameter from the prop actually passed at the call site rather than requiring the caller to specify it.
