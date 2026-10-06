# Next.js

What experienced Next.js engineers forget before an interview, grouped by subtopic. Covers the App Router as of Next.js 16.3; React semantics (Server Components, Suspense, Actions) are in [react.md](react.md), and rendering strategies in general in [frontend.md](frontend.md).

## Rendering

### Static and dynamic rendering

- Without Cache Components, a route is **prerendered at build** unless it reads request-time data: `cookies()`, `headers()`, `searchParams`, `connection()`, or `fetch` with `cache: 'no-store'`.
- Since **Next.js 15** a plain `fetch` isn't cached, yet a route that only uses it is still prerendered — the build-time response stays in the HTML until revalidation; `await connection()` forces request time.
- Segment configs choose explicitly: `export const dynamic = 'force-dynamic'`, `export const revalidate = 60` (ISR).
- `generateStaticParams` prerenders chosen params; others render on first request unless `dynamicParams = false` makes them 404.

### Cache Components

- **`cacheComponents: true`** (Next.js 16, replaces `experimental.ppr` and `dynamicIO`) makes everything dynamic by default; cache explicitly with `'use cache'`.
- The build prerenders a **static shell** (Partial Prerendering); request-time data goes inside `<Suspense>` and streams into the same response, or gets cached — a page with no static shell fails the build.
- In development, 16.3 validates that every navigation renders instantly and flags code that would block; `export const instant = false` accepts a blocking route.
- The `dynamic`, `revalidate`, `fetchCache`, and `dynamicParams` segment configs are errors under Cache Components.
- Opt-in in 16.x; planned as the default in a future major.

### Streaming and `loading.tsx`

- **`loading.tsx`** wraps the segment's page in `<Suspense>`: navigation shows the fallback at once while the shared layout stays interactive.
- Once streaming starts, the status (**200**) and headers are already sent — a `notFound()` or `redirect()` inside streamed content can't change the status code.
- Wrap each slow component in its own `<Suspense>` so it streams separately instead of blocking the whole page.

### Server-side waterfalls

- Sequential `await`s in one component, or a parent awaiting before rendering a child that fetches, run independent requests one after another.
- Start independent requests together: **`Promise.all`**, or create the promises first and await them later.
- Suspense streams results as they arrive but doesn't parallelize fetches the code itself serializes.

### Client-only code

- Everything in `app/` is a Server Component until a `'use client'` boundary (see [react.md](react.md)).
- `dynamic(() => import('./Map'), { ssr: false })` skips server rendering for browser-only libraries, but only inside a Client Component — a Server Component errors.
- **`useSearchParams`** in a prerendered route client-renders everything up to the nearest `<Suspense>`; without one the production build fails.

## Caching

### Caching layers before Cache Components

| Layer | Where | Stores | Default since Next.js 15 |
|---|---|---|---|
| Request memoization | server, one render | duplicate `fetch` GETs | on |
| Data Cache | server, persistent | `fetch` responses | **off** (on in 14) — opt in with `cache: 'force-cache'` or `next: { revalidate }` |
| Full Route Cache | server, persistent | HTML + RSC payload of prerendered routes | on for static routes |
| Router Cache | browser memory | RSC payload of visited and prefetched segments | layouts and loading states reused; pages **0 s** (`staleTimes.dynamic`); any revalidation in a Server Action clears it |

### `'use cache'`

- Caches the return value of a function, component, or whole file; the key includes the build, the function, and its serialized **arguments and closed-over values**.
- Can't call `cookies()` or `headers()` inside — read them outside and pass the values in, or use `'use cache: private'` (per user, kept only in browser memory).
- Default storage is in memory per server instance; **`'use cache: remote'`** stores entries in a shared cache handler across instances.
- `cacheLife` sets `stale` (client, minimum 30 s), `revalidate` (server, stale-while-revalidate), and `expire`; the **default profile** is 5 min / 15 min / never.
- `cacheTag('posts')` labels an entry for on-demand invalidation.

### Invalidation APIs

| API | Callable from | Effect |
|---|---|---|
| `revalidateTag(tag, 'max')` | Server Actions, Route Handlers | marks tagged entries stale; the next visitor gets stale content while it refreshes (SWR); the one-argument form is deprecated in 16 |
| `updateTag(tag)` | Server Actions only | expires entries and reads fresh data in the same request (**read-your-writes**) |
| `revalidatePath('/blog')` | Server Actions, Route Handlers | invalidates everything rendered for a path |
| `refresh()` | Server Actions only | re-renders uncached data; the cache is untouched |
| `router.refresh()` | Client Components | re-fetches the current route's RSC payload, keeps client state |

### Request memoization

- Identical `fetch` GETs in one render pass run once across layouts, pages, and `generateMetadata` — not in Route Handlers.
- For database and SDK calls, wrap the function in React **`cache()`** so `generateMetadata` and the page share one query.
- Memoization lasts **one request**; persistence across requests needs `'use cache'` or the Data Cache.

## Routing

### Special files

