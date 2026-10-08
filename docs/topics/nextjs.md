# Next.js

What experienced Next.js engineers forget before an interview, grouped by subtopic. Covers the App Router as of Next.js 16.4; React semantics (Server Components, Suspense, Actions) are in [react.md](react.md), and rendering strategies in general in [frontend.md](frontend.md).

## Rendering

### Static and dynamic rendering

- Without Cache Components, a route is prerendered at build unless it reads request-time data: [`cookies()`](https://nextjs.org/docs/app/api-reference/functions/cookies), [`headers()`](https://nextjs.org/docs/app/api-reference/functions/headers), [`searchParams`](https://nextjs.org/docs/app/api-reference/file-conventions/page#searchparams-optional), [`connection()`](https://nextjs.org/docs/app/api-reference/functions/connection), or [`fetch`](https://nextjs.org/docs/app/api-reference/functions/fetch) with `cache: 'no-store'`.
- Since [Next.js 15](https://nextjs.org/blog/next-15) a plain `fetch` isn't cached, yet a route that only uses it is still prerendered — the build-time response stays in the HTML until revalidation; `await connection()` forces request time.
- [Segment configs](https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config) choose explicitly: `export const dynamic = 'force-dynamic'`, `export const revalidate = 60` ([ISR](https://nextjs.org/docs/app/guides/incremental-static-regeneration)).
- [`generateStaticParams`](https://nextjs.org/docs/app/api-reference/functions/generate-static-params) prerenders chosen params; others render on first request unless [`dynamicParams = false`](https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/dynamicParams) makes them 404.

### Cache Components

- [`cacheComponents: true`](https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents) (Next.js 16, replaces `experimental.ppr` and `dynamicIO`) makes everything dynamic by default; cache explicitly with [`'use cache'`](https://nextjs.org/docs/app/api-reference/directives/use-cache).
- The build prerenders a static shell ([Partial Prerendering](https://nextjs.org/docs/app/glossary#partial-prerendering-ppr)); request-time data goes inside [`<Suspense>`](https://react.dev/reference/react/Suspense) and streams into the same response, or gets cached — a page with no static shell fails the build.
- In development, 16.3 validates that every navigation renders instantly and flags code that would block; [`export const instant = false`](https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/instant) accepts a blocking route, and on the highest segment also skips the static-shell check.
- [`export const ensureStatic = 'navigation'`](https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/ensureStatic) (16.4) fails the build if anything in the route would render at request time.
- The `dynamic`, `revalidate`, `fetchCache`, and `dynamicParams` segment configs are errors under Cache Components.
- Opt-in config in 16.x, but [`create-next-app` enables it since 16.4](https://nextjs.org/blog/next-16-4); planned as the default in Next.js 17.

### Streaming and `loading.tsx`

- [`loading.tsx`](https://nextjs.org/docs/app/api-reference/file-conventions/loading) wraps the segment's page in [`<Suspense>`](https://react.dev/reference/react/Suspense): navigation shows the fallback at once while the shared layout stays interactive.
- Once [streaming](https://nextjs.org/docs/app/guides/streaming) starts, the status (200) and headers are already sent — a [`notFound()`](https://nextjs.org/docs/app/api-reference/functions/not-found) or [`redirect()`](https://nextjs.org/docs/app/api-reference/functions/redirect) inside streamed content can't change the status code.
- Wrap each slow component in its own `<Suspense>` so it streams separately instead of blocking the whole page.

### Server-side waterfalls

- Sequential `await`s in one component, or a parent awaiting before rendering a child that fetches, run independent requests one after another.
- Start independent requests together: [`Promise.all`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/all), or create the promises first and await them later.
- [Suspense](https://react.dev/reference/react/Suspense) streams results as they arrive but doesn't parallelize fetches the code itself serializes.

### Client-only code

- Everything in `app/` is a Server Component until a [`'use client'`](https://nextjs.org/docs/app/api-reference/directives/use-client) boundary (see [react.md](react.md)).
- [`dynamic(() => import('./Map'), { ssr: false })`](https://nextjs.org/docs/app/guides/lazy-loading) skips server rendering for browser-only libraries, but only inside a Client Component — a Server Component errors.
- [`useSearchParams`](https://nextjs.org/docs/app/api-reference/functions/use-search-params) in a prerendered route client-renders everything up to the nearest `<Suspense>`; without one the production build fails.

## Caching

### Caching layers before Cache Components

| Layer | Where | Stores | Default since Next.js 15 |
|---|---|---|---|
| [Request memoization](https://nextjs.org/docs/app/guides/caching-without-cache-components#deduplicating-requests) | server, one render | duplicate `fetch` GETs | on |
| [Data Cache](https://nextjs.org/docs/app/guides/caching-without-cache-components#caching-fetch-requests) | server, persistent | `fetch` responses | off (on in 14) — opt in with `cache: 'force-cache'` or `next: { revalidate }` |
| Full Route Cache | server, persistent | HTML + RSC payload of prerendered routes | on for static routes |
| Router Cache | browser memory | RSC payload of visited and prefetched segments | layouts and loading states reused; pages 0 s ([`staleTimes.dynamic`](https://nextjs.org/docs/app/api-reference/config/next-config-js/staleTimes)); any revalidation in a Server Action clears it |

### `'use cache'`

- [`'use cache'`](https://nextjs.org/docs/app/api-reference/directives/use-cache) caches the return value of a function, component, or whole file; the key includes the build, the function, and its serialized arguments and closed-over values.
- Can't call `cookies()` or `headers()` inside — read them outside and pass the values in, or use [`'use cache: private'`](https://nextjs.org/docs/app/api-reference/directives/use-cache-private) (per user, kept only in browser memory).
- Default storage is in memory per server instance; [`'use cache: remote'`](https://nextjs.org/docs/app/api-reference/directives/use-cache-remote) stores entries in a shared [cache handler](https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheHandlers) across instances.
- [`cacheLife`](https://nextjs.org/docs/app/api-reference/functions/cacheLife) sets `stale` (client, minimum 30 s), `revalidate` (server, stale-while-revalidate), and `expire`; the default profile is 5 min / 15 min / never.
- [`cacheTag('posts')`](https://nextjs.org/docs/app/api-reference/functions/cacheTag) labels an entry for on-demand invalidation.

### Invalidation APIs

| API | Callable from | Effect |
|---|---|---|
| [`revalidateTag(tag, 'max')`](https://nextjs.org/docs/app/api-reference/functions/revalidateTag) | Server Actions, Route Handlers | marks tagged entries stale; the next visitor gets stale content while it refreshes (SWR); the one-argument form is deprecated in 16 |
| [`updateTag(tag)`](https://nextjs.org/docs/app/api-reference/functions/updateTag) | Server Actions only | expires entries and reads fresh data in the same request (read-your-writes) |
| [`revalidatePath('/blog')`](https://nextjs.org/docs/app/api-reference/functions/revalidatePath) | Server Actions, Route Handlers | invalidates everything rendered for a path |
| [`refresh()`](https://nextjs.org/docs/app/api-reference/functions/refresh) | Server Actions only | re-renders uncached data; the cache is untouched |
| [`router.refresh()`](https://nextjs.org/docs/app/api-reference/functions/use-router) | Client Components | re-fetches the current route's RSC payload, keeps client state |

### Request memoization

- Identical `fetch` GETs in one render pass run once across layouts, pages, and [`generateMetadata`](https://nextjs.org/docs/app/api-reference/functions/generate-metadata) — not in Route Handlers.
- For database and SDK calls, wrap the function in React [`cache()`](https://react.dev/reference/react/cache) so `generateMetadata` and the page share one query.
- Memoization lasts one request; persistence across requests needs [`'use cache'`](https://nextjs.org/docs/app/api-reference/directives/use-cache) or the Data Cache.

## Routing

### Special files

| File | Role |
|---|---|
| [`layout`](https://nextjs.org/docs/app/api-reference/file-conventions/layout) | shared UI; persists across navigations without re-rendering |
| [`template`](https://nextjs.org/docs/app/api-reference/file-conventions/template) | like a layout, but remounts when its segment changes |
| [`loading`](https://nextjs.org/docs/app/api-reference/file-conventions/loading) | `<Suspense>` fallback for the segment |
| [`error`](https://nextjs.org/docs/app/api-reference/file-conventions/error) | error boundary; must be a Client Component |
| [`not-found`](https://nextjs.org/docs/app/api-reference/file-conventions/not-found) | UI for `notFound()` |
| [`global-error`](https://nextjs.org/docs/app/api-reference/file-conventions/error#global-error) | replaces the root layout on error; renders its own `<html>` and `<body>` |
| [`route`](https://nextjs.org/docs/app/api-reference/file-conventions/route) | Route Handler; can't share a segment with `page` |
| [`default`](https://nextjs.org/docs/app/api-reference/file-conventions/default) | fallback for an unmatched parallel-route slot |

### Error handling

- [`error.tsx`](https://nextjs.org/docs/app/api-reference/file-conventions/error) wraps the segment's page and nested segments but not its own layout — a layout error goes to the parent's boundary, and a root layout error to `global-error.tsx`.
- [`retry()`](https://nextjs.org/docs/app/api-reference/file-conventions/error#retry) (stable in 16.3) re-fetches and re-renders Server Component children; [`reset()`](https://nextjs.org/docs/app/api-reference/file-conventions/error#reset) only clears the client error state, so it can't recover from a server error.
- [`catchError(Fallback)`](https://nextjs.org/docs/app/api-reference/functions/catchError) from `next/error` (16.3) builds component-level boundaries that let `redirect()` and `notFound()` pass through.
- In production, Server Component errors reach the client as a generic message plus a [`digest`](https://nextjs.org/docs/app/api-reference/file-conventions/error#errordigest) that matches the server log entry.

### Layouts and templates

- [Layouts](https://nextjs.org/docs/app/api-reference/file-conventions/layout) persist: navigating between child pages doesn't remount or re-render them, so their state survives and only changed segments are fetched (partial rendering).
- A Server Component layout can't read the current pathname or `searchParams` — use [`usePathname`](https://nextjs.org/docs/app/api-reference/functions/use-pathname)/[`useSearchParams`](https://nextjs.org/docs/app/api-reference/functions/use-search-params) in a Client Component.
- [`template.tsx`](https://nextjs.org/docs/app/api-reference/file-conventions/template) remounts when its own segment, including dynamic params, changes — not on deeper navigations or search-param changes; use it for enter animations or per-page effects.

### Dynamic segments

- [`params`](https://nextjs.org/docs/app/api-reference/file-conventions/dynamic-routes) and `searchParams` are Promises since Next.js 15 (`await params`); [16 removed sync access](https://nextjs.org/docs/app/guides/upgrading/version-16), as for `cookies()`, `headers()`, and [`draftMode()`](https://nextjs.org/docs/app/api-reference/functions/draft-mode).
- [`(group)`](https://nextjs.org/docs/app/api-reference/file-conventions/route-groups) folders organize routes without adding a URL segment and allow several root layouts; [`_folder`](https://nextjs.org/docs/app/getting-started/project-structure#private-folders) is private and never routed.
- [`next/root-params`](https://nextjs.org/docs/app/api-reference/functions/next-root-params) (16.3) reads root params like `[lang]` from any Server Component without prop drilling.

### Parallel and intercepting routes

- [`@slot`](https://nextjs.org/docs/app/api-reference/file-conventions/parallel-routes) folders render several pages in one layout at once (dashboard panels, modals); slots aren't URL segments.
- On a hard load, a slot with no match renders [`default.tsx`](https://nextjs.org/docs/app/api-reference/file-conventions/default) — required for every slot since Next.js 16, or the build fails.
- [Intercepting routes](https://nextjs.org/docs/app/api-reference/file-conventions/intercepting-routes) like `(.)photo/[id]` show a route inside the current layout on client navigation; a refresh or shared link renders the full page — the photo-modal pattern.
- `(..)` and `(...)` match one segment up and the app root — counted in route segments, not folders.

### Metadata

- A layout or page exports a static `metadata` object or an async [`generateMetadata`](https://nextjs.org/docs/app/api-reference/functions/generate-metadata) — Server Components only.
- Metadata from nested segments [merges shallowly](https://nextjs.org/docs/app/api-reference/functions/generate-metadata#merging): a child's `openGraph` replaces the parent's whole `openGraph`, so spread shared fields in.
- `generateMetadata` can call `redirect()` and `notFound()`, and its `fetch` calls are memoized with the page's.

### Navigation and prefetching

- Without Partial Prefetching, [`<Link>`](https://nextjs.org/docs/app/api-reference/components/link#prefetch) prefetches when it enters the viewport, in production only: static routes fully, dynamic routes down to the nearest `loading.tsx`; `prefetch={true}` fetches the full route.
- Next.js 16 downloads a shared layout once across many links and only [prefetches](https://nextjs.org/docs/app/guides/prefetching) segments not already cached.
- [Partial Prefetching](https://nextjs.org/docs/app/api-reference/config/next-config-js/partialPrefetching) (16.3, `partialPrefetching: true`) prefetches one reusable shell per route instead of a request per link; `prefetch={true}` adds the link's cached, URL-dependent content.
- In the App Router, [`useRouter`](https://nextjs.org/docs/app/api-reference/functions/use-router) comes from `next/navigation`; `next/router` belongs to the Pages Router.

## Server Actions

### Server Actions in Next.js

- A [`'use server'`](https://nextjs.org/docs/app/api-reference/directives/use-server) function passed to `<form action>` works without JavaScript ([progressive enhancement](https://developer.mozilla.org/en-US/docs/Glossary/Progressive_Enhancement)); event handlers can call it too.
- Always a POST; Next.js rejects requests whose `Origin` host doesn't match `x-forwarded-host` or `host` (CSRF check, see [security.md](security.md)); [`serverActions.allowedOrigins`](https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions#allowedorigins) adds extra hosts.
- The request body limit is 1 MB by default ([`serverActions.bodySizeLimit`](https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions#bodysizelimit)).
- After the mutation, call [`updateTag`](https://nextjs.org/docs/app/api-reference/functions/updateTag) or [`revalidatePath`](https://nextjs.org/docs/app/api-reference/functions/revalidatePath), then `redirect`; the response carries the updated RSC payload in the same round trip.
- [`after(fn)`](https://nextjs.org/docs/app/api-reference/functions/after) (stable since 15.1) runs logging or analytics after the response is sent — in Server Actions, Route Handlers, and Server Components.

### Closures and action IDs

- An inline Server Action can capture variables from the component that renders it; Next.js [encrypts](https://nextjs.org/docs/app/guides/data-security#closures-and-encryption) them before sending them to the client — still, never capture secrets.
- Action IDs are encrypted, non-deterministic, and regenerated per build; unused actions are dropped from the client bundle.
- Several self-hosted instances need the same [`NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`](https://nextjs.org/docs/app/guides/data-security#overwriting-encryption-keys-advanced) at build, or one instance can't decrypt another's closures ("Failed to find Server Action").

### `redirect` and `notFound`

- [`redirect()`](https://nextjs.org/docs/app/api-reference/functions/redirect) and [`notFound()`](https://nextjs.org/docs/app/api-reference/functions/not-found) work by throwing — call them outside `try`, or call [`unstable_rethrow(err)`](https://nextjs.org/docs/app/api-reference/functions/unstable_rethrow) first in the `catch`.
- `redirect` responds 307 by default; in a Server Action it becomes a client navigation (303 without JavaScript); [`permanentRedirect`](https://nextjs.org/docs/app/api-reference/functions/permanentRedirect) uses 308.
- In client event handlers use [`router.push`](https://nextjs.org/docs/app/api-reference/functions/use-router) — `redirect` only works during render and in server code.

### Route Handlers vs Server Actions

| | [Route Handler](https://nextjs.org/docs/app/api-reference/file-conventions/route) (`route.ts`) | [Server Action](https://nextjs.org/docs/app/guides/server-actions) |
|---|---|---|
| Caller | any HTTP client | your own React UI |
| Methods | GET, POST, PUT, DELETE, … | POST only |
| Use for | webhooks, public APIs, streamed responses, non-React clients | mutations from forms and buttons |
| Data fetching | yes | no — dispatched one at a time, uncached |
| Caching | GET only: opt-in since 15, on by default in 14 | never |

## Proxy and security

### `proxy.ts`

- [`proxy.ts`](https://nextjs.org/docs/app/api-reference/file-conventions/proxy) (renamed from `middleware.ts` in Next.js 16) runs before routing and caches on every matched request: redirects, rewrites, headers, A/B tests, i18n.
- It runs on the Node.js runtime only; `middleware.ts` still works for the [Edge runtime](https://nextjs.org/docs/app/api-reference/edge) but is deprecated.
- Narrow it with [`config.matcher`](https://nextjs.org/docs/app/api-reference/file-conventions/proxy#matcher), excluding `_next/static`, `_next/image`, and assets; there's one proxy file per project.

### Authorization placement

- [Proxy](https://nextjs.org/docs/app/api-reference/file-conventions/proxy) is for optimistic checks only (decode the session cookie, redirect) — it also runs on prefetches, so no database calls.
- Real authorization belongs in a [Data Access Layer](https://nextjs.org/docs/app/guides/data-security#data-access-layer) that verifies the session next to every query, Server Action, and Route Handler.
- [CVE-2025-29927](https://nvd.nist.gov/vuln/detail/CVE-2025-29927) (March 2025, CVSS 9.1): a spoofed `x-middleware-subrequest` header skipped middleware entirely; fixed in 15.2.3 and 14.2.25 — apps that checked auth only in middleware were open.

### Server-only code

- [`import 'server-only'`](https://nextjs.org/docs/app/getting-started/server-and-client-components#preventing-environment-poisoning) fails the build if a module with secrets or database access ends up in client code.
- Props passed to Client Components are serialized into the page — return [DTOs](https://nextjs.org/docs/app/guides/data-security#data-access-layer) from the data layer, not raw rows.

## Build and deployment

### Environment variables

- [`NEXT_PUBLIC_*`](https://nextjs.org/docs/app/guides/environment-variables#bundling-environment-variables-for-the-browser) values are inlined into client JS at build time — changing them at runtime does nothing, so one Docker image can't serve several environments that way.
- Other variables are server-only and read when the code runs: at build for prerendered routes, per request for dynamic ones.
- [Next.js 16 removed](https://nextjs.org/docs/app/guides/upgrading/version-16) `serverRuntimeConfig` and `publicRuntimeConfig` — use environment variables.

### Output modes and self-hosting

- [`output: 'standalone'`](https://nextjs.org/docs/app/api-reference/config/next-config-js/output#automatically-copying-traced-files) traces only the files and `node_modules` the server needs into `.next/standalone`; copy `public/` and `.next/static` yourself or serve them from a CDN.
- [`output: 'export'`](https://nextjs.org/docs/app/guides/static-exports#unsupported-features) emits static files only: no proxy, Server Actions, ISR, rewrites, cookies, or default image optimization.
- ISR and `'use cache'` entries live per instance by default — several instances need a shared [cache handler](https://nextjs.org/docs/app/guides/self-hosting#caching-and-isr).

### Version skew

- During a rolling deploy, old clients can request deleted chunks, call Server Action IDs the new build doesn't know, or fetch incompatible RSC payloads.
- [`deploymentId`](https://nextjs.org/docs/app/api-reference/config/next-config-js/deploymentId) tags assets (`?dpl=`) and navigations (`x-deployment-id`); a mismatch triggers a full reload instead of a client navigation.
- Vercel's [Skew Protection](https://vercel.com/docs/skew-protection) keeps old deployments reachable for a while; self-hosted setups keep old static assets around after a deploy.

### Turbopack and runtimes

- [Turbopack](https://nextjs.org/docs/app/api-reference/turbopack) is the default bundler for `next dev` and `next build` since Next.js 16; `--webpack` opts out.
- Its [file-system cache](https://nextjs.org/docs/app/api-reference/config/next-config-js/turbopackFileSystemCache) is on by default for dev since 16.1 and for builds since 16.3.
- `next build` no longer lints — [Next.js 16 removed `next lint`](https://nextjs.org/docs/app/guides/upgrading/version-16).
- The [Edge runtime](https://nextjs.org/docs/app/api-reference/edge) (`export const runtime = 'edge'`) runs on V8 isolates with Web APIs only — no `fs` or native modules; Node.js is the default and supports every feature.

## Built-in components

### `next/image`

- [`next/image`](https://nextjs.org/docs/app/api-reference/components/image) resizes and converts to WebP/AVIF on demand, lazy-loads by default, and needs `width`/`height` or [`fill`](https://nextjs.org/docs/app/api-reference/components/image#fill) to reserve space against layout shift.
- A `fill` image without [`sizes`](https://nextjs.org/docs/app/api-reference/components/image#sizes) is assumed to be `100vw` wide and downloads a larger file than needed.
- Mark the LCP image with `loading="eager"` or `fetchPriority="high"`; [`preload`](https://nextjs.org/docs/app/api-reference/components/image#preload) adds a `<link>` in `<head>` for early discovery; `priority` is deprecated since Next.js 16.
- Remote hosts must match [`images.remotePatterns`](https://nextjs.org/docs/app/api-reference/components/image#remotepatterns); `images.domains` is deprecated.
- Next.js 16 defaults: a 4-hour [`minimumCacheTTL`](https://nextjs.org/docs/app/api-reference/components/image#minimumcachettl), `qualities: [75]`, and local IPs blocked.

### `next/font`

- [`next/font`](https://nextjs.org/docs/app/api-reference/components/font) downloads Google Fonts at build time and serves them from your own domain — no runtime request to Google.
- Generates a fallback font with [`size-adjust`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@font-face/size-adjust) metrics, so the swap to the web font barely shifts layout.

### `next/script`

| Strategy | Loads |
|---|---|
| [`beforeInteractive`](https://nextjs.org/docs/app/api-reference/components/script#beforeinteractive) | before hydration, injected into the server HTML; root layout only |
| [`afterInteractive`](https://nextjs.org/docs/app/api-reference/components/script#afterinteractive) (default) | after some of the page hydrates |
| [`lazyOnload`](https://nextjs.org/docs/app/api-reference/components/script#lazyonload) | during browser idle time |
| [`worker`](https://nextjs.org/docs/app/api-reference/components/script#worker) (experimental) | in a web worker through [Partytown](https://partytown.qwik.dev/); Pages Router only |

## Pages Router

### Data fetching functions

| Pages Router | Runs | App Router equivalent |
|---|---|---|
| [`getStaticProps`](https://nextjs.org/docs/pages/api-reference/functions/get-static-props) | at build; again after `revalidate` seconds ([ISR](https://nextjs.org/docs/pages/guides/incremental-static-regeneration)) | a prerendered Server Component, or `'use cache'` |
| [`getServerSideProps`](https://nextjs.org/docs/pages/api-reference/functions/get-server-side-props) | on every request | a Server Component reading request data |
| [`getStaticPaths`](https://nextjs.org/docs/pages/api-reference/functions/get-static-paths) | at build | `generateStaticParams` |
| [`pages/api/*`](https://nextjs.org/docs/pages/building-your-application/routing/api-routes) | per request | Route Handlers |

### Pages Router differences

- Every page ships its JS and hydrates in full — no Server Components.
- [`_app`](https://nextjs.org/docs/pages/building-your-application/routing/custom-app) wraps every page (global layout and state); [`_document`](https://nextjs.org/docs/pages/building-your-application/routing/custom-document) customizes the HTML shell and renders only on the server.
- Nested layouts need the [per-page `getLayout` pattern](https://nextjs.org/docs/pages/building-your-application/routing/pages-and-layouts#per-page-layouts); the router is [`next/router`](https://nextjs.org/docs/pages/api-reference/functions/use-router).
- [`getStaticPaths` `fallback`](https://nextjs.org/docs/pages/api-reference/functions/get-static-paths#fallback-false): `false` → 404 for unknown paths; `true` → a fallback page first (`router.isFallback`); `'blocking'` → server-render the first request, then cache it.
- Both routers can coexist during a migration, but the same route in `app/` and `pages/` fails the build.
