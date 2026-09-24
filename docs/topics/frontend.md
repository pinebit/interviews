# Frontend Cheatsheet

The 20 most frequently asked frontend interview topics, with short answers. For language mechanics see [javascript.md](javascript.md) and [typescript.md](typescript.md), and for web vulnerabilities see [security.md](security.md).

## 1. CSR vs SSR vs SSG vs ISR — when do you use which?

**Client-side rendering (CSR)**: the server sends a near-empty HTML shell and a JS bundle; the browser fetches data and renders. Fast subsequent navigations, but slow first paint and poor SEO without extra work. **Server-side rendering (SSR)**: the server renders HTML per request — fast first paint and SEO-friendly, at the cost of server load and slower time-to-first-byte than a static file. **Static site generation (SSG)**: pages are rendered to HTML at build time and served from a CDN — fastest and cheapest, but content is only as fresh as the last build. **Incremental static regeneration (ISR)**: like SSG, but pages can be rebuilt on a schedule or on-demand after deploy, trading a little freshness for CDN-level speed on mostly-static content.

Rule of thumb: mostly-static content (marketing, docs) → SSG/ISR; content that must be fresh and indexable per request (product pages, feeds) → SSR; highly interactive, behind-login apps where SEO doesn't matter (dashboards) → CSR.

## 2. What is the critical rendering path?

The sequence from receiving bytes to pixels on screen: parse HTML into the **DOM**, parse CSS into the **CSSOM**, combine them into the **render tree** (visible nodes only), **layout/reflow** (compute size and position of every element), then **paint** (fill in pixels) and **composite** (layer things like `transform`/`opacity` onto the GPU).

