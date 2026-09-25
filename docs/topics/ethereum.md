# Ethereum

What experienced Ethereum engineers forget before an interview, grouped by subtopic.

## Accounts and transactions

### Account model

- **EOA** (controlled by a secp256k1 key) vs **contract account** (controlled by its code); only EOAs originate transactions.
- **Nonce** counts sent transactions per EOA — prevents replay and orders transactions; a stuck transaction blocks all later ones until replaced by the same nonce with a higher fee.
- Address derivation: EOA = last 20 bytes of `keccak256(pubkey)`; `CREATE` = last 20 bytes of `keccak256(rlp([sender, nonce]))`; `CREATE2` = deterministic from a salt and init code, so a not-yet-deployed address is predictable.

### Transaction types and lifecycle

- Types: legacy, **2930** (access lists), **1559** (base fee + priority fee), **4844** (blob), **7702** (set-code, EOA delegates to contract code, from Pectra, May 2025).
- Lifecycle: signed → propagated to the **mempool** → a **builder** assembles a block (MEV-Boost / PBS separates block-building from proposing) → the proposer publishes it → validators **attest** → finalized after **2 epochs (~12.8 min)**.
- Before finality a block can be **reorged**; exchanges and bridges wait for finality or a number of confirmations.

## Gas and fees

### EIP-1559 fee market

- Fee = `gasUsed × (baseFee + priorityFee)`. **Base fee** is set by the protocol, moves **±12.5%** per block toward a 50%-full target, and is **burned**. **Priority fee** (tip) goes to the proposer.
- Users set `maxFeePerGas` / `maxPriorityFeePerGas`; unused headroom is refunded.
- Only the **base fee** is burned (the tip is not), so ETH supply shrinks whenever burn exceeds new issuance.

### Gas costs and refunds

- Base transaction cost **21,000** gas; calldata costs **16 gas/non-zero byte, 4 gas/zero byte**.
- **EIP-7623** (Pectra, May 2025) adds a calldata **floor price** (40/10 gas per non-zero/zero byte) for data-heavy transactions, pushing bulk data to blobs.
- **EIP-7825** (Fusaka, Dec 2025) caps a single transaction at **2²⁴ ≈ 16.7M gas**, independent of the block gas limit.
- **Cold/warm access** (EIP-2929): first touch of a storage slot in a transaction (cold `SLOAD`) costs **2,100**; first touch of an address (cold `CALL`/`BALANCE`/`EXT*`) costs **2,600**; any warm (already-touched) access costs **100**.
- Clearing a storage slot to zero gives a partial gas refund, capped at **1/5** of the transaction's total gas (EIP-3529, down from the pre-London 1/2).
- The per-block gas limit is not fixed by protocol — it moves by validator vote, roughly ±1/1024 per block — so treat any specific number as a snapshot, not a constant.

## EVM and storage

### Execution model

