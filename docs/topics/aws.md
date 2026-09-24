# AWS

What experienced AWS developers and DevOps engineers forget before an interview, grouped by subtopic. For database internals see [database.md](database.md); for delivery semantics and retries see [distributed.md](distributed.md); for deployment patterns and Terraform see [devops.md](devops.md).

## Identity and access

### Policy evaluation

- Requests start with an **implicit deny**; an applicable **explicit deny** wins over an allow. Identity and resource policies can grant access, while permissions boundaries, session policies, and Organizations SCPs/RCPs constrain it; [resource-policy grants to session principals have important exceptions](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic_policy-eval-denyallow.html).
- A role needs both a **trust policy** allowing the principal to assume it and permissions for the resulting session to perform actions. [AWS IAM documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html).
- An **SCP** caps permissions in member accounts; it does not grant permissions by itself. [AWS Organizations documentation](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html).

### Workload credentials

- Use **temporary role credentials** for EC2, ECS tasks, and Lambda; use OIDC federation for external CI so pipelines do not store long-lived AWS keys. [AWS IAM documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html), [AWS STS documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html).
- In ECS, the **task role** grants the application access to AWS APIs; the **execution role** lets the ECS agent pull images, fetch configured secrets, and send logs. [AWS ECS documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-iam-roles.html).

## Networking

### Public and private subnets

