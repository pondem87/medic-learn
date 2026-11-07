# Terraform deployment

The infrastructure targets **af-south-1 (Cape Town)** and reuses your existing public
Route 53 hosted zone. It serves:

- Application: `https://api.mededbotswana.co.bw` and `https://www.mededbotswana.co.bw`.
- Cognito managed login: `https://oidc.api.mededbotswana.co.bw`.
- Static assets: the generated CloudFront HTTPS hostname, backed by a private S3 bucket.
- Media: a separate private S3 bucket; cards have authorized downloads, and general
  Django media storage uses short-lived signed URLs. No public media route is added.

## Topology and defaults

Three AZs each have public, private application and isolated data subnets. ALB and
NAT use public subnets. Fargate web, worker and migration tasks have no public IPs.
RDS and MQ use data subnets with no internet default route. Security groups allow
HTTPS to ALB, ALB to port 8000, tasks to PostgreSQL 5432 and RabbitMQ TLS 5671.
Tasks reach AWS APIs through HTTPS/NAT; S3 uses a gateway endpoint.

Development defaults are one NAT, one web task, one worker, Single-AZ PostgreSQL 17
(`db.t4g.micro`) and single-instance RabbitMQ 4.2 (`mq.m7g.medium`). Setting
`high_availability=true` enables three NATs, two web tasks, Multi-AZ RDS and three-node
MQ. Review the plan carefully: changing MQ deployment mode can replace the broker.
The worker always remains singleton and its deployments do not overlap.

RDS storage, S3 and Secrets Manager are encrypted. RDS retains seven days of backups
and requires a final snapshot; deletion protection is enabled by default. Buckets
cannot be destroyed while nonempty. Static storage is versioned; media is deliberately
unversioned so deleting a student card does not leave historical copies.

ALB, NAT, RDS and MQ have standing costs even with ECS services disabled. The selected
Single-AZ/single-NAT defaults trade availability for development cost; they are not
an HA production topology. Infrastructure is prepared locally, not automatically applied.

## State and initial configuration

Use Terraform 1.16.2, AWS CLI v2, Docker, and the project's uv environment. AWS credentials
come from your normal profile/SSO/role, not Terraform variables. Enable Cape Town in your
AWS account if it is not already enabled. Commit `.terraform.lock.hcl`, never state or plans.

Terraform state contains generated DB/broker passwords, Cognito client secrets and
application encryption keys. Use an encrypted, versioned private S3 backend with
restricted IAM and native state locking. If no backend already exists, bootstrap one:

```bash
terraform -chdir=infrastructure/state init
terraform -chdir=infrastructure/state plan -var='bucket_name=YOUR-UNIQUE-STATE-BUCKET'
terraform -chdir=infrastructure/state apply -var='bucket_name=YOUR-UNIQUE-STATE-BUCKET'
```

After creating the bucket, migrate the bootstrap root's state into the same bucket
under a separate key so both Terraform roots have remote state:

```bash
cp infrastructure/state/backend.tf.example infrastructure/state/backend.tf
cp infrastructure/state/backend.hcl.example infrastructure/state/backend.hcl
# Set the bucket name in backend.hcl; keep the bootstrap key separate.
terraform -chdir=infrastructure/state init -migrate-state -backend-config=backend.hcl
```

Confirm the migration succeeded before removing any local state backup. The generated
backend declaration and local inputs are ignored; `prevent_destroy` protects the bucket.
For both roots, grant operators only the required bucket/key access: bucket listing,
GetObject/PutObject on state, and GetObject/PutObject/DeleteObject on the matching
`.tflock` object. Bootstrap and application keys must differ. Keep backend access out
of runtime ECS roles. No DynamoDB table is needed for native S3 locking.

Application state uses the same bucket with its own S3 key:

```bash
cp infrastructure/terraform/backend.hcl.example infrastructure/terraform/backend.hcl
cp infrastructure/terraform/terraform.tfvars.example infrastructure/terraform/terraform.tfvars
# Fill in the state bucket, existing hosted_zone_id and actual mobile callback/logout URIs.
terraform -chdir=infrastructure/terraform init -backend-config=backend.hcl
terraform -chdir=infrastructure/terraform plan -out=deployment.tfplan
terraform -chdir=infrastructure/terraform apply deployment.tfplan
```

The first apply leaves services at zero tasks (`services_enabled=false`) while creating
ECR, networking, databases, identity, buckets and task definitions. It can take time for
RDS, MQ, certificates, DNS and CloudFront to become ready. It does not run migrations.

The hosted zone must cover `mededbotswana.co.bw` and already be publicly delegated.
Terraform creates only the specified application/custom-domain aliases and certificate
validation records. If any already exist, import those records into the matching
Terraform resource addresses and inspect the plan; do not blindly overwrite DNS.
Existing deployed Cognito/S3 resources also require import rather than replacement.
The previous CloudFormation template was not deployed by this implementation and is removed.

