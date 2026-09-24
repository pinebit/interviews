# Frontend

What experienced frontend engineers forget before an interview, grouped by subtopic. For language mechanics see [javascript.md](javascript.md) and [typescript.md](typescript.md); for web vulnerabilities see [security.md](security.md).

## Rendering strategies

### CSR, SSR, SSG, ISR, streaming

| Strategy | Renders | Trade-off |
|---|---|---|
| CSR | in the browser after JS loads | slow first paint/SEO, fast subsequent nav |
| SSR | on the server, per request | fresh + SEO-friendly, higher server load |
| SSG | at build time | fastest/cheapest, stale until rebuild |
| ISR | like SSG, rebuilt on schedule/demand | near-CDN speed, bounded staleness |

- **Streaming SSR**: the server sends HTML in chunks as it becomes ready instead of waiting for the whole page, letting the browser start painting above-the-fold content before slower data-dependent sections resolve.
- **Hydration**: the client attaches event listeners/state to server-rendered HTML rather than re-rendering from scratch — a **hydration mismatch** (server and client render different output) causes a visible flash or a React warning, usually from `Date.now()`, `Math.random()`, or browser-only APIs used during the render itself.
- **Islands architecture**: most of the page ships as static HTML with no JS; only interactive "islands" hydrate independently — smaller JS payload than full-page hydration.
- **React Server Components**: components that render only on the server, sending serialized output (not JS) to the client — reduces bundle size for logic that never needs to run in the browser, at the cost of a stricter serialization boundary between server and client components.

## Browser pipeline

### Critical rendering path

- Parse HTML → **DOM**; parse CSS → **CSSOM**; combine → **render tree** (visible nodes only) → **layout** (size/position) → **paint** (pixels) → **composite** (GPU layers).
- `<script>` blocks HTML parsing unless `async` (loads without stalling, runs whenever ready, no order guarantee) or `defer` (loads without stalling, runs in order after parsing) — `type="module"` scripts are deferred by default.
- Layout-triggering properties (`width`, `top`) cost layout + paint + composite; **`transform`/`opacity`** can skip straight to composite (GPU-accelerated) — but only if the element is already promoted to its own compositor layer.
- **Layout thrashing**: interleaved reads (`el.offsetHeight`) and writes (`el.style.width = ...`) in a loop force synchronous reflow on every iteration — batch reads, then writes.

### CSS layout

- **Flexbox** lays out items along one axis (row or column) — ideal for a toolbar or centering content. **Grid** lays out items on two axes at once — ideal for overall page layout or a card grid. Rule of thumb: flexbox for a single row/column, grid for two-dimensional layout.
- **Specificity** resolves conflicting rules of equal cascade origin: inline style > ID > class/attribute/pseudo-class > element; `!important` jumps ahead of normal specificity but is still resolved by specificity between two competing `!important` rules, and cascade layers/origin can still outrank it.

### Client-side routing

- The router intercepts navigation and updates the URL via the **History API** (`pushState`/`replaceState`) without a full page reload, then renders the matching component.
- A direct hit or refresh on a client-only route goes straight to the **server**, which must be configured to serve the SPA's `index.html` for unknown paths — otherwise refreshing `/profile` 404s, since the router only takes over once the JS has loaded.

## Performance

### Core Web Vitals

- **LCP ≤ 2.5s** (largest visible element render time), **INP ≤ 200ms** (a high-percentile interaction latency across the visit — one worst outlier is dropped for every ~50 interactions on interaction-heavy pages — reported at the 75th percentile of real users, **replaced FID in March 2024**), **CLS ≤ 0.1** (unexpected visible content shift).
- Fixes: explicit `width`/`height` or `aspect-ratio` on images (CLS), preloading the LCP image/font, avoiding render-blocking resources, breaking up long JS tasks (INP).

### Bundle and loading

- **Code splitting**: route-based or `import()`-based lazy loading, so the initial bundle only ships what the first screen needs.
- **Tree shaking** requires ES module syntax and side-effect-free code to reliably remove unused exports.
- `preload` (fetch this exact resource now, needed soon), `prefetch` (fetch this at low priority, might be needed later), `preconnect` (open the connection early, resource unknown yet) — using the wrong one wastes bandwidth or misses the point entirely.

## Caching

### HTTP and service worker caching