- A subnet is **public** when its route table points internet-bound traffic to an internet gateway; an EC2 instance also needs a public address and permissive rules to receive internet traffic. [AWS VPC documentation](https://docs.aws.amazon.com/vpc/latest/userguide/route-table-options.html).
- A **NAT gateway** in a public subnet lets private-subnet instances initiate IPv4 internet connections; the private subnet routes outbound traffic to it. [AWS VPC documentation](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-troubleshooting.html).

### Network filters and endpoints

- **Security groups** are stateful and attach to network interfaces; **network ACLs** are stateless and apply at subnet boundaries, so return traffic needs an explicit ACL rule. [AWS VPC documentation](https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html).
- **Gateway VPC endpoints** route S3 and DynamoDB traffic without a NAT device or internet gateway; interface endpoints use private IPs and AWS PrivateLink for supported services. [AWS VPC documentation](https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html).

## Compute

### Workload choice

| Service | Use when | Operational boundary |
|---|---|---|
| EC2 | OS, runtime, or host control matters | manage instances and scaling |
| ECS on Fargate | containers without worker-node management | manage tasks, services, and capacity settings |
| EKS | Kubernetes APIs and ecosystem are required | manage workloads; worker capacity can be managed with EKS Auto Mode or Fargate |
| Lambda | event-driven, bounded work | manage function concurrency, timeouts, and event handling |

[AWS compute documentation](https://docs.aws.amazon.com/whitepapers/latest/aws-overview/compute-services.html), [EKS Auto Mode documentation](https://docs.aws.amazon.com/eks/latest/userguide/automode.html).

### Lambda limits and concurrency

- Standard Lambda functions have a **15-minute** maximum timeout; synchronous invocation payloads are **6 MB** each way (streamed responses have a higher limit). Lambda Managed Instances support up to **90 minutes** for eligible asynchronous and event-source invocations. [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html), [quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html).
- **Reserved concurrency** guarantees capacity and caps a function; **provisioned concurrency** pre-initializes environments to reduce startup latency and incurs separate charges. [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html).

### ECS service mechanics

- An ECS **task definition** specifies containers and resources; a **service** maintains the desired number of tasks and replaces failed ones. [AWS ECS documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_services.html).
- An Application Load Balancer routes at **L7** by HTTP attributes; a Network Load Balancer routes at **L4** for TCP/UDP-style traffic. [AWS ALB documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html), [NLB documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html).

## Storage and databases

### S3 consistency and versions

- S3 has **strong read-after-write consistency** for object PUT and DELETE, including list results; a successfully written object is immediately readable. [AWS S3 documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html).
- With **versioning**, deleting an object without a version ID adds a delete marker; deleting a specific version permanently removes it. Lifecycle rules can expire noncurrent versions. [AWS S3 documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/versioning-workflows.html).
- A **presigned URL** grants temporary access using the signer's permissions and expires no later than the credentials used to sign it. [AWS S3 documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).

### Block and shared files

- **EBS** is block storage attached to EC2 instances in the same Availability Zone; Multi-Attach works only for eligible volumes and instances and requires a clustered filesystem for simultaneous writes. [AWS EBS documentation](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volumes-multi.html).
- **EFS** is shared file storage mountable by instances across Availability Zones in one Region. [AWS EFS documentation](https://docs.aws.amazon.com/efs/latest/ug/how-it-works.html).

### Managed database behavior

- An RDS **Multi-AZ DB instance** uses a synchronous standby for failover; that standby does **not** serve reads. Use a read replica or Multi-AZ DB cluster for read scaling. [AWS RDS documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html).
- DynamoDB reads are **eventually consistent by default**; strong reads are available on tables and local secondary indexes, **not GSIs**. [AWS DynamoDB documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html).
- DynamoDB global tables support both **multi-Region eventual** and **multi-Region strong** consistency modes (strong mode since June 2025); specify the mode before stating cross-Region read behavior. [AWS DynamoDB documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-global-table-design.html).

## Events and workflows

### SQS delivery

- A received SQS message stays in the queue but is hidden for its **visibility timeout**; delete it after successful processing. Expiry or duplicate delivery can expose it again, so consumers still need idempotency. [AWS SQS documentation](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html).
- FIFO queues order messages **within a message group**. A repeated deduplication ID suppresses duplicate sends only within a **5-minute window**; it is not permanent business-level deduplication. [AWS SQS documentation](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-key-terms.html).

### Lambda with SQS

- Lambda **polls** SQS and invokes the function with a batch; by default, one failed record makes the whole batch visible again after the visibility timeout. Enable **partial batch responses** to retry only failed records. [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html).
- Set the queue visibility timeout at least as long as the function timeout; configure the **DLQ on the SQS queue**, not the Lambda asynchronous-failure destination. [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html), [failure destinations](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-retain-records.html).

### Routing and orchestration

- **SNS** pushes to subscribers; **EventBridge** matches event patterns and routes to targets, with optional archive/replay; **SQS** retains work for consumers to poll. Choose based on routing and consumer behavior, not service names. [AWS SNS documentation](https://docs.aws.amazon.com/sns/latest/dg/welcome.html), [EventBridge documentation](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html), [SQS documentation](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html).
- Step Functions **Standard** workflows use exactly-once execution unless a task has explicit retries; **asynchronous Express** is at-least-once, while **synchronous Express** is at-most-once. Retried external side effects still need idempotency. [AWS Step Functions documentation](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html).

## Operations

### Observability and audit

- **CloudWatch** holds metrics, logs, and alarms; **CloudTrail** records account API activity. CloudTrail **data events** such as S3 object access are not logged by default when creating a trail. [AWS CloudWatch documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html), [CloudTrail documentation](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-events.html).
- **VPC Flow Logs** show accepted/rejected IP traffic metadata, not packet payloads; use them when route and security-rule debugging needs evidence. [AWS VPC documentation](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html).

### Infrastructure changes and secrets

- CloudFormation **change sets** preview resource replacements or deletions before execution. Standard change sets compare templates; **drift-aware change sets** also compare actual resource state. [AWS CloudFormation documentation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html), [drift-aware changes](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/drift-aware-change-sets.html).
- Secrets Manager can **rotate** a secret in both its store and the backing service; use runtime retrieval or refresh so an application picks up the new value. [AWS Secrets Manager documentation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html).

### Capacity and cost guardrails

- Service **quotas** can stop scaling before the application reaches its own limits; check the relevant account and Region quota before a load test or launch. [AWS Service Quotas documentation](https://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html).
- **AWS Budgets** alerts follow billing-data updates, at least daily; use CloudWatch service metrics for operational alarms. **Cost Explorer** is for spend analysis. [AWS Budgets documentation](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-best-practices.html), [AWS Cost Management documentation](https://docs.aws.amazon.com/cost-management/latest/userguide/).
- EC2 **Spot** capacity can be reclaimed; stop/terminate interruption notices give about **2 minutes** on a best-effort basis (hibernation starts immediately). Checkpoint work and replace capacity proactively. [AWS EC2 documentation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html).
