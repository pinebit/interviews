# Networking

What experienced engineers forget about networking before an interview, grouped by subtopic. For TLS see [security.md](security.md); for load balancers, CDNs, and real-time delivery see [system.md](system.md); for sockets and epoll see [os.md](os.md).

## End to end

### Loading a URL

- DNS resolves the name → [TCP handshake](https://www.rfc-editor.org/rfc/rfc9293#section-3.5) (1 RTT) → [TLS 1.3](https://www.rfc-editor.org/rfc/rfc9846) handshake (1 RTT) → HTTP request → response → the browser parses and renders ([frontend.md](frontend.md)).
- A cold HTTPS request over TCP costs about 3 RTTs before the first response byte; [HTTP/3](https://www.rfc-editor.org/rfc/rfc9114) saves one, and resumption with [0-RTT](https://www.rfc-editor.org/rfc/rfc9846#section-2.3) saves more.
- Every later request reuses the connection, which is why [keep-alive](https://www.rfc-editor.org/rfc/rfc9112#section-9.3) and connection pools matter.

### Connection failure signatures

| Symptom | Usual cause | Check with |
|---|---|---|
| Name doesn't resolve, or resolves to an old IP | [NXDOMAIN](https://www.rfc-editor.org/rfc/rfc9499#section-3), stale cache, [TTL](https://en.wikipedia.org/wiki/Time_to_live#DNS_records) not expired | [`dig`](https://bind9.readthedocs.io/en/latest/manpages.html#dig-dns-lookup-utility) (answer, TTL) |
| Connection refused | RST: host reachable, nothing listening on the port | [`ss -tlnp`](https://man7.org/linux/man-pages/man8/ss.8.html) on the server |
| Connect timeout | SYN dropped: firewall, security group, or dead host; Linux [retries the SYN](https://docs.kernel.org/networking/ip-sysctl.html#tcp-variables) for ~131 s (~127 s before Linux 6.5), so set connect timeouts | `traceroute`/`mtr`, [`tcpdump`](https://www.tcpdump.org/manpages/tcpdump.1.html) for SYNs |
| Connection reset by peer | peer crashed, or a middlebox dropped the flow after its idle timeout | `tcpdump`/[Wireshark](https://www.wireshark.org/docs/) around the RST |
| [502](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/502) from a proxy | upstream refused, reset, or sent an invalid response | proxy error log, `ss -tanp` states |
| [504](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/504) from a proxy, or just slow | upstream didn't answer in time | [`curl -w '%{time_connect} %{time_appconnect} %{time_starttransfer}'`](https://curl.se/docs/manpage.html#-w) per phase |

## TCP

### Handshake and connection queues

- [SYN → SYN-ACK → ACK](https://www.rfc-editor.org/rfc/rfc9293#section-3.5): one RTT before any data.
- The kernel keeps a [SYN queue](https://blog.cloudflare.com/syn-packet-handling-in-the-wild/) (half-open) and an [accept queue](https://man7.org/linux/man-pages/man2/listen.2.html) (established, waiting for [`accept()`](https://man7.org/linux/man-pages/man2/accept.2.html)); an overflowing accept queue drops connections under load.
- A [SYN flood](https://en.wikipedia.org/wiki/SYN_flood) fills the SYN queue; [SYN cookies](https://en.wikipedia.org/wiki/SYN_cookies) encode state in the sequence number so no queue slot is needed.

### Teardown and TIME_WAIT

- The side that closes first enters [TIME_WAIT](https://www.rfc-editor.org/rfc/rfc9293#section-3.6.1) for 2×MSL (60 s on Linux) so delayed packets can't corrupt a new connection on the same port pair.
- Many short-lived outbound connections exhaust [ephemeral ports](https://en.wikipedia.org/wiki/Ephemeral_port) (~28k by default) — reuse connections (keep-alive, pooling) instead of tuning the kernel.
- Many connections in [CLOSE_WAIT](https://www.rfc-editor.org/rfc/rfc9293#section-3.6) mean the application never called [`close()`](https://man7.org/linux/man-pages/man2/close.2.html) — a bug in your code, not the network.

### Flow and congestion control

- [Flow control](https://en.wikipedia.org/wiki/Transmission_Control_Protocol#Flow_control) (receive window) protects the receiver; [congestion control](https://www.rfc-editor.org/rfc/rfc5681) (congestion window) protects the network.
- [Slow start](https://www.rfc-editor.org/rfc/rfc5681#section-3.1) begins at [10 segments](https://www.rfc-editor.org/rfc/rfc6928) (~14 KB) and roughly doubles per RTT — why the first 14 KB of a page matter and why new connections are slow.
- Throughput ≤ window / RTT ([bandwidth-delay product](https://en.wikipedia.org/wiki/Bandwidth-delay_product)) — high-latency links need large windows.
- [CUBIC](https://www.rfc-editor.org/rfc/rfc9438) (Linux default) backs off on packet loss; [BBR](https://datatracker.ietf.org/doc/draft-ietf-ccwg-bbr/) models bandwidth and RTT instead, doing better on lossy links.

### Retransmission and loss recovery

- The retransmission timeout ([RTO](https://www.rfc-editor.org/rfc/rfc6298)) derives from smoothed RTT; Linux floors it at 200 ms (initial 1 s) and doubles it on each retry.
- One lost packet on a quiet connection can therefore add ≥ 200 ms — a classic cause of p99 spikes.
- [Fast retransmit](https://www.rfc-editor.org/rfc/rfc5681#section-3.2): 3 duplicate ACKs resend the missing segment without waiting for the RTO; [SACK](https://www.rfc-editor.org/rfc/rfc2018) tells the sender exactly which ranges arrived.
- A lost last segment produces no duplicate ACKs; Linux's [tail loss probe](https://www.rfc-editor.org/rfc/rfc8985) resends it after ~2 RTTs instead of waiting for the RTO.

### Keepalive and half-open connections

- [TCP keepalive](https://man7.org/linux/man-pages/man7/tcp.7.html) probes an idle connection to detect a dead peer (Linux: first probe after 2 hours by default); [HTTP keep-alive](https://www.rfc-editor.org/rfc/rfc9112#section-9.3) only means reusing a connection — unrelated.
- A peer that crashes or loses the network without sending FIN/RST leaves a [half-open connection](https://www.rfc-editor.org/rfc/rfc9293#section-3.5.1), invisible until you write or probe.
- Keep the client's idle timeout shorter than the server's or load balancer's, or requests land on connections the other side just closed (sporadic 502s and resets).

### Nagle and delayed ACKs

- [Nagle's algorithm](https://www.rfc-editor.org/rfc/rfc9293#section-3.7.4) holds small writes until earlier data is acknowledged; combined with the receiver's [delayed ACK](https://www.rfc-editor.org/rfc/rfc9293#section-3.8.6.3) it adds ~40 ms stalls on Linux (~200 ms on Windows) for request-response traffic.
- Set [`TCP_NODELAY`](https://man7.org/linux/man-pages/man7/tcp.7.html) for latency-sensitive protocols (most RPC libraries do).

### Head-of-line blocking

- TCP delivers bytes in order, so one lost packet [stalls everything behind it](https://en.wikipedia.org/wiki/Head-of-line_blocking) — even data for unrelated [HTTP/2 streams](https://www.rfc-editor.org/rfc/rfc9113#section-5).
- HTTP/1.1 blocks at the request level, HTTP/2 fixes that but not TCP's, and [QUIC](https://www.rfc-editor.org/rfc/rfc9000) fixes both: streams are delivered independently, so a lost packet stalls only the streams whose data it carried.

## HTTP

### HTTP/1.1

- [Persistent connections](https://www.rfc-editor.org/rfc/rfc9112#section-9.3) (keep-alive), but one outstanding request per connection in practice ([pipelining](https://www.rfc-editor.org/rfc/rfc9112#section-9.3.2) is unused).
- Browsers open about 6 connections per host to parallelize.

### HTTP/2

- Binary framing with many [multiplexed streams](https://www.rfc-editor.org/rfc/rfc9113#section-5) on one TCP connection and [HPACK](https://www.rfc-editor.org/rfc/rfc7541) header compression.
- Fixes HTTP-level head-of-line blocking but not TCP-level: one lost packet stalls all streams.
- Server push is effectively dead — [Chrome removed it in 2022](https://developer.chrome.com/blog/removing-push); use [`103 Early Hints`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/103) or [preload](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/preload) instead.

### HTTP/3 and QUIC

- [UDP](https://www.rfc-editor.org/rfc/rfc768) has no handshake, ordering, or retransmission, so [QUIC](https://www.rfc-editor.org/rfc/rfc9000) implements them in user space; DNS, VoIP, and games use UDP directly and handle loss themselves.
- QUIC runs over UDP with [TLS 1.3 built in](https://www.rfc-editor.org/rfc/rfc9001): 1-RTT setup (0-RTT on resumption) and independent stream delivery, so no cross-stream head-of-line blocking; [loss detection and congestion control](https://www.rfc-editor.org/rfc/rfc9002) stay per connection.
- [Connection migration](https://www.rfc-editor.org/rfc/rfc9000#section-9): a connection ID survives an IP change (Wi-Fi → cellular).
- Clients discover it via the [`Alt-Svc`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Alt-Svc) header or a [DNS HTTPS record](https://www.rfc-editor.org/rfc/rfc9460); many networks block UDP, so browsers fall back to TCP.

### WebSocket handshake

- Starts as HTTP/1.1 [`Upgrade: websocket`](https://www.rfc-editor.org/rfc/rfc6455#section-4) → [`101 Switching Protocols`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/101), then framed full-duplex messages on the same TCP connection.
- Proxies and load balancers need idle timeouts above the app's [ping interval](https://www.rfc-editor.org/rfc/rfc6455#section-5.5.2), or they drop quiet connections.

### Client IP behind proxies

- L7 proxies append the peer's address to [`X-Forwarded-For`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Forwarded-For); clients can forge earlier entries, so trust only those your own proxies added — read from the right, skipping known proxy hops.
- L4 load balancers either preserve the source IP or pass it in a [PROXY protocol](https://www.haproxy.org/download/1.8/doc/proxy-protocol.txt) header, which the backend must be configured to expect.
- Rate limits, geo-blocking, and audit logs depend on it: taking the leftmost entry lets any client spoof its IP.

## DNS

### Resolution path

- Stub resolver → [recursive resolver](https://en.wikipedia.org/wiki/Domain_Name_System#Recursive_and_caching_name_server) (ISP, 1.1.1.1, VPC resolver) → [root](https://en.wikipedia.org/wiki/Root_name_server) → [TLD](https://en.wikipedia.org/wiki/Top-level_domain) → authoritative server; each answer is cached for its [TTL](https://en.wikipedia.org/wiki/Time_to_live#DNS_records) at every layer.
- Failed lookups are cached too ([negative caching](https://www.rfc-editor.org/rfc/rfc2308), from the [SOA record](https://en.wikipedia.org/wiki/SOA_record)).

### Record types

- [A/AAAA](https://en.wikipedia.org/wiki/List_of_DNS_record_types) (IPv4/IPv6), [CNAME](https://www.rfc-editor.org/rfc/rfc1912#section-2.4) (alias — not allowed at the zone apex), MX, NS, SRV.
- TXT carries [SPF](https://www.rfc-editor.org/rfc/rfc7208), [DKIM](https://www.rfc-editor.org/rfc/rfc6376), [DMARC](https://www.rfc-editor.org/rfc/rfc9989), and domain verification; [CAA](https://www.rfc-editor.org/rfc/rfc8659) limits which CAs may issue certificates; [HTTPS/SVCB](https://www.rfc-editor.org/rfc/rfc9460) advertise protocol hints such as HTTP/3.

### TTL trade-offs

- Low [TTL](https://en.wikipedia.org/wiki/Time_to_live#DNS_records) = faster failover and migration, more queries; high TTL = fewer queries, slow changes.
- Before a migration, lower the TTL at least one old-TTL in advance — resolvers keep the old record until it expires; some clients (JVMs, apps with their own cache) ignore TTLs anyway.

### Transport and privacy

- UDP port 53 by default, [TCP for large responses](https://www.rfc-editor.org/rfc/rfc7766): an answer bigger than the client's advertised [EDNS](https://www.rfc-editor.org/rfc/rfc6891) buffer size (commonly [1232 bytes](https://www.dnsflagday.net/2020/), to avoid fragmentation) is truncated and retried over TCP.
- [DoT](https://www.rfc-editor.org/rfc/rfc7858)/[DoH](https://www.rfc-editor.org/rfc/rfc8484) encrypt queries to the resolver; [DNSSEC](https://www.rfc-editor.org/rfc/rfc9364) signs records for authenticity but doesn't encrypt them.

## IP and routing

### Addressing and CIDR

- [`/24`](https://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing) = 256 addresses, `/16` = 65,536; each bit less doubles the block.
- [Private ranges](https://www.rfc-editor.org/rfc/rfc1918): 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16; 100.64.0.0/10 is [carrier-grade NAT](https://www.rfc-editor.org/rfc/rfc6598); AWS reserves [5 addresses](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-sizing.html) per subnet.

### Routing tables

- The kernel picks the [longest prefix match](https://en.wikipedia.org/wiki/Longest_prefix_match): a `/32` route beats a `/24`, which beats the default route `0.0.0.0/0` (the gateway).
- On the local link, [ARP](https://www.rfc-editor.org/rfc/rfc826) (IPv6: [neighbor discovery](https://www.rfc-editor.org/rfc/rfc4861)) resolves the next hop's MAC address; MACs change at every hop, while IPs stay end to end unless NAT rewrites them.
- [`ip route get <addr>`](https://man7.org/linux/man-pages/man8/ip-route.8.html) shows the route, interface, and source address the kernel would use.

### NAT

- [NAT](https://en.wikipedia.org/wiki/Network_address_translation) rewrites source IP and port and tracks each flow in a [connection-tracking table](https://en.wikipedia.org/wiki/Netfilter#Connection_tracking) — unsolicited inbound connections are dropped unless a [port forward](https://en.wikipedia.org/wiki/Port_forwarding) or static mapping exists.
- One public IP offers at most ~64k source ports per destination IP:port (AWS NAT gateway: [55k](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html)), so heavy traffic to one endpoint exhausts it; a full [conntrack table](https://docs.kernel.org/networking/nf_conntrack-sysctl.html) drops new connections.

### MTU and fragmentation

- Ethernet [MTU](https://en.wikipedia.org/wiki/Maximum_transmission_unit) 1500 → TCP [MSS](https://en.wikipedia.org/wiki/Maximum_segment_size) 1460 over IPv4 (1440 over IPv6); tunnels (VPN, [VXLAN](https://www.rfc-editor.org/rfc/rfc7348)) shrink it.
- [Path MTU discovery](https://www.rfc-editor.org/rfc/rfc1191) needs ICMP "fragmentation needed" messages; firewalls that drop ICMP cause [black holes](https://en.wikipedia.org/wiki/Path_MTU_Discovery#Problems) — small requests work, large ones hang.

### Anycast and BGP

- [BGP](https://www.rfc-editor.org/rfc/rfc4271) exchanges routes between [autonomous systems](https://en.wikipedia.org/wiki/Autonomous_system_%28Internet%29); a bad announcement or withdrawal can take a whole company offline ([Facebook, October 2021](https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/)).
- [Anycast](https://en.wikipedia.org/wiki/Anycast) announces one IP from many locations and BGP delivers each client to the nearest by routing policy (usually, not always, the lowest-latency) — CDNs, public DNS resolvers, DDoS absorption.

### IPv6

- [128-bit addresses](https://www.rfc-editor.org/rfc/rfc8200), no NAT needed; hosts configure themselves with [SLAAC](https://www.rfc-editor.org/rfc/rfc4862), and a subnet is normally a `/64`.
- Dual-stack clients prefer IPv6 but race both families ([Happy Eyeballs](https://www.rfc-editor.org/rfc/rfc8305)) so a broken path doesn't stall connections.
