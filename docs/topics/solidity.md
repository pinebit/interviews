# Solidity

What experienced Solidity engineers forget before an interview, grouped by subtopic.

## Language semantics

### Visibility and mutability

- [`external`](https://docs.soliditylang.org/en/latest/contracts.html#function-visibility) functions are callable internally only as `this.f()` — a real external call; `public` works both ways.
- `private` isn't secret: anyone can read any storage slot off-chain with [`eth_getStorageAt`](https://ethereum.org/developers/docs/apis/json-rpc/#eth-getstorageat).
- External calls to [`view`/`pure`](https://docs.soliditylang.org/en/latest/contracts.html#view-functions) functions use `STATICCALL` ([EIP-214](https://eips.ethereum.org/EIPS/eip-214)), so a state change inside them reverts at runtime — except library `view` functions, called with `DELEGATECALL` and not enforced.

### Inheritance and linearization

- Bases are listed most base-like first: `contract D is B, C` (both `is A`) [linearizes](https://docs.soliditylang.org/en/latest/contracts.html#multiple-inheritance-and-linearization) to D → C → B → A ([C3](https://docs.python.org/3/howto/mro.html), like Python's MRO).
- `super` calls the next contract in the linearization, not the declared parent: in D, `super.f()` inside C calls B even though C only inherits A.
- Overridable functions need `virtual`; [overriding](https://docs.soliditylang.org/en/latest/contracts.html#function-overriding) needs `override`, and `override(B, C)` when several bases define it; implementing a single interface's function needs no `override` since 0.8.8.

### Modifiers

- `_` marks where the function body runs in a [modifier](https://docs.soliditylang.org/en/latest/contracts.html#function-modifiers); a `return` in the body only leaves the body, so code after `_` still runs after the return.
- Modifiers apply left to right; `_` may run several times, and if it never runs the body is skipped and return values stay at their defaults.
- Legacy codegen inlines modifier code at every use — move the logic into an internal function to shrink bytecode; [via-IR](https://docs.soliditylang.org/en/latest/ir-breaking-changes.html) emits modifiers as functions.

### Libraries and user-defined types

- `internal` [library](https://docs.soliditylang.org/en/latest/contracts.html#libraries) functions are inlined into the caller (a `JUMP`); `public`/`external` ones run through `DELEGATECALL` into a separately deployed, linked library.
- Libraries have no state variables and can't receive ETH; [`using L for T`](https://docs.soliditylang.org/en/latest/contracts.html#using-for) attaches their functions to a type, and `global` (user-defined types only) applies it in every file.
- [User-defined value types](https://docs.soliditylang.org/en/latest/types.html#user-defined-value-types) (`type Price is uint256;`, 0.8.8) are zero-cost wrappers that stop mixing units; `using {add as +} for Price global` binds operators.

### Arithmetic and casts

- Overflow and underflow [revert since 0.8](https://docs.soliditylang.org/en/latest/control-structures.html#checked-or-unchecked-arithmetic) with `Panic(0x11)`; `unchecked { }` opts out for proven-safe math.
- [Explicit downcasts](https://docs.soliditylang.org/en/latest/types.html#explicit-conversions) truncate silently, even in 0.8: `uint8(uint256(300)) == 44` — use [`SafeCast`](https://docs.openzeppelin.com/contracts/5.x/api/utils#SafeCast).
- `int` ↔ `uint` conversions reinterpret bits: `uint256(int256(-1)) == type(uint256).max`.
- Division truncates, so multiply before dividing; OpenZeppelin's [`Math.mulDiv`](https://docs.openzeppelin.com/contracts/5.x/api/utils#Math-mulDiv-uint256-uint256-uint256-) keeps a 512-bit intermediate so the product can't overflow.

## Data and storage

### Data locations

- `storage` is persistent state; `memory` is per call; `calldata` is read-only input — the cheapest [data location](https://docs.soliditylang.org/en/latest/types.html#data-location) for external array and struct parameters.
- Storage → memory assignment [copies](https://docs.soliditylang.org/en/latest/types.html#data-location-and-assignment-behavior); memory → memory copies only the reference; a local `storage` variable is a pointer into state.

### Storage layout

- Variables under 32 bytes [pack](https://docs.soliditylang.org/en/latest/internals/layout_in_storage.html) into shared slots in declaration order; structs and arrays always start a new slot.
- A `mapping` value lives at [`keccak256(key . slot)`](https://docs.soliditylang.org/en/latest/internals/layout_in_storage.html#mappings-and-dynamic-arrays); a dynamic array stores its length at the slot and elements from `keccak256(slot)`.
- [`string`/`bytes`](https://docs.soliditylang.org/en/latest/internals/layout_in_storage.html#bytes-and-string) up to 31 bytes sit in the slot itself with `length * 2` in the lowest byte; longer ones store `length * 2 + 1` there and data from `keccak256(slot)`.
- With inheritance, slots follow the [C3 linearization](https://docs.python.org/3/howto/mro.html), most base-like contract first — reordering bases shifts every slot.

### Transient and relocated storage

- [`transient`](https://docs.soliditylang.org/en/latest/contracts.html#transient-storage) state variables (0.8.28, value types only) compile to `TSTORE`/`TLOAD` ([EIP-1153](https://eips.ethereum.org/EIPS/eip-1153)): 100 gas, cleared at the end of the transaction — see [ethereum.md](ethereum.md).
- They can't have initializers, and they persist across calls within one transaction — a lock or flag must be reset explicitly, or a later call in a batch sees it.

### Mapping and delete gotchas

- [Mappings](https://docs.soliditylang.org/en/latest/types.html#mapping-types) have no length and can't be iterated; every key "exists" with a zero value — keep an [`EnumerableSet`](https://docs.openzeppelin.com/contracts/5.x/api/utils#EnumerableSet)/`EnumerableMap` to enumerate.
- [`delete` on a struct skips its mappings](https://docs.soliditylang.org/en/latest/types.html#delete): the entries survive and reappear if the struct is reused.
- `delete arr[i]` zeroes the element without shrinking the array; swap with the last element and `pop()` to remove it.
- `delete` on a dynamic storage array clears every element — its gas grows with the length.

## Calls and ABI

### Function selectors and fallback

- Calldata starts with a 4-byte [selector](https://docs.soliditylang.org/en/latest/abi-spec.html#function-selector) (first 4 bytes of `keccak256("fn(types)")`) followed by ABI-encoded arguments; selectors can collide, a risk in proxy dispatchers.
- No matching selector → [`fallback()`](https://docs.soliditylang.org/en/latest/contracts.html#fallback-function); plain ETH with empty calldata → [`receive()`](https://docs.soliditylang.org/en/latest/contracts.html#receive-ether-function) (or a payable fallback); a contract with neither rejects plain ETH.

### call, delegatecall, staticcall

- [`call`](https://docs.soliditylang.org/en/latest/units-and-global-variables.html#members-of-address-types) runs in the callee's context; `delegatecall` runs the callee's code on the caller's storage, `msg.sender`, and `msg.value`; `staticcall` forbids state changes.
- The 63/64 rule ([EIP-150](https://eips.ethereum.org/EIPS/eip-150)): a call forwards at most 63/64 of remaining gas, keeping 1/64 for the caller.
- `delegatecall` keeps `msg.value`, so a payable multicall that delegatecalls itself credits one payment many times (the [2021 SushiSwap MISO bug](https://www.paradigm.xyz/2021/08/two-rights-might-make-a-wrong)); the same happens reading `msg.value` in a loop.

### Sending ETH

- [`transfer` reverts and `send` returns `false`](https://docs.soliditylang.org/en/latest/units-and-global-variables.html#members-of-address-types) on failure; both forward only a 2,300-gas stipend — too little for most smart wallets, and brittle when opcode costs change ([EIP-1884](https://eips.ethereum.org/EIPS/eip-1884) broke receivers in 2019).
- Both are [deprecated since 0.8.31](https://github.com/argotorg/solidity/releases/tag/v0.8.31), ahead of removal in 0.9; use `(bool ok, ) = to.call{value: amount}("")`, check `ok`, and guard against reentrancy.
- ETH can arrive without running your code — another contract's `selfdestruct`, fee recipient or withdrawal credits — so `address(this).balance` can exceed internal accounting; never use it in a strict equality.

### ABI encoding pitfalls

- A low-level call to an address with no code succeeds — check `code.length` first when you expect a contract ([precompiles](https://www.evm.codes/precompiled) have no code either); [high-level calls revert instead](https://docs.soliditylang.org/en/latest/control-structures.html#external-function-calls).
- [`abi.encodePacked`](https://docs.soliditylang.org/en/latest/abi-spec.html#non-standard-packed-mode) of several dynamic values can collide (`("a","bc")` vs `("ab","c")`) — hash `abi.encode` output for signatures.
- [`abi.encodeCall`](https://docs.soliditylang.org/en/latest/units-and-global-variables.html#abi-encoding-and-decoding-functions) (0.8.11) type-checks the function and arguments; `abi.encodeWithSignature` silently accepts a typo in the signature string.

### Event encoding

- An [indexed](https://docs.soliditylang.org/en/latest/abi-spec.html#events) `string`, `bytes`, array, or struct is stored as its keccak256 hash — the value can't be recovered from the log.
- [`anonymous` events](https://docs.soliditylang.org/en/latest/contracts.html#events) drop the signature topic, allowing 4 indexed parameters, but can't be filtered by event name.
- Non-indexed parameters are ABI-encoded into the log data; contracts can't read logs back — see [ethereum.md](ethereum.md).

## Security

### Reentrancy

- An external call [re-enters](https://docs.soliditylang.org/en/latest/security-considerations.html#reentrancy) before state updates: single-function, cross-function, cross-contract, or read-only (a view function returns pre-update state to another protocol).
- Fix with [Checks-Effects-Interactions](https://docs.soliditylang.org/en/latest/security-considerations.html#use-the-checks-effects-interactions-pattern) plus a reentrancy guard; OpenZeppelin's [`ReentrancyGuardTransient`](https://docs.openzeppelin.com/contracts/5.x/api/utils#ReentrancyGuardTransient) keeps the lock in transient storage.
- Hooks are external calls too: [ERC-721](https://eips.ethereum.org/EIPS/eip-721)/[1155](https://eips.ethereum.org/EIPS/eip-1155) `safeTransfer` receivers, [ERC-777](https://eips.ethereum.org/EIPS/eip-777) hooks, and ETH sent to a contract.

### Access control

- Missing modifiers and unprotected [initializers](https://docs.openzeppelin.com/contracts/5.x/api/proxy#Initializable) let anyone call admin functions.
- Authenticate with `msg.sender`, never [`tx.origin`](https://docs.soliditylang.org/en/latest/security-considerations.html#tx-origin) — a malicious contract the owner calls can pass a `tx.origin` check.
- `msg.sender == tx.origin` no longer proves there is no code in the path: since [EIP-7702](https://eips.ethereum.org/EIPS/eip-7702) (Pectra, May 2025) a delegated EOA runs code and makes several calls per transaction.
- `code.length == 0` doesn't prove an EOA either: it's 0 for a contract still in its constructor, and a 7702-delegated EOA has code.

### Admin keys and governance

- [`Ownable2Step`](https://docs.openzeppelin.com/contracts/5.x/api/access#Ownable2Step) makes the new owner accept the transfer, so a typo in the address can't brick ownership.
- Route admin actions through a [timelock](https://docs.openzeppelin.com/contracts/5.x/api/governance#TimelockController) controlled by a multisig, giving users a window to exit before a change lands.
- Flash-loan governance attacks borrow voting power for one transaction ([Beanstalk](https://rekt.news/beanstalk-rekt/), April 2022, ~$182M lost); snapshot voting power at proposal creation ([`ERC20Votes`](https://docs.openzeppelin.com/contracts/5.x/api/token/erc20#ERC20Votes) checkpoints) and add a voting delay.

### Signature replay and malleability

- Signed messages without a nonce, chainId, and deadline can be replayed on another chain or later ([EIP-712](https://eips.ethereum.org/EIPS/eip-712) domains bind the chain and contract).
- ECDSA `s` can be flipped (`n − s`) into a second valid signature — enforce low-`s` ([EIP-2](https://eips.ethereum.org/EIPS/eip-2)) and never use a signature as a unique ID.
- Raw [`ecrecover`](https://docs.soliditylang.org/en/latest/units-and-global-variables.html#mathematical-and-cryptographic-functions) returns `address(0)` on a bad signature, which matches an unset signer — use OpenZeppelin's [`ECDSA`](https://docs.openzeppelin.com/contracts/5.x/api/utils/cryptography#ECDSA), which reverts and enforces low-`s`.
- Smart-contract wallets (Safe, [ERC-4337](https://eips.ethereum.org/EIPS/eip-4337) accounts) sign via [ERC-1271](https://eips.ethereum.org/EIPS/eip-1271) `isValidSignature`; OpenZeppelin's [`SignatureChecker`](https://docs.openzeppelin.com/contracts/5.x/api/utils/cryptography#SignatureChecker) tries ECDSA, then ERC-1271, and [ERC-6492](https://eips.ethereum.org/EIPS/eip-6492) wraps signatures from wallets not yet deployed.

### Denial of service

- Unbounded loops over user-growable arrays eventually exceed the gas limit — paginate or cap the size.
- Pushing ETH to many receivers fails if one reverts (a contract without `receive`) — switch to [pull payments](https://docs.soliditylang.org/en/latest/common-patterns.html#withdrawal-from-contracts) (a withdraw function).
- A malicious callee can return huge data that Solidity copies into memory even when discarded — a returnbomb; cap the copy with an assembly `call` (as in [`ExcessivelySafeCall`](https://github.com/nomad-xyz/ExcessivelySafeCall)).

### Randomness and block data

- [`block.prevrandao`](https://docs.soliditylang.org/en/latest/units-and-global-variables.html#block-and-transaction-properties) (0.8.18, replaced `difficulty`; [EIP-4399](https://eips.ethereum.org/EIPS/eip-4399)) is known to the proposer, who can bias it by withholding a block — use [Chainlink VRF](https://docs.chain.link/vrf) or commit-reveal.
- `blockhash(n)` returns 0 for blocks older than 256; [EIP-2935](https://eips.ethereum.org/EIPS/eip-2935) (Pectra) serves 8,191 hashes from a system contract, but the opcode is unchanged.
- Anything derived from block data can be computed by an attacker's contract in the same transaction, which reverts when the outcome is bad.

## Integration risks

### Token integration quirks

- [Non-standard ERC-20s](https://github.com/d-xo/weird-erc20) (USDT) return nothing or `false` from `transfer` — use [`SafeERC20`](https://docs.openzeppelin.com/contracts/5.x/api/token/erc20#SafeERC20).
- Fee-on-transfer and rebasing tokens break "amount sent = amount received" assumptions — measure balance deltas.
- Changing a non-zero allowance lets the spender [front-run the change](https://eips.ethereum.org/EIPS/eip-20#approve) and spend old + new.
- USDT's `approve` reverts unless the current allowance is 0 — [`SafeERC20.forceApprove`](https://docs.openzeppelin.com/contracts/5.x/api/token/erc20#SafeERC20-forceApprove-contract-IERC20-address-uint256-) resets it first.
- Blocklists (USDC, USDT) make any transfer to or from a flagged address revert.

### Oracle integration

- Never price assets off a DEX spot price — manipulation and TWAPs in [ethereum.md](ethereum.md).
- Chainlink [`latestRoundData`](https://docs.chain.link/data-feeds/api-reference#latestrounddata): check staleness (`updatedAt` against the feed's heartbeat) and `answer > 0`; on L2s also check the [sequencer uptime feed](https://docs.chain.link/data-feeds/l2-sequencer-feeds).
- Feeds have their own [decimals](https://docs.chain.link/data-feeds/api-reference#decimals) (USD pairs use 8, ETH pairs 18) — scale before combining with token amounts.

### Front-running and slippage

- Public-mempool transactions can be front-run or [sandwiched](https://ethereum.org/developers/docs/mev/#mev-examples-sandwich-trading): the attacker trades right before and after the victim's swap.
- Swap and liquidity functions take a `minAmountOut` and a `deadline` chosen off-chain by the user; a minimum computed on-chain from the current spot price protects nothing.
- Use [commit-reveal](https://en.wikipedia.org/wiki/Commitment_scheme) for bids, auctions, and games where seeing a pending transaction gives an edge; MEV mechanics in [ethereum.md](ethereum.md).

### Rounding and precision

- Round in the protocol's favor: [ERC-4626](https://eips.ethereum.org/EIPS/eip-4626#security-considerations) rounds shares down on deposit and up on withdraw.
- [First-depositor inflation attack](https://docs.openzeppelin.com/contracts/5.x/erc4626#security-concern-inflation-attack): the attacker mints 1 wei of shares and donates assets, so the next depositor's shares round down to 0 — mitigate with virtual shares ([OpenZeppelin's decimals offset](https://docs.openzeppelin.com/contracts/5.x/erc4626#defending-with-a-virtual-offset)) or dead shares.
- Tokens mix decimals (USDC 6, WETH 18) — normalize before math and never compare raw amounts across tokens.

## Gas optimization

### Gas optimization patterns

- `SSTORE` cost compares the slot's value at transaction start, now, and new ([EIP-2200](https://eips.ethereum.org/EIPS/eip-2200)): a clean slot (now == start) costs 20,000 gas from zero or 2,900 from non-zero; a dirty slot or a no-op costs 100; +2,100 if cold ([EIP-2929](https://eips.ethereum.org/EIPS/eip-2929)) — see [ethereum.md](ethereum.md).
- [Pack](https://docs.soliditylang.org/en/latest/internals/layout_in_storage.html) small variables that are read and written together into one slot.
- [`constant`/`immutable`](https://docs.soliditylang.org/en/latest/contracts.html#constant-and-immutable-state-variables) values are embedded in bytecode — no `SLOAD`.
- Cache storage reads in local variables inside loops; use `calldata` parameters.
- [Custom errors](https://docs.soliditylang.org/en/latest/contracts.html#errors) are cheaper than revert strings; the compiler [already skips overflow checks](https://soliditylang.org/blog/2023/10/25/solidity-0.8.22-release-announcement/) on simple loop-counter increments, so `unchecked { ++i; }` is no longer needed there.

### Code size limit

- Deployed code is capped at 24,576 bytes ([EIP-170](https://eips.ethereum.org/EIPS/eip-170)) and initcode at 49,152 ([EIP-3860](https://eips.ethereum.org/EIPS/eip-3860), Shanghai).
- Workarounds: move logic into external libraries, split into several contracts, lower optimizer `runs`, or use the [Diamond](https://eips.ethereum.org/EIPS/eip-2535) pattern.

### Clones and factories

- An [EIP-1167](https://eips.ethereum.org/EIPS/eip-1167) minimal proxy is 45 bytes of runtime code that `delegatecall`s a fixed implementation, so deploying many instances (vaults, wallets, pools) costs a fraction of a full deployment.
- Clones can't be upgraded and run no constructor: they need an initializer, and each call pays an extra `DELEGATECALL`.
- [`CREATE2`](https://eips.ethereum.org/EIPS/eip-1014) sets the address to `keccak256(0xff ++ deployer ++ salt ++ keccak256(initcode))[12:]`, known before deployment (counterfactual wallets).
- Derive the salt from the caller and the init parameters, or a front-runner can take the predicted address with other arguments.

## Upgradeability

### Proxy patterns

| Pattern | Upgrade logic lives in | Note |
|---|---|---|
| [Transparent](https://docs.openzeppelin.com/contracts/5.x/api/proxy#TransparentUpgradeableProxy) | proxy (admin-only path) | admin can't call the implementation |
| [UUPS](https://docs.openzeppelin.com/contracts/5.x/api/proxy#UUPSUpgradeable) ([ERC-1822](https://eips.ethereum.org/EIPS/eip-1822)) | implementation | cheaper proxy; an implementation without upgrade code bricks it |
| [Beacon](https://docs.openzeppelin.com/contracts/5.x/api/proxy#BeaconProxy) | shared beacon contract | upgrades many proxies at once |
| Diamond ([EIP-2535](https://eips.ethereum.org/EIPS/eip-2535)) | proxy routing to many facets | per-selector implementations |

- Every pattern keeps storage in the proxy and `delegatecall`s the implementation.

### Proxy storage and initializers

- The implementation address sits at the pseudo-random [EIP-1967](https://eips.ethereum.org/EIPS/eip-1967) slot, away from the implementation's own variables.
- New versions only append storage variables, never reorder — or use [ERC-7201](https://eips.ethereum.org/EIPS/eip-7201) namespaced storage.
- Constructors don't run through a proxy: use [initializers](https://docs.openzeppelin.com/contracts/5.x/api/proxy#Initializable), and call [`_disableInitializers()`](https://docs.openzeppelin.com/contracts/5.x/api/proxy#Initializable-_disableInitializers--) in the implementation's constructor.
- `immutable` values live in the implementation's bytecode, so every proxy shares the values set at implementation deployment.

### Upgrade safety

- A proxy function whose selector matches an implementation function shadows it — Transparent proxies route by caller, UUPS proxies have no functions of their own.
- An uninitialized UUPS implementation let anyone take ownership and upgrade it to a `selfdestruct` contract, bricking every proxy ([OpenZeppelin advisory, 2021](https://github.com/OpenZeppelin/openzeppelin-contracts/security/advisories/GHSA-5vp3-v4hc-gx76)); since [EIP-6780](https://eips.ethereum.org/EIPS/eip-6780) the code survives.
- [Metamorphic contracts](https://github.com/0age/metamorphic) redeployed different code at one address via `CREATE2` + `SELFDESTRUCT`; EIP-6780 (Cancun) ended the trick.
- OpenZeppelin's [Upgrades plugins](https://docs.openzeppelin.com/upgrades-plugins/) (Foundry, Hardhat) diff storage layouts and flag unsafe patterns before an upgrade.

## Errors and reverts

### Error types

- `require(cond, "msg")` and `revert("msg")` encode [`Error(string)`](https://docs.soliditylang.org/en/latest/control-structures.html#panic-via-assert-and-error-via-require) (selector `0x08c379a0`).
- `assert`, overflow, division by zero, and out-of-bounds access raise `Panic(uint256)` with codes `0x01`, `0x11`, `0x12`, `0x32`.
- [Before 0.8](https://docs.soliditylang.org/en/latest/080-breaking-changes.html), `assert` hit the `INVALID` opcode and burned all remaining gas; now it reverts like any other error.
- [Custom errors](https://docs.soliditylang.org/en/latest/contracts.html#errors) (0.8.4) encode a selector plus arguments; [`require(cond, MyError())`](https://soliditylang.org/blog/2024/09/04/solidity-0.8.27-release-announcement/) accepts them since 0.8.26 (via-IR) / 0.8.27 (legacy).

### try/catch limits

- [`try`/`catch`](https://docs.soliditylang.org/en/latest/control-structures.html#try-catch) works only on external calls and `new` contract creation, not on internal calls.
- Catches only reverts inside the callee: undecodable return data or a target with no code reverts the caller.
- Clauses: `catch Error(string memory)`, `catch Panic(uint256)`, and `catch (bytes memory)` for everything else — a custom error can't be caught by name.
- The callee can burn 63/64 of the gas ([EIP-150](https://eips.ethereum.org/EIPS/eip-150)), leaving too little for the `catch` block.

### Revert data bubbling

- A low-level [`call`](https://docs.soliditylang.org/en/latest/units-and-global-variables.html#members-of-address-types) returns `(bool success, bytes memory data)`: a callee revert gives `success == false` instead of bubbling up — always check it.
- Re-throw the callee's error unchanged with [assembly](https://docs.soliditylang.org/en/latest/assembly.html): `revert(add(data, 32), mload(data))`.
- OpenZeppelin's [`Address.functionCall`](https://docs.openzeppelin.com/contracts/5.x/api/utils#Address-functionCall-address-bytes-) does both.

## Compiler and tooling

### Compiler pipelines

- [via-IR](https://docs.soliditylang.org/en/latest/ir-breaking-changes.html) compiles through [Yul](https://docs.soliditylang.org/en/latest/yul.html): stronger cross-function optimization and fewer "stack too deep" errors (it moves variables to memory), but slower builds; legacy is still the default.
- via-IR changes some semantics: each contract initializes its state variables right before its own constructor, and modifiers reset return variables at every `_`.
- [Optimizer `runs`](https://docs.soliditylang.org/en/latest/internals/optimizer.html) (default 200) is the expected number of executions per opcode: lower favors deployment cost, higher favors call cost.

### EVM version targeting

- [`evmVersion`](https://docs.soliditylang.org/en/latest/using-the-compiler.html#setting-the-evm-version-to-target) picks the target hard fork; the default moved to `shanghai` in 0.8.20 (emits `PUSH0`, [EIP-3855](https://eips.ethereum.org/EIPS/eip-3855)), `cancun` in 0.8.25, `prague` in 0.8.30, and `osaka` in 0.8.31.
- Code with an opcode the target chain lacks fails to deploy — `PUSH0` broke L2 deployments in 2023; set `evmVersion` to the oldest chain you target.
- Pin the [pragma](https://docs.soliditylang.org/en/latest/layout-of-source-files.html#version-pragma) (`pragma solidity 0.8.37;`) in contracts you deploy; a floating `^0.8.0` suits libraries.

### Testing with Foundry

- Tests are Solidity contracts; [cheatcodes](https://www.getfoundry.sh/reference/cheatcodes/overview) (`vm.prank`, `vm.warp`, `vm.deal`, `vm.expectRevert`) set the caller, time, balances, and expected failures.
- [Fuzz tests](https://www.getfoundry.sh/forge/testing) take random arguments (256 runs by default); [`bound()`](https://www.getfoundry.sh/reference/forge-std/bound) constrains them.
- [Invariant tests](https://www.getfoundry.sh/guides/invariant-testing) call random sequences of handler functions and check properties after each (total supply = sum of balances).
- [Fork tests](https://www.getfoundry.sh/guides/fork-testing) (`--fork-url`) run against live chain state.

### Static analysis and formal verification

- [Slither](https://github.com/crytic/slither) flags known bug patterns (reentrancy, shadowing, uninitialized storage) in seconds.
- Symbolic and formal tools ([Halmos](https://github.com/a16z/halmos), [Certora](https://docs.certora.com/), the built-in [SMTChecker](https://docs.soliditylang.org/en/latest/smtchecker.html)) prove properties for all inputs, not just sampled ones.

## Inline assembly

### Memory layout

- `0x00`–`0x3f` is scratch space for hashing, `0x40` holds the [free memory pointer](https://docs.soliditylang.org/en/latest/internals/layout_in_memory.html), `0x60` is the zero slot; allocation starts at `0x80` — hence bytecode starting `6080604052`.
- Memory is never freed within a call: Solidity only bumps the free memory pointer.

### Assembly gotchas

- No overflow or bounds checks, and values narrower than 256 bits may carry [dirty upper bits](https://docs.soliditylang.org/en/latest/internals/variable_cleanup.html) — mask them.
- Mark blocks [`assembly ("memory-safe")`](https://docs.soliditylang.org/en/latest/assembly.html#memory-safety) (0.8.13) so via-IR can still move variables to memory.
- `return` and `revert` in [inline assembly](https://docs.soliditylang.org/en/latest/assembly.html) end the whole call, not just the current function.
- Storage variables expose [`.slot` and `.offset`](https://docs.soliditylang.org/en/latest/assembly.html#access-to-external-variables-functions-and-libraries); calldata arrays expose `.offset` and `.length`.
