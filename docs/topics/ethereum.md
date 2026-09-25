# Ethereum

What experienced Ethereum engineers forget before an interview, grouped by subtopic.

## Accounts and transactions

### Account model

- **EOA** (controlled by a secp256k1 key) vs **contract account** (controlled by its code); only EOAs originate transactions.
- The **nonce** counts an EOA's sent transactions — it prevents replay and orders them.
- A stuck transaction blocks every later nonce until replaced by one with the same nonce and a higher fee.

### Address derivation

- EOA: last 20 bytes of `keccak256(pubkey)`.
- **`CREATE`**: last 20 bytes of `keccak256(rlp([sender, nonce]))`.
- **`CREATE2`**: derived from the deployer, a salt, and the init code hash, so an address is predictable before deployment (counterfactual wallets).

### Transaction types

| Type | EIP | Adds |
|---|---|---|
| 0 | legacy | single `gasPrice` |
| 1 | 2930 | access lists (pre-warmed addresses and slots) |
| 2 | **1559** | base fee + priority fee |
| 3 | **4844** | blobs for rollup data |
| 4 | **7702** | set-code: an EOA delegates to contract code (Pectra, May 2025) |

### Transaction lifecycle

- Signed → propagated to the **mempool** → a builder assembles a block (**PBS** via MEV-Boost separates building from proposing) → the proposer publishes it → validators attest.
- **Finalized after 2 epochs (~12.8 min)**; before that a block can be reorged, so exchanges and bridges wait for finality or several confirmations.

## Gas and fees

### EIP-1559 fee market

- Fee = `gasUsed × (baseFee + priorityFee)`; users set `maxFeePerGas` and `maxPriorityFeePerGas`, and unused headroom is refunded.
- The **base fee** moves up to **±12.5%** per block toward a 50%-full target and is **burned**; the tip goes to the proposer.
- ETH supply shrinks whenever the burn exceeds new issuance.

### Calldata costs

- A transaction costs **21,000** gas base; calldata costs 16 gas per non-zero byte, 4 per zero byte.
- **EIP-7623** (Pectra) adds a floor of 40/10 gas per non-zero/zero byte for data-heavy transactions, pushing bulk data to blobs.

### Storage access costs

- EIP-2929: the first (**cold**) `SLOAD` of a slot costs **2,100**; the first touch of an address (`CALL`, `BALANCE`, `EXT*`) costs 2,600; any warm access costs 100.
- Clearing a slot to zero earns a refund, capped at **1/5** of the transaction's gas since London (EIP-3529, was 1/2).

### Gas limits

- **EIP-7825** (Fusaka, December 2025) caps one transaction at **2²⁴ ≈ 16.7M gas**, whatever the block limit.
- The block gas limit isn't fixed by protocol: validators move it by up to ~1/1024 per block, so any number is a snapshot.

## EVM and storage

### Execution model

- Stack-based, **256-bit words**, stack depth 1024 — only the top **16** items are reachable, the source of "stack too deep".
- Memory expansion cost is **quadratic** in size; storage is the most expensive resource, priced per 32-byte slot.

### Storage layout

- Variables under 32 bytes **pack** into shared slots in declaration order.
- A `mapping` value lives at **`keccak256(key . slot)`**; a dynamic array stores its length at the slot and elements from `keccak256(slot)`.

### Transient storage and SELFDESTRUCT

- **Transient storage** (`TSTORE`/`TLOAD`, EIP-1153, Cancun) costs 100 gas and is cleared after each transaction — cheap reentrancy locks.
- **`SELFDESTRUCT`** only sends ETH since Cancun (**EIP-6780**); code and storage are deleted only when called in the same transaction as creation.

### Events and logs

- Logs live in the **receipt**, not storage — far cheaper, but contracts can't read them.
- Up to **3 indexed** parameters become searchable topics, plus the event signature hash as topic 0.

### World state and light clients

- World state (address → account) is a **Merkle Patricia Trie**; each contract's storage is its own trie.
- A block header commits to the state, transactions, and receipts roots, so a **light client** verifies a balance or receipt with a Merkle proof instead of the full state.

## Solidity

### Data locations

- **`storage`** is persistent state; `memory` is per call; **`calldata`** is read-only input — the cheapest location for external array and struct parameters.
- Storage → memory assignment **copies**; memory → memory copies only the reference; a local `storage` variable is a pointer into state.

### Checked arithmetic

- Overflow and underflow **revert since 0.8** (`Panic(0x11)`); `unchecked { }` opts out for proven-safe math.
- Division **truncates**, so multiply before dividing to keep precision.

### Gas optimization patterns

- **Pack** small variables that are read and written together into one slot.
- **`constant`/`immutable`** values are embedded in bytecode — no `SLOAD`.
- Cache storage reads in local variables inside loops; use `calldata` parameters.
- **Custom errors** (0.8.4) are cheaper than revert strings; 0.8.22 made simple loop-counter increments unchecked automatically.

## Calls and ABI

### Function selectors and fallback

- Calldata starts with a 4-byte **selector** (first 4 bytes of `keccak256("fn(types)")`) followed by ABI-encoded arguments; selectors can collide, a risk in proxy dispatchers.
- No matching selector → **`fallback()`**; plain ETH with empty calldata → **`receive()`** (or a payable fallback); a contract with neither rejects plain ETH.

### call, delegatecall, staticcall