| File | Role |
|---|---|
| `layout` | shared UI; persists across navigations without re-rendering |
| `template` | like a layout, but remounts when its segment changes |
| `loading` | `<Suspense>` fallback for the segment |
| `error` | error boundary; must be a Client Component |
| `not-found` | UI for `notFound()` |
| `global-error` | replaces the root layout on error; renders its own `<html>` and `<body>` |
| `route` | Route Handler; can't share a segment with `page` |
| `default` | fallback for an unmatched parallel-route slot |

### Error handling

- `error.tsx` wraps the segment's page and nested segments but **not its own layout** — a layout error goes to the parent's boundary, and a root layout error to `global-error.tsx`.
- **`retry()`** re-fetches and re-renders Server Component children; `reset()` only clears the client error state, so it can't recover from a server error.
- `catchError(Fallback)` from `next/error` (16.3) builds component-level boundaries that let `redirect()` and `notFound()` pass through.
- In production, Server Component errors reach the client as a generic message plus a **`digest`** that matches the server log entry.

### Layouts and templates

- Layouts persist: navigating between child pages doesn't remount or re-render them, so their state survives and only changed segments are fetched (**partial rendering**).
- A Server Component layout can't read the current pathname or `searchParams` — use `usePathname`/`useSearchParams` in a Client Component.
- `template.tsx` remounts when its own segment, including dynamic params, changes — not on deeper navigations or search-param changes; use it for enter animations or per-page effects.

### Dynamic segments

- **`params` and `searchParams` are Promises** since Next.js 15 (`await params`); 16 removed sync access, as for `cookies()`, `headers()`, and `draftMode()`.
- `(group)` folders organize routes without adding a URL segment and allow several root layouts; `_folder` is private and never routed.
- `next/root-params` (16.3) reads root params like `[lang]` from any Server Component without prop drilling.

### Parallel and intercepting routes

- **`@slot`** folders render several pages in one layout at once (dashboard panels, modals); slots aren't URL segments.
- On a hard load, a slot with no match renders `default.tsx` — required for every slot since **Next.js 16**, or the build fails.
- **Intercepting routes** like `(.)photo/[id]` show a route inside the current layout on client navigation; a refresh or shared link renders the full page — the photo-modal pattern.
- `(..)` and `(...)` match one segment up and the app root — counted in route segments, not folders.

### Metadata

- A layout or page exports a static `metadata` object or an async **`generateMetadata`** — Server Components only.
- Metadata from nested segments merges **shallowly**: a child's `openGraph` replaces the parent's whole `openGraph`, so spread shared fields in.
- `generateMetadata` can call `redirect()` and `notFound()`, and its `fetch` calls are memoized with the page's.

### Navigation and prefetching

- Without Partial Prefetching, `<Link>` prefetches when it enters the viewport, **in production only**: static routes fully, dynamic routes down to the nearest `loading.tsx`; `prefetch={true}` fetches the full route.
- Next.js 16 downloads a shared layout once across many links and only prefetches segments not already cached.
- **Partial Prefetching** (16.3, `partialPrefetching: true`) prefetches one reusable shell per route instead of a request per link; `prefetch={true}` adds the link's cached, URL-dependent content.
- In the App Router, `useRouter` comes from `next/navigation`; `next/router` belongs to the Pages Router.

## Server Actions

### Server Actions in Next.js

- A `'use server'` function passed to `<form action>` works **without JavaScript** (progressive enhancement); event handlers can call it too.
- Always a **POST**; Next.js rejects requests whose `Origin` host doesn't match `x-forwarded-host` or `host` (CSRF check); `serverActions.allowedOrigins` adds extra hosts.
- The request body limit is **1 MB** by default (`serverActions.bodySizeLimit`).
- After the mutation, call `updateTag` or `revalidatePath`, then `redirect`; the response carries the updated RSC payload in the same round trip.
- `after(fn)` (stable since 15.1) runs logging or analytics after the response is sent — in Server Actions, Route Handlers, and Server Components.

### Closures and action IDs

- An inline Server Action can capture variables from the component that renders it; Next.js **encrypts** them before sending them to the client — still, never capture secrets.
- Action IDs are encrypted, non-deterministic, and regenerated per build; unused actions are dropped from the client bundle.
- Several self-hosted instances need the same **`NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`** at build, or one instance can't decrypt another's closures ("Failed to find Server Action").

### `redirect` and `notFound`

- **`redirect()`** and `notFound()` work by throwing — call them outside `try`, or call `unstable_rethrow(err)` first in the `catch`.
- `redirect` responds 307 by default; in a Server Action it becomes a client navigation (303 without JavaScript); `permanentRedirect` uses 308.
- In client event handlers use `router.push` — `redirect` only works during render and in server code.

### Route Handlers vs Server Actions

| | Route Handler (`route.ts`) | Server Action |
|---|---|---|
| Caller | any HTTP client | your own React UI |
| Methods | GET, POST, PUT, DELETE, … | POST only |
| Use for | webhooks, public APIs, streamed responses, non-React clients | mutations from forms and buttons |
| Data fetching | yes | no — dispatched one at a time, uncached |
| Caching | GET only: opt-in since 15, on by default in 14 | never |

