# Frontend

What experienced frontend engineers forget before an interview, grouped by subtopic. For language mechanics see [javascript.md](javascript.md) and [typescript.md](typescript.md); for web vulnerabilities and token storage see [security.md](security.md).

## Rendering strategies

### CSR, SSR, SSG, ISR

| Strategy | Renders | Trade-off |
|---|---|---|
| CSR | in the browser after JS loads | slow first paint and SEO, fast later navigation |
| SSR | on the server, per request | fresh and SEO-friendly, higher server load |
| SSG | at build time | fastest and cheapest, stale until rebuild |
| ISR | like SSG, regenerated on a schedule or on demand | near-CDN speed, bounded staleness |

### Streaming SSR and hydration

- **Streaming SSR** flushes HTML in chunks, so the shell paints before slow data-dependent sections resolve.
- **Hydration** attaches listeners and state to server HTML instead of re-rendering it.
- A **hydration mismatch** comes from render output that differs between server and client — `Date.now()`, `Math.random()`, `window` checks during render.

### Islands and Server Components

- **Islands architecture**: the page is static HTML; only interactive islands ship JS and hydrate independently.
- **React Server Components** render only on the server and send serialized output, not code — less JS, but props crossing into client components must be serializable.

### Client-side routing

- The router intercepts navigation and updates the URL with the **History API** (`pushState`), no full reload.
- A refresh on `/profile` hits the **server**, which must fall back to `index.html` for unknown paths or it 404s.

## Browser pipeline

### Critical rendering path

- HTML → DOM, CSS → CSSOM → **render tree** (visible nodes) → layout → paint → composite.
- CSS is **render-blocking**; a classic `<script>` is **parser-blocking**.

### Script loading: async, defer, module

- **`async`**: downloads in parallel, runs as soon as it arrives, no order guarantee.
- **`defer`**: downloads in parallel, runs in order after parsing; `type="module"` is deferred by default.

### Compositor-only animation

- Changing `width`/`top` re-runs layout + paint + composite; **`transform`/`opacity`** can skip to composite on the GPU once the element has its own layer.
- `will-change: transform` promotes a layer ahead of time; too many layers waste GPU memory.

### Layout thrashing

- Alternating reads (`offsetHeight`) and writes (`style.width`) in a loop forces a **synchronous reflow** each time.
- Batch all reads, then all writes — or schedule writes in `requestAnimationFrame`.

## CSS

### CSS layout and specificity

- **Flexbox** for one axis (a toolbar, centering); **Grid** for two axes (page layout, card grids).
- **Specificity**: inline > ID > class/attribute/pseudo-class > element; cascade layers and origin rank above specificity, and `!important` inverts layer order.

### Stacking contexts

- `z-index` only compares elements **within the same stacking context** — why `z-index: 9999` sometimes "doesn't work".
- `opacity < 1`, `transform`, `filter`, `position: fixed`, and positioned elements with a `z-index` each create a new context.

### Modern CSS features

- **Container queries** (`@container`) style a component by its container's size, not the viewport — reusable responsive components.
- **`:has()`** selects a parent by its children (`form:has(:invalid)`); native **nesting** and `subgrid` remove common preprocessor and wrapper hacks.
- All Baseline since 2023.

### View transitions

- **View Transitions API** animates between two DOM states: `document.startViewTransition(update)` snapshots old and new, then cross-fades or morphs elements sharing a `view-transition-name`.
- Same-document transitions are Baseline since Firefox 144 (October 2025); multi-page apps opt in with `@view-transition { navigation: auto }`.

## Performance

### Core Web Vitals

| Metric | Good at p75 | Measures |
|---|---|---|
| **LCP** | ≤ 2.5 s | render time of the largest visible element |
| **INP** | ≤ 200 ms | worst-ish interaction latency over the visit; **replaced FID in March 2024** |
| **CLS** | ≤ 0.1 | unexpected layout shift |

### Fixing Web Vitals

- **LCP**: preload the hero image or font, cut render-blocking resources, fast TTFB.
- **INP**: break long tasks (> **50 ms**) and yield to the main thread.
- CLS: reserve space with `width`/`height` or `aspect-ratio`.

### Bundle size

- **Code splitting** by route or with dynamic `import()` keeps the first bundle to what the first screen needs.
- **Tree shaking** needs ES modules and side-effect-free code (`"sideEffects": false`).

### Images

- **`srcset`/`sizes`** let the browser pick a resolution per viewport; AVIF/WebP are much smaller than JPEG/PNG.
- `loading="lazy"` for below-the-fold images — never on the LCP image, which should get **`fetchpriority="high"`**.

### Main-thread offloading

- **Web Workers** run JS on another thread (no DOM access), talking via `postMessage` (structured clone, or transfer an `ArrayBuffer` for free).
- **`content-visibility: auto`** skips layout and paint for off-screen sections.