- `call` runs in the callee's context; **`delegatecall`** runs the callee's code on the **caller's** storage, `msg.sender`, and `msg.value`; `staticcall` forbids state changes.
- The **63/64 rule**: a call forwards at most 63/64 of remaining gas, keeping 1/64 for the caller.

### ABI encoding pitfalls

- Low-level `call` returns a **`bool`** instead of reverting — always check it.
- **`abi.encodePacked`** of several dynamic values can collide (`("a","bc")` vs `("ab","c")`) — hash `abi.encode` output for signatures.

## Smart contract security

### Reentrancy

- An external call re-enters before state updates: **single-function**, cross-function, or **read-only** (a view function returns pre-update state to another protocol).
- Fix with **Checks-Effects-Interactions** plus a reentrancy guard.

### Access control

- Missing modifiers and **unprotected initializers** let anyone call admin functions.
- Authenticate with `msg.sender`, never **`tx.origin`** — a malicious contract the owner calls can pass a `tx.origin` check.

### Oracle manipulation

- A DEX **spot price** can be moved within one transaction using a flash loan, then read by a victim protocol.
- Use **TWAPs** or a push oracle such as Chainlink, and check staleness.

### Signature replay and malleability

- Signed messages without a **nonce, chainId, and deadline** can be replayed on another chain or later.
- ECDSA `s` can be flipped (`n − s`) into a second valid signature — enforce **low-`s`** and never use a signature as a unique ID.

### Token integration quirks

- Non-standard ERC-20s return nothing or `false` from `transfer` — use **SafeERC20**.
- **Fee-on-transfer** and rebasing tokens break "amount sent = amount received" assumptions — measure balance deltas.
- Unbounded loops over user-growable arrays become a gas **denial of service**.

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

## Signatures and standards

### Signing

- ECDSA over **secp256k1**, signature `(v, r, s)`; **`ecrecover`** returns `address(0)` for an invalid signature — always check.
- **EIP-191** (`personal_sign`) prefixes messages so a signed message can never double as a transaction.

### EIP-712 and permits

- **EIP-712** signs typed data with a domain separator (name, version, chainId, contract) — readable in wallets, not replayable across contracts or chains.
- **ERC-1271** lets contract wallets "sign" via `isValidSignature`.
- **EIP-2612 `permit`** and Permit2 grant ERC-20 approvals by signature instead of a transaction.

### Token standards

| Standard | Kind | Note |
|---|---|---|
| ERC-20 | fungible | `approve` + `transferFrom`; infinite approvals are a risk |
| ERC-721 | NFT, unique `tokenId` | `safeTransferFrom` calls `onERC721Received` (a reentrancy point) |
| ERC-1155 | multi-token | batch transfers |
| ERC-4626 | tokenized vault | share/asset math; first-depositor inflation attack |

### Account abstraction

- **ERC-4337**: users sign UserOperations, bundlers submit them to a singleton EntryPoint, and **paymasters** can sponsor gas — no protocol change.
- **EIP-7702** lets an existing EOA delegate to smart-wallet code while keeping its address.

## Consensus (PoS)

### Slots, epochs, finality

- **12 s slots**, 32-slot (~6.4 min) epochs; each slot has a random proposer and a committee that attests.
- **Gasper** = LMD-GHOST (fork choice by attestation weight) + **Casper FFG** (checkpoints with 2/3 of stake become justified, then finalized).

### Slashing and penalties

- **Slashing** burns stake for provable misbehavior: double proposals or contradictory (surround or double) attestations.
- The **inactivity leak** drains offline validators while the chain can't finalize.
- EIP-7251 (Pectra) raised the **maximum effective balance to 2048 ETH**, so large operators consolidate validators.

## Scaling

### Rollups

| Type | Examples | Proof | L1 withdrawal |
|---|---|---|---|
| **Optimistic** | Arbitrum, OP Mainnet, Base | fraud proofs in a challenge window | ~7 days |
| **ZK** | zkSync, Starknet, Scroll, Linea | validity proof per batch | once the proof verifies |

### Sequencers and data availability

- Rollups post transaction data to L1 for **data availability**, so anyone can rebuild state and challenge or exit.
- Most use a **centralized sequencer** for ordering, with forced inclusion through L1 as the censorship backstop.

### Blobs and PeerDAS

- **EIP-4844** blobs are cheap, temporary data (pruned after ~18 days), separate from calldata.
- **PeerDAS** (Fusaka) lets nodes check blob availability by **sampling**; Blob Parameter Only (BPO) forks then raise blob capacity without other changes.

## DeFi and MEV

### AMMs

- Uniswap v2: constant product **`x·y = k`**; larger trades move the price more, hence slippage limits.
- **Impermanent loss**: the pool sells the rising asset, so LPs can end up worse than holding, offset by fees.
- v3 adds **concentrated liquidity** in chosen price ranges; v4 uses a singleton contract with hooks.

### Lending and flash loans

- Lending (Aave, Compound) is over-collateralized; a **health factor** below 1 allows liquidation at a discount.
- **Flash loans** are uncollateralized but must be repaid in the same transaction or everything reverts — turning manipulable prices into large exploits.

### MEV

- **Sandwich attacks** (front-run and back-run a victim's swap), arbitrage back-running, and liquidations.
- Mitigations: private order flow (Flashbots Protect), tight **slippage limits**, and PBS so small validators earn MEV too.

### Bridge exploits

- Bridges hold large locked pools, making them prime targets.
- **Ronin** (5 of 9 validator keys compromised), **Wormhole** (signature verification bypass), **Nomad** (bad initialization let anyone forge messages).
