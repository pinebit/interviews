# TypeScript Cheatsheet

The 20 most frequently asked TypeScript interview topics, with short answers.

## 1. What is structural typing, and how does it differ from nominal typing?

TypeScript uses **structural typing** ("duck typing" for the type system): two types are compatible if their **shapes match** — same members, compatible types — regardless of declared name or inheritance. A class `Duck` with a `quack()` method is assignable to an interface `{ quack(): void }` even with no explicit `implements`.

This differs from **nominal typing** (Java, C#), where compatibility requires an explicit declared relationship. Structural typing enables flexible duck-typed APIs but means two unrelated types with identical shapes are interchangeable, which can hide bugs (mitigated with branded/nominal types when needed).

## 2. What is the difference between `interface` and `type`?

Both describe object shapes and are largely interchangeable for that purpose. **`interface`** supports **declaration merging** (reopening the same interface name adds members) and is generally preferred for public object/class APIs. **`type`** can alias unions, tuples, primitives, mapped/conditional types — anything an interface can't express.

A class can `implements` either. Since TS 4.2+, error messages generally prefer showing `interface`-style names. Rule of thumb: use `interface` for extendable object contracts, `type` for everything else (unions, utility compositions).

## 3. What do `unknown`, `any`, and `never` mean?

**`any`** opts out of type checking entirely — assignable to/from anything, no safety. **`unknown`** is the type-safe counterpart: anything is assignable **to** it, but you must **narrow** it (via `typeof`, `instanceof`, a type guard) before using it — the correct type for values from untyped sources like JSON or API responses.

**`never`** represents a value that can never occur — a function that always throws or loops forever returns `never`. It's also the result of narrowing a union to nothing, and is useful for **exhaustiveness checks** in switch statements (assigning the unreachable branch to a `never`-typed variable causes a compile error if a case is missed).

## 4. How do generics work?

Generics let a type or function be parameterized: `function identity<T>(x: T): T`. This preserves the specific type through the function instead of widening to `any` or `unknown`, giving both flexibility and type safety — the caller's argument type flows through to the return type.

**Constraints** (`<T extends { id: string }>`) restrict what `T` can be. Default type parameters (`<T = string>`) provide a fallback. Common built-in generics: `Array<T>`, `Promise<T>`, `Map<K, V>`, `Record<K, V>`.

## 5. What are union and intersection types?

A **union** (`A | B`) means a value could be either type — TypeScript only allows accessing members common to all members of the union until you **narrow** it. An **intersection** (`A & B`) combines all members of both types into one — the value must satisfy every constituent type simultaneously.

**Discriminated unions** (a shared literal "tag" field, e.g. `{ kind: 'circle', r: number } | { kind: 'square', s: number }`) let `switch (shape.kind)` narrow the type automatically per case — one of TypeScript's most useful patterns for modeling variants safely.

## 6. What is type narrowing, and what mechanisms enable it?

**Narrowing** is TypeScript refining a broader type to a more specific one within a code branch, based on runtime checks: `typeof x === 'string'`, `x instanceof Foo`, `'prop' in obj`, truthiness checks, and **discriminant checks** on tagged unions. The compiler tracks control flow (**control flow analysis**) to apply the narrowed type only where it's provably true.

A **user-defined type guard** (`function isFish(x: Fish | Bird): x is Fish`) lets you encapsulate a custom narrowing check as a reusable function, since arbitrary logic isn't otherwise inferable by the compiler.

## 7. What are mapped types and conditional types?

A **mapped type** transforms each property of an existing type: `{ [K in keyof T]: T[K] }`, the basis for built-in utilities like `Partial<T>`, `Readonly<T>`, `Pick<T, K>`. Modifiers `+`/`-` with `?` and `readonly` add or strip optionality/mutability per property.

A **conditional type** (`T extends U ? X : Y`) picks between two types based on a check, and can be distributive over unions. `infer` inside a conditional extracts a sub-type, powering utilities like `ReturnType<T>` and `Parameters<T>`.

## 8. What is the difference between `readonly` and `const`?

**`const`** is a JS-level binding: the variable itself can't be reassigned, but if it holds an object, the object's properties are still mutable. **`readonly`** is a TypeScript-only, compile-time-only annotation on a property or array (`readonly x: number`, `ReadonlyArray<T>`) preventing reassignment of that property after construction — it's erased at compile time and enforces nothing at runtime.

`as const` on a literal narrows it to its most specific literal type and makes nested properties `readonly` recursively — commonly used for literal-typed config objects and enabling precise tuple/union inference.

## 9. How does TypeScript compile to JavaScript? What is type erasure?

The compiler (`tsc`) performs **type erasure**: type annotations, interfaces, generics, and type-only imports are stripped away, producing plain JavaScript — most type-level constructs add **no runtime footprint** or performance cost. This means you can't do `typeof x === SomeInterface` at runtime; only structural runtime checks work. (A few constructs, like numeric `enum`s and legacy decorators, do emit real runtime code — see below.)

`tsconfig.json`'s `target` controls the output JS version (ES2020, etc.); `module` controls the module system (CommonJS, ESNext). `strict: true` enables the full set of strictness flags (`strictNullChecks`, `noImplicitAny`, etc.) and should be the default for new projects.

## 10. What are enums, and why are some considered problematic?

A numeric `enum Color { Red, Green, Blue }` compiles to a bidirectional runtime object (value→name and name→value), unlike most TS constructs which erase completely — this adds real JS output and bundle size. **`const enum`** avoids this by inlining values at compile time, but under `isolatedModules` (required by transpile-only tools) it can't be referenced from another compiled-in-isolation file (an *ambient* `const enum` declared in a `.d.ts`).

Many teams prefer **union of string literals** (`type Color = 'red' | 'green' | 'blue'`) or `as const` object maps instead — no runtime overhead, easier to serialize, and behaves more predictably across module boundaries.

## 11. What is declaration merging, and where do `.d.ts` files fit in?

**Declaration merging** combines multiple declarations of the same name into one — two `interface Foo` blocks merge their members; a `namespace` can merge with a function or class of the same name to attach static-like members. This underlies how libraries let you augment global types (e.g. extending `Express.Request`).

**`.d.ts`** files contain only type declarations, no implementation — used to describe the shape of plain-JS libraries (`@types/*` packages from DefinitelyTyped) or to ship types alongside a compiled library separately from its `.js` output.

## 12. What is the difference between `interface` extension and class inheritance?

`interface B extends A` merges A's members into B's required shape — purely a compile-time contract. `class B extends A` is real JS inheritance — a runtime prototype chain, with `super()` calls and inherited method implementations, not just shape.

A class can also `implements` multiple interfaces (contract only, no shared implementation) but can only `extends` one class (single inheritance) — a common way to combine structural contracts with a single implementation base.

## 13. How do decorators work in TypeScript?

A **decorator** (`@decorator`) is a function applied to a class, method, property, or (legacy only) parameter at definition time to modify or annotate it — commonly used by frameworks like Angular and NestJS for dependency injection and metadata (routes, validation rules).

TypeScript originally shipped an experimental decorators implementation (`experimentalDecorators`, stage 2 proposal, metadata-heavy, supports parameter decorators). TS 5.0 added support for the **stage 3 ECMAScript decorators** standard, which has a different, simpler runtime shape and drops parameter decorators — the two are not compatible, so check which a given codebase/framework targets.

## 14. What are utility types, and which are most commonly used?

Built-in generic types that transform other types: `Partial<T>` (all props optional), `Required<T>` (all props required), `Pick<T, K>` (subset of keys), `Omit<T, K>` (exclude keys), `Record<K, V>` (object type with keys `K` and values `V`), `Readonly<T>` (all props readonly).

Others worth knowing: `ReturnType<F>` / `Parameters<F>` (extract a function's return/argument types), `Awaited<T>` (unwrap a `Promise` type, including nested promises). Most are implemented via **mapped and conditional types**, and reading their source is a good way to learn advanced type mechanics.

## 15. What is module augmentation and why is it used?

**Module augmentation** applies declaration merging (see above) across a module boundary: `declare module 'express' { interface Request { user?: User } }` adds a property to Express's `Request` type without touching its source. It's typically placed in a `.d.ts` file so it stays a type-only addition, though a `.ts` file works too as long as the module is still imported/referenced somewhere.

Common uses: extending third-party library types with plugin-added members, adding environment-specific globals, or patching gaps in incomplete `@types` packages.

## 16. How does type inference work, and what is contextual typing?

TypeScript infers types without annotations wherever possible: `let x = 5` infers `number`; a function's return type is inferred from its `return` statements. **Contextual typing** flows the expected type from the surrounding context into an expression — e.g. an array method callback's parameter types are inferred from the array's element type without you annotating them.

**Best common type** inference picks a type that fits all elements of an array literal, widening to a union or a common supertype as needed. Excess property checks (extra unexpected properties trigger an error) apply specifically to **object literals** assigned directly, not to variables assigned afterward.

## 17. What are function overloads?

**Overload signatures** let a function have multiple valid call signatures with different parameter/return type combinations, followed by one **implementation signature** that's a superset compatible with all overloads (the implementation signature itself isn't visible to callers). Useful when a function's return type depends on which arguments/argument types were passed, more precisely than a union parameter type alone could express.

Prefer overloads sparingly — often a well-designed generic function or a discriminated union parameter achieves the same clarity with less duplication.

## 18. What does `strictNullChecks` do, and how do you handle `null`/`undefined`?

Without it, `null` and `undefined` are assignable to every type (a major historical source of runtime errors — "the billion dollar mistake"). With **`strictNullChecks`** on, they're only assignable where explicitly allowed (`T | null`, `T | undefined`), forcing explicit handling — one of the most valuable strict flags and part of `strict: true`.

Operators for handling optionality: **optional chaining** `obj?.prop` (short-circuits to `undefined` if `obj` is nullish), **nullish coalescing** `a ?? b` (fallback only for `null`/`undefined`, unlike `||` which also triggers on falsy values like `0` or `''`), and the **non-null assertion** `x!` (tells the compiler to trust you — no runtime check, use sparingly).

## 19. What's the difference between `tsc` type-checking and a bundler like esbuild/swc transpiling TypeScript?

`tsc` performs full **type checking** and can also emit JS, but its emit is relatively slow. Bundlers like esbuild, swc, and Babel's TS preset do **transpile-only**: they strip types file-by-file without checking cross-file type correctness, which is far faster — commonly used for dev builds and bundling, with `tsc --noEmit` run separately (often in CI) purely for type checking.

This split matters because a transpile-only tool will happily emit incorrect JS from type-invalid code (e.g. it can't catch cross-file type errors since it doesn't build a full type graph) — type errors surface later, at `tsc --noEmit` or CI time, not at bundle time.

## 20. How do you type a generic React/DOM event handler and generic component props?

Event handler types come from `@types/react` or the DOM lib: `(e: React.ChangeEvent<HTMLInputElement>) => void` for a typed input's `onChange`, `(e: React.MouseEvent<HTMLButtonElement>) => void` for a click. Using the specific generic parameter (`HTMLInputElement` vs a generic `Element`) gives you correctly typed `e.target.value` without casts.

Generic component props (`function List<T>(props: { items: T[]; render: (item: T) => ReactNode })`) let a reusable component stay type-safe across different item types, inferred from the `items` array passed at the call site — preferred over `any`-typed props or excessive prop-type unions for shared components.
