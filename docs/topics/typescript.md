# TypeScript

What experienced TypeScript engineers forget before an interview, grouped by subtopic.

## Type system semantics

### Structural typing

- Compatibility is by **shape**, not declared name — an object satisfies an interface just by having the members; no `implements` needed.

### Excess property checks

- Only **fresh object literals** get excess-property errors: `const p: Point = { x: 1, y: 2, z: 3 }` fails.
- The same literal assigned to a variable first, then to `Point`, passes — the check never runs.

### `any`, `unknown`, `never`

- **`any`** turns checking off in both directions; **`unknown`** accepts anything but must be narrowed before use.
- **`never`** is the empty type — the result of exhaustive narrowing and of functions that never return.

### `interface` vs `type`

- `interface` supports **declaration merging** (reopening adds members) and gives clearer error messages for object shapes.
- `type` can alias unions, tuples, and mapped/conditional types, which `interface` can't express.

### Variance annotations

- Generic types are checked by structure, so variance is inferred; **`in`**/**`out`** annotations (`interface Producer<out T>`, 4.7) declare contravariance/covariance explicitly — faster checks and clearer errors.
- Arrays are treated **covariantly** (`Dog[]` assignable to `Animal[]`) even though writes make that unsound.

### Method bivariance

- Under `strictFunctionTypes`, function-typed properties (`f: (x: T) => void`) check parameters **contravariantly**.
- Method shorthand (`f(x: T): void`) stays **bivariant** on purpose — unsound, but keeps common override patterns compiling.

## Narrowing

### Control-flow narrowing

- `typeof`, `instanceof`, `in`, equality, and truthiness checks narrow a variable inside the branch where they're provably true.
- **Discriminated unions**: a shared literal tag (`kind`) lets `switch (x.kind)` narrow each case.

### Custom type guards

- A **type predicate** (`x is Fish`) or an **`asserts x is T`** function packages narrowing the compiler can't infer.
- **Inferred type predicates** (5.5): a boolean-returning function that already narrows gets `x is T` automatically, e.g. `arr.filter(x => x !== undefined)`.

### Exhaustiveness with `never`

- In a `default` branch, assign the value to a `never` variable; adding a new union member then fails to compile until handled.

### `as` vs `satisfies` vs `!`

- **`x as T`** is an unchecked assertion — it only rejects conversions between unrelated types (bypass: `as unknown as T`).
- **`satisfies T`** (4.9) checks without changing the inferred type; **`x!`** strips `null`/`undefined` with no runtime check.

## Type-level programming

### Conditional types

- Conditional types **distribute** over a naked type parameter: `C<A | B>` = `C<A> | C<B>`; wrap as `[T] extends [U]` to disable it.
- **`infer`** extracts a part of a type, powering `ReturnType<T>` and `Parameters<T>`.

### Mapped and template literal types

- Mapped types (`{ [K in keyof T]: T[K] }`) transform each property; `as` remaps keys; `+`/`-` add or strip `readonly` and `?`.
- Template literal types build string unions: `` `on${Capitalize<Event>}` ``.

### Inference controls

- **`const` type parameters** (5.0) infer literal types without the caller writing `as const`.
- **`NoInfer<T>`** (5.4) excludes a position from inference, so a default argument can't widen `T`.

### Utility types on unions

- **`Omit` and `Pick` aren't distributive**: `Omit<A | B, 'id'>` keeps only keys common to both, collapsing the union.
- Write a distributive version: `type DistOmit<T, K extends PropertyKey> = T extends unknown ? Omit<T, K> : never`.
- `keyof (A | B)` is only the shared keys; `Partial` and `Readonly` are **shallow**.

### Branded types

- Structural typing makes `UserId` and `OrderId` both plain `string`s; **brand** them for nominal-like safety: `type UserId = string & { readonly __brand: 'UserId' }`.
- Create values only through a validating function (`asUserId(s)`); the brand has no runtime cost.

## Compilation and tooling

### Type erasure

- Types, interfaces, and type-only imports are erased — **zero runtime footprint**.
- Exceptions that emit runtime code: **all `enum`s**, `namespace`s with values, parameter properties, and legacy decorators.

### Transpile-only builds

- esbuild, swc, and Babel strip types **file by file** without type checking — fast, but they emit JS from type-invalid code.
- **`isolatedModules`** flags constructs a single-file transpiler can't handle; **`verbatimModuleSyntax`** requires explicit `import type`, so elision needs no type analysis.

### Node type stripping

- Node runs `.ts` files by stripping types, on by default **since Node 22.18 / 23.6**.
- **`erasableSyntaxOnly`** (**5.8**) forbids syntax that can't simply be erased (enums, parameter properties, value namespaces), guaranteeing a file runs there.

### Module resolution

- **`moduleResolution: bundler`** mirrors bundlers (extensionless imports allowed); **`nodenext`** mirrors Node exactly, requiring file extensions in ESM.
- `node10` (the old `node`) ignores `package.json` `exports` and is deprecated in 6.0.

### TypeScript 6.0 defaults

- **TypeScript 6.0** (March 2026), the last JS-based release, turns **`strict` on by default** and defaults `module` to `esnext` and `target` to `es2025`.
- **`types` defaults to `[]`**: global `@types` packages are no longer auto-included — add `"types": ["node"]` or get "Cannot find name 'process'".
- Deprecates `target: es5`, `moduleResolution: node10`, `baseUrl`, `outFile`, and AMD/UMD/SystemJS output; 7.0 removes them.

### TypeScript 7 native compiler

- **TypeScript 7** (2026) ships the Go port of the compiler (`tsgo` in preview): roughly **10×** faster builds with parallel checking.
- Its stable programmatic API is planned for **7.1**, so some tools (typescript-eslint, Vue/Svelte/Angular language tooling) still need the 6.x JS compiler.

## Strictness flags

### The `strict` family

- **`strict`** enables `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, `strictPropertyInitialization`, and more — on by default since 6.0.
- Without **`strictNullChecks`**, `null`/`undefined` are assignable to every type.

### Flags outside `strict`

- **`noUncheckedIndexedAccess`**: `arr[i]` and `record[key]` become `T | undefined`.
- **`exactOptionalPropertyTypes`**: `x?: number` means "absent", no longer "absent or explicitly `undefined`".

## Declarations and runtime features

### Enums and alternatives

- Numeric enums compile to a **bidirectional** object (name ↔ value); string enums map one way.
- **`const enum`** values are inlined, but break under `isolatedModules` when imported from declaration files — many teams use string-literal unions or `as const` objects instead.

### Declaration files and augmentation

- **`.d.ts`** files hold only types, describing JS libraries or shipping types beside compiled output.
- **`declare global`** and **module augmentation** (`declare module 'express' { interface Request { user?: User } }`) extend third-party types.

### Decorators

- **Standard decorators** (TC39, **5.0**) have no parameter decorators and no metadata by default.
- **`experimentalDecorators`** is the older, incompatible form still used by Angular and NestJS — check which one a codebase uses.

## Typing patterns

### Overloads

- Several **overload signatures** followed by one implementation signature that callers can't see.
- Resolution picks the **first matching** signature top-down — list specific before general; prefer generics or a union parameter when they're precise enough.

### Readonly and `as const`

- `readonly T[]` blocks `push`/`splice` at compile time; **`as const`** narrows a literal to its most specific type and makes it deeply `readonly`.
- Both are compile-time only — nothing is frozen at runtime.