The Cognito certificate uses an aliased AWS provider in **us-east-1**; ALB's certificate
is in Cape Town. Cognito needs its immediate parent `api.mededbotswana.co.bw` to resolve.
Terraform orders the ALB alias first and waits for propagation before domain creation.
If public DNS propagation takes longer, wait and retry the apply. See
[AWS custom-domain prerequisites](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-add-custom-domain.html).

## Build, publish, migrate, then enable services

Run from the repository root, choosing a new immutable release tag:

```bash
export AWS_REGION=af-south-1
release_tag=YOUR_RELEASE_TAG
repository=$(terraform -chdir=infrastructure/terraform output -raw ecr_repository_url)
registry=${repository%%/*}
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$registry"
docker build --platform linux/amd64 -f docker/Dockerfile -t "$repository:$release_tag" .
docker push "$repository:$release_tag"
```

The image is non-root, contains Gunicorn and a static manifest, and excludes `.env`,
state and private uploads. Collectstatic runs without production credentials. The image
includes the RDS trust bundle; database and broker connections validate TLS hostnames.

Publish assets from that exact image before enabling the release. Do not use `--delete`:
old hashed assets must remain available to pages served by an earlier image during rollout.

```bash
asset_dir=$(mktemp -d)
asset_container=$(docker create "$repository:$release_tag")
docker cp "$asset_container:/app/staticfiles/." "$asset_dir/"
docker rm "$asset_container"
static_bucket=$(terraform -chdir=infrastructure/terraform output -raw static_bucket)
aws s3 sync "$asset_dir/" "s3://$static_bucket/static/" --cache-control 'public,max-age=300'
aws ecr describe-images --repository-name "${repository#*/}" --image-ids "imageTag=$release_tag" --query 'imageDetails[0].imageDigest' --output text
```

Set the returned immutable `image_digest` in your ignored tfvars, keeping services
**disabled** on the initial release. Apply to register the real task definitions,
then run the bootstrap/migration task:

```bash
terraform -chdir=infrastructure/terraform plan -out=deployment.tfplan
terraform -chdir=infrastructure/terraform apply deployment.tfplan
uv run python scripts/run_migration_task.py
```

The one-off task receives RDS administrator credentials from its own execution role,
creates/updates `medic_app`, grants access to the application database/schema and runs
migrations as that application user. Web and worker tasks never receive RDS administrator
credentials. The script verifies container exit status; failure must be resolved before
turning on services. The runtime role owns its application schema for migrations, but
has no RDS superuser privileges. Logs are under `/ecs/meded-development`.

After successful migration set `services_enabled=true`, plan and apply. ALB health
probes `/health/` (process liveness, not a provider/database readiness check); ordinary
traffic redirects to HTTPS. Deployment circuit breakers roll back unhealthy ECS rollouts.
Web uses a rolling deployment; worker briefly stops before replacement to avoid overlapping
publishers. Subsequent schema changes must be backward compatible during rollout; keep
services disabled for initial or deliberately coordinated breaking migrations.

For subsequent releases, register the new migration task with services disabled during
maintenance, run migrations, then re-enable the new image. For zero-downtime upgrades,
use a reviewed release workflow that registers/runs the migration task before updating
web/worker services; this repository does not automatically mutate services outside Terraform.

## Secrets, email and operation

Terraform generates application secrets and places them in Secrets Manager. ECS injects
them at task startup. The task definition environment contains nonsecret configuration;
outputs expose resource identifiers, not plaintext credentials. Secret version changes
trigger service deployment. Session-key replacement invalidates encrypted provider values;
coordinate credential rotation and session invalidation. RabbitMQ's initial user is managed
only at broker creation; changing its Terraform password can replace the broker. Follow
Amazon MQ's supported user-management procedure for in-place rotation.

Application mail uses SES with the Fargate role. Supply an existing verified
`email_identity_arn` and `email_from`, and complete SES production-access requirements
before enabling real notifications. Without that identity, Cognito uses its limited
development sender and application SES delivery is unavailable. Verify that the SES
identity region is supported by Cognito for your user-pool region. No mail credentials
are embedded in the image. Local development continues to use SMTP/Mailpit.

Application media permissions cover `cards/` and `uploads/` in the private media bucket.
Static publishing is a release-operator permission; runtime tasks cannot rewrite public
assets. Use the emitted static URL in Django (Terraform injects it automatically).
Generic media URL generation must follow authorization; signed URLs expire after 60 seconds.
Student cards still use the staff download endpoint and durable deletion, not public URLs.

## Infrastructure validation

```bash
terraform fmt -check -recursive infrastructure
terraform -chdir=infrastructure/terraform init -backend=false -input=false
terraform -chdir=infrastructure/terraform validate
terraform -chdir=infrastructure/terraform test
docker build -f docker/Dockerfile -t medic-learn:check .
```

