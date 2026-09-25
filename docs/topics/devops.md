# DevOps

What experienced DevOps engineers forget before an interview, grouped by subtopic. For AWS service behavior see [aws.md](aws.md); for Linux internals see [os.md](os.md).

## Deployment and release

### Deployment strategies

| Strategy | Mechanism | Trade-off |
|---|---|---|
| Rolling | replace instances gradually | little spare capacity; old and new run side by side |
| Blue-green | two full environments, switch traffic at once | instant rollback; double capacity |
| Canary | small traffic share first, then expand or revert | smallest blast radius; needs good metrics |

- Every strategy needs health checks and an **automatic stop/rollback** condition.

### Feature flags

- Flags **decouple deploy from release**: code ships dark and is turned on per user, percentage, or region — and turned off without a deploy.
- Stale flags are debt: give each one an owner and a removal date.

### Rollbacks

- Roll back by shifting traffic or redeploying the previous **immutable artifact**; it never undoes data changes already made.

### Zero-downtime schema changes

- **Expand-and-contract**: add the new schema (backward compatible) → deploy code that handles both → backfill → remove the old schema in a later release.
- A destructive migration (dropping a column old code still reads) makes rollback impossible.
- Keep each DDL short and lock-safe (`lock_timeout`, concurrent index builds) — see [database.md](database.md).

## Containers

### How containers work

- A container is a Linux process with **namespaces** (isolated view: PID, network, mount, UTS, IPC, user) and **cgroups** (resource limits: CPU, memory, I/O).
- The filesystem is image layers stacked with **OverlayFS** plus a thin writable layer; all containers share the **host kernel**, unlike VMs.
- The OCI runtime (**runc**) sets this up; containerd/CRI-O manage images and lifecycles above it.

### Dockerfile practices

- **Multi-stage builds** keep compilers out of the final image; pin base images by digest; copy dependency manifests before source to reuse cached layers.
- Run as **non-root**; never put secrets in `ARG`, `ENV`, or copied files — layers keep them even if a later layer deletes them (use BuildKit secret mounts).

### PID 1 and signals

- PID 1 gets no default signal handlers, so an app not written for it may ignore **`SIGTERM`** and be killed after the grace period.
- Use the **exec form** (`CMD ["app"]`, not `CMD app`, which wraps it in a shell) and a tiny init (`tini`, `--init`) to forward signals and reap zombies.

### Container networking and storage

- On a user-defined bridge network, containers resolve each other by name; `EXPOSE` only documents a port, `-p` publishes it.
- **Volumes** are Docker-managed and survive the container; **bind mounts** map a host path; the writable layer dies with the container.

## Kubernetes architecture

### Control plane

- The **API server** is the only component talking to **etcd**; the **scheduler** assigns Pods to nodes; **controllers** reconcile actual state toward desired state.
- Everything is declarative and level-triggered: `kubectl apply` succeeding means the object was stored, not that the app is healthy.

### Node components

- **kubelet** runs the node's Pods through the container runtime (CRI) and reports status.
- **kube-proxy** (iptables/IPVS) or an **eBPF** CNI such as Cilium implements Service virtual IPs.

## Kubernetes workloads

### Workload types

