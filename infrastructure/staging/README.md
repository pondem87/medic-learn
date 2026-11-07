# Staging deployment

This Terraform root creates a separate staging environment in `af-south-1` using the
existing `mededbotswana.co.bw` public hosted zone and the existing private Terraform
state bucket. It owns `api.staging.mededbotswana.co.bw`,
`www.staging.mededbotswana.co.bw`, and `oidc.api.staging.mededbotswana.co.bw`.
It does not read the application deployment's state or share its Cognito users,
application secrets, ECR images, database, broker, or media buckets.

## Topology

Two AZs contain public ALB subnets and private Fargate subnets. One NAT supports
outbound AWS API and image traffic. The web, worker, PostgreSQL, RabbitMQ, backup,
and migration tasks have no public IP. Security groups limit PostgreSQL to web,
worker, migration, and backup tasks and RabbitMQ to application tasks. Cloud Map
supplies private DNS for the data services. Database and broker tasks are single
instances. ECS stops the old data task before starting a replacement, so a deploy
or Fargate retirement can interrupt staging. Their separate EFS access points
retain data between replacements; they are never mounted by two data tasks at once.

PostgreSQL and RabbitMQ use the same major/minor image tags as local Compose. Their
private protocol connections do not use TLS; EFS mounts use TLS and IAM. Staging
uses the production Django settings for browser HTTPS, secure cookies, Cognito,
private media, and role checks. Keep staging test identities and media separate from
real user information. The staging site is publicly reachable; registration and
privileged features still require authentication and authorization.

## State and first deployment

Use a distinct backend key. Terraform state contains generated passwords and client
secrets; restrict its bucket IAM. Review any existing staging DNS records before
applying and import records already in use. Cognito checks the public parent
`api.staging.mededbotswana.co.bw` A record before accepting its custom domain.
The ALB certificate is in Cape Town; the Cognito certificate is in `us-east-1`.

```bash
cp infrastructure/staging/backend.hcl.example infrastructure/staging/backend.hcl
cp infrastructure/staging/terraform.tfvars.example infrastructure/staging/terraform.tfvars
# Set the state bucket, hosted zone ID and the actual mobile deep links.
terraform -chdir=infrastructure/staging init -backend-config=backend.hcl
terraform -chdir=infrastructure/staging plan -out=staging.tfplan
terraform -chdir=infrastructure/staging apply staging.tfplan
```

The initial apply starts PostgreSQL and RabbitMQ but leaves web and worker at zero.
Wait for both data services to reach steady state. Publish each image to its own
staging ECR repository with a new immutable release tag:

```bash
export AWS_REGION=af-south-1
release_tag=YOUR_RELEASE_TAG
repository=$(terraform -chdir=infrastructure/staging output -raw ecr_repository_url)
backup_repository=$(terraform -chdir=infrastructure/staging output -raw backup_repository_url)
registry=${repository%%/*}
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$registry"
docker build --platform linux/amd64 -f docker/Dockerfile -t "$repository:$release_tag" .
docker push "$repository:$release_tag"
docker build --platform linux/amd64 -f docker/staging-backup.Dockerfile -t "$backup_repository:$release_tag" .
docker push "$backup_repository:$release_tag"
aws ecr describe-images --repository-name "${repository#*/}" --image-ids "imageTag=$release_tag" --query 'imageDetails[0].imageDigest' --output text
aws ecr describe-images --repository-name "${backup_repository#*/}" --image-ids "imageTag=$release_tag" --query 'imageDetails[0].imageDigest' --output text
```

Put the returned values in ignored staging tfvars as `image_digest` and
`backup_image_digest`. Publish the app image's `/app/staticfiles/` to the
`static_bucket` output under `static/`, using the release steps in the
[main deployment guide](../README.md#build-publish-migrate-then-enable-services).
Apply Terraform again with services still disabled, then run:

```bash
uv run python scripts/run_migration_task.py --terraform-directory infrastructure/staging
```

The migration task creates the unprivileged `medic_app` database role and applies
schema migrations. Once it exits successfully, set `services_enabled=true`, plan,
review, and apply. Both image digests are required to enable services; the backup
schedule activates with them. Cognito's default development sender has limits.
Configure an existing verified SES identity for application email delivery and
broader identity-email testing. Staff bootstrap uses `link_cognito` with a
confirmed staging Cognito subject as described in the main deployment guide.

## Recovery and validation

A scheduled Fargate task runs `pg_dump` at 02:00 UTC daily. It uploads an encrypted
custom-format dump to the private staging backup bucket; the `postgres/` prefix
expires after seven days. Check `/ecs/meded-staging` backup task logs and the bucket
for a recent dump. Test a restore to a separate database before relying on backups.
For example, download a chosen dump to a secure temporary directory, create an
empty local test database owned by the restore role, then run
`pg_restore --no-owner --no-privileges --exit-on-error -d RESTORE_DATABASE DUMP_FILE`.
Check key account and activity counts before deleting that temporary database and
dump. Do not restore over the running staging database; stop application writers
and take a fresh backup before a separately reviewed recovery operation.
RabbitMQ state survives task replacement through EFS, but queued messages have no
separate disaster-recovery backup. EFS or single-node broker failure can interrupt
staging; this environment does not model managed RDS/MQ failover or their TLS links.

```bash
terraform fmt -check infrastructure/staging
terraform -chdir=infrastructure/staging init -backend=false -input=false
terraform -chdir=infrastructure/staging validate
terraform -chdir=infrastructure/staging test
```

After deployment, test DNS and HTTPS on all three hosts, signup and confirmation,
password reset, TOTP MFA, staff review, media access, and mobile PKCE. Replace each
data service task in turn and confirm that an account and a queued message remain.
Before teardown, export required test data and review the plan: destroying the EFS
filesystem or Cognito pool permanently removes staging data and test identities.
Nonempty S3 buckets block accidental destroy; deletion protection defaults to on
for Cognito and the ALB.