Mocked tests validate development/HA topology, private networking, custom domains,
private buckets, singleton worker deployment and rejection of enabled services without
an image digest. They do not call AWS or verify account quotas, DNS delegation, regional
capacity or live resource creation. Use a real reviewed Terraform plan before applying.

## Identity cutover and staff bootstrap

Back up the development database before applying migrations. Existing account IDs
and data remain; old passwords and sessions are invalidated and prior profile
validation is reset. No password import or automatic email linking is performed.
Historical proof/blacklist tables can remain but no longer authenticate users.

Register and confirm an identity in Cognito, then explicitly bind it and grant staff:

```bash
uv run python manage.py link_cognito staff@example.com COGNITO_SUBJECT --staff --reason 'Initial staff bootstrap; identity checked'
uv run python manage.py manage_council 'Botswana registry name' --actor staff@example.com --reason 'Approved registry option'
```

The link command verifies subject and confirmed email against Cognito. It refuses
conflicting or blocked identities. Staff account and category permissions are
independent. Council choices are operator-managed with staff attribution; names
are not invented or seeded as verified registry facts.

## Web and mobile contracts

Web keeps `/register/`, `/login/`, `/verify/`, `/profile/` and POST-only `/logout/`.
Recovery uses `/password/forgot/` and `/password/reset/`; optional TOTP uses
`/mfa/setup/` and `/mfa/challenge/`. Fresh login (five minutes) is required for setup.
Django sessions last eight hours. Passwords are never persisted. Cognito token
values retained in database sessions are encrypted; browser cookies contain only
Django session identifiers. Setup secrets are shown only on a no-store page.
Lost authenticators require staff to record an external identity check and reason.

Native mobile uses Cognito managed login, authorization code and S256 PKCE, with
openid, email, profile, aws.cognito.signin.user.admin and medic-api/access scopes.
Exchange the code at Cognito's token endpoint using the identical redirect URI and
code verifier. Store tokens in the mobile OS secure store. API calls use
`Authorization: Bearer ACCESS_TOKEN`; ID tokens are rejected. Access tokens last
five minutes, refresh tokens seven days with rotation. The mobile implementation
must revoke its refresh token and clear local tokens on logout, and use Cognito's
logout endpoint to clear managed-login cookies. Already-issued access tokens can
remain valid until expiry because DRF verifies signatures offline.

GET/PATCH `/api/v1/me/` permits confirmed users to manage onboarding and bio.
Only name, phone, biography and notifications_enabled are writable. Responses
include category, validation, verified details, version and allowed_roles.
GET `/api/v1/councils/` lists active council choices.
POST `/api/v1/me/submissions/` takes category and council_id/registration_number
for professionals or multipart card for students. Staff actions at
`/api/v1/accounts/{uuid}/actions/` require reason; review/approve/return/reject/revoke/
update also require version. Local JWT issue/refresh and email-proof APIs are removed.
Use X-Active-Role (learner by default) for future role-gated mobile capabilities;
web selection is per session. Capability endpoints must enforce VerifiedRole or
require_role on every request. No course or training delivery endpoints exist yet.

## Verification, evidence and operations

Professionals submit council and registration number. Staff manually check registry
entries, then enter registered name, profession, council and number. Students upload
JPEG/PNG/PDF cards up to 10 MB; staff enter registered name, programme and school.
School contact and periodic rechecks are deferred. Staff start review, then approve,
return for correction or reject. Approval grants student learner access or professional
learner/trainer access. Revocation and category resubmission remove access immediately.
Biographies/contact details remain user-provided and unverified after approval.

Card downloads require staff authentication. Approval/rejection disables downloads
immediately and queues deletion; the worker retries storage failures. Keep the worker
running. Unattached uploads are cleanup-addressable and recovered after an hour.
Staff pages show pending operation failures. Cards are not part of audit payloads.
Image uploads are decoded/re-encoded; PDFs are parsed and served as attachments.
This is format validation, not an antivirus guarantee.

Activity records include actor, subject, time, reason and field changes; staff see
history, users see outcomes. PostgreSQL prevents record update/delete. A database
owner can still disable those protections; this is not external tamper-proof storage.
Cognito access/MFA operations are serialized per account and retried durably. Local
restrictions apply immediately; out-of-band AWS changes are not a realtime Django
session revocation feed. Use staff actions for blocks and recovery.

## Acceptance

Automated checks use mocked Cognito and isolated PostgreSQL; they do not deploy AWS.
After configuration, smoke-test signup/confirmation, password login, TOTP setup and
challenge, reset, staff-assisted recovery, both profile reviews and evidence deletion.
Use a PKCE-capable mobile test client to obtain tokens, confirm ID/wrong-client/expired
rejection, and verify local suspension blocks API and web access. Inspect pending
operations and activity history. Live AWS validation requires an explicitly configured
pool; do not describe unit tests as live provider acceptance.