CSS in the `<head>` blocks rendering (the browser won't paint with unknown styles); `<script>` tags block HTML parsing unless marked `async`/`defer` (which let the script load without stalling the parser, `defer` also guaranteeing execution order and running after parsing). Layout and paint are the expensive steps — changing `width`/`top`/layout properties triggers layout + paint + composite on every affected element (expensive). Changing `transform`/`opacity` can skip layout and paint entirely and go straight to composite (cheap, GPU-accelerated), but only if the browser has already promoted that element to its own compositor layer (e.g. via `will-change` or an existing 3D transform) — which is why animations should prefer `transform`/`opacity` and, for anything animated repeatedly, hint the browser to layer it in advance.

## 3. What is the virtual DOM, and why does diffing/reconciliation matter?

The **virtual DOM** is a lightweight in-memory tree of plain objects mirroring the UI. On a state change, the framework builds a new virtual tree, **diffs** it against the previous one, and applies only the minimal set of changes to the real DOM — because triggering layout and paint on the real DOM is much more expensive than comparing plain objects, and batching updates avoids the repeated forced reads/writes that cause **layout thrashing**.

**Keys** in a list tell the diffing algorithm which items are the same across renders (matched by key, not position), so reordering doesn't destroy and recreate every item's DOM node and state. Using array index as a key breaks this when the list is reordered or filtered — items can silently pick up the wrong state.

## 4. How do you manage state in a frontend app?

Match the tool to the **scope** of the state: **local component state** (a form field, a toggle) needs nothing more than the framework's built-in state; **shared state between a few nearby components** is usually best lifted to their common parent or passed via context; **global app state** (current user, theme, cart) needs a dedicated store (Redux, Zustand, Pinia) when many unrelated components read and write it; **server state** (data fetched from an API — has its own lifecycle of loading/error/staleness/caching) is a different problem from client state and is usually better handled by a data-fetching library (React Query, SWR, Apollo) than stuffed into a global store.

Prop drilling (passing a prop through several layers that don't use it, just to reach a deep child) is the signal to reach for context or a store — but only once it actually hurts; adding global state for a two-level prop pass is premature.

## 5. What are common state/effect pitfalls in component frameworks (e.g. React hooks)?

**Stale closures**: an effect or callback captures a variable's value at the time it was created; if that variable changes later but isn't in the dependency array, the callback keeps using the old value. **Missing/incorrect dependencies**: omitting a dependency to "stop it re-running" hides real bugs — the fix is usually to restructure the effect (e.g. use a ref, or derive the value inside the effect) rather than lie to the dependency array. **Effects that should be derived state**: computing a value from props/state inside `useEffect` + `setState` causes an extra render and a flash of stale UI — just compute it directly during render.

**Infinite loops**: an effect that updates a piece of state it also depends on, without a condition, re-fires forever. Cleanup functions (returned from an effect) matter for anything with a lifetime beyond one render — subscriptions, timers, event listeners — otherwise they leak across re-renders and unmounts.

## 6. How does browser caching work for a web app?

**HTTP caching**: `Cache-Control: max-age=<seconds>` lets the browser reuse a response without asking the server; `no-cache` means revalidate every time (via `ETag`/`Last-Modified` and a `304 Not Modified` round trip if unchanged); `no-store` means never cache. Static assets (JS/CSS bundles) are typically served with a long `max-age` plus a **content hash in the filename** (`app.a3f9c1.js`), so the filename itself changes whenever the content does — the browser can cache "forever" safely, and a new deploy is just a new filename referenced by fresh HTML (served with `no-cache` so the reference always updates).

A **service worker** sits between the app and the network and can implement custom caching strategies (cache-first, network-first, stale-while-revalidate) and offline support — powerful, but a stale service worker can also be the reason users don't see a new deploy until they hard-refresh.

## 7. What is code splitting, and why does bundle size matter?

**Code splitting** breaks one large JS bundle into smaller chunks loaded on demand (per route, or lazily on user interaction) instead of shipping the entire app upfront. Every extra kilobyte delays **parse and execute** time, which is especially costly on slower mobile CPUs and networks — a large bundle directly hurts time-to-interactive even if the network is fast.

Techniques: route-based splitting (load a page's code only when navigating to it), lazy-loading heavy components (a chart library, a rich text editor) behind `import()`, and **tree shaking** (the bundler removes exports that are never imported — requires ES module syntax and side-effect-free code to work reliably). Measure with a bundle analyzer before guessing what to split.

## 8. What are Core Web Vitals?

Google's user-centric performance metrics: **LCP (Largest Contentful Paint)** — time until the largest visible element renders, a proxy for "does the page feel loaded" (target < 2.5s); **INP (Interaction to Next Paint)** — a single value summarizing responsiveness across the whole page visit (roughly the worst interaction, ignoring outliers), replacing FID as the responsiveness metric (target < 200ms), and reported at the 75th percentile across real users in field data; **CLS (Cumulative Layout Shift)** — how much visible content unexpectedly shifts during load (target < 0.1), usually caused by images/ads/fonts without reserved space.

Common fixes: set explicit `width`/`height` (or `aspect-ratio`) on images to prevent CLS, preload the LCP image/font, avoid render-blocking resources, and break up long JavaScript tasks to keep INP low.

## 9. How do you make a UI accessible?

Use **semantic HTML** first (`<button>`, `<nav>`, `<label>`) — it gives you keyboard interaction, focus handling, and screen-reader semantics for free; reaching for ARIA to patch a `<div>` that's acting like a button is a last resort, not a default. Ensure everything reachable by mouse is also reachable and operable by **keyboard** (tab order, visible focus states, `Escape` closes modals). Give every image meaningful `alt` text (or `alt=""` if purely decorative), label every form input, and keep color contrast at or above WCAG AA (4.5:1 for normal text).

Test with a keyboard only (unplug the mouse) and a screen reader (VoiceOver/NVDA) — many issues (a modal that doesn't trap focus, a custom dropdown invisible to assistive tech) only surface that way, not from an automated linter alone.

## 10. How does CSS layout work?

The **box model**: every element is `content` + `padding` + `border` + `margin`. `box-sizing: border-box` (widely used as a reset) makes `width`/`height` include padding and border, matching how most people intuitively size things. **Specificity** resolves conflicting rules of equal cascade origin: inline style > ID > class/attribute/pseudo-class > element. A `!important` declaration jumps ahead of normal rules regardless of specificity, but two competing `!important` rules are still resolved by specificity between themselves, and cascade layers/origin (e.g. user-agent vs author styles) can still take precedence over it — so it doesn't override literally everything, and it's best avoided.

**Flexbox** lays out items along one axis (row or column), ideal for a toolbar, nav bar, or centering content. **Grid** lays out items on two axes at once (rows and columns together), ideal for overall page layout or a card grid. Rule of thumb: flexbox for a single row/column of items, grid for a two-dimensional layout.

## 11. What is responsive design?

Design that adapts to different viewport sizes rather than shipping a fixed layout: fluid layouts (`%`, `fr`, `flex`) instead of fixed pixel widths, **media queries** (`@media (min-width: 768px)`) to change layout at breakpoints, and a **mobile-first** approach (base styles target the smallest screen, media queries add complexity for larger ones) — generally easier to reason about than starting desktop-first and fighting overrides downward.

Related: responsive images (`srcset`/`sizes` so the browser picks an appropriately sized image instead of downloading a huge one for a small slot), relative units (`rem` for type so it respects user font-size preferences), and testing real devices, not just a resized desktop browser window — touch targets and viewport quirks differ.

## 12. How do you handle forms and validation on the frontend?

Validate at multiple points: **on blur/submit** for immediate, helpful feedback (validating on every keystroke while a field is still empty just annoys the user), and always again **server-side** — client-side validation is a UX convenience, never a security boundary, since it's trivial to bypass (see Q17 for the controlled/uncontrolled input tradeoff that shapes how validation state is tracked).

Prefer a **schema** (Zod, Yup) shared between field-level checks and submit-time validation so the rules live in one place instead of being duplicated per field. For complex forms, a form library (React Hook Form, Formik) handles validation timing, error state, and re-render performance so you don't reinvent it — React Hook Form in particular defaults to uncontrolled inputs internally specifically to avoid a re-render on every keystroke in a large form.

## 13. How does client-side routing work in a single-page app?

The router intercepts navigation (link clicks, back/forward) and updates the URL via the **History API** (`pushState`/`replaceState`) without a full page reload, then renders the matching component — giving app-like navigation while keeping the URL shareable and bookmarkable.

Gotchas: a full page **reload/direct URL hit** goes straight to the server, which must be configured to serve the SPA's `index.html` for unknown paths (otherwise a refresh on `/profile` 404s) — the router only takes over once the JS has loaded. **Code-split routes** (Q7) mean navigating to a new route may trigger a lazy chunk load — show a loading state for that gap.

## 14. What is CORS, and why does it block frontend requests?

**CORS (Cross-Origin Resource Sharing)** is a browser security mechanism: by default, JavaScript running on `origin-a.com` cannot read responses from `api-b.com` (a different origin = different scheme, host, or port) unless the server at `api-b.com` explicitly allows it via `Access-Control-Allow-Origin` (and related headers). It protects **users**, not the API — the request often still reaches the server and executes; CORS only blocks the **browser from handing the response back to the calling script**, so it's not a substitute for server-side auth.

**Simple requests** (GET/POST with plain headers) go straight through with the origin checked on the response; requests with custom headers, non-simple content types, or methods like `PUT`/`DELETE` trigger a **preflight** `OPTIONS` request first, which the server must also answer correctly. `Access-Control-Allow-Origin: *` cannot be combined with credentials (cookies) — a specific origin must be echoed back for credentialed requests.

## 15. How do you prevent XSS on the frontend?

**XSS (cross-site scripting)** happens when untrusted data is rendered as executable HTML/JS. Modern frameworks (React, Vue, Angular) **escape text content by default**, so `{userInput}` in JSX is safe — the danger is explicit opt-outs like `dangerouslySetInnerHTML` / `v-html` / `innerHTML`, which must only ever receive sanitized HTML (e.g. via DOMPurify), never raw user input.

Other angles: never build URLs for `href`/`src` from unvalidated user input (can enable `javascript:` URIs), and set a **Content-Security-Policy** header as defense-in-depth so even a missed escape has a much harder time executing. See [security.md](security.md) for XSS types and CSRF, which is primarily a backend/cookie concern but affects how the frontend sends authenticated requests.

## 16. How do you manage authentication state on the frontend?

Store tokens where they're least exposed to the risk that matters most: an **httpOnly cookie** (set by the server, inaccessible to JavaScript) protects the token from being stolen via **XSS**, but is vulnerable to **CSRF** unless paired with `SameSite` and a CSRF token — the standard choice for most web apps. Storing a token in **memory** (a JS variable, lost on refresh) avoids CSRF and keeps the token out of persistent storage an injected script could exfiltrate at leisure, but doesn't eliminate XSS risk entirely — a script running on the page can still act through the authenticated app or intercept the token in use — and it requires re-authenticating (silently, via a refresh flow) on every page load. Storing a token in **`localStorage`** is the least safe option — any injected script (XSS) can read it directly — and is best avoided for anything sensitive despite being the easiest to implement.

Whatever the storage, keep **access tokens short-lived** and use a **refresh token** (itself httpOnly and tightly scoped) to get new ones silently, so a leaked access token has a small blast radius.

## 17. Controlled vs uncontrolled components?

A **controlled** component's value lives in the framework's state and is passed back in as a prop (`value={state}` + `onChange`) — the framework is the single source of truth, enabling validation-as-you-type, formatting, and conditional UI driven by that value. An **uncontrolled** component holds its own value internally (native DOM state), read only when needed via a ref — less code and fewer re-renders, but you lose live visibility into the value.

Neither is strictly better: controlled inputs are the default when the value drives other UI (character counters, dependent fields, live validation); uncontrolled inputs (or an uncontrolled-by-default form library) suit large or simple forms, file inputs (which can't be controlled — the browser owns the file value), and integrating with non-framework code.

## 18. How do you test frontend code?

**Unit tests**: pure functions and hooks in isolation (Jest/Vitest) — fast, no DOM needed for logic-only code. **Component tests**: render a component in a simulated DOM (React Testing Library, Vue Test Utils) and assert on behavior from the user's perspective (what's on screen, what happens on click) rather than implementation details (internal state, private methods) — testing implementation details makes tests break on harmless refactors. **End-to-end tests**: drive a real browser through a real user flow (Playwright, Cypress) against a running app — catches integration issues unit/component tests can't (routing, real network calls, real CSS), but slower and more brittle, so reserve for critical user journeys (checkout, login).

Favor the same **test pyramid** shape as backend testing (many unit/component tests, fewer e2e) for the same reason: fast feedback and easier failure diagnosis.

## 19. Composition vs inheritance in UI component design?

Modern frontend frameworks favor **composition**: build complex UI by combining small, focused components (passing components as props/children — e.g. a `<Modal>` that renders whatever `children` it's given) rather than an inheritance hierarchy (`SpecialButton extends Button`). Composition is more flexible — a component can be composed differently in different contexts without a rigid class hierarchy dictating its shape — and matches how frameworks like React are designed to work (no traditional class inheritance between components is expected).

Common composition patterns: **children/slots** for "wrap arbitrary content," **render props / scoped slots** for "let the parent control how something renders," and **compound components** (e.g. `<Tabs><Tabs.Tab/><Tabs.Panel/></Tabs>`) for a group of components that implicitly share state via context.

## 20. How do you debug a frontend performance issue?

Start in the browser's **Performance panel**: record a trace of the slow interaction and look at the flame graph for long tasks (anything over ~50ms blocks the main thread and delays input response), excessive re-renders, or layout thrashing (repeated read-then-write of layout properties in a loop, forcing synchronous reflow). The **Lighthouse**/PageSpeed report surfaces lab-based performance issues (LCP, CLS, and TBT as a proxy for responsiveness — Lighthouse's default run doesn't measure INP directly, since INP needs real interactions) with concrete suggestions; for real INP numbers, use field data (CrUX, `web-vitals` library, or a RUM tool). Framework devtools (React DevTools Profiler) show which components re-rendered and why — often the fix is memoization (`useMemo`/`React.memo`) or fixing a prop that changes identity every render (a new object/array/function literal passed as a prop).

For **memory leaks**: take two heap snapshots (Memory panel) before and after repeating an action (open/close a modal many times) and diff them — growing detached DOM nodes or retained closures usually point to a missing cleanup (an event listener or subscription never removed, see Q5).
</content>
