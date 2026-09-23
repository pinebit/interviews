# DevOps Cheatsheet

The 20 most frequently asked DevOps interview topics, with short answers.

## 1. What is CI/CD, and what belongs in a deployment pipeline?

**Continuous integration (CI)** merges small changes often and checks each commit with a build, tests, and static or security checks. **Continuous delivery** keeps a tested artifact ready to release; **continuous deployment** automatically releases every change that passes the pipeline.

Build the artifact once, give it an immutable version or image digest, then promote that same artifact through environments. Keep credentials out of source control, make pipeline failures visible, and separate a successful build from proof that the production rollout is healthy.

## 2. How do rolling, blue-green, and canary deployments differ?

- **Rolling** replaces instances gradually; it uses little spare capacity, but old and new versions coexist during the rollout.
- **Blue-green** runs two full environments and switches traffic at once; rollback is quick, but capacity costs more.
- **Canary** sends a small share of traffic to the new version, checks metrics, then increases the share or rolls back.

All three need health checks and a way to stop the rollout. Use **feature flags** when code must deploy before a feature becomes visible. See [system.md](system.md) for availability targets and observability.

## 3. How do you roll back a release safely, including database changes?

Revert traffic or redeploy the **previous immutable artifact** when the new release fails. Watch error rate, latency, and business metrics during the rollout; preserve logs and the failed version for diagnosis. Rolling back code does not automatically undo data changes.

Use **expand-and-contract migrations**: first add a backward-compatible schema, deploy code that can handle both forms, migrate data, then remove the old schema in a later release. Back up data and test recovery; destructive migrations can make a code rollback impossible.

## 4. What is the difference between a Docker image and a container?

An **image** is an immutable package of application files and runtime dependencies, built in layers from a Dockerfile. A **container** is a running instance of an image with its own writable layer, process tree, and isolation through OS namespaces and resource controls.

Containers share the host kernel, unlike virtual machines with their own guest kernel. Treat containers as disposable: put persistent data in a **volume** or external store, and use an image digest when a deployment must pull exactly the artifact you tested.

## 5. How do you write a small, secure Dockerfile?

Use a **multi-stage build** so compilers and build tools stay out of the final image. Choose a trusted, maintained base image; pin versions or digests for repeatability; copy dependency manifests before source to reuse cached layers; and keep build context small with `.dockerignore`.

Run as a **non-root user** where possible, include only runtime files, and scan the final image. Do not put secrets in `ARG`, `ENV`, or copied files: image layers and build history can expose them. Supply runtime secrets through the deployment platform.

## 6. How do Docker networking and storage work?

Containers on the same **user-defined bridge network** can reach each other by container name; publishing a port maps a host port to a container port. `EXPOSE` documents an intended port but does not publish it. A container's writable layer is ephemeral when the container is removed.

Use **volumes** for durable container data, **bind mounts** when the container needs a specific host path, and external storage when data must survive host loss or move between hosts. Persisting a database in one local volume is not a backup or a high-availability design.

## 7. What are the main Kubernetes control-plane and node components?

The **API server** accepts desired state, **etcd** stores cluster state, the **scheduler** assigns unscheduled Pods to nodes, and **controllers** reconcile actual state toward desired state. On each node, the **kubelet** runs assigned Pods through a container runtime, while networking components implement service connectivity.

Kubernetes is **declarative**: you submit objects describing what should exist, and controllers keep trying to make reality match. A successful `kubectl apply` means the API accepted the object; it does not prove the application is healthy.

## 8. When do you use a Pod, Deployment, StatefulSet, DaemonSet, Job, or CronJob?

A **Pod** is the smallest deployable unit and may contain tightly coupled containers. A **Deployment** manages interchangeable, usually stateless Pods through ReplicaSets and supports rolling updates. A **StatefulSet** gives Pods stable identities and storage claims for stateful workloads.

A **DaemonSet** runs a Pod on each eligible node, a **Job** runs work to completion, and a **CronJob** creates Jobs on a schedule. Create a workload controller rather than a bare Pod when you need replacement after failure.

## 9. How do Kubernetes Services expose Pods?

A **Service** selects Pods and gives their changing IPs a stable DNS name and endpoint. **ClusterIP** is internal, **NodePort** opens a port on nodes, and **LoadBalancer** asks an integration to provision an external load balancer.

For HTTP routing by host or path, use **Ingress** with an Ingress controller, or **Gateway API** with a compatible controller. Neither routing resource forwards traffic by itself. Check selectors and ready endpoints first when a Service has no backends; see [distributed.md](distributed.md) for service discovery.

## 10. What do Kubernetes probes, resource requests, and autoscaling do?

**Readiness** controls whether a Pod receives Service traffic; **liveness** restarts a stuck container; **startup** delays the other probes while an application initializes. A bad liveness check can cause a restart loop under load.

CPU and memory **requests** guide scheduling; **limits** cap usage (CPU throttles, while exceeding a memory limit can cause an OOM kill). A **HorizontalPodAutoscaler (HPA)** changes replica count from metrics; node autoscaling adds capacity if Pods cannot be scheduled. Scaling replicas will not fix a saturated database.