- Stack-based, **256-bit words**, stack depth **1024** (only the top 16 items are directly reachable — the source of Solidity's "stack too deep").
- Memory expansion cost is **quadratic** in size; storage (`SSTORE`/`SLOAD`) is the most expensive resource, priced per 32-byte slot.
- Storage layout: variables under 32 bytes pack into shared slots; a `mapping`'s value slot is `keccak256(key . baseSlot)`; dynamic arrays store length at the slot and elements at `keccak256(slot)`.

### Transient storage and logs

- **Transient storage** (`TSTORE`/`TLOAD`, EIP-1153, Cancun) is cleared after each transaction — cheap reentrancy locks without permanent storage cost.
- **Logs** (events) live in the receipt, not storage: up to **3 indexed** parameters become searchable topics (plus the event signature hash as topic 0); contracts cannot read their own logs.
- `CREATE`/`CREATE2` addresses as above; **`SELFDESTRUCT`** no longer deletes code/storage or refunds gas except when called in the same transaction as creation (EIP-6780, neutered post-Cancun).

### World state and light clients

- World state (address → account) is a **Merkle Patricia Trie**; each contract's storage is its own trie. A block header commits to three roots: **state root**, **transactions root**, **receipts root**.
- A single root hash lets a **light client** verify a balance, transaction, or receipt with a compact **Merkle proof**, without downloading the full state — the mechanism behind "trust-minimized" wallets and cross-chain bridges that verify L1 state.

## Calls and ABI

### Dispatch and low-level calls

- A call's `data` starts with a 4-byte **selector** (first 4 bytes of `keccak256("fn(types)")`) followed by ABI-encoded arguments; different functions can collide on a selector by chance, a real risk in proxy dispatchers.
- No matching selector → **`fallback()`** runs; plain ETH transfer with empty calldata → **`receive()`** (or payable `fallback` if no `receive`); a contract with neither rejects plain ETH.
- **`call`** runs in the callee's context; **`delegatecall`** runs the callee's code in the **caller's** storage/`msg.sender`/`msg.value`; **`staticcall`** forbids state changes.
- The **63/64 rule**: a call forwards at most 63/64 of remaining gas, leaving 1/64 with the caller — relevant for reentrancy-guard gas-griefing analysis.
- Always check the `bool` return of a low-level `call`; `abi.encodePacked` of several dynamic arguments can collide (`("a","bc")` vs `("ab","c")`) — use `abi.encode` when hashing for signatures.

## Smart contract security

### Reentrancy, access control, oracles

- **Reentrancy** (single-function, cross-function, and **read-only** reentrancy via view functions reading pre-update state) — fix with **Checks-Effects-Interactions** plus a guard.
- **Access control** — missing `onlyOwner`, unprotected initializers, using `tx.origin` instead of `msg.sender` for auth.
- **Oracle/price manipulation** — spot DEX prices moved within one transaction via flash loan; use TWAPs or a push oracle like Chainlink instead.
- **Signature replay/malleability** — missing nonce/chainId/deadline in signed messages; `s` can be flipped (`n - s`) unless the verifier enforces low-`s`.

### Unchecked calls, proxies, token quirks

- **Unchecked calls** — ignoring a low-level `call`'s return, or `transfer`/`transferFrom` on non-standard ERC-20s (use SafeERC20).
- **Delegatecall storage collisions**, **uninitialized proxies**, **fee-on-transfer/rebasing tokens** breaking balance assumptions, **unbounded-loop DoS**.
- Integer over/underflow is checked by default **since Solidity 0.8** — still possible inside `unchecked` blocks.

## Upgradeability

### Proxy patterns

- All upgrade patterns route calls through a proxy that holds **storage** and `delegatecall`s to an **implementation**.

| Pattern | Upgrade logic lives in | Note |
|---|---|---|
| **Transparent** | proxy (admin-only path) | admin can't call the implementation |
| **UUPS** (ERC-1822) | implementation | cheaper proxy; an implementation without upgrade code bricks it |
| **Beacon** | shared beacon contract | upgrades many proxies at once |
| **Diamond** (EIP-2535) | proxy routing to many facets | per-selector implementations |

- Implementation address stored at the pseudo-random **EIP-1967** slot to avoid collision with the implementation's own variables; new versions must only **append** storage, never reorder — or use **ERC-7201 namespaced storage**.
- Constructors don't run through a proxy — use **initializer** functions, and call `_disableInitializers()` in the implementation's own constructor so it can't be initialized directly.

## Signatures and standards

### Signing

- ECDSA over **secp256k1**; signature is `(v, r, s)`. **`ecrecover`** returns `address(0)` on an invalid signature — always check.
- **EIP-191** (`personal_sign`) prefixes messages so a signed message can never double as a valid transaction.
- **EIP-712** signs typed structured data with a domain separator (name, version, chainId, verifying contract) — human-readable in wallets, not replayable across contracts/chains.
- **ERC-1271** lets smart-contract wallets "sign" via `isValidSignature`; **EIP-2612 `permit`** and **Permit2** allow ERC-20 approvals via an off-chain signature instead of a transaction.

### Token and account standards

- **ERC-20** fungible, **ERC-721** NFTs (unique `tokenId`, `safeTransferFrom` checks `onERC721Received`), **ERC-1155** multi-token with batch transfers, **ERC-4626** tokenized yield vaults.
- **ERC-4337** account abstraction: users sign **UserOperations**, **bundlers** submit them to a singleton **EntryPoint**, **paymasters** can sponsor gas — all without protocol changes.
- **EIP-7702** complements it: an EOA can delegate to smart-wallet code while keeping its address, avoiding fund migration.

## Consensus (PoS)

### Gasper

- Time is divided into **12 s slots** and **32-slot (~6.4 min) epochs**; each slot has a randomly chosen proposer and a committee that **attests**.
- **Gasper** = **LMD-GHOST** (fork choice: heaviest attestation weight) + **Casper FFG** (finality: 2/3-stake-voted checkpoints become justified, then finalized ~2 epochs later).
- **Slashing** burns stake for provably malicious behavior (double proposing, surrounding/contradictory attestations); smaller **inactivity leak** penalties hit offline validators, worse during non-finality.
- **Maximum effective balance raised to 2048 ETH** (EIP-7251, Pectra) lets large operators consolidate validators instead of running many at the old 32 ETH cap.

## Scaling

### Rollups

- **Optimistic** (Arbitrum, Optimism, Base) assumes validity, allows **fraud proofs** during a challenge window (~7 days) — slow withdrawals to L1.
- **ZK** (zkSync, Starknet, Scroll, Linea) posts a validity proof per batch — fast finality on L1 once verified, at the cost of expensive proof generation.
- Both post data to L1 for **data availability**; most still rely on a centralized **sequencer** for ordering, with forced-inclusion mechanisms as a censorship-resistance backstop.

### Blobs and PeerDAS

- **EIP-4844** blobs are cheap, temporary data separate from calldata, pruned after a retention window measured in days, not permanently stored.
- **Fusaka**'s **PeerDAS** lets nodes verify blob availability by sampling instead of downloading every blob, and ships alongside **Blob Parameter Only (BPO)** forks that step up blob target/max capacity without further protocol changes.

## DeFi and MEV

### AMMs

- Uniswap v2: constant product **`x·y = k`**; larger trades move price more (**price impact**), hence **slippage** limits.
- **Impermanent loss**: as price moves, the pool sells the rising asset, so LPs can end up worse off than holding, offset by trading fees.
- **v3** adds **concentrated liquidity** in chosen price ranges (positions as NFTs, more capital-efficient); **v4** uses a singleton contract plus **hooks** for custom pool logic.

### Lending and MEV

- Lending (Aave, Compound): over-collateralized borrowing; **health factor** below 1 triggers **liquidation** at a discount.
- **Flash loans** — uncollateralized, must be repaid in the same transaction or the whole transaction reverts; legitimate for arbitrage/liquidation/collateral swaps, but turn manipulable spot prices into large exploits.
- **MEV** types: sandwich attacks, back-running/arbitrage, liquidations. Mitigations: private order flow (e.g. Flashbots Protect), slippage limits, PBS to keep small validators competitive.
- Bridges are prime exploit targets since they hold large locked pools: **Ronin** (compromised validator keys), **Wormhole** (signature verification bug), **Nomad** (bad initialization let anyone forge messages).
