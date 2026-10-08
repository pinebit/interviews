# TypeScript

What experienced TypeScript engineers forget before an interview, grouped by subtopic.

## Type system semantics

### Excess property checks

- Only fresh object literals get [excess-property errors](https://www.typescriptlang.org/docs/handbook/2/objects.html#excess-property-checks): `const p: Point = { x: 1, y: 2, z: 3 }` fails.
- The same literal assigned to a variable first, then to `Point`, passes — the check never runs.

### `any`, `unknown`, `never`

- [`any`](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#any) turns checking off in both directions; [`unknown`](https://www.typescriptlang.org/docs/handbook/2/functions.html#unknown) accepts anything but must be narrowed before use.
- [`never`](https://www.typescriptlang.org/docs/handbook/2/functions.html#never) is the empty type — the result of exhaustive narrowing and of functions that never return.

### `{}`, `object`, and index signatures

- `{}` means any non-nullish value — strings and numbers included — not "empty object"; `Object` behaves the same.
- [`object`](https://www.typescriptlang.org/docs/handbook/2/functions.html#object) is any non-primitive; `Record<string, never>` is a truly empty object.
- With an [index signature](https://www.typescriptlang.org/docs/handbook/2/objects.html#index-signatures) (`Record<string, T>`), every key reads as present and typed `T` unless [`noUncheckedIndexedAccess`](https://www.typescriptlang.org/tsconfig/#noUncheckedIndexedAccess) is on.

### Function assignability

- A function returning a value is assignable to a [`void`-returning](https://www.typescriptlang.org/docs/handbook/2/functions.html#return-type-void) function type, so `arr.forEach(x => out.push(x))` compiles and the result is ignored.
- A function with [fewer parameters](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#comparing-two-functions) is assignable to one with more: callbacks may ignore arguments (`arr.map(x => x * 2)`).
- Only the contextual case is relaxed: a function declared with a `void` return type still can't return a value.

### `interface` vs `type`

- `interface` supports [declaration merging](https://www.typescriptlang.org/docs/handbook/declaration-merging.html) (reopening adds members) and gives clearer error messages for object shapes.
- [`type`](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#differences-between-type-aliases-and-interfaces) can alias unions, tuples, and mapped/conditional types, which `interface` can't express.

### Variance annotations

- Generic types are checked by structure, so variance is inferred; [`in`/`out` annotations](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-7.html#optional-variance-annotations-for-type-parameters) (`interface Producer<out T>`, 4.7) declare contravariance/covariance explicitly — faster checks and clearer errors.
- Arrays are treated covariantly (`Dog[]` assignable to `Animal[]`) even though writes make that [unsound](https://www.typescriptlang.org/docs/handbook/type-compatibility.html#a-note-on-soundness).

### Method bivariance

- Under [`strictFunctionTypes`](https://www.typescriptlang.org/tsconfig/#strictFunctionTypes), function-typed properties (`f: (x: T) => void`) check parameters contravariantly.
- Method shorthand (`f(x: T): void`) stays [bivariant](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-6.html#strict-function-types) on purpose — unsound, but keeps common override patterns compiling.

## Narrowing

### Control-flow narrowing

- `typeof`, `instanceof`, `in`, equality, and truthiness checks [narrow](https://www.typescriptlang.org/docs/handbook/2/narrowing.html) a variable inside the branch where they're provably true.
- [Discriminated unions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions): a shared literal tag (`kind`) lets `switch (x.kind)` narrow each case.
- [Exhaustiveness](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking): in the `default` branch, assign the value to a `never` variable; adding a new union member then fails to compile until handled.

### Custom type guards

- A [type predicate](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#using-type-predicates) (`x is Fish`) or an [`asserts x is T`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-7.html#assertion-functions) function packages narrowing the compiler can't infer.
- [Inferred type predicates](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-5.html#inferred-type-predicates) (5.5): a boolean-returning function that already narrows gets `x is T` automatically, e.g. `arr.filter(x => x !== undefined)`.

### `as` vs `satisfies` vs `!`

- [`x as T`](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions) is an unchecked assertion — it only rejects conversions between unrelated types (bypass: `as unknown as T`).
- [`satisfies T`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html#the-satisfies-operator) (4.9) checks without changing the inferred type; [`x!`](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#non-null-assertion-operator-postfix-) strips `null`/`undefined` with no runtime check.

## Type-level programming

### Conditional types

- [Conditional types distribute](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html#distributive-conditional-types) over a naked type parameter: `C<A | B>` = `C<A> | C<B>`; wrap as `[T] extends [U]` to disable it.
- [`infer`](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html#inferring-within-conditional-types) extracts a part of a type, powering [`ReturnType<T>`](https://www.typescriptlang.org/docs/handbook/utility-types.html#returntypetype) and `Parameters<T>`.

### Mapped and template literal types

- [Mapped types](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html) (`{ [K in keyof T]: T[K] }`) transform each property; [`as` remaps keys](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html#key-remapping-via-as); [`+`/`-`](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html#mapping-modifiers) add or strip `readonly` and `?`.
- [Template literal types](https://www.typescriptlang.org/docs/handbook/2/template-literal-types.html) build string unions: `` `on${Capitalize<Event>}` ``.

### Inference controls

- [`const` type parameters](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#const-type-parameters) (5.0) infer literal types without the caller writing `as const`.
- [`NoInfer<T>`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-4.html#the-noinfer-utility-type) (5.4) excludes a position from inference, so a default argument can't widen `T`.

### Utility types on unions

- [`Omit`](https://www.typescriptlang.org/docs/handbook/utility-types.html#omittype-keys) and `Pick` aren't distributive: `Omit<A | B, 'id'>` keeps only keys common to both, collapsing the union.
- Write a distributive version: `type DistOmit<T, K extends PropertyKey> = T extends unknown ? Omit<T, K> : never`.
- `keyof (A | B)` is only the shared keys; [`Partial`](https://www.typescriptlang.org/docs/handbook/utility-types.html#partialtype) and `Readonly` are shallow.

### Branded types

- Types are compatible by shape, not declared name ([structural typing](https://www.typescriptlang.org/docs/handbook/type-compatibility.html)), so `UserId` and `OrderId` are both plain `string`s; brand them for nominal-like safety: `type UserId = string & { readonly __brand: 'UserId' }`.
- Create values only through a validating function (`asUserId(s)`); the brand has no runtime cost.

## Compilation and tooling

### Type erasure

- Types, interfaces, and type-only imports are [erased](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#erased-types) — zero runtime footprint.
- Exceptions that emit runtime code: [`enum`s](https://www.typescriptlang.org/docs/handbook/enums.html) (a `const enum` is inlined instead), [`namespace`s](https://www.typescriptlang.org/docs/handbook/namespaces.html) with values, [parameter properties](https://www.typescriptlang.org/docs/handbook/2/classes.html#parameter-properties), and [legacy decorators](https://www.typescriptlang.org/docs/handbook/decorators.html).

### Transpile-only builds

- [esbuild](https://esbuild.github.io/content-types/#typescript-caveats), [swc](https://swc.rs/), and [Babel](https://babeljs.io/docs/babel-preset-typescript) strip types file by file without type checking — fast, but they emit JS from type-invalid code.
- [`isolatedModules`](https://www.typescriptlang.org/tsconfig/#isolatedModules) flags constructs a single-file transpiler can't handle; [`verbatimModuleSyntax`](https://www.typescriptlang.org/tsconfig/#verbatimModuleSyntax) requires explicit `import type`, so elision needs no type analysis.

### Node type stripping

- Node runs `.ts` files by [stripping types](https://nodejs.org/api/typescript.html#type-stripping), on by default since Node 22.18 / 23.6.
- [`erasableSyntaxOnly`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html#the---erasablesyntaxonly-option) (5.8) forbids syntax that can't simply be erased (enums, parameter properties, value namespaces); Node still ignores tsconfig (`paths`, JSX) and needs explicit `.ts` import extensions.

### Module resolution

- [`moduleResolution: bundler`](https://www.typescriptlang.org/tsconfig/#moduleResolution) mirrors bundlers (extensionless imports allowed); `nodenext` mirrors Node exactly, requiring file extensions in ESM.
- `node10` (the old `node`) ignores `package.json` `exports`; it is [deprecated in 6.0](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/#deprecated---moduleresolution-node-aka---moduleresolution-node10) and removed in 7.0.

### TypeScript 6.0 defaults

- [TypeScript 6.0](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/) (March 2026), the last JS-based release, turns [`strict`](https://www.typescriptlang.org/tsconfig/#strict) on by default and defaults `module` to `esnext` and `target` to `es2025`.
- [`types`](https://www.typescriptlang.org/tsconfig/#types) defaults to `[]`: global `@types` packages are no longer auto-included — add `"types": ["node"]` or get "Cannot find name 'process'".
- [Deprecates](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/#breaking-changes-and-deprecations-in-typescript-60) `target: es5`, `moduleResolution: node10`, `baseUrl`, `outFile`, and AMD/UMD/SystemJS output — errors unless `"ignoreDeprecations": "6.0"`; 7.0 removes them.

### TypeScript 7 native compiler

- [TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/) (July 2026) is the Go port of the compiler, still installed as `typescript` with a `tsc` binary (previews shipped as `tsgo` in `@typescript/native-preview`).
- Full builds are typically 8–12× faster than 6.0: parsing, emit, and [type checking run in parallel](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/#type-checker-parallelization) (`--checkers`, default 4).
- It ships no compiler API yet (planned for 7.1), so tools built on the 6.0 API (Vue, Svelte, and Angular template checking) still need 6.0 alongside.

## Strictness flags

### The `strict` family

- [`strict`](https://www.typescriptlang.org/tsconfig/#strict) enables `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, `strictPropertyInitialization`, and more — on by default since 6.0.
- Without [`strictNullChecks`](https://www.typescriptlang.org/tsconfig/#strictNullChecks), `null`/`undefined` are assignable to every type except `never`.

### Flags outside `strict`

- [`noUncheckedIndexedAccess`](https://www.typescriptlang.org/tsconfig/#noUncheckedIndexedAccess): `arr[i]` and `record[key]` become `T | undefined`.
- [`exactOptionalPropertyTypes`](https://www.typescriptlang.org/tsconfig/#exactOptionalPropertyTypes): `x?: number` means "absent", no longer "absent or explicitly `undefined`".

## Declarations and runtime features

### Enums and alternatives

- Numeric enums compile to a [bidirectional](https://www.typescriptlang.org/docs/handbook/enums.html#reverse-mappings) object (name ↔ value); string enums map one way.
- [`const enum`](https://www.typescriptlang.org/docs/handbook/enums.html#const-enums) values are inlined, but [break under `isolatedModules`](https://www.typescriptlang.org/docs/handbook/enums.html#const-enum-pitfalls) when imported from declaration files — many teams use string-literal unions or `as const` objects instead.

### Declaration files and augmentation

- [`.d.ts`](https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html) files hold only types, describing JS libraries or shipping types beside compiled output.
- [`declare global`](https://www.typescriptlang.org/docs/handbook/declaration-merging.html#global-augmentation) and [module augmentation](https://www.typescriptlang.org/docs/handbook/declaration-merging.html#module-augmentation) (`declare module 'express' { interface Request { user?: User } }`) extend third-party types.

### Decorators

- [Standard decorators](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators) (TC39, 5.0) have no parameter decorators and no metadata by default.
- [`experimentalDecorators`](https://www.typescriptlang.org/tsconfig/#experimentalDecorators) is the older, incompatible form still used by Angular and NestJS — check which one a codebase uses.

## Typing patterns

### Runtime validation at boundaries

- Types are erased: `JSON.parse` and `res.json()` return `any`, and env vars or `as` casts are unchecked, so data can violate its declared type at runtime.
- Parse untrusted input with a schema library ([Zod](https://zod.dev/), [Valibot](https://valibot.dev/), [ArkType](https://arktype.io/)) and derive the type from the schema (`type User = z.infer<typeof User>`), so the two can't drift.
- Type unparsed input as [`unknown`](https://www.typescriptlang.org/docs/handbook/2/functions.html#unknown), not `any`, so it must be validated or narrowed before use.

### Overloads

- Several [overload signatures](https://www.typescriptlang.org/docs/handbook/2/functions.html#function-overloads) followed by one implementation signature that callers can't see.
- Resolution picks the [first matching](https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html#ordering) signature top-down — list specific before general; prefer generics or a union parameter when they're precise enough.

### Readonly and `as const`

- [`readonly T[]`](https://www.typescriptlang.org/docs/handbook/2/objects.html#the-readonlyarray-type) blocks `push`/`splice` at compile time; [`as const`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-4.html#const-assertions) narrows a literal to its most specific type and makes it deeply `readonly` — but not arrays/objects it only references.
- Both are compile-time only — nothing is frozen at runtime.
