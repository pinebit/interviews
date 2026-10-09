# AWS

What experienced AWS developers and DevOps engineers forget before an interview, grouped by subtopic; facts follow the AWS documentation. For PostgreSQL and Redis internals see [postgresql.md](postgresql.md) and [redis.md](redis.md); for delivery semantics and retries see [distributed.md](distributed.md); for deployment patterns and Terraform see [devops.md](devops.md).

## Identity and access

### Policy evaluation

- Requests start with an [implicit deny](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html); any applicable explicit deny wins over every allow.
- [Identity and resource policies](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_identity-vs-resource.html) grant; [permissions boundaries](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html), [session policies](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_session), and [SCPs](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)/[RCPs](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html) only cap what can be granted.
- A role needs both a [trust policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html#id_roles_terms-and-concepts) allowing the principal to assume it and permissions for the resulting session to perform actions.

### Workload credentials

- Use [temporary role credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html) for EC2, ECS tasks, and Lambda; use [OIDC federation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html) for external CI so pipelines do not store long-lived AWS keys.
- In ECS, the [task role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html) grants the application access to AWS APIs; the [execution role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html) lets the ECS agent pull images, fetch configured secrets, and send logs.

### Cross-account access

- Within one account, an allow in the identity policy or the resource policy suffices ([KMS key policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html) and role trust policies are exceptions).
- [Across accounts](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic-cross-account.html), both sides must allow: the resource policy trusts the other account or principal, and that principal's identity policy grants the action.
- [Third parties](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_common-scenarios_third-party.html) assume your role with an `sts:ExternalId` condition, preventing the [confused-deputy problem](https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html).
- [`aws:PrincipalOrgID`](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgid) in a resource policy limits access to accounts in your organization.

### KMS and envelope encryption

- [`GenerateDataKey`](https://docs.aws.amazon.com/kms/latest/APIReference/API_GenerateDataKey.html) returns a data key in plaintext (use it, then discard it) and wrapped under the KMS key (store it with the data) — the envelope pattern in [security.md](security.md); KMS [`Encrypt`](https://docs.aws.amazon.com/kms/latest/APIReference/API_Encrypt.html) itself takes at most 4 KB.
- Every KMS key has a [key policy](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html); IAM policies grant access only if the [key policy delegates to the account](https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html).

## Networking

### Public and private subnets

- A subnet is [public](https://docs.aws.amazon.com/vpc/latest/userguide/configure-subnets.html) when its route table points internet-bound traffic to an [internet gateway](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html); an EC2 instance also needs a public address and permissive rules to receive internet traffic.
- A [NAT gateway](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html) in a public subnet lets private-subnet instances initiate IPv4 internet connections; the private subnet routes outbound traffic to it.

### Network filters and endpoints

- [Security groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html) are stateful and attach to network interfaces; [network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html) are stateless and apply at subnet boundaries, so return traffic needs an explicit ACL rule.
- [Gateway VPC endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html) route S3 and DynamoDB traffic without a NAT device or internet gateway; [interface endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html) use private IPs and [AWS PrivateLink](https://docs.aws.amazon.com/vpc/latest/privatelink/what-is-privatelink.html) for supported services.

### ALB vs NLB

| | ALB | NLB |
|---|---|---|
| Layer | [L7](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html): HTTP(S), gRPC, WebSockets | [L4](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html): TCP, UDP, TLS, QUIC |
| Routing | host, path, header, query string | port; [listener rules](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-listeners.html#listener-rules) route by source IP version (since September 2026) |
| Addresses | changing IPs; use the DNS name | static IP per AZ ([Elastic IPs](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html) optional) |
| Client IP | in [`X-Forwarded-For`](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/x-forwarded-headers.html) | preserved, or sent via [PROXY protocol v2](https://www.haproxy.org/download/3.2/doc/proxy-protocol.txt) |
| Extras | [OIDC/Cognito auth](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html), [WAF](https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html), [Lambda targets](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/lambda-functions.html) | TLS passthrough, PrivateLink services, very high throughput |
| [Cross-zone](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html#cross-zone-load-balancing) | on by default | off by default; cross-AZ data is charged when on |

[Gateway Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/gateway/introduction.html) inserts inline appliances such as third-party firewalls.

### Connecting VPCs

| Option | Topology | Note |
|---|---|---|
| [VPC peering](https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html) | one-to-one | [not transitive](https://docs.aws.amazon.com/vpc/latest/peering/vpc-peering-basics.html), CIDRs can't overlap, no per-GB fee within an AZ |
| [Transit Gateway](https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html) | hub and spoke | transitive routing across many VPCs and on-prem; per-attachment and per-GB fees |
| [PrivateLink](https://docs.aws.amazon.com/vpc/latest/privatelink/what-is-privatelink.html) | one service, consumer → provider | overlapping CIDRs fine; exposes one endpoint, not a network |

### Route 53 routing

- [Policies](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html): simple, [weighted](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy-weighted.html) (canary), latency, [failover](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy-failover.html) (with [health checks](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover.html)), geolocation, geoproximity, multivalue.
- [Alias records](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html) work at the zone apex (`example.com` → ALB/CloudFront), where a CNAME isn't allowed; queries are free when the target is an AWS resource, but billed when it is a plain record in the same zone.

## Compute

### Workload choice

| Service | Use when | You still manage |
|---|---|---|
| [EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html) | OS, runtime, or host control matters | instances, patching, scaling |
| [ECS on Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html) | containers without managing nodes | [task definitions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html), services |
| [EKS](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html) | Kubernetes APIs and ecosystem are required | workloads; nodes unless [Auto Mode](https://docs.aws.amazon.com/eks/latest/userguide/automode.html) or Fargate |
| [Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html) | event-driven, bounded work | concurrency, timeouts, event handling |

### Lambda limits and concurrency

- Maximum timeout 15 minutes; synchronous payloads 6 MB each way ([quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html); [streamed responses](https://docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html) allow more).
- [Reserved concurrency](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html) guarantees capacity and caps a function; [provisioned concurrency](https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html) pre-initializes environments to reduce startup latency and incurs separate charges.

### Lambda cold starts and scaling

- A cold start downloads code, starts the runtime, and runs [init code](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html); the [INIT phase is billed](https://aws.amazon.com/blogs/compute/aws-lambda-standardizes-billing-for-init-phase/) since August 2025.
- Reduce it with provisioned concurrency or [SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html) (Java, Python, .NET), which restores a snapshot of an initialized environment — make sure [randomness](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html) and [connections](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-best-practices.html#snapstart-networking) are recreated after restore.
- Default 1,000 concurrent executions per account per Region; each function [scales](https://docs.aws.amazon.com/lambda/latest/dg/scaling-behavior.html) by up to 1,000 more every 10 seconds.

### API Gateway vs ALB

- API Gateway [REST API](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html): auth, throttling, [usage plans](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html), [request validation](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-method-request-validation.html); integration timeout 29 s by default (raisable for Regional and private APIs, see [quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html)).
- [HTTP API](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html): cheaper, [JWT](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html)/Lambda/IAM authorizers and throttling, but no usage plans or request validation; integration timeout max 30 s ([quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html)).
- ALB in front of Lambda or containers can [authenticate via OIDC/Cognito](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html) but has no throttling, usage plans, or validation; [LCU pricing](https://aws.amazon.com/elasticloadbalancing/pricing/) is usually cheaper at sustained high volume.

## Storage and databases

### S3 consistency and versions

- S3 has [strong read-after-write consistency](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html#ConsistencyModel) for object PUT and DELETE, including list results; a successfully written object is immediately readable.
- With [versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html), deleting an object without a version ID adds a [delete marker](https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeleteMarker.html); deleting a specific version permanently removes it. [Lifecycle rules](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html) can expire noncurrent versions.
- A [presigned URL](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html) grants temporary access using the signer's permissions and expires no later than the credentials used to sign it.

### S3 access and CloudFront

- New buckets [block public access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html) and disable ACLs ([bucket owner enforced](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html)) by default since April 2023; objects are encrypted with [SSE-S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingServerSideEncryption.html) by default since January 2023.
- Serve a private bucket through CloudFront with [Origin Access Control](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html), which replaces the legacy OAI; the bucket policy allows only that distribution.
- CloudFront [signed URLs or signed cookies](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PrivateContent.html) gate private content at the edge; S3 presigned URLs bypass the CDN.

### S3 performance and classes

- Each [prefix](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html) supports about 3,500 writes and 5,500 reads per second; spread hot keys over prefixes.
- [Classes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html) trade storage price against retrieval cost and latency: Standard → Standard-IA → Glacier Instant/Flexible/Deep Archive; [Intelligent-Tiering](https://docs.aws.amazon.com/AmazonS3/latest/userguide/intelligent-tiering.html) moves objects automatically.

### Block and shared files

- [EBS](https://docs.aws.amazon.com/ebs/latest/userguide/what-is-ebs.html) is block storage attached to EC2 instances in the same Availability Zone; [Multi-Attach](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volumes-multi.html) works only for eligible volumes and instances and requires a clustered filesystem for simultaneous writes.
- [EFS](https://docs.aws.amazon.com/efs/latest/ug/whatisefs.html) is shared file storage mountable by instances across Availability Zones in one Region.

### Managed database behavior

- An RDS [Multi-AZ DB instance](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html) uses a synchronous standby for failover; that standby does not serve reads. Use a [read replica](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html) or [Multi-AZ DB cluster](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/multi-az-db-clusters-concepts.html) for read scaling.
- DynamoDB reads are [eventually consistent by default](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html); strong reads are available on tables and local secondary indexes, not GSIs.
- DynamoDB [global tables](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GlobalTables.html) support multi-Region eventual and multi-Region strong consistency (strong since June 2025).

### Aurora storage

- The [storage volume](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Overview.StorageReliability.html) keeps 6 copies across 3 AZs; a write needs 4 of 6, so writes survive losing an AZ; the 3-of-6 read [quorum](https://www.amazon.science/publications/amazon-aurora-design-considerations-for-high-throughput-cloud-native-relational-databases) survives an AZ plus one more copy.
- Normal reads go to one storage node known to be current; quorum reads are only needed during recovery.
- Up to 15 [replicas](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Replication.html) share the same storage volume, so replica lag is usually well under 100 ms and failover doesn't copy data.

### DynamoDB partitions and indexes

- Each [partition](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html) serves about 3,000 RCU and 1,000 WCU and holds ~10 GB; a hot partition key throttles even if table capacity is fine.
- [GSIs](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html) have their own capacity and are eventually consistent; a throttled GSI [throttles writes to the base table](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/gsi-throttling.html). [LSIs](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/LSI.html) must be defined at table creation.
- Items are at most 400 KB ([quotas](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html)); [transactions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html) cover up to 100 items; [TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html) deletes are background work that can lag by days.

## Events and workflows

### SQS delivery

- A received SQS message stays in the queue but is hidden for its [visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html); delete it after successful processing. Expiry or duplicate delivery can expose it again, so consumers still need idempotency.
- [FIFO queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-fifo-queues.html) order messages within a message group. A repeated [deduplication ID](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagededuplicationid-property.html) suppresses duplicate sends only within a 5-minute window; it is not permanent business-level deduplication.

### Lambda with SQS

- [Lambda polls SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html) and invokes the function with a batch; by default, one failed record makes the whole batch visible again after the visibility timeout. Enable [partial batch responses](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html) to retry only failed records.
- Set the queue visibility timeout to 6× the function timeout plus the batching window (Lambda rejects anything below 1×); configure the [DLQ on the SQS queue](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html), not the Lambda [asynchronous-failure destination](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-retain-records.html).

### Routing and orchestration

- [SNS](https://docs.aws.amazon.com/sns/latest/dg/welcome.html) pushes to subscribers; EventBridge matches [event patterns](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html) and routes to targets, with optional [archive/replay](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html); [SQS](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) retains work for consumers to poll.
- Step Functions [Standard](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html) workflows use exactly-once execution unless a task has explicit retries; asynchronous Express is at-least-once, while synchronous Express is at-most-once. Retried external side effects still need idempotency.

## Operations

### Observability and audit

- [CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html) holds metrics, logs, and alarms; [CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html) records account API activity. CloudTrail [data events](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-data-events-with-cloudtrail.html) such as S3 object access are not logged by default when creating a trail.
- [VPC Flow Logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html) record accepted/rejected IP traffic metadata, not packet payloads — for debugging routes and security rules.

### Infrastructure changes and secrets

- CloudFormation [change sets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html) preview resource replacements or deletions before execution. Standard change sets compare templates; [drift-aware change sets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/drift-aware-change-sets.html) also compare actual resource state.
- Secrets Manager can [rotate](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html) a secret in both its store and the backing service; use runtime retrieval or refresh so an application picks up the new value.

### Capacity and cost guardrails

- [Service quotas](https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html) are per account and Region and often stop scaling before the application does — many are soft and raised by request.
- EC2 [Spot](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-spot-instances.html) capacity can be reclaimed; stop/terminate [interruption notices](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html) give about 2 minutes on a best-effort basis (hibernation starts immediately). Checkpoint work and replace capacity proactively.

### Cost drivers

- [NAT gateway](https://aws.amazon.com/vpc/pricing/) data processing (~$0.045/GB in us-east-1, plus hourly) is a classic surprise; S3 and DynamoDB gateway endpoints are free and skip it.
- [Cross-AZ traffic](https://aws.amazon.com/ec2/pricing/on-demand/) costs ~$0.01/GB in each direction, so chatty services and replicas spread across AZs add up.
- Internet egress and [CloudWatch Logs](https://aws.amazon.com/cloudwatch/pricing/) ingestion (~$0.50/GB) are the other usual suspects.
- Discounts: [Savings Plans](https://aws.amazon.com/savingsplans/) and [Reserved Instances](https://aws.amazon.com/ec2/pricing/reserved-instances/) (up to ~72% for 1–3 year commitments), [Spot](https://aws.amazon.com/ec2/spot/) (up to ~90%), [Graviton](https://aws.amazon.com/ec2/graviton/) (roughly 20% cheaper per hour than comparable x86).
