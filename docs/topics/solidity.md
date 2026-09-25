# Solidity

What experienced Solidity engineers forget before an interview, grouped by subtopic.

## Language semantics

### Visibility and mutability

- `external` functions are callable internally only as `this.f()` — a real external call; `public` works both ways.
- **`private` isn't secret**: anyone can read any storage slot off-chain with `eth_getStorageAt`.
- External calls to `view`/`pure` functions use **`STATICCALL`**, so a state change inside them reverts at runtime.

### Inheritance and linearization

- Bases are listed **most base-like first**: `contract D is B, C` (both `is A`) linearizes to D → C → B → A (C3, like Python's MRO).
- **`super`** calls the next contract in the linearization, not the declared parent: in D, `super.f()` inside C calls B even though C only inherits A.
- Overridable functions need `virtual`; overriding needs `override`, and `override(B, C)` when several bases define it.

### Modifiers

- `_` marks where the function body runs; a `return` in the body only leaves the body, so code after `_` still runs **after the return**.
- Modifiers apply left to right; `_` may run several times, and if it never runs the body is skipped and return values stay at their defaults.
- Modifier code is **inlined** at every use — move the logic into an internal function to shrink bytecode.
- `virtual` modifiers are deprecated since 0.8.31, ahead of 0.9.

### Libraries and user-defined types

- `internal` library functions are inlined into the caller (a `JUMP`); `public`/`external` ones run through **`DELEGATECALL`** into a separately deployed, linked library.
- Libraries have no state variables and can't receive ETH; `using L for T` attaches their functions to a type, and `global` (0.8.13, user-defined types only) applies it in every file.
- **User-defined value types** (`type Price is uint256;`, 0.8.8) are zero-cost wrappers that stop mixing units; `using {add as +} for Price global` binds operators (0.8.19).

### Arithmetic and casts

- Overflow and underflow **revert since 0.8** with `Panic(0x11)`; `unchecked { }` opts out for proven-safe math.
- **Explicit downcasts truncate silently**, even in 0.8: `uint8(uint256(300)) == 44` — use SafeCast.
- `int` ↔ `uint` conversions reinterpret bits: `uint256(int256(-1)) == type(uint256).max`.
- Division **truncates**, so multiply before dividing; OpenZeppelin's `Math.mulDiv` keeps a 512-bit intermediate so the product can't overflow.

## Data and storage

### Data locations

- **`storage`** is persistent state; `memory` is per call; **`calldata`** is read-only input — the cheapest location for external array and struct parameters.
- Storage → memory assignment **copies**; memory → memory copies only the reference; a local `storage` variable is a pointer into state.

### Storage layout

- Variables under 32 bytes **pack** into shared slots in declaration order; structs and arrays always start a new slot.
- A `mapping` value lives at **`keccak256(key . slot)`**; a dynamic array stores its length at the slot and elements from `keccak256(slot)`.
- `string`/`bytes` up to 31 bytes sit in the slot itself with `length * 2` in the lowest byte; longer ones store `length * 2 + 1` there and data from `keccak256(slot)`.
- With inheritance, slots follow the **C3 linearization**, most base-like contract first — reordering bases shifts every slot.

### Transient and relocated storage

- **`transient`** state variables (0.8.28, value types only) compile to `TSTORE`/`TLOAD`: 100 gas, cleared at the end of the transaction — see [ethereum.md](ethereum.md).
- They can't have initializers, and they **persist across calls within one transaction** — a lock or flag must be reset explicitly, or a later call in a batch sees it.
- **`layout at <slot>`** (0.8.29) moves a contract's storage to a custom base slot; `layout at erc7201("my.app")` (0.8.35) uses an ERC-7201 namespace's base slot.

### Mapping and delete gotchas

- Mappings have no length and can't be iterated; every key "exists" with a zero value — keep an `EnumerableSet`/`EnumerableMap` to enumerate.
- **`delete` on a struct skips its mappings**: the entries survive and reappear if the struct is reused.
- `delete arr[i]` zeroes the element without shrinking the array; swap with the last element and `pop()` to remove it.
- `delete` on a dynamic storage array clears every element — its gas grows with the length.

## Calls and ABI

### Function selectors and fallback

- Calldata starts with a 4-byte **selector** (first 4 bytes of `keccak256("fn(types)")`) followed by ABI-encoded arguments; selectors can collide, a risk in proxy dispatchers.
- No matching selector → **`fallback()`**; plain ETH with empty calldata → **`receive()`** (or a payable fallback); a contract with neither rejects plain ETH.

### call, delegatecall, staticcall

- `call` runs in the callee's context; **`delegatecall`** runs the callee's code on the **caller's** storage, `msg.sender`, and `msg.value`; `staticcall` forbids state changes.
- The **63/64 rule** (EIP-150): a call forwards at most 63/64 of remaining gas, keeping 1/64 for the caller.
- `delegatecall` keeps `msg.value`, so a payable multicall that delegatecalls itself credits one payment many times (the 2021 SushiSwap MISO bug); the same happens reading `msg.value` in a loop.

### Sending ETH

- `transfer` reverts and `send` returns `false` on failure; both forward only a **2,300-gas stipend** — too little for most smart wallets, and brittle when opcode costs change (EIP-1884 broke receivers in 2019).
- Both are **deprecated since 0.8.31**, ahead of removal in 0.9; use `(bool ok, ) = to.call{value: amount}("")`, check `ok`, and guard against reentrancy.
- ETH can arrive without running your code — another contract's `selfdestruct`, fee recipient or withdrawal credits — so **`address(this).balance`** can exceed internal accounting; never use it in a strict equality.

### ABI encoding pitfalls

- A low-level call to an address with **no code succeeds** — check `code.length` first; high-level calls revert instead.
- **`abi.encodePacked`** of several dynamic values can collide (`("a","bc")` vs `("ab","c")`) — hash `abi.encode` output for signatures.
- **`abi.encodeCall`** (0.8.11) type-checks the function and arguments; `abi.encodeWithSignature` silently accepts a typo in the signature string.

### Event encoding

- An **indexed** `string`, `bytes`, array, or struct is stored as its **keccak256 hash** — the value can't be recovered from the log.
- **`anonymous`** events drop the signature topic, allowing 4 indexed parameters, but can't be filtered by event name.
- Non-indexed parameters are ABI-encoded into the log data; contracts can't read logs back — see [ethereum.md](ethereum.md).

## Security

### Reentrancy

- An external call re-enters before state updates: **single-function**, cross-function, cross-contract, or **read-only** (a view function returns pre-update state to another protocol).
- Fix with **Checks-Effects-Interactions** plus a reentrancy guard; OpenZeppelin's `ReentrancyGuardTransient` keeps the lock in transient storage.
- Hooks are external calls too: ERC-721/1155 `safeTransfer` receivers, ERC-777 hooks, and ETH sent to a contract.

### Access control

- Missing modifiers and **unprotected initializers** let anyone call admin functions.
- Authenticate with `msg.sender`, never **`tx.origin`** — a malicious contract the owner calls can pass a `tx.origin` check.
- **`msg.sender == tx.origin`** no longer proves there is no code in the path: since EIP-7702 (Pectra, May 2025) a delegated EOA runs code and makes several calls per transaction.
- `code.length == 0` doesn't prove an EOA either: it's 0 for a contract still in its constructor, and a 7702-delegated EOA has code.

### Signature replay and malleability

- Signed messages without a **nonce, chainId, and deadline** can be replayed on another chain or later.
- ECDSA `s` can be flipped (`n − s`) into a second valid signature — enforce **low-`s`** and never use a signature as a unique ID.
- Raw `ecrecover` returns `address(0)` on a bad signature, which matches an unset signer — use OpenZeppelin's `ECDSA`, which reverts and enforces low-`s`.

### Token integration quirks

- Non-standard ERC-20s (USDT) return nothing or `false` from `transfer` — use **SafeERC20**.
- **Fee-on-transfer** and rebasing tokens break "amount sent = amount received" assumptions — measure balance deltas.
- Changing a non-zero allowance lets the spender front-run the change and spend old + new.
- USDT's `approve` reverts unless the current allowance is 0 — `SafeERC20.forceApprove` resets it first.
- Blocklists (USDC, USDT) make any transfer to or from a flagged address revert.

### Oracle integration

- A DEX **spot price** can be moved within one transaction using a flash loan — use a TWAP or Chainlink; see [ethereum.md](ethereum.md).
- Chainlink `latestRoundData`: check **staleness** (`updatedAt` against the feed's heartbeat) and `answer > 0`; on L2s also check the **sequencer uptime feed**.
- Feeds have their own decimals (USD pairs use 8, ETH pairs 18) — scale before combining with token amounts.

### Denial of service

- **Unbounded loops** over user-growable arrays eventually exceed the gas limit — paginate or cap the size.
- Pushing ETH to many receivers fails if one reverts (a contract without `receive`) — switch to **pull payments** (a withdraw function).
- A malicious callee can return huge data that Solidity copies into memory even when discarded — a **returnbomb**; cap the copy with an assembly `call`.

### Randomness and block data

- **`block.prevrandao`** (0.8.18, replaced `difficulty`) is known to the proposer, who can bias it by withholding a block — use **Chainlink VRF** or commit-reveal.
- `blockhash(n)` returns 0 for blocks older than **256**; EIP-2935 (Pectra) serves 8,191 hashes from a system contract, but the opcode is unchanged.
- Anything derived from block data can be computed by an attacker's contract in the same transaction, which reverts when the outcome is bad.
- On L1, `block.timestamp` advances in fixed 12 s slots; L2 sequencers set it within looser bounds.

### Rounding and precision

- Round **in the protocol's favor**: ERC-4626 rounds shares down on deposit and up on withdraw.
- **First-depositor inflation attack**: the attacker mints 1 wei of shares and donates assets, so the next depositor's shares round down to 0 — mitigate with virtual shares (OpenZeppelin's decimals offset) or dead shares.
- Tokens mix decimals (USDC 6, WETH 18) — normalize before math and never compare raw amounts across tokens.

## Gas optimization

### Gas optimization patterns

- An `SSTORE` costs **20,000** gas to set a zero slot and 2,900 to change a non-zero one (+2,100 if cold) — see [ethereum.md](ethereum.md).
- **Pack** small variables that are read and written together into one slot.
- **`constant`/`immutable`** values are embedded in bytecode — no `SLOAD`.
- Cache storage reads in local variables inside loops; use `calldata` parameters.
- Custom errors are cheaper than revert strings; 0.8.22 made simple loop-counter increments unchecked automatically.

### Code size limit

- Deployed code is capped at **24,576 bytes** (EIP-170) and initcode at 49,152 (EIP-3860, Shanghai).
- Workarounds: move logic into external libraries, split into several contracts, lower optimizer `runs`, or use the Diamond pattern.
- **EIP-7954**, scheduled for Glamsterdam, raises the limits to 64 KiB and 128 KiB.

## Upgradeability

### Proxy patterns

| Pattern | Upgrade logic lives in | Note |
|---|---|---|
| **Transparent** | proxy (admin-only path) | admin can't call the implementation |
| **UUPS** (ERC-1822) | implementation | cheaper proxy; an implementation without upgrade code bricks it |
| **Beacon** | shared beacon contract | upgrades many proxies at once |
| **Diamond** (EIP-2535) | proxy routing to many facets | per-selector implementations |

- Every pattern keeps **storage in the proxy** and `delegatecall`s the implementation.

### Proxy storage and initializers

- The implementation address sits at the pseudo-random **EIP-1967** slot, away from the implementation's own variables.
- New versions only append storage variables, never reorder — or use **ERC-7201** namespaced storage.
- Constructors don't run through a proxy: use **initializers**, and call `_disableInitializers()` in the implementation's constructor.
- `immutable` values live in the implementation's bytecode, so every proxy shares the values set at implementation deployment.

### Upgrade safety

- A proxy function whose selector matches an implementation function shadows it — Transparent proxies route by caller, UUPS proxies have no functions of their own.
- An **uninitialized UUPS implementation** let anyone take ownership and upgrade it to a `selfdestruct` contract, bricking every proxy (OpenZeppelin advisory, 2021); since EIP-6780 the code survives.
- **Metamorphic contracts** redeployed different code at one address via `CREATE2` + `SELFDESTRUCT`; EIP-6780 (Cancun) ended the trick.
- OpenZeppelin's Upgrades plugins (Foundry, Hardhat) diff storage layouts and flag unsafe patterns before an upgrade.

## Errors and reverts

### Error types

- `require(cond, "msg")` and `revert("msg")` encode **`Error(string)`** (selector `0x08c379a0`).
- `assert`, overflow, division by zero, and out-of-bounds access raise **`Panic(uint256)`** with codes `0x01`, `0x11`, `0x12`, `0x32`.
- Before 0.8, `assert` hit the `INVALID` opcode and burned all remaining gas; now it reverts like any other error.
- **Custom errors** (0.8.4) encode a selector plus arguments; `require(cond, MyError())` works since 0.8.26 with via-IR and 0.8.27 with legacy codegen.

### try/catch limits

- Works only on **external calls** and `new` contract creation, not on internal calls.
- Catches only reverts inside the callee: undecodable return data or **a target with no code** reverts the caller.
- Clauses: `catch Error(string memory)`, `catch Panic(uint256)`, and `catch (bytes memory)` for everything else — a custom error can't be caught by name.
- The callee can burn 63/64 of the gas, leaving too little for the `catch` block.

### Revert data bubbling

- A low-level `call` returns `(bool success, bytes memory data)` and **doesn't revert** — always check `success`.
- Re-throw the callee's error unchanged with assembly: `revert(add(data, 32), mload(data))`.
- OpenZeppelin's `Address.functionCall` does both.

## Compiler and tooling

### Compiler pipelines

- **via-IR** compiles through Yul: stronger cross-function optimization and fewer "stack too deep" errors (it moves variables to memory), but slower builds; legacy is still the default.
- via-IR changes some semantics: each contract initializes its state variables right before its own constructor, and modifiers reset return variables at every `_`.
- Optimizer **`runs`** (default 200) is the expected number of executions per opcode: lower favors deployment cost, higher favors call cost.

### EVM version targeting

- **`evmVersion`** picks the target hard fork; the default moved to `shanghai` in 0.8.20 (emits **`PUSH0`**), `cancun` in 0.8.25, `prague` in 0.8.30, and `osaka` in 0.8.31.
- Code with an opcode the target chain lacks fails to deploy — `PUSH0` broke L2 deployments in 2023; set `evmVersion` to the oldest chain you target.
- Pin the pragma (`pragma solidity 0.8.37;`) in contracts you deploy; a floating `^0.8.0` suits libraries.

### Testing with Foundry

- Tests are Solidity contracts; **cheatcodes** (`vm.prank`, `vm.warp`, `vm.deal`, `vm.expectRevert`) set the caller, time, balances, and expected failures.
- **Fuzz tests** take random arguments (256 runs by default); `bound()` constrains them.
- **Invariant tests** call random sequences of handler functions and check properties after each (total supply = sum of balances).
- Fork tests (`--fork-url`) run against live chain state.

### Static analysis and formal verification

- **Slither** flags known bug patterns (reentrancy, shadowing, uninitialized storage) in seconds.
- Symbolic and formal tools (Halmos, Certora, the built-in SMTChecker) prove properties for all inputs, not just sampled ones.

## Inline assembly

### Memory layout

- `0x00`–`0x3f` is scratch space for hashing, **`0x40` holds the free memory pointer**, `0x60` is the zero slot; allocation starts at **`0x80`** — hence bytecode starting `6080604052`.
- Memory is never freed within a call: Solidity only bumps the free memory pointer.

### Assembly gotchas

- No overflow or bounds checks, and values narrower than 256 bits may carry **dirty upper bits** — mask them.
- Mark blocks **`assembly ("memory-safe")`** (0.8.13) so via-IR can still move variables to memory; the `/// @solidity memory-safe-assembly` comment is deprecated since 0.8.31.
- `return` and `revert` in assembly end the whole call, not just the current function.
- Storage variables expose `.slot` and `.offset`; calldata arrays expose `.offset` and `.length`.
