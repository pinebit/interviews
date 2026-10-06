# React

What experienced React engineers forget before an interview, grouped by subtopic. Covers React 19.3; for rendering strategies, the browser pipeline, and Web Vitals see [frontend.md](frontend.md); for the framework layer see [nextjs.md](nextjs.md).

## Rendering model

### Render and commit

- **Render phase**: React calls components to compute the next tree; **commit phase**: it applies DOM changes, runs layout effects, then passive effects (usually after paint).
- Render must be **pure** — it may run more than once for one commit (Strict Mode, interrupted concurrent renders).
- A component re-renders on its own state change, a parent re-render (unless memoized), or a consumed context value change — never because a prop changed on its own.

### Reconciliation and keys

- A different element **type** at the same position unmounts the old subtree and its state; the same type updates in place.
- **Keys** match list items across renders; an array index as key attaches the wrong state after reorder or filter.
- A component defined inside another component is a new type on every render, so its subtree remounts and loses state each time.

### State and tree position

- State belongs to a **position** in the tree, not to a variable: `{isAdmin ? <Form /> : <Form />}` keeps one shared state.
- Changing a component's **`key`** remounts it and resets its state — the clean way to reset a form when the selected item changes.

### State snapshots and batching

- State is a **snapshot** per render: `setCount(count + 1)` twice adds 1; the updater form `setCount(c => c + 1)` twice adds 2.
- **Automatic batching** (React 18+) merges all updates from one tick into one render, including in timeouts and promises.
- `flushSync(() => setValue(x))` opts out: it renders and commits synchronously before returning.
- Setting state to an `Object.is`-equal value skips the re-render — mutating an object in place and setting it again does nothing.
- `useRef` holds a mutable value across renders without triggering a re-render; don't read or write it during render.

### Fiber and concurrent rendering

- **Fiber** splits rendering into interruptible units: the render phase can pause, restart, or be discarded; the commit phase is synchronous.
- Time slicing applies only to updates marked non-urgent (transitions, deferred values); other updates render without yielding.
- **Tearing**: an interrupted render can read different values from a mutable external store in different components — `useSyncExternalStore` prevents it.

## Hooks

### Rules of Hooks

- React identifies each hook's state by **call order**, so hooks run at the top level in the same order every render — no conditions, loops, or calls after an early return.
- **`use`** is the exception: it may be called inside `if` and loops, but not inside `try/catch`.
- Custom hooks share logic, not state: each call gets its own state.

### Effect timing

| Hook | Runs | Use for |
|---|---|---|
| `useEffect` | after commit, usually after paint | subscriptions, syncing with external systems |
| `useLayoutEffect` | after DOM mutation, **before paint** (blocks it) | measuring layout and re-rendering without flicker (tooltips) |
| `useInsertionEffect` | before layout effects | CSS-in-JS style injection |

### Stale closures

- An effect or callback sees the values from the render that created it; a value missing from the dependency array stays **stale**.
- Fix by restructuring (a ref, a functional `setState`, moving the logic into the effect, an Effect Event) — not by silencing the lint rule.

### Effect Events

- **`useEffectEvent`** (stable in 19.2) wraps logic that must read the latest props or state without re-running the effect: `onConnected` sees the current `theme` while the effect depends only on `roomId`.
- Effect Events stay out of dependency arrays and may only be called from effects in the same component.
- Only for code that is conceptually an event fired by the effect — not a way to silence the lint rule.

### Unnecessary effects

- Deriving state inside an effect + `setState` causes an extra render and a flash — **compute it during render**.
- Logic caused by a user action belongs in the event handler, not in an effect watching a flag.
- Every subscription, timer, or listener an effect creates needs a **cleanup** function.

### Data fetching in effects

- Responses can arrive **out of order**: ignore stale ones in the effect cleanup (an `ignore` flag or `AbortController`), or a slow earlier request overwrites newer data.
- Effect-based fetching creates **waterfalls** (parent fetches → child mounts → child fetches); hoist fetching to route loaders, Server Components, or a query library.
- Strict Mode runs setup → cleanup → setup in development, so the request fires twice; the cleanup is what makes the first response get ignored.