- `Cache-Control: no-cache` means **revalidate every time** (via `ETag`/`Last-Modified`, `304` if unchanged) — despite the name, it doesn't mean "don't cache." `no-store` means never cache at all. `max-age` applies to the browser; **`s-maxage`** applies to shared caches (CDN) and overrides `max-age` there.
- Long `max-age` **plus a content hash in the filename** (`app.a3f9c1.js`) lets the browser cache "forever" safely — a new deploy is a new filename, referenced by fresh HTML served with `no-cache`.
- **ETag** validation lets a `304 Not Modified` skip re-downloading a body the client already has, saving bandwidth without skipping the revalidation round trip.
- **Service workers** implement custom strategies (cache-first, network-first, stale-while-revalidate) and offline support — a stale service worker is also a common reason users don't see a new deploy until a hard refresh.

## React internals and pitfalls

### Reconciliation

- **Keys** tell the diff algorithm which list items are the same across renders (matched by key, not position); using array index as a key breaks this under reordering/filtering, silently attaching the wrong state to an item.
- What triggers a re-render: state change, parent re-render (propagates to children regardless of their own props unless memoized), or context value change.
- **React Compiler** (stable **1.0**, released **October 2025**) automatically memoizes components and values at build time, reducing the need for manual `useMemo`/`useCallback`/`React.memo` in code it can fully analyze.

### Hooks and effects pitfalls

- **Stale closures**: an effect/callback captures a variable's value at creation time; a variable that changes later but isn't in the dependency array keeps the old value — the fix is usually restructuring (a ref, or deriving the value inside the effect), not silencing the lint rule.
- Effect **dependencies and cleanup**: computing a value from props/state inside an effect + `setState` causes an extra render and a stale-UI flash — compute it directly during render instead. Cleanup functions matter for anything outliving one render (subscriptions, timers, listeners).
- **Strict Mode double invocation**: in development, Strict Mode intentionally mounts, unmounts, and remounts components (and re-runs some functions twice) to surface effects that aren't idempotent or cleanup that's missing — it's a diagnostic, not a production behavior.
- **Memoization** (`useMemo`, `React.memo`) avoids recomputation/re-render only when it actually skips more work than the memoization itself costs; a common miss is a new object/array/function literal passed as a prop every render, defeating `React.memo` on the child.

### Controlled vs uncontrolled inputs

- Controlled inputs (`value` + `onChange`) make the framework the source of truth, needed when the value drives other UI; uncontrolled inputs (read via ref) mean less code and fewer re-renders — file inputs can't be controlled at all, since the browser owns the file value.

## State management

### Scope-matched state

- Local component state → framework built-ins. Shared between a few nearby components → lift to the common parent or pass via context. Global app state (user, theme, cart) → a dedicated store, justified once many unrelated components read/write it.
- **Server state** (fetched data, with its own loading/error/staleness/caching lifecycle) is a different problem from client state — a data-fetching library (TanStack Query, SWR) handles it better than stuffing it into a global store.
- Prop drilling is the signal to reach for context/a store — but only once it actually hurts; adding global state for a two-level prop pass is premature.

## Accessibility

### Semantic-first

- **Semantic HTML first** (`<button>`, `<nav>`, `<label>`) — free keyboard interaction, focus handling, and screen-reader semantics; ARIA on a `<div>` acting like a button is a last resort. This is the **first rule of ARIA**: don't use ARIA if a native HTML element/attribute already has the semantics you need.
- **Focus management in SPAs**: client-side navigation doesn't reset focus the way a full page load does — move focus to the new view's heading (or an appropriate landmark) on route change, or screen-reader users stay "stuck" where they were.
- Keep color **contrast ≥ 4.5:1** for normal text (WCAG AA); ensure everything mouse-reachable is also keyboard-reachable with a visible focus state.

## Security in the browser

### Token storage

- **httpOnly cookie** (server-set, JS-inaccessible): protects against **XSS** token theft, vulnerable to **CSRF** unless paired with `SameSite` + a CSRF token — the standard choice for most web apps.
- **In memory**: avoids CSRF and persistent exposure, but lost on refresh (needs a silent refresh flow) and still reachable by a script actively running on the page.
- **`localStorage`**: least safe — any injected script (XSS) reads it directly — avoid for sensitive tokens despite being the easiest to implement.
- See [security.md](security.md) for the underlying XSS/CSRF/CORS mechanics this choice defends against.