### Resource hints

- **`preload`**: fetch this exact resource now, it's needed for the current page.
- **`prefetch`**: low-priority fetch for a likely next navigation.
- **`preconnect`**: open DNS + TCP + TLS early when the resource URL isn't known yet.

## Caching

### Cache-Control directives

- **`no-cache`** means **revalidate every time**, not "don't cache"; `no-store` means never store.
- `max-age` applies to every cache; **`s-maxage`** overrides it for shared caches (CDN).

### Hashed assets and validators

- Long `max-age` + `immutable` on **content-hashed filenames** (`app.a3f9c1.js`), with HTML served `no-cache` — each deploy is a new URL.
- `ETag`/`Last-Modified` let the server answer **`304 Not Modified`** — saves the body, not the round trip.

### Service workers

- **Service workers** implement cache-first, network-first, or stale-while-revalidate strategies and offline support.
- A waiting service worker is a common reason users keep seeing the old deploy.

## React rendering model

### Reconciliation and keys

- **Keys** match list items across renders; an array index as key attaches the wrong state after reorder or filter.
- A component re-renders on its own state change, a **parent re-render** (unless memoized), or a consumed **context value** change.

### Fiber and concurrent rendering

- **Fiber** splits rendering into interruptible units: the render phase can pause, restart, or be discarded; the **commit phase** applies DOM changes synchronously.
- Render must therefore be **pure** — it may run more than once for one commit.
- React 18 batches all state updates automatically, including in timeouts and promises.

### Transitions and Suspense

- **`useTransition`**/`startTransition` mark an update as non-urgent, so typing stays responsive while a heavy re-render runs; `useDeferredValue` defers a derived value.
- **`<Suspense>`** shows a fallback while children wait for code or data; with streaming SSR each boundary streams in separately.

### React 19 APIs

- **Actions**: async functions passed to `<form action>` or `useActionState`, with pending state handled by React; `useOptimistic` shows the expected result before the server confirms.
- **`use(promise)`** reads a promise or context during render, suspending until it resolves; `ref` is a normal prop (no `forwardRef`).
- 19.2: **`<Activity>`** keeps hidden UI mounted with state preserved; `useEffectEvent` reads the latest props/state inside an effect without making them dependencies.

### React Compiler

- **React Compiler** (stable 1.0, **October 2025**) auto-memoizes components and values at build time, replacing most manual `useMemo`/`useCallback`/`memo`.
- It relies on the Rules of React (pure render, no mutating props or state) and skips code it can't prove safe.

### Strict Mode double invocation

- In development, **Strict Mode** double-calls render functions to expose impure rendering.
- It also mounts → unmounts → remounts each component to expose effects with **missing cleanup**; production runs once.

## React hooks pitfalls

### Stale closures

- An effect or callback sees the values from the render that created it; a value missing from the dependency array stays **stale**.
- Fix by restructuring (a ref, a functional `setState`, moving the logic into the effect) — not by silencing the lint rule.

### Effects: when not to use one

- Deriving state inside an effect + `setState` causes an extra render and a flash — **compute it during render**.
- Every subscription, timer, or listener an effect creates needs a **cleanup** function.

### Memoization pitfalls

- `React.memo` is defeated by a **new object, array, or function** literal passed as a prop on every render.
- Memoize only when the skipped work costs more than the comparison.

### Controlled vs uncontrolled inputs

- **Controlled** (`value` + `onChange`): React owns the value — needed when it drives other UI.
- **Uncontrolled** (read via ref): less code, fewer re-renders; a file input is always uncontrolled.

## State management

### Where state lives

- Local state → lift to the nearest common parent → context → a **dedicated store** only when many unrelated components share it.
- Reach for context or a store when prop drilling actually hurts, not for a two-level pass.

### Server state vs client state

- **Server state** (fetched data) has its own caching, staleness, refetching, and loading lifecycle — use TanStack Query or SWR, not a global client store.
- These libraries dedupe requests, cache by **query key**, and refetch after invalidating a key on mutation.

## Accessibility

### Semantic HTML and ARIA

- Native elements (`<button>`, `<nav>`, `<label>`) come with keyboard, focus, and screen-reader behavior for free.
- **First rule of ARIA**: don't use ARIA when a native element already has the semantics.

### Focus management in SPAs

- Client-side navigation doesn't reset focus — **move focus** to the new view's heading on route change.
- Everything clickable must be keyboard-reachable with a visible focus indicator; a `<dialog>` opened with `showModal()` makes the rest of the page inert.

### Contrast

- **WCAG AA**: **4.5:1** for normal text, **3:1** for large text and UI components.
- Never convey information by color alone (error states need text or an icon).