## 11. How do you manage configuration, secrets, and access in Kubernetes?

Use **ConfigMaps** for non-sensitive settings and **Secrets** for sensitive values. Kubernetes Secret values are base64 encoded, which is not encryption; enable encryption at rest, restrict access with **RBAC**, and use an external secret manager where appropriate. Give workloads dedicated service accounts with the permissions they need.

Use **NetworkPolicies** to restrict Pod traffic when the network plugin supports them, and avoid privileged containers. Rotate credentials and avoid putting secrets in image layers or Git.

## 12. How do you debug a failing Kubernetes rollout?

Start with `kubectl rollout status`, `get pods`, and `describe pod`: events reveal scheduling failures, image pull errors, probe failures, and OOM kills. Then inspect `logs --previous` for a restarting container and verify environment settings, Service selectors, endpoints, and dependencies.

**Pending** usually points to scheduling, quotas, or storage; **ImagePullBackOff** to an image or registry credential; **CrashLoopBackOff** to a repeatedly failing process or probe. Fix the cause or roll back with `kubectl rollout undo`; do not just raise replica count.

## 13. When would you choose EC2, ECS, EKS, or Lambda on AWS?

**EC2** gives control of virtual machines and their operating systems. **ECS** orchestrates containers with AWS-native APIs; **EKS** runs managed Kubernetes for teams that need its API and ecosystem. **Lambda** runs event-driven functions without managing servers, but its execution model and limits must fit the workload.

With ECS or EKS, **Fargate** can run supported containers without managing worker servers. Choose the simplest option that meets runtime, scaling, networking, and operational requirements; Kubernetes adds control and operational complexity.

## 14. What are a VPC, public and private subnets, security groups, and NAT?

A **VPC** is an isolated AWS network. A subnet is **public** when its route table points internet-bound traffic to an internet gateway; a **private** subnet lacks that route. A public subnet alone does not make an instance reachable: it also needs a public address and permissive security rules.

**Security groups** are stateful rules attached to resources; **network ACLs** are stateless rules at the subnet boundary. A **NAT gateway** can give private-subnet resources outbound IPv4 internet access without allowing unsolicited inbound connections. Spread critical resources across availability zones.

## 15. How does AWS IAM implement least privilege?

**IAM policies** grant or deny actions on resources, with optional conditions. Attach narrowly scoped policies to **roles** assumed by workloads and people, using temporary credentials instead of long-lived access keys. An explicit deny overrides an allow.

Separate deployment roles from runtime roles; restrict who can assume each role, and grant only the actions and resources needed. For CI, use **OIDC federation** to obtain short-lived credentials rather than storing AWS keys in the pipeline.

## 16. How do you choose AWS storage and database services?

**S3** stores objects such as uploads, backups, and static assets; **EBS** is block storage attached to compute; **EFS** is shared file storage. **RDS/Aurora** are managed relational databases; **DynamoDB** is a managed key-value/document database designed around access patterns.

Match the data model, access pattern, latency, and durability needs. Multi-AZ database failover, read replicas, and backups solve different problems; test restores and know your **RPO/RTO**. See [database.md](database.md) for database internals and [system.md](system.md) for availability design.

## 17. What is Terraform's core workflow?

Terraform is **infrastructure as code**: declare resources in HCL, then run `terraform init` to install providers and configure the backend, `terraform plan` to inspect proposed changes, and `terraform apply` to make them. Providers call cloud APIs; Terraform builds a dependency graph to order operations.

Review the plan for replacements and deletions before applying it. Pin provider and module versions, keep configuration in version control, and run plans in CI. A plan is a preview; external changes between planning and applying still need attention.

## 18. What is Terraform state, and why use a remote backend?

**State** maps Terraform resource addresses to real infrastructure and may contain sensitive values. Keep it in a protected **remote backend** with access controls, backups, and state locking so two runs cannot write it concurrently. Never commit `terraform.tfstate`.

**Drift** is a difference between configuration, state, and the real infrastructure, often caused by manual changes. A normal plan refreshes managed objects and shows changes needed to reconcile them; investigate drift before applying, especially if the plan would replace data-bearing resources.

## 19. How do Terraform modules and environments work?

A **module** packages reusable resources behind inputs and outputs; the root module calls child modules. Keep modules small, version them, and expose only the values callers need. Separate production and non-production state and credentials so an apply cannot accidentally cross environments.

**Workspaces** provide multiple states for one configuration, but they are not an access-control boundary. For environments with different permissions or lifecycle, use separate backend configurations or root modules instead of relying on workspace names alone.

## 20. What are GitOps and the core DevOps feedback loops?

**GitOps** stores desired deployment configuration in Git; a controller such as Argo CD or Flux detects changes and reconciles the cluster. Pull-based reconciliation makes drift visible and provides an audit trail, but secret handling and emergency changes still need a defined process.

**DevOps** joins development and operations around small changes, automation, and fast feedback from production. Track delivery with deployment frequency, lead time for changes, change failure rate, and failed deployment recovery time; track reliability with user-facing SLOs. See [system.md](system.md) for observability and SLOs.
