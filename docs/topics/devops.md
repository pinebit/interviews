# DevOps

What experienced DevOps engineers forget before an interview, grouped by subtopic. For AWS service behavior see [aws.md](aws.md); for Linux internals see [os.md](os.md).

## Deployment and release

### Deployment strategies

| Strategy | Mechanism | Trade-off |
|---|---|---|
| [Rolling](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-update-deployment) | replace instances gradually | little spare capacity; old and new run side by side |
| [Blue-green](https://martinfowler.com/bliki/BlueGreenDeployment.html) | two full environments, switch traffic at once | instant rollback; double capacity |
| [Canary](https://martinfowler.com/bliki/CanaryRelease.html) | small traffic share first, then expand or revert | smallest blast radius; needs good metrics |

- Every strategy needs health checks and an [automatic stop/rollback](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/) condition.

### Feature flags

- [Flags](https://martinfowler.com/articles/feature-toggles.html) decouple deploy from release: code ships [dark](https://martinfowler.com/bliki/DarkLaunching.html) and is turned on per user, percentage, or region — and turned off without a deploy.
- Stale flags are debt: give each one an owner and a removal date.

### Rollbacks

- Roll back by shifting traffic or redeploying the previous [immutable artifact](https://martinfowler.com/bliki/ImmutableServer.html); it never undoes data changes already made.
- So the previous version must run against the new schema — keep migrations backward compatible.

### Zero-downtime schema changes

- [Expand-and-contract](https://martinfowler.com/bliki/ParallelChange.html): add the new schema (backward compatible) → deploy code that handles both → backfill → remove the old schema in a later release.
- A destructive migration (dropping a column old code still reads) makes rollback impossible.
- Keep each DDL short and lock-safe ([`lock_timeout`](https://www.postgresql.org/docs/current/runtime-config-client.html#GUC-LOCK-TIMEOUT), [concurrent index builds](https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY)) — see [postgresql.md](postgresql.md).

### Incident response

- Assign roles: an [incident commander](https://sre.google/sre-book/managing-incidents/) coordinates while others handle communications and operations.
- Mitigate first (roll back, flip a flag, fail over); find the root cause later.
- Write a [blameless postmortem](https://sre.google/sre-book/postmortem-culture/): timeline, contributing factors, and action items with owners.
- Track time to detect and [time to recover](https://en.wikipedia.org/wiki/Mean_time_to_recovery) (MTTD, MTTR); link a [runbook](https://en.wikipedia.org/wiki/Runbook) from every alert.

## Containers

### How containers work

- A container is a Linux process with [namespaces](https://man7.org/linux/man-pages/man7/namespaces.7.html) (isolated view: PID, network, mount, UTS, IPC, user) and [cgroups](https://man7.org/linux/man-pages/man7/cgroups.7.html) (resource limits: CPU, memory, I/O).
- The filesystem is image layers stacked with [OverlayFS](https://docs.kernel.org/filesystems/overlayfs.html) plus a thin writable layer; all containers share the host kernel, unlike VMs.
- The [OCI runtime](https://github.com/opencontainers/runtime-spec) ([runc](https://github.com/opencontainers/runc)) sets this up; [containerd](https://containerd.io/docs/)/[CRI-O](https://cri-o.io/) manage images and lifecycles above it.

### Dockerfile practices

- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/) keep compilers out of the final image; [pin base images by digest](https://docs.docker.com/build/building/best-practices/#pin-base-image-versions); copy dependency manifests before source to reuse [cached layers](https://docs.docker.com/build/cache/).
- Run as [non-root](https://docs.docker.com/build/building/best-practices/#user); never put secrets in [`ARG`](https://docs.docker.com/reference/dockerfile/#arg), [`ENV`](https://docs.docker.com/reference/dockerfile/#env), or copied files — layers keep them even if a later layer deletes them (use BuildKit [secret mounts](https://docs.docker.com/build/building/secrets/)).

### PID 1 and signals

- PID 1 gets no [default signal handlers](https://man7.org/linux/man-pages/man2/kill.2.html), so an app not written for it may ignore [`SIGTERM`](https://man7.org/linux/man-pages/man7/signal.7.html) and be killed after the grace period.
- Use the [exec form](https://docs.docker.com/reference/dockerfile/#shell-and-exec-form) (`CMD ["app"]`, not `CMD app`, which wraps it in a shell) and a tiny init ([`tini`](https://github.com/krallin/tini), [`--init`](https://docs.docker.com/reference/cli/docker/container/run/#init)) to forward signals and reap zombies.

## Kubernetes architecture

### Control plane

- The [API server](https://kubernetes.io/docs/concepts/architecture/#kube-apiserver) is the only component talking to [etcd](https://etcd.io/docs/); the [scheduler](https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/) assigns Pods to nodes; [controllers](https://kubernetes.io/docs/concepts/architecture/controller/) reconcile actual state toward desired state.
- Everything is [declarative](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/) and level-triggered: `kubectl apply` succeeding means the object was stored, not that the app is healthy.
- A [bare Pod](https://kubernetes.io/docs/concepts/workloads/pods/#working-with-pods) has no controller, so nothing recreates it after a node failure — run workloads through a [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/), [StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/), [DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/), or [Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/).

### Node components

- [kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/) runs the node's Pods through the container runtime ([CRI](https://kubernetes.io/docs/concepts/containers/cri/)) and reports status.
- [kube-proxy](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/) or an [eBPF](https://ebpf.io/what-is-ebpf/) CNI such as [Cilium](https://docs.cilium.io/en/stable/overview/intro/) implements [Service virtual IPs](https://kubernetes.io/docs/reference/networking/virtual-ips/).

### Packaging and extension

- [Helm](https://helm.sh/docs/) templates charts with values and tracks releases; [Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/) patches plain YAML with overlays, no templating.
- [CRDs](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) + [operators](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/) extend the API: an operator's controller reconciles custom resources (databases, certificates) like built-in objects.

## Kubernetes workloads

### Rolling update tuning

- [`maxSurge`](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#max-surge) (extra Pods above desired) and [`maxUnavailable`](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#max-unavailable) (Pods allowed down) — both default 25%.
- New Pods count as available only after readiness passes (plus [`minReadySeconds`](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#min-ready-seconds)), so a broken readiness probe stalls the rollout safely.

### Sidecars and init containers

- [Init containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/) run to completion, in order, before app containers start.
- [Native sidecars](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/) (an init container with `restartPolicy: Always`, GA in 1.33) start before the app and stop after it — fixing Jobs that never finished because a sidecar kept running.

### Scheduling constraints

- [Taints](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) on nodes repel Pods unless they have a matching toleration (dedicated GPU nodes).
- [Node affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity) attracts Pods to labeled nodes; pod anti-affinity or [topology spread constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/) spread replicas across nodes and zones.

### PodDisruptionBudgets

- A [PDB](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) (`minAvailable` or `maxUnavailable`) limits only disruptions that go through the [Eviction API](https://kubernetes.io/docs/concepts/scheduling-eviction/api-eviction/) — [node drains](https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/), autoscaler scale-down.
- It doesn't stop crashes, direct Pod deletes, or Deployment rolling updates (those follow `maxUnavailable`).
- A PDB that allows zero disruptions blocks node drains forever.

### Persistent volumes

- A [PVC](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) requests storage; a [StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/) provisions a matching PV dynamically.
- [Access modes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes): `ReadWriteOnce` (one node — most block storage) vs `ReadWriteMany` (shared file systems such as EFS or NFS).
- [`WaitForFirstConsumer`](https://kubernetes.io/docs/concepts/storage/storage-classes/#volume-binding-mode) binding delays provisioning until the Pod is scheduled, so a zonal disk lands in the Pod's zone.
- Dynamic volumes default to [reclaim policy](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#reclaiming) `Delete` (the disk goes with the PVC); `Retain` keeps it.

## Kubernetes networking

### Services

- A [Service](https://kubernetes.io/docs/concepts/services-networking/service/) gives a changing set of Pods (chosen by label selector) a stable virtual IP and DNS name: [ClusterIP](https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types) (internal), NodePort, LoadBalancer (cloud LB).
- No traffic? Check the selector and readiness first: `kubectl get endpointslices` (the [Endpoints API is deprecated](https://kubernetes.io/blog/2025/04/24/endpoints-deprecation/) since 1.33).
- General service-discovery patterns: see [system.md](system.md).

### Ingress and Gateway API

- [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/) and [Gateway API](https://gateway-api.sigs.k8s.io/) route HTTP by host and path — neither does anything without a [controller](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/).
- [ingress-nginx was retired](https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/) in March 2026 (no more fixes); new setups use Gateway API implementations ([Envoy Gateway](https://gateway.envoyproxy.io/), Cilium, cloud controllers).

### NetworkPolicy

- By default all Pods can reach all Pods; a [NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/) selecting a Pod switches it to deny-by-default for the listed direction.
- Enforcement needs a CNI that supports it ([Calico](https://docs.tigera.io/calico/latest/about/), [Cilium](https://docs.cilium.io/en/stable/security/policy/)) — otherwise policies are silently ignored.

## Kubernetes operations

### Probes

- [Readiness](https://kubernetes.io/docs/concepts/workloads/pods/probes/) gates Service traffic; liveness restarts a stuck container; startup holds off both during slow boots.
- A liveness probe that checks dependencies or times out under load causes restart cascades — keep it a cheap local check.

### Requests, limits, QoS

- [Requests drive scheduling; limits cap usage](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) — over the CPU limit the container is [throttled](https://docs.kernel.org/scheduler/sched-bwc.html).
- At the memory limit the kernel reclaims (page cache) first and OOMKills only if usage still can't stay under it.
- Requests vs limits set the [QoS class](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/) (Guaranteed / Burstable / BestEffort), which decides eviction order under [node pressure](https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/).
- [In-place Pod resize](https://kubernetes.io/docs/tasks/configure-pod-container/resize-container-resources/) (GA in 1.35) changes CPU/memory requests without restarting the Pod.

### Autoscaling

- [HPA](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/) scales replicas from metrics; [VPA](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler) adjusts requests; [Cluster Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)/[Karpenter](https://karpenter.sh/docs/) add nodes when Pods can't be scheduled.
- HPA utilization targets are a percentage of requests, so Pods without CPU requests can't scale on CPU; scale-down waits out a 5-minute [stabilization window](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/#stabilization-window) by default.
- [KEDA](https://keda.sh/docs/latest/concepts/) scales on external events (queue length, consumer lag), down to zero; Karpenter also [consolidates](https://karpenter.sh/docs/concepts/disruption/#consolidation) underused nodes.
- More replicas don't help when the bottleneck is a saturated downstream database.

### Graceful Pod shutdown

- On [deletion](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination), endpoint updates ([EndpointSlice](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/#conditions) marks the Pod terminating, not ready) and the kubelet's shutdown run concurrently, so the Pod may still receive traffic briefly.
- The kubelet runs [`preStop`](https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/) first, then sends `SIGTERM` — a short `preStop` sleep covers that race.
- `terminationGracePeriodSeconds` (default 30 s) covers `preStop` plus shutdown; then the kubelet sends `SIGKILL`. App-side steps are in [backend.md](backend.md).

### Debugging Pod states

- `Pending`: unschedulable (resources, quota, taints, unbound volume). [`ImagePullBackOff`](https://kubernetes.io/docs/concepts/containers/images/#imagepullbackoff): wrong image or registry credentials. [`CrashLoopBackOff`](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-restarts): the process or its liveness probe keeps failing.
- [`kubectl describe pod`](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_describe/) shows events; [`kubectl logs --previous`](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_logs/) shows the crashed container's last output.

## Kubernetes security

### Pod security

- [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) enforces the privileged, baseline, or [restricted](https://kubernetes.io/docs/concepts/security/pod-security-standards/#restricted) profile per namespace via labels; [PodSecurityPolicy](https://kubernetes.io/docs/concepts/security/pod-security-policy/) was removed in 1.25.
- A hardened [`securityContext`](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/): `runAsNonRoot`, `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, drop all capabilities, `seccompProfile: RuntimeDefault`.
- `privileged: true`, [`hostPath`](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath) mounts, and `hostNetwork`/`hostPID` effectively hand over the node.
- [Kyverno](https://kyverno.io/docs/introduction/) or [OPA Gatekeeper](https://open-policy-agent.github.io/gatekeeper/website/docs/) enforce custom rules (allowed registries, no `latest` tags, required labels).

### ServiceAccounts and workload identity

- Each Pod runs as a [ServiceAccount](https://kubernetes.io/docs/concepts/security/service-accounts/); [RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) Roles bound to it limit what it may do through the Kubernetes API.
- Its tokens are [projected](https://kubernetes.io/docs/concepts/storage/projected-volumes/#serviceaccounttoken), short-lived, and audience-bound; set [`automountServiceAccountToken: false`](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#opt-out-of-api-credential-automounting) when the app doesn't call the API.
- Workload identity maps a ServiceAccount to a cloud role (EKS [IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html) or [Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html), GKE [Workload Identity](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/workload-identity)) — no static cloud keys in Secrets.

### ConfigMaps and Secrets

- [Secret](https://kubernetes.io/docs/concepts/configuration/secret/) values are only base64-encoded; enable [encryption at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/) ([KMS](https://kubernetes.io/docs/tasks/administer-cluster/kms-provider/)), restrict access with RBAC, or sync from a vault ([External Secrets Operator](https://external-secrets.io/latest/)).
- Env vars from a [ConfigMap](https://kubernetes.io/docs/concepts/configuration/configmap/) don't update in a running Pod; [mounted files do](https://kubernetes.io/docs/concepts/configuration/configmap/#mounted-configmaps-are-updated-automatically) (eventually) — most apps still need a restart.

## Terraform

### Plan and apply

- [`init`](https://developer.hashicorp.com/terraform/cli/commands/init) (providers, backend) → [`plan`](https://developer.hashicorp.com/terraform/cli/commands/plan) (diff) → [`apply`](https://developer.hashicorp.com/terraform/cli/commands/apply); review every plan for replacements — replacing a stateful resource usually means data loss.
- [`lifecycle`](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle) `{ prevent_destroy = true }` and `create_before_destroy` guard critical resources.

### State and locking

- [State](https://developer.hashicorp.com/terraform/language/state) maps resource addresses to real objects and can [hold secrets](https://developer.hashicorp.com/terraform/language/manage-sensitive-data) — keep it in a [remote backend](https://developer.hashicorp.com/terraform/language/backend) with [locking](https://developer.hashicorp.com/terraform/language/state/locking), never in Git.
- Drift: out-of-band changes show up in the next plan, which proposes reverting them.

### count vs for_each

- [`count`](https://developer.hashicorp.com/terraform/language/meta-arguments/count) addresses instances by index (`aws_instance.web[2]`): removing one element shifts every later index, so each later instance takes its neighbor's config and is updated in place or replaced, and the last one is destroyed.
- [`for_each`](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each) keys instances by stable map or set keys (`aws_instance.web["api"]`), so adding or removing one touches only that one.
- `for_each` keys must be known at plan time, not computed during apply; switching between the two needs `moved` blocks.

### Refactoring resources

- [`moved`](https://developer.hashicorp.com/terraform/language/modules/develop/refactoring) blocks record a renamed address, so the plan doesn't destroy and recreate it.
- [`import`](https://developer.hashicorp.com/terraform/language/import) blocks (1.5) adopt existing resources into state.
- [`removed`](https://developer.hashicorp.com/terraform/language/block/removed) blocks (1.7) drop a resource from config; the default destroys it — only `lifecycle { destroy = false }` keeps the real object.

### Modules, workspaces, OpenTofu

- [Modules](https://developer.hashicorp.com/terraform/language/modules) package resources behind inputs and outputs.
- [Workspaces](https://developer.hashicorp.com/terraform/language/state/workspaces) give one configuration several states but are not an access boundary — isolate environments with separate backends or root modules.
- [OpenTofu](https://opentofu.org/docs/) is the open-source fork of Terraform with the same workflow.

## CI/CD and GitOps

### CI pipeline practices

- [Trunk-based development](https://trunkbaseddevelopment.com/): short-lived branches merged at least daily, unfinished work behind flags.
- Build once, promote the same image digest through environments — never rebuild per environment.
- [Cache dependencies](https://docs.github.com/en/actions/concepts/workflows-and-actions/dependency-caching) keyed on the lock-file hash, run fast checks first, and [pin third-party CI actions by commit SHA](https://docs.github.com/en/actions/reference/security/secure-use#using-third-party-actions).

### Pull-based reconciliation

- A controller ([Argo CD](https://argo-cd.readthedocs.io/en/stable/), [Flux](https://fluxcd.io/flux/)) watches a Git repo of desired state and reconciles the cluster — the cluster pulls, so CI needs no cluster credentials.
- Manual `kubectl` changes are drift: Flux reapplies every interval, Argo CD reverts them only with [`selfHeal`](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/#automatic-self-healing) on; emergency fixes must land in Git too.
