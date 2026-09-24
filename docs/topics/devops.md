# DevOps

What experienced DevOps engineers forget before an interview, grouped by subtopic. For AWS service behavior, see [aws.md](aws.md).

## Deployment and release

### Deployment strategies

| Strategy | Mechanism | Trade-off |
|---|---|---|
| Rolling | replace instances gradually | little spare capacity; old and new coexist during rollout |
| Blue-green | two full environments, switch traffic at once | fast rollback; doubles capacity cost |
| Canary | small traffic share to new version, expand or revert | safest exposure; needs good metrics to judge |

- **Feature flags** decouple deploy from release when code must ship before a feature becomes visible.
- All three strategies need health checks and an automatic stop condition — a rollout without one is just a slow, unmonitored release.

### Rollback and migrations

- Roll back by reverting traffic or redeploying the previous **immutable artifact** — rolling back code does not undo data changes already made.
- **Expand-and-contract migrations**: add a backward-compatible schema change → deploy code handling both old and new forms → migrate data → remove the old schema in a later release. Destructive migrations (dropping a column the old code still reads) can make a code rollback impossible.

## Containers

### Images and Dockerfiles

- An **image** is immutable, built in layers from a Dockerfile; a **container** is a running instance with its own writable layer. Containers share the host kernel, unlike VMs.
- **Multi-stage builds** keep compilers/build tools out of the final image; pin base image versions/digests; copy dependency manifests before source to reuse cached layers.
- Run as **non-root**; never put secrets in `ARG`/`ENV`/copied files — image layers and build history can leak them even if a later layer deletes them.
- PID 1 doesn't get default signal handling — a process not designed to be PID 1 can ignore `SIGTERM` and hang on shutdown; use `tini` or the exec form of `CMD` (`CMD ["app"]`, not `CMD app`) so signals reach the process directly.

### Networking and storage

- Containers on a user-defined bridge network reach each other by name; `EXPOSE` only documents a port, publishing (`-p`) actually maps it to the host.
- **Volumes** — durable, Docker-managed. **Bind mounts** — a specific host path. A container's writable layer disappears when the container is removed; a single local volume is not a backup or an HA design.

## Kubernetes architecture

### Control plane and node

- **API server** accepts desired state; **etcd** stores it; the **scheduler** assigns unscheduled Pods to nodes; **controllers** reconcile actual state toward desired state.
- Node-side: **kubelet** runs assigned Pods through the container runtime; **kube-proxy** (or eBPF equivalent) implements Service connectivity.
- Kubernetes is declarative and level-triggered: a successful `kubectl apply` means the API accepted the object, not that the application is healthy — the reconciliation loop keeps nudging reality toward the spec indefinitely.

## Kubernetes workloads and networking

### Workload types

- **Pod** — smallest deployable unit, can hold tightly coupled containers. **Deployment** — interchangeable stateless Pods via ReplicaSets, rolling updates. **StatefulSet** — stable identity + storage per Pod, for stateful workloads.
- **DaemonSet** — one Pod per eligible node. **Job** — runs to completion. **CronJob** — creates Jobs on a schedule.
- Use a controller, not a bare Pod, whenever the workload should be replaced after failure.

### Services and routing

- **Service** gives Pods' changing IPs a stable DNS name via label selectors. **ClusterIP** (internal), **NodePort** (opens a node port), **LoadBalancer** (provisions an external LB via cloud integration).
- **Ingress** (with a controller) or **Gateway API** route HTTP by host/path — the resource alone forwards nothing without a controller implementing it.
- A Service with no backends usually means a selector/label mismatch or no ready endpoints — check `kubectl get endpoints` before anything else. See [distributed.md](distributed.md) for the general service-discovery model this builds on.

## Kubernetes operations

### Probes and resources

- **Readiness** gates Service traffic; **liveness** restarts a stuck container; **startup** delays both while the app initializes — a liveness probe that's too aggressive under load causes a restart loop that makes the outage worse.
- **Requests** guide scheduling; **limits** cap usage — CPU is throttled past its limit, memory past its limit gets the container **OOMKilled**. Requests vs limits set the Pod's **QoS class** (Guaranteed/Burstable/BestEffort), which drives eviction order under node pressure.
- **HPA** scales replica count from metrics; **VPA** resizes requests/limits; **Cluster Autoscaler**/**Karpenter** add node capacity when Pods can't be scheduled. Scaling replicas doesn't fix a saturated downstream database.

### Config, secrets, and debugging

- **ConfigMaps** for non-sensitive settings, **Secrets** for sensitive ones — Secret values are only **base64-encoded, not encrypted**, by default; enable encryption at rest and restrict access via **RBAC**.
- Debugging states: **`Pending`** (scheduling/quota/storage), **`ImagePullBackOff`** (image or registry credential), **`CrashLoopBackOff`** (repeatedly failing process or probe) — use `kubectl describe pod` for events and `logs --previous` for a restarting container's last output before fixing the cause or `kubectl rollout undo`.

## Terraform

### Core workflow

- `terraform init` (providers, backend) → `terraform plan` (preview) → `terraform apply` (execute); always review a plan for unexpected replacements/deletions before applying — a resource replacement often means data loss for stateful resources.
- **State** maps resource addresses to real infrastructure and can contain sensitive values — keep it in a protected **remote backend** with locking so concurrent runs can't corrupt it; never commit `terraform.tfstate`.
- **Drift**: real infrastructure diverges from state, often via manual changes outside Terraform — a plan refreshes state and shows what's needed to reconcile it.
- **`import`** brings an existing resource under Terraform management; **`moved`** blocks record a resource's renamed/refactored address so a plan doesn't propose destroy-and-recreate.
- **Modules** package reusable resources behind inputs/outputs. **Workspaces** give one configuration multiple states but are **not an access-control boundary** — use separate backends/root modules, not workspace names alone, to isolate environments with different permissions.

## GitOps

### Pull-based reconciliation

- A controller (**Argo CD**, **Flux**) watches a Git repo holding desired deployment config and reconciles the cluster to match — pull-based, so the cluster never needs inbound CI credentials.
- Drift from manual `kubectl` changes becomes visible on the next reconciliation and is usually auto-corrected — emergency out-of-band changes still need a defined process so they aren't silently reverted.