## Proxy and security

### `proxy.ts`

- **`proxy.ts`** (renamed from `middleware.ts` in Next.js 16) runs before routing and caches on every matched request: redirects, rewrites, headers, A/B tests, i18n.
- It runs on the **Node.js runtime** only; `middleware.ts` still works for the Edge runtime but is deprecated.
- Narrow it with `config.matcher`, excluding `_next/static`, `_next/image`, and assets; there's one proxy file per project.

### Authorization placement

- Proxy is for **optimistic checks** only (decode the session cookie, redirect) — it also runs on prefetches, so no database calls.
- Real authorization belongs in a **Data Access Layer** that verifies the session next to every query, Server Action, and Route Handler.
- **CVE-2025-29927** (March 2025, CVSS 9.1): a spoofed `x-middleware-subrequest` header skipped middleware entirely; fixed in 15.2.3 and 14.2.25 — apps that checked auth only in middleware were open.

### Server-only code

- `import 'server-only'` fails the build if a module with secrets or database access ends up in client code.
- Props passed to Client Components are serialized into the page — return DTOs from the data layer, not raw rows.

## Build and deployment

### Environment variables

- **`NEXT_PUBLIC_*`** values are inlined into client JS at **build time** — changing them at runtime does nothing, so one Docker image can't serve several environments that way.
- Other variables are server-only and read when the code runs: at build for prerendered routes, per request for dynamic ones.
- Next.js 16 removed `serverRuntimeConfig` and `publicRuntimeConfig` — use environment variables.

### Output modes and self-hosting

- **`output: 'standalone'`** traces only the files and `node_modules` the server needs into `.next/standalone`; copy `public/` and `.next/static` yourself or serve them from a CDN.
- **`output: 'export'`** emits static files only: no proxy, Server Actions, ISR, rewrites, cookies, or default image optimization.
- ISR and `'use cache'` entries live per instance by default — several instances need a shared cache handler.

### Version skew

- During a rolling deploy, old clients can request deleted chunks, call Server Action IDs the new build doesn't know, or fetch incompatible RSC payloads.
- **`deploymentId`** tags assets (`?dpl=`) and navigations (`x-deployment-id`); a mismatch triggers a full reload instead of a client navigation.
- Vercel's Skew Protection keeps old deployments reachable for a while; self-hosted setups keep old static assets around after a deploy.

### Turbopack and runtimes

- **Turbopack** is the default bundler for `next dev` and `next build` since **Next.js 16**; `--webpack` opts out.
- Its file-system cache is on by default for dev since 16.1 and for builds since 16.3.
- `next build` no longer lints — Next.js 16 removed `next lint`.
- The Edge runtime (`export const runtime = 'edge'`) runs on V8 isolates with Web APIs only — no `fs` or native modules; Node.js is the default and supports every feature.

## Built-in components

### `next/image`

- Resizes and converts to WebP/AVIF on demand, lazy-loads by default, and needs `width`/`height` or **`fill`** to reserve space against layout shift.
- A `fill` image without `sizes` is assumed to be `100vw` wide and downloads a larger file than needed.
- Mark the LCP image with **`preload`**, which replaced `priority` (deprecated in Next.js 16).
- Remote hosts must match `images.remotePatterns`; `images.domains` is deprecated.
- Next.js 16 defaults: a 4-hour `minimumCacheTTL`, `qualities: [75]`, and local IPs blocked.

### `next/font`

- Downloads Google Fonts at **build time** and serves them from your own domain — no runtime request to Google.
- Generates a fallback font with `size-adjust` metrics, so the swap to the web font barely shifts layout.

### `next/script`

| Strategy | Loads |
|---|---|
| `beforeInteractive` | before hydration, injected into the server HTML; root layout only |
| `afterInteractive` (default) | after some of the page hydrates |
| `lazyOnload` | during browser idle time |
| `worker` (experimental) | in a web worker through Partytown; Pages Router only |

## Pages Router

### Data fetching functions

| Pages Router | Runs | App Router equivalent |
|---|---|---|
| `getStaticProps` | at build; again after `revalidate` seconds (ISR) | a prerendered Server Component, or `'use cache'` |
| `getServerSideProps` | on every request | a Server Component reading request data |
| `getStaticPaths` | at build | `generateStaticParams` |
| `pages/api/*` | per request | Route Handlers |

### Pages Router differences

- Every page ships its JS and hydrates in full — no Server Components.
- `_app` wraps every page (global layout and state); `_document` customizes the HTML shell and renders only on the server.
- Nested layouts need the per-page `getLayout` pattern; the router is `next/router`.
- `getStaticPaths` `fallback`: `false` → 404 for unknown paths; `true` → a fallback page first (`router.isFallback`); `'blocking'` → server-render the first request, then cache it.
- Both routers can coexist during a migration, but the same route in `app/` and `pages/` fails the build.
