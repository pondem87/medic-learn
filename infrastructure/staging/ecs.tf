resource "aws_ecr_repository" "app" {
  name                 = local.name
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }
}
resource "aws_ecr_repository" "backup" {
  name                 = "${local.name}-backup"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }
}
resource "aws_ecs_cluster" "main" {
  name = local.name
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${local.name}"
  retention_in_days = 30
}
locals {
  ecs_trust = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }] })
  environment = [for name, value in {
    DJANGO_SETTINGS_MODULE      = "config.settings.production"
    DJANGO_ALLOWED_HOSTS        = join(",", local.domains)
    DJANGO_CSRF_TRUSTED_ORIGINS = join(",", [for domain in local.domains : "https://${domain}"])
    AWS_REGION                  = "af-south-1"
    COGNITO_POOL_ID             = aws_cognito_user_pool.main.id
    COGNITO_WEB_CLIENT_ID       = aws_cognito_user_pool_client.web.id
    COGNITO_MOBILE_CLIENT_ID    = aws_cognito_user_pool_client.mobile.id
    EVIDENCE_BUCKET             = aws_s3_bucket.assets["media"].id
    MEDIA_BUCKET                = aws_s3_bucket.assets["media"].id
    DJANGO_STATIC_URL           = "https://${aws_cloudfront_distribution.static.domain_name}/static/"
    DATABASE_HOST               = "postgres.staging.internal"
    DATABASE_NAME               = "medic"
    DATABASE_USER               = "medic_app"
    DATABASE_SSL_MODE           = "disable"
    RABBITMQ_QUEUE_TYPE         = "quorum"
    EMAIL_BACKEND               = "medic_learn.messages.ses_backend.EmailBackend"
    SES_REGION                  = var.email_identity_arn == "" ? "af-south-1" : split(":", var.email_identity_arn)[3]
    DEFAULT_FROM_EMAIL          = var.email_from
  } : { name = name, value = value }]
  app_secrets = [for name in ["DJANGO_SECRET_KEY", "COGNITO_SESSION_KEY", "DATABASE_PASSWORD", "RABBITMQ_URL", "COGNITO_WEB_CLIENT_SECRET"] : { name = name, valueFrom = "${aws_secretsmanager_secret.app.arn}:${name}::" }]
  workloads = {
    web     = { cpu = "512", memory = "1024", command = ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"] }
    worker  = { cpu = "256", memory = "512", command = ["python", "manage.py", "runworker"] }
    migrate = { cpu = "512", memory = "1024", command = ["python", "scripts/bootstrap_database.py"] }
  }
  data_services = {
    postgres = { image = "postgres:17.6@sha256:00bc86618629af00d2937fdc5a5d63db3ff8450acf52f0636ec813c7f4902929", cpu = "512", memory = "1024", port = 5432, mount = "/var/lib/postgresql/data", security_group = aws_security_group.database.id }
    rabbit   = { image = "rabbitmq:4.1.4-management@sha256:294b01e1796a8acede4619f32a1c394fae1f8021e57986ea01aad38dc2a4f502", cpu = "512", memory = "1024", port = 5672, mount = "/var/lib/rabbitmq", security_group = aws_security_group.broker.id }
  }
}
resource "aws_iam_role" "execution" {
  for_each           = toset(["app", "migrate", "data", "backup"])
  name               = "${local.name}-${each.key}-execution"
  assume_role_policy = local.ecs_trust
}
resource "aws_iam_role_policy_attachment" "execution" {
  for_each   = aws_iam_role.execution
  role       = each.value.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
resource "aws_iam_role_policy" "execution_secrets" {
  for_each = aws_iam_role.execution
  role     = each.value.id
  policy   = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = contains(["app", "backup"], each.key) ? [aws_secretsmanager_secret.app.arn] : each.key == "migrate" ? [aws_secretsmanager_secret.app.arn, aws_secretsmanager_secret.data.arn] : [aws_secretsmanager_secret.data.arn] }] })
}
resource "aws_iam_role" "application" {
  name               = "${local.name}-application"
  assume_role_policy = local.ecs_trust
}
resource "aws_iam_role_policy" "application" {
  role = aws_iam_role.application.id
  policy = jsonencode({ Version = "2012-10-17", Statement = concat([
    { Effect = "Allow", Action = ["cognito-idp:AdminGetUser", "cognito-idp:AdminUserGlobalSignOut", "cognito-idp:AdminSetUserMFAPreference", "cognito-idp:AdminEnableUser", "cognito-idp:AdminDisableUser"], Resource = aws_cognito_user_pool.main.arn },
    { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"], Resource = ["${aws_s3_bucket.assets["media"].arn}/cards/*", "${aws_s3_bucket.assets["media"].arn}/uploads/*"] }
  ], var.email_identity_arn == "" ? [] : [{ Effect = "Allow", Action = ["ses:SendRawEmail"], Resource = var.email_identity_arn }]) })
}
resource "aws_iam_role" "data" {
  for_each           = local.data_services
  name               = "${local.name}-${each.key}"
  assume_role_policy = local.ecs_trust
}
resource "aws_iam_role_policy" "data_efs" {
  for_each = local.data_services
  role     = aws_iam_role.data[each.key].id
  policy   = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["elasticfilesystem:ClientMount", "elasticfilesystem:ClientWrite"], Resource = aws_efs_file_system.data.arn, Condition = { StringEquals = { "elasticfilesystem:AccessPointArn" = aws_efs_access_point.data[each.key].arn } } }] })
}
resource "aws_ecs_task_definition" "app" {
  for_each                 = local.workloads
  family                   = "${local.name}-${each.key}"
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.execution[each.key == "migrate" ? "migrate" : "app"].arn
  task_role_arn            = aws_iam_role.application.arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  container_definitions = jsonencode([merge({
    name        = "app"
    image       = local.image
    essential   = true
    user        = "10001:10001"
    command     = each.value.command
    environment = concat(local.environment, each.key == "migrate" ? [{ name = "DATABASE_ADMIN_USER", value = "medic_admin" }] : [])
    secrets = concat(local.app_secrets, each.key == "migrate" ? [
      { name = "DATABASE_ADMIN_PASSWORD", valueFrom = "${aws_secretsmanager_secret.data.arn}:DATABASE_ADMIN_PASSWORD::" }
    ] : [])
    stopTimeout      = 60
    linuxParameters  = { initProcessEnabled = true }
    logConfiguration = { logDriver = "awslogs", options = { awslogs-group = aws_cloudwatch_log_group.app.name, awslogs-region = "af-south-1", awslogs-stream-prefix = each.key } }
  }, each.key == "web" ? { portMappings = [{ containerPort = 8000, protocol = "tcp" }] } : {})])
}
resource "aws_ecs_task_definition" "data" {
  for_each                 = local.data_services
  family                   = "${local.name}-${each.key}"
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.execution["data"].arn
  task_role_arn            = aws_iam_role.data[each.key].arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  volume {
    name = "data"
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.data.id
      transit_encryption = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.data[each.key].id
        iam             = "ENABLED"
      }
    }
  }
  container_definitions = jsonencode([{
    name      = each.key
    image     = each.value.image
    essential = true
    environment = each.key == "postgres" ? [
      { name = "POSTGRES_DB", value = "medic" },
      { name = "POSTGRES_USER", value = "medic_admin" },
      { name = "PGDATA", value = "/var/lib/postgresql/data/pgdata" }
      ] : [
      { name = "RABBITMQ_DEFAULT_USER", value = "medic" },
      { name = "RABBITMQ_NODENAME", value = "rabbit@localhost" }
    ]
    secrets = each.key == "postgres" ? [
      { name = "POSTGRES_PASSWORD", valueFrom = "${aws_secretsmanager_secret.data.arn}:DATABASE_ADMIN_PASSWORD::" }
      ] : [
      { name = "RABBITMQ_DEFAULT_PASS", valueFrom = "${aws_secretsmanager_secret.data.arn}:RABBITMQ_PASSWORD::" },
      { name = "RABBITMQ_ERLANG_COOKIE", valueFrom = "${aws_secretsmanager_secret.data.arn}:RABBITMQ_ERLANG_COOKIE::" }
    ]
    mountPoints      = [{ sourceVolume = "data", containerPath = each.value.mount, readOnly = false }]
    portMappings     = [{ containerPort = each.value.port, protocol = "tcp" }]
    healthCheck      = each.key == "postgres" ? { command = ["CMD-SHELL", "pg_isready -U medic_admin -d medic"], interval = 10, timeout = 5, retries = 6, startPeriod = 60 } : { command = ["CMD", "rabbitmq-diagnostics", "-q", "ping"], interval = 15, timeout = 5, retries = 6, startPeriod = 90 }
    stopTimeout      = 120
    logConfiguration = { logDriver = "awslogs", options = { awslogs-group = aws_cloudwatch_log_group.app.name, awslogs-region = "af-south-1", awslogs-stream-prefix = each.key } }
  }])
}
resource "aws_ecs_service" "data" {
  for_each                           = local.data_services
  name                               = "${local.name}-${each.key}"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.data[each.key].arn
  launch_type                        = "FARGATE"
  platform_version                   = "1.4.0"
  desired_count                      = 1
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100
  wait_for_steady_state              = true
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  network_configuration {
    subnets          = [aws_subnet.application[0].id]
    security_groups  = [each.value.security_group]
    assign_public_ip = false
  }
  service_registries { registry_arn = aws_service_discovery_service.data[each.key].arn }
  depends_on = [aws_efs_mount_target.data, aws_iam_role_policy.data_efs, aws_iam_role_policy.execution_secrets, aws_route.outbound]
}
resource "aws_ecs_service" "app" {
  for_each                           = toset(["web", "worker"])
  name                               = "${local.name}-${each.key}"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.app[each.key].arn
  launch_type                        = "FARGATE"
  platform_version                   = "1.4.0"
  desired_count                      = var.services_enabled ? 1 : 0
  deployment_minimum_healthy_percent = each.key == "worker" ? 0 : 100
  deployment_maximum_percent         = each.key == "worker" ? 100 : 200
  health_check_grace_period_seconds  = each.key == "web" ? 60 : null
  triggers                           = { secrets_version = aws_secretsmanager_secret_version.app.version_id }
  wait_for_steady_state              = true
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  network_configuration {
    subnets          = aws_subnet.application[*].id
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = false
  }
  dynamic "load_balancer" {
    for_each = each.key == "web" ? [1] : []
    content {
      target_group_arn = aws_lb_target_group.web.arn
      container_name   = "app"
      container_port   = 8000
    }
  }
  lifecycle {
    precondition {
      condition     = !var.services_enabled || (var.image_digest != null && var.backup_image_digest != null)
      error_message = "Publish the staging app and backup images, then run migrations before enabling services."
    }
  }
  depends_on = [aws_ecs_service.data, aws_lb_listener_rule.web, aws_iam_role_policy.application, aws_iam_role_policy.execution_secrets]
}