### `useSyncExternalStore`

- Subscribes components to an external store (a browser API, Redux, Zustand) with no **tearing** under concurrent rendering.
- `getSnapshot` must return the **same value** while the store is unchanged — returning a new object on each call re-renders forever.
- `getServerSnapshot` supplies the value for server rendering and hydration.

## State management

### Context performance

- Every consumer re-renders when the provider's `value` changes **identity** — an inline object literal changes it on every render.
- Memoize the value, split fast- and slow-changing state into separate contexts, or use a store with selectors (`useSyncExternalStore`, Zustand) so components subscribe to slices.
- Context suits low-frequency values (theme, locale, current user), not fast-changing shared state.

### Server state vs client state

- **Server state** (fetched data) has its own caching, staleness, refetching, and loading lifecycle — use TanStack Query or SWR, not a global client store.
- These libraries dedupe requests, cache by **query key**, and refetch after invalidating a key on mutation.

### State placement and stores

- Shareable UI state (filters, tabs, pagination) belongs in the **URL** — it survives reloads and works with the back button and shared links.
- `useReducer` fits updates that touch several fields or follow named events; `dispatch` has a stable identity, so a context holding only `dispatch` never re-renders its consumers.
- **Selectors** limit re-renders: Redux `useSelector` and Zustand re-render a component only when its selected value changes by reference.
- A selector that builds a new object or array on each call defeats that — use `shallowEqual`/`useShallow` or a memoized selector.
- Jotai splits state into atoms; a component re-renders only for the atoms it reads.

## Performance

### Memoization pitfalls

- `React.memo` is defeated by a **new object, array, or function** literal passed as a prop on every render.
- `memo` compares each prop with `Object.is`; a custom `arePropsEqual` that ignores function props leaves the child calling **stale closures**.
- `useCallback` only helps when the function goes to a memoized child or into a dependency array.
- Memoize only when the skipped work costs more than the comparison.

### React Compiler

- **React Compiler** (stable 1.0, **October 2025**) auto-memoizes components and values at build time, replacing most manual `useMemo`/`useCallback`/`memo`.
- It relies on the Rules of React (pure render, no mutating props or state) and skips code it can't prove safe.

### Profiling

- The React DevTools **Profiler** records which components rendered, how long they took, and why.
- **Performance Tracks** (19.2) add React's scheduler and component work to the Chrome DevTools Performance panel.

### Virtualization and code splitting

- Long lists: **virtualize** (TanStack Virtual, react-window) so only the visible rows mount.
- `lazy(() => import('./Chart'))` inside `<Suspense>` splits a component into its own chunk, loaded on first render.

## Server Components

### Server and Client Components

- Server Components are the default in an RSC framework — there's **no directive** for them; `'use server'` marks Server Functions.
- **`'use client'`** marks a module boundary: the module and everything it imports become client code.
- Client Components still pre-render to HTML on the server; "client" means their code also ships and hydrates.
- Server Components can be `async` but have no state, effects, or browser APIs, and their code never reaches the client.
- A Client Component can't import a Server Component, but it can render one passed as **`children`** or another prop.

### Serialization boundary

- Props crossing from server to client must be **serializable**: primitives, plain objects and arrays, `Date`, `Map`, `Set`, `BigInt`, typed arrays, Promises, JSX, and Server Functions.
- Plain functions and class instances can't cross — pass data, and keep event handlers inside the Client Component.
- An unawaited Promise passed as a prop starts the work on the server; the client reads it with **`use()`** inside `<Suspense>`.
- Every prop lands in the RSC payload the browser downloads — pass only the fields the component needs, never whole database rows.

### Server Functions

