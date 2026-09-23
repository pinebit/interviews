# Ethereum Cheatsheet

The 20 most frequently asked Ethereum interview topics, with short answers.

## 1. What types of accounts exist? What is a nonce?

There are two types of accounts. **Externally Owned Accounts (EOAs)** are controlled by a private key (secp256k1). Only EOAs can start a transaction. **Contract accounts** are controlled by their code and run only when called. Both have an address, an ETH balance, and a **nonce**. Contracts also have code and storage. An address is the last 20 bytes of the Keccak-256 hash of the public key (EOA) or is derived from the deployer's address and nonce (`CREATE`) or from a salt and init code (`CREATE2`, predictable addresses).

For an EOA, the **nonce** counts sent transactions. Each transaction must use the next nonce, which **prevents replay** and **orders** a sender's transactions. A stuck transaction blocks every later one until it is **replaced** by a transaction with the same nonce and a higher fee. Since the Pectra upgrade (2025), **EIP-7702** lets an EOA delegate to contract code, which enables batching and sponsored gas without moving funds to a new account.

## 2. How does gas work? What did EIP-1559 change?

**Gas** measures computational work. Every EVM opcode has a fixed gas cost. It prevents infinite loops (the halting problem) and prices the scarce resources: computation, storage, and bandwidth. The sender sets a **gas limit**. If execution runs out of gas, all state changes **revert, but the fee is still charged**.

Under **EIP-1559** (2021), the fee is `gasUsed × (baseFee + priorityFee)`. The **base fee** is set by the protocol. It changes by up to ±12.5% per block to keep blocks 50% full, and it is **burned**. The **priority fee** (tip) goes to the block proposer. Users set `maxFeePerGas` and `maxPriorityFeePerGas`, and any unused part of the max fee is refunded. Result: fees are easier to predict, and ETH can become deflationary when usage is high.

## 3. What is the EVM? Storage vs memory vs calldata?

The **Ethereum Virtual Machine** is a deterministic, **stack-based** VM with 256-bit words. Every node runs it to execute transactions and must reach the same resulting state. Contracts are compiled (Solidity or Vyper) to EVM bytecode. Execution is single-threaded and sandboxed, and code can't access anything outside the chain (that's what **oracles** are for).

Data locations:

- **Storage** — persistent key-value store per contract, 32-byte slots. Very expensive to write (`SSTORE` ~20k gas for zero→non-zero).
- **Memory** — temporary, erased after each external call. Cost grows quadratically with size.
- **Calldata** — read-only transaction input. The cheapest place for function arguments.
- **Stack** — up to 1024 items. Only the top 16 are reachable, which is why Solidity throws "stack too deep".
- **Transient storage** (`TSTORE`/`TLOAD`, 2024) — cleared after each transaction. Cheap reentrancy locks.

## 4. What are the most common smart contract vulnerabilities?

- **Reentrancy** — an external call lets the callee call back into your contract before state is updated (The DAO hack, 2016). Fix: the **Checks-Effects-Interactions** pattern (validate, update state, *then* make external calls) plus a reentrancy guard.
- **Access control** — missing `onlyOwner` checks, unprotected initializers, using `tx.origin` for authentication.
- **Oracle / price manipulation** — using spot DEX prices that can be moved within one transaction using a **flash loan**. Use TWAPs or Chainlink instead.
- **Integer overflow** — checked by default since Solidity 0.8. Still possible inside `unchecked` blocks.
- **Unchecked external calls** — ignoring the `bool` returned by a low-level `call`, or by `transfer` on non-standard ERC-20 tokens (use SafeERC20).
- **Front-running / signature replay** — signatures without a nonce, chainId, and deadline can be reused.
- **Denial of service** — loops over arrays with no size limit, or relying on an external call that can always revert.

Defense in depth: use audited libraries (OpenZeppelin), test with fuzzing and invariant tests (Foundry), run static analyzers (Slither), get audits, and add emergency pause mechanisms for high-value contracts.

## 5. What is the lifecycle of a transaction?

1. The user **signs** the transaction (nonce, to, value, data, gas limit, fee fields, chainId for replay protection across chains) and sends it to a node over RPC.
2. It spreads through the peer-to-peer network into the **mempool** (the pool of pending transactions).
3. A block builder picks transactions, usually by highest tip and MEV profit. With **Proposer-Builder Separation** (MEV-Boost), specialized **builders** assemble blocks and **relays** pass them to the proposer, who takes the highest bid.
4. The proposer publishes the block. Validators **attest** to it and every node re-executes it.
5. The transaction gets a **receipt** (status, gas used, logs). After about 2 epochs it is **finalized** and can't be reverted without burning a large amount of stake.

