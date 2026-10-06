# Frontend

What experienced frontend engineers forget before an interview, grouped by subtopic. For language mechanics see [javascript.md](javascript.md) and [typescript.md](typescript.md); for web vulnerabilities and token storage see [security.md](security.md); for React and Next.js see [react.md](react.md) and [nextjs.md](nextjs.md).

## Rendering strategies

### CSR, SSR, SSG, ISR

| Strategy | Renders | Trade-off |
|---|---|---|
| CSR | in the browser after JS loads | slow first paint and SEO, fast later navigation |
| SSR | on the server, per request | fresh and SEO-friendly, higher server load |
| SSG | at build time | fastest and cheapest, stale until rebuild |
| ISR | like SSG, regenerated in the background after a revalidate interval or on demand | near-CDN speed; serves stale until regeneration succeeds |

### Streaming SSR and hydration

- **Streaming SSR** flushes HTML in chunks, so the shell paints before slow data-dependent sections resolve.
- **Hydration** runs the render on the client and attaches listeners to the server HTML, reusing the DOM instead of recreating it.
- A **hydration mismatch** (server and client render different output) can force the framework to re-render that part on the client — React's causes and fixes in [react.md](react.md).

### Islands and Server Components

- **Islands architecture**: the page is static HTML; only interactive islands ship JS and hydrate independently.
- **React Server Components** render only on the server and send serialized output, not code — only Client Components ship JS and hydrate (see [react.md](react.md)).

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

### Specificity and the cascade

- **Specificity**: inline > ID > class/attribute/pseudo-class > element; cascade layers and origin rank above specificity, and `!important` inverts layer order.

### Stacking contexts

- `z-index` only compares elements **within the same stacking context** — why `z-index: 9999` sometimes "doesn't work".
- `opacity < 1`, `transform`, `filter`, `position: fixed`, and positioned elements with a `z-index` each create a new context.

### Modern CSS features

- **Container queries** (`@container`) style a component by its container's size, not the viewport — reusable responsive components.
- **`:has()`** selects a parent by its children (`form:has(:invalid)`), which used to need JavaScript.

### View transitions

- **View Transitions API** animates between two DOM states: `document.startViewTransition(update)` snapshots old and new, then cross-fades or morphs elements sharing a `view-transition-name`.
- Multi-page apps opt in to cross-document transitions with `@view-transition { navigation: auto }`.

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
- **Tree shaking** needs ES modules; `"sideEffects": false` also lets the bundler drop unused modules whole — list CSS and polyfill files as exceptions.

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

### Browser storage

| Storage | Size | Notes |
|---|---|---|
| Cookies | ~4 KB each | sent with every request to the domain |
| `localStorage` | ~5 MB per origin | **synchronous** (blocks the main thread), strings only |
| `sessionStorage` | ~5 MB per origin | per tab, cleared when the tab closes |
| **IndexedDB** | a share of free disk | async, structured data, available in workers |
| Cache API | a share of free disk | request/response pairs, used by service workers |

Any XSS can read all of them except `HttpOnly` cookies — token storage in [security.md](security.md).

### Service workers

- **Service workers** implement cache-first, network-first, or stale-while-revalidate strategies and offline support.
- A waiting service worker is a common reason users keep seeing the old deploy.

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