- **`'use server'`** marks async functions the client can call: React serializes the arguments, POSTs them, and returns the serialized result.
- Every exported Server Function is a **public endpoint** — anyone can call it with crafted arguments, so authenticate, authorize, and validate inside each one.
- Designed for mutations: the client dispatches them **one at a time** and their results aren't cached, so they're a poor fit for data fetching.
- A Server Function passed to `<form action>` or `formAction`, or called inside a transition, is a Server Action.

### RSC protocol vulnerabilities

- **React2Shell** (CVE-2025-55182, December 2025, CVSS **10.0**): unauthenticated remote code execution through Flight-protocol deserialization in `react-server-dom-*` 19.0.0, 19.1.0–19.1.1, and 19.2.0 (fixed in 19.0.1, 19.1.2, 19.2.1), exploited within days.
- Follow-up denial-of-service and source-code-exposure CVEs needed several more patch rounds into 2026 — stay on the latest patch of the RSC packages and the framework.
- Client-only React apps were unaffected — only servers that decode RSC requests (Next.js App Router, React Router RSC mode, Waku).

## Concurrency and Suspense

### Transitions

- **`startTransition`**/`useTransition` mark an update as non-urgent: it renders in the background, typing interrupts it, and the old UI stays visible; `isPending` flags it.
- A transition can't drive a controlled input's `value` — the input update must stay urgent.
- **`useDeferredValue(value)`** renders with the old value first and the new one in the background — for values you receive rather than set.
- An async function in `startTransition` (React 19) keeps `isPending` true until it settles; state set after an `await` needs its own `startTransition`.
- Async transitions can finish **out of order**; `useActionState` and `<form action>` keep them in order, a hand-rolled flow needs its own queue or abort.

### Suspense boundaries

- Suspense activates for `lazy`, `use(promise)`, and Suspense-enabled frameworks — **not** for fetching in an effect or event handler.
- Content that suspends again shows the fallback again, unless the update was a **transition**, which keeps the old UI on screen.
- Promises passed to `use` must be **cached**: one created during render is new on every render and never resolves for React ("uncached promise").
- React reveals boundaries at most once every 300 ms, so boundaries that resolve close together appear together.

### Activity

- **`<Activity mode="hidden">`** (19.2) hides its children with `display: none` but keeps their state and DOM.
- Hidden children **unmount their effects** and process updates only when React is otherwise idle; switching back to `visible` re-runs the effects.
- Use it for tabs that keep their state and for pre-rendering a likely next screen in the background.

### View Transitions

- **`<ViewTransition>`** (stable in 19.3) animates elements on enter, exit, update, and shared-element moves with the browser View Transition API (see [frontend.md](frontend.md)).
- It only animates updates inside a **Transition**, a Suspense reveal, or `useDeferredValue`; a plain `setState` doesn't animate.
- `addTransitionType('next')` inside `startTransition` picks a different animation for the same element depending on the cause.

## Forms and Actions

### Actions

- An **Action** is an async function passed to `<form action>`, `formAction`, or `startTransition`; React tracks its pending state and sends thrown errors to the nearest error boundary.
- After a `<form action>` succeeds, React **resets uncontrolled fields** (`requestFormReset` does it manually).
- `useActionState(action, initialState)` returns `[state, formAction, isPending]` and passes the previous state to the action as its first argument.
- **`useFormStatus()`** reads the pending state of the parent `<form>`, so it must be called in a component rendered inside that form.

### Optimistic updates

- **`useOptimistic(state, updateFn)`** shows the expected result immediately while an Action runs.
- When the Action settles, the optimistic value is dropped and the real state shows — a failure rolls back automatically.

### Controlled and uncontrolled inputs

- `value={undefined}` followed by a string flips an input from uncontrolled to controlled and warns — initialize with `''`.
- `onChange` fires on every keystroke (the native `input` event), unlike the DOM `change` event.

## SSR and hydration

### Hydration mismatches