Before finality, blocks can be **reorged** (replaced by a competing chain), so exchanges and bridges wait for finality or for a number of confirmations.

## 6. How does Proof of Stake work in Ethereum?

Since **The Merge** (September 2022), Ethereum uses Proof of Stake. **Validators** stake at least **32 ETH**. Time is divided into **slots (12 s)** and **epochs (32 slots, ~6.4 min)**. Each slot has a randomly chosen **proposer** who builds the block, and a committee of validators **attests** (votes) to it.

A node runs two clients: an **execution client** (Geth, Nethermind, Reth; runs transactions and holds state) and a **consensus client** (Prysm, Lighthouse; handles PoS). They talk to each other through the Engine API.

The consensus protocol, **Gasper**, combines **LMD-GHOST** (fork choice: pick the chain with the most attestation weight) with **Casper FFG** (finality). A checkpoint that gets 2/3 of the stake's votes is **justified**, and the one before it becomes **finalized**, after about **2 epochs (~13 min)**. **Slashing** burns part of the stake for provably malicious behavior (double proposing, contradictory votes). Smaller **inactivity penalties** apply to validators that are offline.

## 7. What are the main token standards?

- **ERC-20** — fungible tokens. `transfer`, `balanceOf`, `approve` + `transferFrom` (lets a contract spend your tokens on your behalf), plus `Transfer`/`Approval` events. Issues: unlimited approvals are a security risk, and the approve race condition. **EIP-2612 `permit`** allows approvals via an off-chain signature, so no extra transaction is needed.
- **ERC-721** — NFTs. Each `tokenId` is unique and has one owner. `safeTransferFrom` checks that a receiving contract can handle NFTs (`onERC721Received`).
- **ERC-1155** — multi-token: fungible and non-fungible tokens in one contract, with batch transfers. Common in games.
- **ERC-4626** — tokenized vaults (a standard interface for yield-bearing deposits).

Tokens are just contracts: balances are a `mapping(address => uint256)` inside the token contract, not something the account holds natively like ETH.

## 8. How does Ethereum differ from Bitcoin?

The core difference is the **state model**. Bitcoin uses **UTXOs**: a transaction consumes unspent outputs and creates new ones, and a "balance" is the sum of UTXOs you can spend. It's easy to validate in parallel, and replay is impossible because an output can only be spent once. Ethereum uses **accounts** with global balances and storage, which is simpler for smart contracts but needs a **nonce** for replay protection and ordering.

Other differences: Bitcoin Script is deliberately **not Turing-complete**, while the EVM runs general-purpose programs metered by gas. Bitcoin uses **Proof of Work** with ~10-minute blocks and probabilistic finality; Ethereum uses **Proof of Stake** with 12-second slots and economic finality. Bitcoin has a **fixed 21M supply**; ETH has no hard cap but burns the base fee, so supply can shrink.

## 9. How do upgradeable contracts work? What is `delegatecall`?

Deployed contract code is **immutable**, so upgrades use a **proxy**: users call a proxy that holds all the **storage** and forwards every call via **`delegatecall`** to an **implementation** contract. `delegatecall` runs the target's code **in the caller's context** — the proxy's storage, `msg.sender`, and `msg.value`. Upgrading means pointing the proxy at a new implementation. (Plain `call` runs in the callee's context; `staticcall` forbids state changes.)

Patterns: **Transparent proxy** (admin calls go to upgrade logic, everyone else to the implementation), **UUPS** (ERC-1822, upgrade logic lives in the implementation — cheaper, but an implementation without it bricks upgrades), **Beacon** (many proxies read their implementation from one beacon), **Diamond** (EIP-2535, many implementation "facets" behind one proxy).

Pitfalls: **storage collisions** — the proxy stores the implementation address at a pseudo-random **EIP-1967 slot**, and new versions must only *append* storage variables, never reorder them (or use **ERC-7201 namespaced storage**). Constructors don't run through a proxy, so use **initializer** functions — and call `_disableInitializers()` in the implementation's constructor so nobody can initialize it directly. Upgradeability is also a trust issue: whoever controls upgrades controls the funds, so use timelocks and multisigs.

## 10. How do Layer 2 rollups work? Optimistic vs ZK?

**Rollups** execute transactions off-chain (on L2), then post compressed transaction data and the resulting **state root** to Ethereum (L1). They inherit L1's security because anyone can rebuild the L2 state from the data posted to L1. Most still rely on a centralized **sequencer** to order transactions.

