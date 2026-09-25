# Networking

What experienced engineers forget about networking before an interview, grouped by subtopic. For TLS see [security.md](security.md); for load balancers, CDNs, and real-time delivery see [system.md](system.md); for sockets and epoll see [os.md](os.md).

## End to end

### Loading a URL

- **DNS** resolves the name → **TCP** handshake (1 RTT) → **TLS 1.3** handshake (1 RTT) → HTTP request → response → the browser parses and renders ([frontend.md](frontend.md)).
- A cold HTTPS request over TCP costs about **3 RTTs** before the first response byte; **HTTP/3** saves one, and resumption with 0-RTT saves more.
- Every later request reuses the connection, which is why keep-alive and connection pools matter.

### Debugging tools

- `dig` (DNS answer, TTL), `curl -v` and `curl -w '%{time_connect} %{time_appconnect} %{time_starttransfer}'` (per-phase timing).
- `ss -tanp` (sockets and states), `traceroute`/`mtr` (path, TTL expiry), `tcpdump`/Wireshark (packets).

## TCP

### Handshake and connection queues

- **SYN → SYN-ACK → ACK**: one RTT before any data.
- The kernel keeps a **SYN queue** (half-open) and an **accept queue** (established, waiting for `accept()`); an overflowing accept queue drops connections under load.
- A **SYN flood** fills the SYN queue; **SYN cookies** encode state in the sequence number so no queue slot is needed.

### Teardown and TIME_WAIT

- The side that **closes first** enters **TIME_WAIT** for 2×MSL (**60 s** on Linux) so delayed packets can't corrupt a new connection on the same port pair.
- Many short-lived outbound connections exhaust **ephemeral ports** (~28k by default) — reuse connections (keep-alive, pooling) instead of tuning the kernel.
- Many connections in **CLOSE_WAIT** mean the application never called `close()` — a bug in your code, not the network.

### Flow and congestion control

- **Flow control** (receive window) protects the receiver; **congestion control** (congestion window) protects the network.
- **Slow start** begins at **10 segments (~14 KB)** and roughly doubles per RTT — why the first 14 KB of a page matter and why new connections are slow.
- Throughput ≤ window / RTT (**bandwidth-delay product**) — high-latency links need large windows.
- **CUBIC** (Linux default) backs off on packet loss; **BBR** models bandwidth and RTT instead, doing better on lossy links.

### Nagle and delayed ACKs

- **Nagle's algorithm** holds small writes until earlier data is acknowledged; combined with the receiver's **delayed ACK** it adds up to **~40 ms** stalls for request-response traffic.
- Set **`TCP_NODELAY`** for latency-sensitive protocols (most RPC libraries do).

### Head-of-line blocking

- TCP delivers bytes in order, so one lost packet stalls everything behind it — even data for unrelated HTTP/2 streams.

### UDP

- No handshake, ordering, retransmission, or congestion control — the application decides.
- Used where latency beats reliability or the protocol handles it itself: DNS, VoIP, games, **QUIC**.

## HTTP versions

### HTTP/1.1

- Persistent connections (keep-alive), but **one outstanding request per connection** in practice (pipelining is unused).
- Browsers open about **6 connections per host** to parallelize — the reason for old tricks like domain sharding and sprite sheets.

### HTTP/2

- Binary framing with many **multiplexed streams** on one TCP connection and **HPACK** header compression.
- Fixes HTTP-level head-of-line blocking but not TCP-level: one lost packet stalls all streams.
- Server push is effectively dead — **Chrome removed it in 2022**; use `103 Early Hints` or preload instead.

### HTTP/3 and QUIC

- **QUIC** runs over UDP with TLS 1.3 built in: **1-RTT** setup (0-RTT on resumption) and loss recovery **per stream**, so no cross-stream head-of-line blocking.
- **Connection migration**: a connection ID survives an IP change (Wi-Fi → cellular).
- Clients discover it via the `Alt-Svc` header or a DNS **HTTPS** record; many networks block UDP, so browsers fall back to TCP.

### WebSocket handshake

- Starts as HTTP/1.1 **`Upgrade: websocket`** → **`101 Switching Protocols`**, then framed full-duplex messages on the same TCP connection.
- Proxies and load balancers need idle timeouts above the app's ping interval, or they drop quiet connections.

## DNS

### Resolution path

- Stub resolver → **recursive resolver** (ISP, 1.1.1.1, VPC resolver) → root → TLD → **authoritative** server; each answer is cached for its **TTL** at every layer.
- Failed lookups are cached too (**negative caching**, from the SOA record).

### Record types

- **A/AAAA** (IPv4/IPv6), **CNAME** (alias — not allowed at the zone apex), **MX**, **NS**, **TXT** (SPF, DKIM, DMARC, domain verification), **SRV**, **CAA** (which CAs may issue certificates), **HTTPS/SVCB** (protocol hints such as HTTP/3).

### TTL trade-offs

- Low TTL = faster failover and migration, more queries; high TTL = fewer queries, slow changes.
- Before a migration, lower the TTL **at least one old-TTL in advance** — resolvers keep the old record until it expires; some clients (JVMs, apps with their own cache) ignore TTLs anyway.

### Transport and privacy

- UDP port 53 by default, **TCP** for large responses (answers above ~**1232 bytes** with EDNS get truncated and retried over TCP).
- **DoT**/**DoH** encrypt queries to the resolver; **DNSSEC** signs records for authenticity but doesn't encrypt them.

## IP and routing

### Addressing and CIDR

- `/24` = 256 addresses, `/16` = 65,536; each bit less doubles the block.
- Private ranges: **10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16**; 100.64.0.0/10 is carrier-grade NAT; AWS reserves **5 addresses** per subnet.

### NAT

- NAT rewrites source IP and port and tracks each flow in a **connection-tracking table** — inbound connections can't be initiated from outside.
- One public IP offers at most ~64k source ports **per destination IP:port** (AWS NAT gateway: **55k**), so heavy traffic to one endpoint exhausts it; a full conntrack table drops new connections.

### MTU and fragmentation

- Ethernet **MTU 1500** → TCP **MSS 1460**; tunnels (VPN, VXLAN) shrink it.
- **Path MTU discovery** needs ICMP "fragmentation needed" messages; firewalls that drop ICMP cause **black holes** — small requests work, large ones hang.

### Anycast and BGP

- **BGP** exchanges routes between autonomous systems; a bad announcement or withdrawal can take a whole company offline (Facebook, October 2021).
- **Anycast** announces one IP from many locations and BGP delivers each client to the nearest — CDNs, public DNS resolvers, DDoS absorption.

### IPv6

- 128-bit addresses, no NAT needed, **SLAAC** self-configuration; dual-stack clients prefer IPv6 and race both (**Happy Eyeballs**) to avoid slow fallbacks.
