# AWS

What experienced AWS developers and DevOps engineers forget before an interview, grouped by subtopic; facts follow the AWS documentation. For database internals see [database.md](database.md); for delivery semantics and retries see [distributed.md](distributed.md); for deployment patterns and Terraform see [devops.md](devops.md).

## Identity and access

### Policy evaluation

- Requests start with an **implicit deny**; any applicable **explicit deny** wins over every allow.
- Identity and resource policies **grant**; permissions boundaries, session policies, and SCPs/RCPs only **cap** what can be granted.
- A role needs both a **trust policy** allowing the principal to assume it and permissions for the resulting session to perform actions.
- An **SCP** caps permissions in member accounts; it does not grant permissions by itself.

### Workload credentials

- Use **temporary role credentials** for EC2, ECS tasks, and Lambda; use OIDC federation for external CI so pipelines do not store long-lived AWS keys.
- In ECS, the **task role** grants the application access to AWS APIs; the **execution role** lets the ECS agent pull images, fetch configured secrets, and send logs.

## Networking

### Public and private subnets

- A subnet is **public** when its route table points internet-bound traffic to an internet gateway; an EC2 instance also needs a public address and permissive rules to receive internet traffic.
- A **NAT gateway** in a public subnet lets private-subnet instances initiate IPv4 internet connections; the private subnet routes outbound traffic to it.

### Network filters and endpoints

- **Security groups** are stateful and attach to network interfaces; **network ACLs** are stateless and apply at subnet boundaries, so return traffic needs an explicit ACL rule.
- **Gateway VPC endpoints** route S3 and DynamoDB traffic without a NAT device or internet gateway; interface endpoints use private IPs and AWS PrivateLink for supported services.

## Compute

### Workload choice

| Service | Use when | Operational boundary |
|---|---|---|
| EC2 | OS, runtime, or host control matters | manage instances and scaling |
| ECS on Fargate | containers without worker-node management | manage tasks, services, and capacity settings |
| EKS | Kubernetes APIs and ecosystem are required | manage workloads; worker capacity can be managed with EKS Auto Mode or Fargate |
| Lambda | event-driven, bounded work | manage function concurrency, timeouts, and event handling |

### Lambda limits and concurrency

- Maximum timeout **15 minutes**; synchronous payloads **6 MB** each way (streamed responses allow more).
- **Lambda Managed Instances** allow up to **90 minutes** for async and event-source invocations (Sept 2026); synchronous calls stay at 15.
- **Reserved concurrency** guarantees capacity and caps a function; **provisioned concurrency** pre-initializes environments to reduce startup latency and incurs separate charges.

### ECS service mechanics

- An ECS **task definition** specifies containers and resources; a **service** maintains the desired number of tasks and replaces failed ones.
- An Application Load Balancer routes at **L7** by HTTP attributes; a Network Load Balancer routes at **L4** for TCP/UDP-style traffic.

## Storage and databases

### S3 consistency and versions

- S3 has **strong read-after-write consistency** for object PUT and DELETE, including list results; a successfully written object is immediately readable.
- With **versioning**, deleting an object without a version ID adds a delete marker; deleting a specific version permanently removes it. Lifecycle rules can expire noncurrent versions.
- A **presigned URL** grants temporary access using the signer's permissions and expires no later than the credentials used to sign it.

### Block and shared files

- **EBS** is block storage attached to EC2 instances in the same Availability Zone; Multi-Attach works only for eligible volumes and instances and requires a clustered filesystem for simultaneous writes.
- **EFS** is shared file storage mountable by instances across Availability Zones in one Region.

### Managed database behavior

- An RDS **Multi-AZ DB instance** uses a synchronous standby for failover; that standby does **not** serve reads. Use a read replica or Multi-AZ DB cluster for read scaling.
- DynamoDB reads are **eventually consistent by default**; strong reads are available on tables and local secondary indexes, **not GSIs**.
- DynamoDB global tables support both **multi-Region eventual** and **multi-Region strong** consistency modes (strong mode since June 2025); specify the mode before stating cross-Region read behavior.

## Events and workflows

### SQS delivery

- A received SQS message stays in the queue but is hidden for its **visibility timeout**; delete it after successful processing. Expiry or duplicate delivery can expose it again, so consumers still need idempotency.
- FIFO queues order messages **within a message group**. A repeated deduplication ID suppresses duplicate sends only within a **5-minute window**; it is not permanent business-level deduplication.

### Lambda with SQS

- Lambda **polls** SQS and invokes the function with a batch; by default, one failed record makes the whole batch visible again after the visibility timeout. Enable **partial batch responses** to retry only failed records.
- Set the queue visibility timeout at least as long as the function timeout; configure the **DLQ on the SQS queue**, not the Lambda asynchronous-failure destination.

### Routing and orchestration

- **SNS** pushes to subscribers; **EventBridge** matches event patterns and routes to targets, with optional archive/replay; **SQS** retains work for consumers to poll. Choose based on routing and consumer behavior, not service names.
- Step Functions **Standard** workflows use exactly-once execution unless a task has explicit retries; **asynchronous Express** is at-least-once, while **synchronous Express** is at-most-once. Retried external side effects still need idempotency.

## Operations

### Observability and audit

- **CloudWatch** holds metrics, logs, and alarms; **CloudTrail** records account API activity. CloudTrail **data events** such as S3 object access are not logged by default when creating a trail.
- **VPC Flow Logs** show accepted/rejected IP traffic metadata, not packet payloads; use them when route and security-rule debugging needs evidence.

### Infrastructure changes and secrets

- CloudFormation **change sets** preview resource replacements or deletions before execution. Standard change sets compare templates; **drift-aware change sets** also compare actual resource state.
- Secrets Manager can **rotate** a secret in both its store and the backing service; use runtime retrieval or refresh so an application picks up the new value.

### Capacity and cost guardrails

- Service **quotas** can stop scaling before the application reaches its own limits; check the relevant account and Region quota before a load test or launch.
- **AWS Budgets** alerts follow billing-data updates, at least daily; use CloudWatch service metrics for operational alarms. **Cost Explorer** is for spend analysis.
- EC2 **Spot** capacity can be reclaimed; stop/terminate interruption notices give about **2 minutes** on a best-effort basis (hibernation starts immediately). Checkpoint work and replace capacity proactively.