- **Hydration** attaches listeners to the server HTML and expects the first client render to match it exactly.
- Mismatch sources: `Date.now()`, `Math.random()`, `typeof window` branches, locale or timezone formatting, invalid nesting (`<div>` inside `<p>`), browser extensions.
- A text or structure mismatch makes React throw away the server HTML and **client-render** up to the nearest Suspense boundary; a mismatched attribute isn't patched at all.
- Fixes: **`useId`** for IDs, client-only values set in an effect, or `use(browser())` (19.3), which renders the Suspense fallback on the server and the component only on the client.
- `suppressHydrationWarning` silences one element's attribute and text mismatches, one level deep; React still doesn't patch them.

### Streaming and selective hydration

- `renderToPipeableStream` (Node) and `renderToReadableStream` (Web Streams) send the shell first; each Suspense boundary streams in later with an inline script that swaps it into place.
- **Selective hydration**: boundaries hydrate independently, and one the user interacts with jumps the queue.
- Crawlers and static generation wait for all content (`onAllReady`); browsers get the shell as soon as it's ready (`onShellReady`).
- **Partial pre-rendering** (19.2): `prerender` produces a static prelude for the CDN, and `resume` fills in the postponed parts per request.

## Errors and Strict Mode

### Error boundaries

- An error boundary catches errors thrown while **rendering** its subtree and shows a fallback UI instead of unmounting the whole app.
- It's still a **class component** (`getDerivedStateFromError`, `componentDidCatch`) or the `react-error-boundary` package; there's no hook equivalent.
- It doesn't catch errors in event handlers or async callbacks (`setTimeout`, promises) — except inside `useTransition`'s `startTransition`, whose errors do reach the boundary.
- React 19 reports each error once through the `createRoot` options `onCaughtError` and `onUncaughtError` instead of re-throwing it.

### Strict Mode double invocation

- In development, **Strict Mode** double-calls render functions to expose impure rendering.
- It also runs an extra effect setup → cleanup → setup cycle on mount (state kept) to expose **missing cleanup**; production skips it.

## DOM, events, and refs

### Synthetic events

- Since **React 17**, listeners attach to the **root container**, not `document`, so several React roots or versions can coexist on a page.
- React 17 removed event pooling; `e.persist()` is a no-op.
- `onScroll` doesn't bubble since React 17.
- `onFocus`/`onBlur` are built on `focusin`/`focusout`, so unlike the DOM events they bubble.

### Portals

- `createPortal(children, node)` renders into another DOM node, so modals and tooltips escape `overflow: hidden` and parent stacking contexts.
- Events bubble through the **React tree**, not the DOM tree: a click inside a portal reaches the React parent's `onClick`.
- Context flows into a portal like into any other child.

### Refs

- `ref` is a regular prop for function components since **React 19** — `forwardRef` is no longer needed.
- A callback ref gets the node on attach; since React 19 it can return a **cleanup** function instead of being called with `null` on detach.
- `useImperativeHandle` exposes a narrow API (`focus()`, `scrollTo()`) instead of the raw DOM node.
- **Fragment refs** (19.3): `<Fragment ref>` gives focus, event-listener, and observer methods over a group of children without a wrapper element.

## Version changes

### React 18

- **`createRoot`** turns on concurrent features; the legacy `ReactDOM.render` kept React 17 behavior.
- Added automatic batching everywhere, `useTransition`/`useDeferredValue`, and Suspense on the server (streaming SSR, selective hydration).
- Added `useId`, `useSyncExternalStore`, and `useInsertionEffect`; Strict Mode started double-running effects in development.

### React 19

- Added `<Context>` as a provider and `<title>`/`<meta>`/`<link>` hoisted into `<head>` from any component, alongside **Actions**, `use`, and `ref` as a prop.
- Removed `ReactDOM.render`/`hydrate`, string refs, legacy context, `propTypes`, and **`defaultProps`** on function components (use default parameters).
- Server Components and Server Functions are stable for apps, but the bundler APIs underneath don't follow semver, so frameworks pin React versions.
