# Frontend

What experienced frontend engineers forget before an interview, grouped by subtopic. For language mechanics see [javascript.md](javascript.md) and [typescript.md](typescript.md); for web vulnerabilities and token storage see [security.md](security.md); for React and Next.js see [react.md](react.md) and [nextjs.md](nextjs.md).

## Rendering strategies

### CSR, SSR, SSG, ISR

| Strategy | Renders | Trade-off |
|---|---|---|
| [CSR](https://web.dev/articles/rendering-on-the-web#client-side) | in the browser after JS loads | slow first paint and SEO, fast later navigation |
| [SSR](https://web.dev/articles/rendering-on-the-web#server-side) | on the server, per request | fresh and SEO-friendly, higher server load |
| [SSG](https://web.dev/articles/rendering-on-the-web#static) | at build time | fastest and cheapest, stale until rebuild |
| [ISR](https://nextjs.org/docs/app/guides/incremental-static-regeneration) | like SSG, regenerated in the background after a revalidate interval or on demand | near-CDN speed; serves stale until regeneration succeeds |

### Streaming SSR and hydration

- [Streaming SSR](https://react.dev/reference/react-dom/server/renderToPipeableStream) flushes HTML in chunks, so the shell paints before slow data-dependent sections resolve.
- [Hydration](https://en.wikipedia.org/wiki/Hydration_%28web_development%29) runs the render on the client and attaches listeners to the server HTML, reusing the DOM instead of recreating it.
- A hydration mismatch (server and client render different output) can force the framework to re-render that part on the client — React's causes and fixes in [react.md](react.md).

### Islands and Server Components

- [Islands architecture](https://docs.astro.build/en/concepts/islands/): the page is static HTML; only interactive islands ship JS and hydrate independently.
- [React Server Components](https://react.dev/reference/rsc/server-components) render only on the server and send serialized output, not code — only Client Components ship JS and hydrate (see [react.md](react.md)).

### Client-side routing

- The router intercepts navigation and updates the URL with the [History API](https://developer.mozilla.org/en-US/docs/Web/API/History_API) ([`pushState`](https://developer.mozilla.org/en-US/docs/Web/API/History/pushState)), no full reload.
- A refresh on `/profile` hits the server, which must fall back to `index.html` for unknown paths or it 404s.

## Browser pipeline

### Critical rendering path

- HTML → [DOM](https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model), CSS → [CSSOM](https://developer.mozilla.org/en-US/docs/Web/API/CSS_Object_Model) → render tree (visible nodes) → layout → paint → composite ([critical rendering path](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Critical_rendering_path)).
- CSS is [render-blocking](https://developer.mozilla.org/en-US/docs/Glossary/Render_blocking); a classic `<script>` is parser-blocking.

### Script loading: async, defer, module

- [`async`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/script#async): downloads in parallel, runs as soon as it arrives, no order guarantee.
- [`defer`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/script#defer): downloads in parallel, runs in order after parsing; [`type="module"`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules#other_differences_between_modules_and_classic_scripts) is deferred by default.

### Compositor-only animation

- Changing `width`/`top` re-runs layout + paint + composite; `transform`/`opacity` can skip to [composite on the GPU](https://web.dev/articles/stick-to-compositor-only-properties-and-manage-layer-count) once the element has its own layer.
- [`will-change: transform`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/will-change) hints the browser to promote a layer ahead of time; too many layers waste GPU memory.

### Layout thrashing

- Alternating reads ([`offsetHeight`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/offsetHeight)) and writes (`style.width`) in a loop forces a [synchronous reflow](https://web.dev/articles/avoid-large-complex-layouts-and-layout-thrashing#avoid_forced_synchronous_layouts) each time.
- Batch all reads, then all writes — or schedule writes in [`requestAnimationFrame`](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame).

## CSS

### Specificity and the cascade

- [Specificity](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascade/Specificity): inline > ID > class/attribute/pseudo-class > element; [cascade layers](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@layer) and [origin](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascade/Introduction#origin_types) rank above specificity, and [`!important`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/important) inverts layer order.

### Stacking contexts

- [`z-index`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/z-index) only compares elements within the same [stacking context](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Positioned_layout/Stacking_context) — why `z-index: 9999` sometimes "doesn't work".
- `opacity < 1`, `transform`, `filter`, `position: fixed`, and positioned elements with a `z-index` each create a new context.

### Modern CSS features

- [Container queries](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Containment/Container_queries) (`@container`) style a component by its container's size, not the viewport — reusable responsive components.
- [`:has()`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/:has) selects a parent by its children (`form:has(:invalid)`), which used to need JavaScript.

### View transitions

- The [View Transition API](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API) animates between two DOM states: [`document.startViewTransition(update)`](https://developer.mozilla.org/en-US/docs/Web/API/Document/startViewTransition) snapshots old and new, then cross-fades or morphs elements sharing a [`view-transition-name`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/view-transition-name).
- Multi-page apps opt in to cross-document transitions with [`@view-transition { navigation: auto }`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@view-transition).

## Performance

### Core Web Vitals

| Metric | Good at p75 | Measures |
|---|---|---|
| [LCP](https://web.dev/articles/lcp) | ≤ 2.5 s | render time of the largest visible element |
| [INP](https://web.dev/articles/inp) | ≤ 200 ms | worst-ish interaction latency over the visit; [replaced FID in March 2024](https://web.dev/blog/inp-cwv-launch) |
| [CLS](https://web.dev/articles/cls) | ≤ 0.1 | unexpected layout shift |

### Fixing Web Vitals

- [LCP](https://web.dev/articles/optimize-lcp): [preload](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/preload) the hero image or font, cut render-blocking resources, fast [TTFB](https://web.dev/articles/ttfb).
- [INP](https://web.dev/articles/optimize-inp): break [long tasks](https://developer.mozilla.org/en-US/docs/Glossary/Long_task) (> 50 ms) and yield to the main thread ([`scheduler.yield()`](https://developer.mozilla.org/en-US/docs/Web/API/Scheduler/yield)).
- [CLS](https://web.dev/articles/optimize-cls): reserve space with `width`/`height` or [`aspect-ratio`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/aspect-ratio).

### Bundle size

- [Code splitting](https://developer.mozilla.org/en-US/docs/Glossary/Code_splitting) by route or with dynamic [`import()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/import) keeps the first bundle to what the first screen needs.
- [Tree shaking](https://developer.mozilla.org/en-US/docs/Glossary/Tree_shaking) needs ES modules; [`"sideEffects": false`](https://webpack.js.org/guides/tree-shaking/#mark-the-file-as-side-effect-free) also lets the bundler drop unused modules whole — list CSS and polyfill files as exceptions.

### Images

- [`srcset`/`sizes`](https://developer.mozilla.org/en-US/docs/Web/HTML/Guides/Responsive_images) let the browser pick a resolution per viewport; [AVIF/WebP](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Image_types) are much smaller than JPEG/PNG.
- [`loading="lazy"`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/img#loading) for below-the-fold images — never on the LCP image, which should get [`fetchpriority="high"`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/img#fetchpriority).

### Main-thread offloading

- [Web Workers](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API) run JS on another thread (no DOM access), talking via [`postMessage`](https://developer.mozilla.org/en-US/docs/Web/API/Worker/postMessage) ([structured clone](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Structured_clone_algorithm), or [transfer](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Transferable_objects) an `ArrayBuffer` for free).
- [`content-visibility: auto`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/content-visibility) skips layout and paint for off-screen sections.

### Resource hints

- [`preload`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/preload): fetch this exact resource now, it's needed for the current page.
- [`prefetch`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/prefetch): low-priority fetch for a likely next navigation.
- [`preconnect`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/preconnect): open DNS + TCP + TLS early when the resource URL isn't known yet.

## Caching

### Cache-Control directives

- [`no-cache`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control#no-cache) means revalidate every time, not "don't cache"; [`no-store`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control#no-store) means never store.
- [`max-age`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control#max-age) applies to every cache; [`s-maxage`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control#s-maxage) overrides it for shared caches (CDN).

### Hashed assets and validators

- Long `max-age` + [`immutable`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control#immutable) on content-hashed filenames (`app.a3f9c1.js`), with HTML served `no-cache` — each deploy is a new URL.
- [`ETag`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/ETag)/[`Last-Modified`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Last-Modified) let the server answer [`304 Not Modified`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/304) — saves the body, not the round trip.

### Browser storage

| Storage | Size | Notes |
|---|---|---|
| [Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies) | ~4 KB each | sent with every request to the domain |
| [`localStorage`](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage) | ~5 MB per origin | synchronous (blocks the main thread), strings only |
| [`sessionStorage`](https://developer.mozilla.org/en-US/docs/Web/API/Window/sessionStorage) | ~5 MB per origin | per tab, cleared when the tab closes |
| [IndexedDB](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API) | a [share of total disk](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria), per-origin quota | async, structured data, available in workers |
| [Cache API](https://developer.mozilla.org/en-US/docs/Web/API/Cache) | same origin quota as IndexedDB | request/response pairs, used by service workers |

Any [XSS](https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/XSS) can read all of them except [`HttpOnly`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#httponly) cookies — token storage in [security.md](security.md).

### Service workers

- [Service workers](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API) implement cache-first, network-first, or [stale-while-revalidate](https://web.dev/articles/offline-cookbook#stale-while-revalidate) strategies and offline support.
- A [waiting service worker](https://web.dev/articles/service-worker-lifecycle#waiting) is a common reason users keep seeing the old deploy.

## Accessibility

### Semantic HTML and ARIA

- Native elements (`<button>`, `<nav>`, `<label>`) come with keyboard, focus, and screen-reader behavior for free.
- [First rule of ARIA](https://www.w3.org/TR/using-aria/#rule1): don't use [ARIA](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA) when a native element already has the semantics.

### Focus management in SPAs

- Client-side navigation doesn't reset focus — move focus to the new view's heading on route change.
- Everything clickable must be keyboard-reachable with a [visible focus indicator](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html); a [`<dialog>`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog) opened with [`showModal()`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/showModal) makes the rest of the page [inert](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/inert).

### Contrast

- [WCAG AA](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html): 4.5:1 for normal text, 3:1 for large text and [UI components](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html).
- Never convey information by [color alone](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) (error states need text or an icon).
