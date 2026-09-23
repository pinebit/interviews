# Ethereum Cheatsheet

The 10 most frequently asked Ethereum interview topics, with short answers.

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

## 4. How does Proof of Stake work in Ethereum?

Since **The Merge** (September 2022), Ethereum uses Proof of Stake. **Validators** stake at least **32 ETH**. Time is divided into **slots (12 s)** and **epochs (32 slots, ~6.4 min)**. Each slot has a randomly chosen **proposer** who builds the block, and a committee of validators **attests** (votes) to it. A node runs two clients: an **execution client** (Geth, Nethermind, Reth; runs transactions and holds state) and a **consensus client** (Prysm, Lighthouse; handles PoS). They talk to each other through the Engine API.

The consensus protocol, **Gasper**, combines **LMD-GHOST** (fork choice: pick the chain with the most attestation weight) with **Casper FFG** (finality). A checkpoint that gets 2/3 of the stake's votes is **justified**, and the one before it becomes **finalized**, after about **2 epochs (~13 min)**. **Slashing** burns part of the stake for provably malicious behavior (double proposing, contradictory votes). Smaller **inactivity penalties** apply to validators that are offline.

## 5. What is the lifecycle of a transaction?

1. The user **signs** the transaction (nonce, to, value, data, gas limit, fee fields, chainId for replay protection across chains) and sends it to a node over RPC.
2. It spreads through the peer-to-peer network into the **mempool** (the pool of pending transactions).
3. A block builder picks transactions, usually by highest tip and MEV profit. With **Proposer-Builder Separation** (MEV-Boost), specialized **builders** assemble blocks and **relays** pass them to the proposer, who takes the highest bid.
4. The proposer publishes the block. Validators **attest** to it and every node re-executes it.
5. The transaction gets a **receipt** (status, gas used, logs). After about 2 epochs it is **finalized** and can't be reverted without burning a large amount of stake.

Before finality, blocks can be **reorged** (replaced by a competing chain), so exchanges and bridges wait for finality or for a number of confirmations.

## 6. What is MEV?

**Maximal Extractable Value** is the profit a block producer (or searchers who pay them) can make by **including, excluding, or reordering** transactions. Common forms: **arbitrage** between DEXs, **liquidations** in lending protocols, **front-running**, and **sandwich attacks** (buy before the victim's swap, sell right after it, and profit from the price impact the victim causes).

Mitigations for users: set tight **slippage limits**, send transactions through **private mempools/RPCs** (e.g. Flashbots Protect), use batch auctions (CoW Swap). Protocol level: PBS separates the job of finding MEV from validating, so that small validators aren't at a disadvantage. There is ongoing work on enshrined PBS (built into the protocol) and on resistance to censorship (inclusion lists).

## 7. What are the most common smart contract vulnerabilities?

- **Reentrancy** — an external call lets the callee call back into your contract before state is updated (The DAO hack, 2016). Fix: the **Checks-Effects-Interactions** pattern (validate, update state, *then* make external calls) plus a reentrancy guard.
- **Access control** — missing `onlyOwner` checks, unprotected initializers, using `tx.origin` for authentication.
- **Oracle / price manipulation** — using spot DEX prices that can be moved within one transaction using a **flash loan**. Use TWAPs or Chainlink instead.
- **Integer overflow** — checked by default since Solidity 0.8. Still possible inside `unchecked` blocks.
- **Unchecked external calls** — ignoring the `bool` returned by a low-level `call`, or by `transfer` on non-standard ERC-20 tokens (use SafeERC20).
- **Front-running / signature replay** — signatures without a nonce, chainId, and deadline can be reused.
- **Denial of service** — loops over arrays with no size limit, or relying on an external call that can always revert.

## 8. What are the main token standards?

- **ERC-20** — fungible tokens. `transfer`, `balanceOf`, `approve` + `transferFrom` (lets a contract spend your tokens on your behalf), plus `Transfer`/`Approval` events. Issues: unlimited approvals are a security risk, and the approve race condition. **EIP-2612 `permit`** allows approvals via an off-chain signature, so no extra transaction is needed.
- **ERC-721** — NFTs. Each `tokenId` is unique and has one owner. `safeTransferFrom` checks that a receiving contract can handle NFTs (`onERC721Received`).
- **ERC-1155** — multi-token: fungible and non-fungible tokens in one contract, with batch transfers. Common in games.
- **ERC-4626** — tokenized vaults (a standard interface for yield-bearing deposits).

Tokens are just contracts: balances are a `mapping(address => uint256)` inside the token contract, not something the account holds natively like ETH.

## 9. How do Layer 2 rollups work? Optimistic vs ZK?

**Rollups** execute transactions off-chain (on L2), then post compressed transaction data and the resulting **state root** to Ethereum (L1). They inherit L1's security because anyone can rebuild the L2 state from the data posted to L1. Most still rely on a centralized **sequencer** to order transactions.

- **Optimistic rollups** (Arbitrum, Optimism, Base) assume state updates are valid. Anyone can submit a **fraud proof** during a **challenge window (~7 days)**, which makes withdrawals to L1 slow.
- **ZK rollups** (zkSync, Starknet, Scroll, Linea) post a **validity proof** (SNARK/STARK) with each batch. Once the proof is verified on L1, the batch is final, so withdrawals are fast. The downside is expensive proof generation.

**EIP-4844** (Dencun, 2024) added **blobs**: cheap, temporary data (pruned after ~18 days) that is separate from calldata. It reduced L2 fees by 10–100×. **PeerDAS** (Fusaka, 2025) lets nodes check blob availability by sampling instead of downloading everything, which raises blob capacity.

## 10. How is state stored? What are events/logs?

Ethereum stores its world state (address → account) in a **Merkle Patricia Trie**. Each contract's storage is also a trie. Every block header contains three **roots**: the **state root**, the **transactions root**, and the **receipts root**. A single hash commits to all the data, so a **light client** can verify a balance or transaction with a **Merkle proof** without downloading the full state. Planned upgrades: **Verkle trees** or binary tries with smaller proofs, and **stateless clients**.

**Events** (logs) are written to transaction receipts, not to contract storage. They are **much cheaper** than storage but **can't be read by contracts**. They exist for off-chain consumers (indexers, UIs, The Graph). Up to 3 `indexed` parameters become **topics** that can be searched (plus the event signature hash as topic 0). Each block header has a **bloom filter** over its logs, so nodes can quickly skip blocks that don't contain a given event.