- **Optimistic rollups** (Arbitrum, Optimism, Base) assume state updates are valid. Anyone can submit a **fraud proof** during a **challenge window (~7 days)**, which makes withdrawals to L1 slow.
- **ZK rollups** (zkSync, Starknet, Scroll, Linea) post a **validity proof** (SNARK/STARK) with each batch. Once the proof is verified on L1, the batch is final, so withdrawals are fast. The downside is expensive proof generation.

**EIP-4844** (Dencun, 2024) added **blobs**: cheap, temporary data (pruned after ~18 days) that is separate from calldata. It reduced L2 fees by 10–100×. **PeerDAS** (Fusaka, 2025) lets nodes check blob availability by sampling instead of downloading everything, which raises blob capacity.

## 11. What is MEV?

**Maximal Extractable Value** is the profit a block producer (or searchers who pay them) can make by **including, excluding, or reordering** transactions. Common forms: **arbitrage** between DEXs, **liquidations** in lending protocols, **front-running**, and **sandwich attacks** (buy before the victim's swap, sell right after it, and profit from the price impact the victim causes).

Mitigations for users: set tight **slippage limits**, send transactions through **private mempools/RPCs** (e.g. Flashbots Protect), use batch auctions (CoW Swap). Protocol level: PBS separates the job of finding MEV from validating, so that small validators aren't at a disadvantage. There is ongoing work on enshrined PBS (built into the protocol) and on resistance to censorship (inclusion lists).

## 12. How do signatures work? What are EIP-191 and EIP-712?

Ethereum uses **ECDSA over secp256k1**. A signature is `(r, s, v)`, and **`ecrecover`** returns the signer's address from a message hash and signature — so contracts verify signatures by comparing the recovered address. Gotchas: `ecrecover` returns **`address(0)`** for invalid signatures (always check), and signatures are **malleable** (`s` can be flipped to `n - s`) — use OpenZeppelin's `ECDSA` library, which enforces low-`s`.

**EIP-191** (`personal_sign`) prefixes messages with `"\x19Ethereum Signed Message:\n" + length`, so a signed message can never be a valid transaction. **EIP-712** signs **typed structured data** with a **domain separator** (name, version, chainId, verifying contract): wallets display readable fields, and signatures can't be replayed on another contract or chain. Always include a **nonce and deadline** in signed messages. **ERC-1271** (`isValidSignature`) lets smart contract wallets "sign" too.

## 13. How do contract calls work: ABI, selectors, `fallback`, `receive`?

A call's `data` starts with a 4-byte **function selector** — the first 4 bytes of `keccak256("transfer(address,uint256)")` — followed by **ABI-encoded** arguments in 32-byte words (dynamic types like `bytes` and arrays are encoded as offsets to their data). The contract's dispatcher compares the selector against its functions.

If no function matches, **`fallback()`** runs; plain ETH transfers with empty calldata go to **`receive()`** (or `fallback` if it's `payable` and there's no `receive`). A contract with neither rejects plain ETH. Note that `abi.encodePacked` with several dynamic arguments can produce **hash collisions** (`"a","bc"` vs `"ab","c"`) — use `abi.encode` for hashing. Different functions can share a selector by chance, which is a real risk in proxies.

## 14. How do you optimize gas?

- **Minimize storage writes and reads** — the dominant cost. A cold `SLOAD` costs 2,100 gas, a warm one 100: cache storage values in local variables inside functions.
- **Pack storage** — variables smaller than 32 bytes declared next to each other share a slot (`uint128 a; uint128 b;`).
- **`constant` and `immutable`** — values baked into bytecode, no storage read.
- **`calldata` instead of `memory`** for read-only external function arguments.
- **Custom errors** (`error Unauthorized()`) instead of revert strings.
- **`unchecked`** blocks for arithmetic that provably can't overflow (e.g. loop counters).
- **Events** instead of storage for data that contracts never read.
- **Mappings over arrays** when you don't need iteration, and no unbounded loops.

Clearing storage gives a partial refund (capped at 1/5 of the transaction's gas since EIP-3529). Measure with Foundry's gas reports rather than guessing — and don't sacrifice readability or safety for tiny savings.

## 15. How do AMMs (like Uniswap) work?

An **Automated Market Maker** replaces the order book with a **liquidity pool** and a pricing formula. Uniswap v2 uses the **constant product** formula **`x × y = k`**: a trade must keep the product of the two reserves constant (plus a 0.3% fee paid to liquidity providers), so the price is the reserve ratio. Large trades move the price more — **price impact** — which is why users set **slippage** limits.

**Liquidity providers** deposit both tokens and receive LP shares. They suffer **impermanent loss**: when the price moves, the pool automatically sells the rising asset, so LPs end up worse off than simply holding (offset by fees). **Uniswap v3** adds **concentrated liquidity** in chosen price ranges (much more capital-efficient, positions are NFTs); **v4** uses a single contract for all pools plus **hooks** for custom logic. **Curve** uses a formula optimized for assets that should trade near 1:1 (stablecoins).

## 16. What are oracles? What is the oracle problem?

Smart contracts can't access off-chain data (prices, weather, sports results), so **oracles** bring it on-chain. The **oracle problem**: the contract is only as trustworthy as its data source — a single-source oracle is a centralized point of failure and manipulation.

**Chainlink** uses decentralized networks of nodes that aggregate data from many sources and **push** updates when the price moves beyond a deviation threshold or a heartbeat elapses. Consumers must check **staleness** (`updatedAt`) and, on L2s, the sequencer uptime feed. **Pull oracles** (Pyth) let users submit signed price updates with their transaction. **On-chain TWAPs** (time-weighted average prices from Uniswap) are trustless but lag, and can be manipulated in low-liquidity pools. Randomness is a special case: `block.prevrandao` is somewhat predictable to validators, so use **Chainlink VRF** for verifiable randomness.

## 17. How is state stored? What are events/logs?

Ethereum stores its world state (address → account) in a **Merkle Patricia Trie**. Each contract's storage is also a trie. Every block header contains three **roots**: the **state root**, the **transactions root**, and the **receipts root**. A single hash commits to all the data, so a **light client** can verify a balance or transaction with a **Merkle proof** without downloading the full state. Planned upgrades: **Verkle trees** or binary tries with smaller proofs, and **stateless clients**.

**Events** (logs) are written to transaction receipts, not to contract storage. They are **much cheaper** than storage but **can't be read by contracts**. They exist for off-chain consumers (indexers, UIs, The Graph). Up to 3 `indexed` parameters become **topics** that can be searched (plus the event signature hash as topic 0). Each block header has a **bloom filter** over its logs, so nodes can quickly skip blocks that don't contain a given event.

## 18. What is account abstraction (ERC-4337)?

**Account abstraction** makes accounts programmable: validation logic (who can sign, how, and who pays gas) is defined in a **smart contract wallet** instead of being fixed to one ECDSA key. This enables **multisig**, **passkeys**, **social recovery**, spending limits, **batched calls**, and **gas sponsorship** or paying gas in ERC-20 tokens.

**ERC-4337** (2023) does it without protocol changes: users sign **UserOperations** that go to a separate mempool; **bundlers** pack them into a normal transaction that calls the singleton **EntryPoint** contract, which calls each wallet's `validateUserOp` and then executes. **Paymasters** are contracts that pay gas on the user's behalf. **EIP-7702** (Pectra, 2025) complements it: an existing EOA can delegate to smart wallet code while keeping its address, so users get these features without migrating funds.

## 19. How do lending protocols and flash loans work?

Lending protocols (**Aave**, **Compound**) pool deposits and let users borrow against **over-collateralized** positions. Each asset has a max **loan-to-value** and a **liquidation threshold**; the **health factor** summarizes a position. If it drops below 1 (collateral price falls), anyone can **liquidate**: repay part of the debt and receive collateral at a discount (the liquidation bonus). Interest rates follow a curve based on the pool's **utilization**.

A **flash loan** lends any amount **with no collateral**, on the condition that it's repaid (plus a small fee) **in the same transaction** — otherwise the whole transaction reverts, as if the loan never happened. Legitimate uses: arbitrage, liquidations, swapping collateral. It also gives attackers huge temporary capital, which turns small bugs — like reading a manipulable spot price — into large exploits.

## 20. How do bridges work and why are they risky?

Bridges move assets and messages between chains. Models: **lock-and-mint** (lock tokens on chain A, mint a wrapped version on chain B), **burn-and-mint** (issuer burns and re-mints the native token, e.g. Circle's CCTP for USDC), and **liquidity networks** (LPs on both chains swap native assets). A rollup's **canonical bridge** inherits L1 security but is slower (e.g. the optimistic challenge window).

The key question is **who verifies that the event on the source chain really happened**: a multisig or external validator set (trusted — the weakest model), optimistic verification with fraud proofs, or **light clients / ZK proofs** (trust-minimized). Bridges hold large pools of locked funds, so they're prime targets: **Ronin** ($625M, compromised validator keys), **Wormhole** ($325M, signature verification bug), **Nomad** ($190M, bad initialization let anyone forge messages).
