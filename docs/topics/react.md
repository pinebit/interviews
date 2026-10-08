# React

What experienced React engineers forget before an interview, grouped by subtopic. Covers React 19.3; for rendering strategies, the browser pipeline, and Web Vitals see [frontend.md](frontend.md); for the framework layer see [nextjs.md](nextjs.md).

## Rendering model

### Render and commit

- [Render phase](https://react.dev/learn/render-and-commit): React calls components to compute the next tree; commit phase: it applies DOM changes, runs layout effects, then passive effects (usually after paint).
- Render must be [pure](https://react.dev/learn/keeping-components-pure) — it may run more than once for one commit ([Strict Mode](https://react.dev/reference/react/StrictMode), interrupted concurrent renders).
- A component re-renders on its own state change, a parent re-render (unless [memoized](https://react.dev/reference/react/memo)), or a consumed context value change — never because a prop changed on its own.

### Reconciliation and keys

- A different element type at the same position [unmounts the old subtree and its state](https://react.dev/learn/preserving-and-resetting-state#different-components-at-the-same-position-reset-state); the same type updates in place.
- [Keys](https://react.dev/learn/rendering-lists#keeping-list-items-in-order-with-key) match list items across renders; an array index as key attaches the wrong state after reorder or filter.
- A component defined inside another component is a new type on every render, so its subtree remounts and loses state each time.

### State and tree position

- State belongs to a [position in the tree](https://react.dev/learn/preserving-and-resetting-state), not to a variable: `{isAdmin ? <Form /> : <Form />}` keeps one shared state.
- Changing a component's [`key`](https://react.dev/learn/preserving-and-resetting-state#option-2-resetting-state-with-a-key) remounts it and resets its state — the clean way to reset a form when the selected item changes.

### State snapshots and batching

- State is a [snapshot](https://react.dev/learn/state-as-a-snapshot) per render: `setCount(count + 1)` twice adds 1; the [updater form](https://react.dev/learn/queueing-a-series-of-state-updates) `setCount(c => c + 1)` twice adds 2.
- [Automatic batching](https://react.dev/blog/2022/03/29/react-v18#new-feature-automatic-batching) (React 18+) merges updates queued in the same event or task into one render, including in timeouts and promises; separate events still render separately.
- [`flushSync(() => setValue(x))`](https://react.dev/reference/react-dom/flushSync) opts out: it renders and commits synchronously before returning.
- Setting state to an [`Object.is`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/is)-equal value skips the re-render — mutating an object in place and setting it again does nothing.
- [`useRef`](https://react.dev/reference/react/useRef) holds a mutable value across renders without triggering a re-render; don't read or write it during render.

### Fiber and concurrent rendering

- [Fiber](https://github.com/acdlite/react-fiber-architecture) splits rendering into interruptible units: the render phase can pause, restart, or be discarded; the commit phase is synchronous.
- Time slicing applies only to updates marked non-urgent ([transitions](https://react.dev/reference/react/useTransition), deferred values); other updates render without yielding.
- [Tearing](https://github.com/reactwg/react-18/discussions/69): an interrupted render can read different values from a mutable external store in different components — [`useSyncExternalStore`](https://react.dev/reference/react/useSyncExternalStore) prevents it.

## Hooks

### Rules of Hooks

- React identifies each hook's state by call order, so hooks run at the top level in the same order every render — no conditions, loops, or calls after an early return ([Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks)).
- [`use`](https://react.dev/reference/react/use) is the exception: it may be called inside `if` and loops, but not inside `try/catch`.
- [Custom hooks](https://react.dev/learn/reusing-logic-with-custom-hooks) share logic, not state: each call gets its own state.

### Effect timing

| Hook | Runs | Use for |
|---|---|---|
| [`useEffect`](https://react.dev/reference/react/useEffect) | after commit, usually after paint | subscriptions, syncing with external systems |
| [`useLayoutEffect`](https://react.dev/reference/react/useLayoutEffect) | after DOM mutation, before paint (blocks it) | measuring layout and re-rendering without flicker (tooltips) |
| [`useInsertionEffect`](https://react.dev/reference/react/useInsertionEffect) | before layout effects | CSS-in-JS style injection |

### Stale closures

- An effect or callback sees the values from the render that created it; a value missing from the [dependency array](https://react.dev/learn/lifecycle-of-reactive-effects#react-verifies-that-you-specified-every-reactive-value-as-a-dependency) stays stale.
- Fix by restructuring (a ref, a functional `setState`, moving the logic into the effect, an [Effect Event](https://react.dev/reference/react/useEffectEvent)) — not by silencing the [lint rule](https://react.dev/reference/eslint-plugin-react-hooks/lints/exhaustive-deps).

### Effect Events

- [`useEffectEvent`](https://react.dev/reference/react/useEffectEvent) ([stable in 19.2](https://react.dev/blog/2025/10/01/react-19-2#use-effect-event)) wraps logic that must read the latest props or state without re-running the effect: `onConnected` sees the current `theme` while the effect depends only on `roomId`.
- Effect Events stay out of dependency arrays and may only be called from effects in the same component.
- Only for code that is conceptually an event fired by the effect — not a way to silence the lint rule.

### Unnecessary effects

- Deriving state inside an effect + `setState` causes an extra render and a flash — [compute it during render](https://react.dev/learn/you-might-not-need-an-effect#updating-state-based-on-props-or-state).
- Logic caused by a user action belongs in the event handler, not in an effect watching a flag ([You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)).
- Every subscription, timer, or listener an effect creates needs a [cleanup](https://react.dev/learn/synchronizing-with-effects#step-3-add-cleanup-if-needed) function.

### Data fetching in effects

- Responses can arrive out of order: ignore stale ones in the effect cleanup (an `ignore` flag or [`AbortController`](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)), or a slow earlier request overwrites newer data ([race conditions](https://react.dev/learn/you-might-not-need-an-effect#fetching-data)).
- Effect-based fetching creates waterfalls (parent fetches → child mounts → child fetches); hoist fetching to route loaders, Server Components, or a query library.
- [Strict Mode](https://react.dev/reference/react/StrictMode) at the root runs setup → cleanup → setup in development, so the request fires twice; the cleanup is what makes the first response get ignored.

### `useSyncExternalStore`

- [`useSyncExternalStore`](https://react.dev/reference/react/useSyncExternalStore) subscribes components to an external store (a browser API, Redux, Zustand) with no tearing under concurrent rendering.
- `getSnapshot` must return the same value while the store is unchanged — returning a new object on each call [re-renders forever](https://react.dev/reference/react/useSyncExternalStore#im-getting-an-error-the-result-of-getsnapshot-should-be-cached).
- `getServerSnapshot` supplies the value for server rendering and hydration.

## State management

### Context performance

- Every consumer re-renders when the provider's `value` changes identity — an inline object literal changes it on every render ([optimizing context](https://react.dev/reference/react/useContext#optimizing-re-renders-when-passing-objects-and-functions)).
- Memoize the value, split fast- and slow-changing state into separate contexts, or use a store with selectors ([`useSyncExternalStore`](https://react.dev/reference/react/useSyncExternalStore), [Zustand](https://zustand.docs.pmnd.rs/)) so components subscribe to slices.
- Context suits low-frequency values (theme, locale, current user), not fast-changing shared state.

### Server state vs client state

- Server state (fetched data) has its own caching, staleness, refetching, and loading lifecycle — use [TanStack Query](https://tanstack.com/query/latest) or [SWR](https://swr.vercel.app/docs/getting-started), not a global client store.
- These libraries dedupe requests, cache by [query key](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys), and refetch after [invalidating a key](https://tanstack.com/query/latest/docs/framework/react/guides/invalidations-from-mutations) on mutation.

### State placement and stores

- Shareable UI state (filters, tabs, pagination) belongs in the URL — it survives reloads and works with the back button and shared links.
- [`useReducer`](https://react.dev/reference/react/useReducer) fits updates that touch several fields or follow named events; `dispatch` has a stable identity, so a context holding only `dispatch` never re-renders its consumers.
- Selectors limit re-renders: Redux [`useSelector`](https://redux.js.org/react-redux/api/hooks#useselector) and Zustand re-render a component only when its selected value changes by reference.
- A selector that builds a new object or array on each call defeats that — use `shallowEqual`/[`useShallow`](https://zustand.docs.pmnd.rs/reference/hooks/use-shallow) or a [memoized selector](https://redux.js.org/usage/deriving-data-selectors).
- [Jotai](https://jotai.org/) splits state into atoms; a component re-renders only for the atoms it reads.

## Performance

### Memoization pitfalls

- [`React.memo`](https://react.dev/reference/react/memo) is defeated by a new object, array, or function literal passed as a prop on every render.
- `memo` compares each prop with `Object.is`; a custom [`arePropsEqual`](https://react.dev/reference/react/memo#specifying-a-custom-comparison-function) that ignores function props leaves the child calling stale closures.
- [`useCallback`](https://react.dev/reference/react/useCallback) only helps when the function goes to a memoized child or into a dependency array.
- Memoize only when the skipped work costs more than the comparison.

### React Compiler

- [React Compiler](https://react.dev/learn/react-compiler) ([stable 1.0, October 2025](https://react.dev/blog/2025/10/07/react-compiler-1)) auto-memoizes components and values at build time, replacing most manual `useMemo`/`useCallback`/`memo`.
- It relies on the [Rules of React](https://react.dev/reference/rules) (pure render, no mutating props or state) and skips code it can't prove safe.

### Profiling

- The [React DevTools](https://react.dev/learn/react-developer-tools) [Profiler](https://legacy.reactjs.org/blog/2018/09/10/introducing-the-react-profiler.html) records which components rendered, how long they took, and why.
- [Performance Tracks](https://react.dev/reference/dev-tools/react-performance-tracks) (19.2) add React's scheduler and component work to the Chrome DevTools Performance panel.

### Virtualization and code splitting

- Long lists: virtualize ([TanStack Virtual](https://tanstack.com/virtual/latest), [react-window](https://github.com/bvaughn/react-window)) so only the visible rows mount.
- [`lazy(() => import('./Chart'))`](https://react.dev/reference/react/lazy) inside `<Suspense>` splits a component into its own chunk, loaded on first render.

## Server Components

### Server and Client Components

- [Server Components](https://react.dev/reference/rsc/server-components) are the default in an RSC framework — there's no directive for them; `'use server'` marks Server Functions.
- [`'use client'`](https://react.dev/reference/rsc/use-client) marks a module boundary: the module and everything it imports become client code.
- Client Components still pre-render to HTML on the server; "client" means their code also ships and hydrates.
- Server Components can be `async` but have no state, effects, or browser APIs, and their code never reaches the client.
- A Client Component can't import a Server Component, but it can render one passed as `children` or another prop.

### Serialization boundary

- Props crossing from server to client must be [serializable](https://react.dev/reference/rsc/use-client#serializable-types): primitives, plain objects and arrays, `Date`, `Map`, `Set`, `BigInt`, typed arrays, Promises, JSX, and Server Functions.
- Plain functions and class instances can't cross — pass data, and keep event handlers inside the Client Component.
- An unawaited Promise passed as a prop starts the work on the server; the client reads it with [`use()`](https://react.dev/reference/react/use) inside `<Suspense>`.
- Every prop lands in the RSC payload the browser downloads — pass only the fields the component needs, never whole database rows.

### Server Functions

- [`'use server'`](https://react.dev/reference/rsc/use-server) marks async functions the client can call: React serializes the arguments, POSTs them, and returns the serialized result.
- Every exported [Server Function](https://react.dev/reference/rsc/server-functions) is a public endpoint — anyone can call it with crafted arguments, so authenticate, authorize, and validate inside each one.
- Designed for mutations: the client dispatches them one at a time and their results aren't cached, so they're a poor fit for data fetching.
- A Server Function passed to `<form action>` or `formAction`, or called inside a transition, is a Server Action.

### RSC protocol vulnerabilities

- React2Shell ([CVE-2025-55182](https://react.dev/blog/2025/12/03/critical-security-vulnerability-in-react-server-components), December 2025, CVSS 10.0): unauthenticated remote code execution through Flight-protocol deserialization in `react-server-dom-*` 19.0.0, 19.1.0–19.1.1, and 19.2.0 (fixed in 19.0.1, 19.1.2, 19.2.1), exploited within days.
- [Follow-up denial-of-service and source-code-exposure CVEs](https://react.dev/blog/2025/12/11/denial-of-service-and-source-code-exposure-in-react-server-components) needed several more patch rounds into 2026 — stay on the latest patch of the RSC packages and the framework.
- Client-only React apps were unaffected — only servers that decode RSC requests (Next.js App Router, React Router RSC mode, Waku).

## Concurrency and Suspense

### Transitions

- [`startTransition`](https://react.dev/reference/react/startTransition)/[`useTransition`](https://react.dev/reference/react/useTransition) mark an update as non-urgent: it renders in the background, typing interrupts it, and the old UI stays visible; `isPending` flags it.
- A transition [can't drive a controlled input's `value`](https://react.dev/reference/react/useTransition#updating-an-input-in-a-transition-doesnt-work) — the input update must stay urgent.
- [`useDeferredValue(value)`](https://react.dev/reference/react/useDeferredValue) renders with the old value first and the new one in the background — for values you receive rather than set.
- An async function in `startTransition` (React 19) keeps `isPending` true until it settles; state set after an `await` needs its own `startTransition`.
- Async transitions can finish out of order; [`useActionState`](https://react.dev/reference/react/useActionState) and `<form action>` keep them in order, a hand-rolled flow needs its own queue or abort.

### Suspense boundaries

- [Suspense](https://react.dev/reference/react/Suspense) activates for `lazy`, `use(promise)`, and Suspense-enabled frameworks — not for fetching in an effect or event handler.
- Content that suspends again shows the fallback again, unless the update was a [transition](https://react.dev/reference/react/Suspense#preventing-already-revealed-content-from-hiding), which keeps the old UI on screen.
- Promises passed to [`use`](https://react.dev/reference/react/use) must be cached: one created during render is new on every render and never resolves for React ("uncached promise").
- React reveals boundaries at most once every 300 ms, so boundaries that resolve close together appear together.

### Activity

- [`<Activity mode="hidden">`](https://react.dev/reference/react/Activity) (19.2) hides its children with `display: none` but keeps their state and DOM.
- Hidden children unmount their effects and process updates only when React is otherwise idle; switching back to `visible` re-runs the effects.
- Use it for tabs that keep their state and for pre-rendering a likely next screen in the background.

### View Transitions

- [`<ViewTransition>`](https://react.dev/reference/react/ViewTransition) ([stable in 19.3](https://react.dev/blog/2026/09/09/react-19-3#view-transition)) animates elements on enter, exit, update, and shared-element moves with the browser [View Transition API](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API) (see [frontend.md](frontend.md)).
- It only animates updates inside a Transition, a Suspense reveal, or `useDeferredValue`; a plain `setState` doesn't animate.
- [`addTransitionType('next')`](https://react.dev/reference/react/addTransitionType) inside `startTransition` picks a different animation for the same element depending on the cause.

## Forms and Actions

### Actions

- An Action is an async function passed to [`<form action>`](https://react.dev/reference/react-dom/components/form), `formAction`, or `startTransition`; React tracks its pending state and sends thrown errors to the nearest error boundary.
- After a `<form action>` succeeds, React resets uncontrolled fields ([`requestFormReset`](https://react.dev/blog/2024/12/05/react-19#form-actions) does it manually).
- [`useActionState(action, initialState)`](https://react.dev/reference/react/useActionState) returns `[state, formAction, isPending]` and passes the previous state to the action as its first argument.
- [`useFormStatus()`](https://react.dev/reference/react-dom/hooks/useFormStatus) reads the pending state of the parent `<form>`, so it must be called in a component rendered inside that form.

### Optimistic updates

- [`useOptimistic(state, updateFn)`](https://react.dev/reference/react/useOptimistic) shows the expected result immediately while an Action runs.
- When the Action settles, the optimistic value is dropped and the real state shows — a failure rolls back automatically.

### Controlled and uncontrolled inputs

- `value={undefined}` followed by a string flips an input from [uncontrolled to controlled](https://react.dev/reference/react-dom/components/input#im-getting-an-error-a-component-is-changing-an-uncontrolled-input-to-be-controlled) and warns — initialize with `''`.
- `onChange` fires on every keystroke (the native [`input`](https://developer.mozilla.org/en-US/docs/Web/API/Element/input_event) event), unlike the DOM [`change`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/change_event) event.

## SSR and hydration

### Hydration mismatches

- [Hydration](https://react.dev/reference/react-dom/client/hydrateRoot) attaches listeners to the server HTML and expects the first client render to match it exactly.
- Mismatch sources: `Date.now()`, `Math.random()`, `typeof window` branches, locale or timezone formatting, invalid nesting (`<div>` inside `<p>`), browser extensions.
- A text or structure mismatch makes React throw away the server HTML and client-render up to the nearest Suspense boundary; a mismatched attribute isn't patched at all.
- Fixes: [`useId`](https://react.dev/reference/react/useId) for IDs, client-only values set in an effect, or [`use(browser())`](https://react.dev/reference/react-dom/browser) (19.3), which renders the Suspense fallback on the server and the component only on the client.
- [`suppressHydrationWarning`](https://react.dev/reference/react-dom/components/common#common-props) silences one element's attribute and text mismatches, one level deep; React still doesn't patch them.

### Streaming and selective hydration

- [`renderToPipeableStream`](https://react.dev/reference/react-dom/server/renderToPipeableStream) (Node) and [`renderToReadableStream`](https://react.dev/reference/react-dom/server/renderToReadableStream) (Web Streams) send the shell first; each Suspense boundary streams in later with an inline script that swaps it into place.
- [Selective hydration](https://github.com/reactwg/react-18/discussions/37): boundaries hydrate independently, and one the user interacts with jumps the queue.
- Crawlers and static generation [wait for all content](https://react.dev/reference/react-dom/server/renderToPipeableStream#waiting-for-all-content-to-load-for-crawlers-and-static-generation) (`onAllReady`); browsers get the shell as soon as it's ready (`onShellReady`).
- Partial pre-rendering (19.2): [`prerender`](https://react.dev/reference/react-dom/static/prerender) produces a static prelude for the CDN, and [`resume`](https://react.dev/reference/react-dom/server/resume) fills in the postponed parts per request.

## Errors and Strict Mode

### Error boundaries

- An [error boundary](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary) catches errors thrown while rendering its subtree and shows a fallback UI instead of unmounting the whole app.
- It's still a class component (`getDerivedStateFromError`, `componentDidCatch`) or the [`react-error-boundary`](https://github.com/bvaughn/react-error-boundary) package; there's no hook equivalent.
- It doesn't catch errors in event handlers or async callbacks (`setTimeout`, promises) — except inside [`useTransition`](https://react.dev/reference/react/useTransition#displaying-an-error-to-users-with-error-boundary)'s `startTransition`, whose errors do reach the boundary.
- React 19 reports each error once through the [`createRoot`](https://react.dev/reference/react-dom/client/createRoot#parameters) options `onCaughtError` and `onUncaughtError` instead of re-throwing it.

### Strict Mode double invocation

- In development, [Strict Mode](https://react.dev/reference/react/StrictMode) double-calls render functions to expose impure rendering.
- When it wraps the root, it also runs an extra effect setup → cleanup → setup cycle on mount (state kept) to expose [missing cleanup](https://react.dev/reference/react/StrictMode#fixing-bugs-found-by-re-running-effects-in-development); production skips it.

## DOM, events, and refs

### Synthetic events

- Since [React 17](https://legacy.reactjs.org/blog/2020/10/20/react-v17.html#changes-to-event-delegation), listeners attach to the root container, not `document`, so several React roots or versions can coexist on a page.
- React 17 removed [event pooling](https://legacy.reactjs.org/docs/legacy-event-pooling.html); `e.persist()` is a no-op.
- `onScroll` doesn't bubble since React 17.
- `onFocus`/`onBlur` are built on [`focusin`](https://developer.mozilla.org/en-US/docs/Web/API/Element/focusin_event)/[`focusout`](https://developer.mozilla.org/en-US/docs/Web/API/Element/focusout_event), so unlike the DOM events they bubble.

### Portals

- [`createPortal(children, node)`](https://react.dev/reference/react-dom/createPortal) renders into another DOM node, so modals and tooltips escape `overflow: hidden` and parent stacking contexts.
- Events bubble through the React tree, not the DOM tree: a click inside a portal reaches the React parent's `onClick`.
- Context flows into a portal like into any other child.

### Refs

- [`ref` is a regular prop](https://react.dev/blog/2024/12/05/react-19#ref-as-a-prop) for function components since React 19 — [`forwardRef`](https://react.dev/reference/react/forwardRef) is no longer needed.
- A callback ref gets the node on attach; since React 19 it can return a [cleanup function](https://react.dev/blog/2024/12/05/react-19#cleanup-functions-for-refs) instead of being called with `null` on detach.
- [`useImperativeHandle`](https://react.dev/reference/react/useImperativeHandle) exposes a narrow API (`focus()`, `scrollTo()`) instead of the raw DOM node.
- [Fragment refs](https://react.dev/reference/react/Fragment) (19.3): `<Fragment ref>` gives focus, event-listener, and observer methods over a group of children without a wrapper element.

## Version changes

### React 18

- [`createRoot`](https://react.dev/reference/react-dom/client/createRoot) turns on concurrent features; the legacy `ReactDOM.render` kept React 17 behavior.
- Added automatic batching everywhere, `useTransition`/`useDeferredValue`, and Suspense on the server (streaming SSR, selective hydration) — [React 18 release notes](https://react.dev/blog/2022/03/29/react-v18).
- Added `useId`, `useSyncExternalStore`, and `useInsertionEffect`; Strict Mode started double-running effects in development.

### React 19

- Added [`<Context>` as a provider](https://react.dev/blog/2024/12/05/react-19#context-as-a-provider) and `<title>`/`<meta>`/`<link>` [hoisted into `<head>`](https://react.dev/blog/2024/12/05/react-19#support-for-metadata-tags) from any component, alongside Actions, `use`, and `ref` as a prop.
- [Removed](https://react.dev/blog/2024/04/25/react-19-upgrade-guide#removed-deprecated-react-apis) `ReactDOM.render`/`hydrate`, string refs, legacy context, `propTypes`, and `defaultProps` on function components (use default parameters).
- Server Components and Server Functions are stable for apps, but the [bundler APIs underneath don't follow semver](https://react.dev/reference/rsc/server-components), so frameworks pin React versions.