- **Deployment**: interchangeable stateless Pods via ReplicaSets. **StatefulSet**: stable names (`db-0`), ordered rollout, a volume per Pod.
- **DaemonSet**: one Pod per node (log agents, CNI). **Job**/**CronJob**: run to completion, once or on a schedule.
- Never run a bare Pod for anything that should come back after failure.

### Rolling update tuning

- **`maxSurge`** (extra Pods above desired) and **`maxUnavailable`** (Pods allowed down) — both default **25%**.
- New Pods count as available only after readiness passes (plus `minReadySeconds`), so a broken readiness probe stalls the rollout safely.

### Sidecars and init containers

- **Init containers** run to completion, in order, before app containers start.
- **Native sidecars** (an init container with `restartPolicy: Always`, **GA in 1.33**) start before the app and stop after it — fixing Jobs that never finished because a sidecar kept running.

### Scheduling constraints

- **Taints** on nodes repel Pods unless they have a matching **toleration** (dedicated GPU nodes).
- **Node affinity** attracts Pods to labeled nodes; **pod anti-affinity** or **topology spread constraints** spread replicas across nodes and zones.

### PodDisruptionBudgets

- A **PDB** (`minAvailable` or `maxUnavailable`) limits **voluntary** disruptions — node drains, upgrades, autoscaler scale-down — not crashes.
- A PDB that allows zero disruptions blocks node drains forever.

## Kubernetes networking

### Services

- A **Service** gives a changing set of Pods (chosen by label selector) a stable virtual IP and DNS name: **ClusterIP** (internal), **NodePort**, **LoadBalancer** (cloud LB).
- No traffic? Check the selector and readiness first: `kubectl get endpointslices` (the Endpoints API is deprecated **since 1.33**).
- General service-discovery patterns: see [system.md](system.md).

### Ingress and Gateway API

- **Ingress** and **Gateway API** route HTTP by host and path — neither does anything without a controller.
- **ingress-nginx was retired in March 2026** (no more fixes); new setups use Gateway API implementations (Envoy Gateway, Cilium, cloud controllers).

### NetworkPolicy

- By default **all Pods can reach all Pods**; a NetworkPolicy selecting a Pod switches it to deny-by-default for the listed direction.
- Enforcement needs a CNI that supports it (Calico, Cilium) — otherwise policies are silently ignored.

## Kubernetes operations

### Probes

- **Readiness** gates Service traffic; **liveness** restarts a stuck container; **startup** holds off both during slow boots.
- A liveness probe that checks dependencies or times out under load causes **restart cascades** — keep it a cheap local check.

### Requests, limits, QoS

- **Requests** drive scheduling; **limits** cap usage — over the CPU limit the container is **throttled**, over the memory limit it's **OOMKilled**.
- Requests vs limits set the **QoS class** (Guaranteed / Burstable / BestEffort), which decides eviction order under node pressure.
- **In-place Pod resize** (GA in **1.35**) changes CPU/memory requests without restarting the Pod.

### Autoscaling

- **HPA** scales replicas from metrics; **VPA** adjusts requests; **Cluster Autoscaler**/**Karpenter** add nodes when Pods can't be scheduled.
- More replicas don't help when the bottleneck is a saturated downstream database.

### Graceful Pod shutdown

- On deletion the Pod is removed from endpoints **and** gets `SIGTERM` at the same time, so it may still receive traffic briefly — a short **`preStop`** sleep covers that race.
- After **`terminationGracePeriodSeconds`** (default **30 s**) the kubelet sends `SIGKILL`; app-side steps are in [backend.md](backend.md).

### ConfigMaps and Secrets

- Secret values are only **base64-encoded**; enable encryption at rest (KMS), restrict access with **RBAC**, or sync from a vault (External Secrets Operator).
- Env vars from a ConfigMap don't update in a running Pod; mounted files do (eventually) — most apps still need a restart.

### Debugging Pod states

- **`Pending`**: unschedulable (resources, quota, taints, unbound volume). **`ImagePullBackOff`**: wrong image or registry credentials. **`CrashLoopBackOff`**: the process or its liveness probe keeps failing.
- `kubectl describe pod` shows events; `kubectl logs --previous` shows the crashed container's last output.

### Packaging and extension

- **Helm** templates charts with values and tracks releases; **Kustomize** patches plain YAML with overlays, no templating.
- **CRDs + operators** extend the API: an operator's controller reconciles custom resources (databases, certificates) like built-in objects.

## Terraform

### Plan and apply

- `init` (providers, backend) → `plan` (diff) → `apply`; review every plan for **replacements** — replacing a stateful resource usually means data loss.
- `lifecycle { prevent_destroy = true }` and `create_before_destroy` guard critical resources.

### State and locking

- **State** maps resource addresses to real objects and can hold secrets — keep it in a **remote backend with locking**, never in Git.
- **Drift**: out-of-band changes show up in the next plan, which proposes reverting them.

### Refactoring resources

- **`moved`** blocks record a renamed address so the plan doesn't destroy and recreate; **`import`** blocks (**1.5**) adopt existing resources; **`removed`** (**1.7**) forgets a resource without destroying it.

### Modules, workspaces, licensing

- **Modules** package resources behind inputs and outputs.
- **Workspaces** give one configuration several states but are **not an access boundary** — isolate environments with separate backends or root modules.
- Terraform moved to the **BSL license in 2023**; **OpenTofu** is the open-source fork with the same workflow.

## GitOps

### Pull-based reconciliation

- A controller (**Argo CD**, **Flux**) watches a Git repo of desired state and reconciles the cluster — the cluster pulls, so CI needs no cluster credentials.
- Manual `kubectl` changes are drift and get reverted on the next sync; emergency fixes must land in Git too.
