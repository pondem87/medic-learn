resource "aws_ecr_repository" "app" {
  name                 = local.name
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
    AWS_REGION                  = var.region
    COGNITO_POOL_ID             = aws_cognito_user_pool.main.id
    COGNITO_WEB_CLIENT_ID       = aws_cognito_user_pool_client.web.id
    COGNITO_MOBILE_CLIENT_ID    = aws_cognito_user_pool_client.mobile.id
    EVIDENCE_BUCKET             = aws_s3_bucket.assets["media"].id
    MEDIA_BUCKET                = aws_s3_bucket.assets["media"].id
    DJANGO_STATIC_URL           = "https://${aws_cloudfront_distribution.static.domain_name}/static/"
    DATABASE_HOST               = aws_db_instance.main.address
    DATABASE_NAME               = aws_db_instance.main.db_name
    DATABASE_USER               = "medic_app"
    DATABASE_SSL_ROOT_CERT      = "/app/docker/rds-ca.pem"
    RABBITMQ_QUEUE_TYPE         = "quorum"
    EMAIL_BACKEND               = "medic_learn.messages.ses_backend.EmailBackend"
    SES_REGION                  = var.email_identity_arn == "" ? var.region : split(":", var.email_identity_arn)[3]
    DEFAULT_FROM_EMAIL          = var.email_from
  } : { name = name, value = value }]
  secrets = [for name in ["DJANGO_SECRET_KEY", "COGNITO_SESSION_KEY", "DATABASE_PASSWORD", "RABBITMQ_URL", "COGNITO_WEB_CLIENT_SECRET"] : { name = name, valueFrom = "${aws_secretsmanager_secret.app.arn}:${name}::" }]
  workloads = {
    web     = { cpu = "512", memory = "1024", command = ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"] }
    worker  = { cpu = "256", memory = "512", command = ["python", "manage.py", "runworker"] }
    migrate = { cpu = "512", memory = "1024", command = ["python", "scripts/bootstrap_database.py"] }
  }
}
resource "aws_iam_role" "execution" {
  name               = "${local.name}-execution"
  assume_role_policy = local.ecs_trust
}
resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
resource "aws_iam_role_policy" "execution_secrets" {
  role   = aws_iam_role.execution.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = aws_secretsmanager_secret.app.arn }] })
}
resource "aws_iam_role" "migration_execution" {
  name               = "${local.name}-migration-execution"
  assume_role_policy = local.ecs_trust
}
resource "aws_iam_role_policy_attachment" "migration_execution" {
  role       = aws_iam_role.migration_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
resource "aws_iam_role_policy" "migration_secrets" {
  role   = aws_iam_role.migration_execution.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = [aws_secretsmanager_secret.app.arn, aws_db_instance.main.master_user_secret[0].secret_arn] }] })
}
resource "aws_iam_role" "app" {
  name               = "${local.name}-application"
  assume_role_policy = local.ecs_trust
}
resource "aws_iam_role_policy" "app" {
  role = aws_iam_role.app.id
  policy = jsonencode({ Version = "2012-10-17", Statement = concat([
    { Effect = "Allow", Action = ["cognito-idp:AdminGetUser", "cognito-idp:AdminUserGlobalSignOut", "cognito-idp:AdminSetUserMFAPreference", "cognito-idp:AdminEnableUser", "cognito-idp:AdminDisableUser"], Resource = aws_cognito_user_pool.main.arn },
    { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"], Resource = ["${aws_s3_bucket.assets["media"].arn}/cards/*", "${aws_s3_bucket.assets["media"].arn}/uploads/*"] }
  ], var.email_identity_arn == "" ? [] : [{ Effect = "Allow", Action = ["ses:SendRawEmail"], Resource = var.email_identity_arn }]) })
}
resource "aws_ecs_task_definition" "app" {
  for_each                 = local.workloads
  family                   = "${local.name}-${each.key}"
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = each.key == "migrate" ? aws_iam_role.migration_execution.arn : aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.app.arn
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
    environment = local.environment
    secrets = concat(local.secrets, each.key == "migrate" ? [
      { name = "DATABASE_ADMIN_USER", valueFrom = "${aws_db_instance.main.master_user_secret[0].secret_arn}:username::" },
      { name = "DATABASE_ADMIN_PASSWORD", valueFrom = "${aws_db_instance.main.master_user_secret[0].secret_arn}:password::" }
    ] : [])
    stopTimeout      = 60
    linuxParameters  = { initProcessEnabled = true }
    logConfiguration = { logDriver = "awslogs", options = { awslogs-group = aws_cloudwatch_log_group.app.name, awslogs-region = var.region, awslogs-stream-prefix = each.key } }
  }, each.key == "web" ? { portMappings = [{ containerPort = 8000, protocol = "tcp" }] } : {})])
}
resource "aws_ecs_service" "app" {
  for_each                           = toset(["web", "worker"])
  name                               = "${local.name}-${each.key}"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.app[each.key].arn
  launch_type                        = "FARGATE"
  platform_version                   = "1.4.0"
  desired_count                      = var.services_enabled ? (each.key == "web" && var.high_availability ? 2 : 1) : 0
  deployment_minimum_healthy_percent = each.key == "worker" ? 0 : 100
  deployment_maximum_percent         = each.key == "worker" ? 100 : 200
  health_check_grace_period_seconds  = each.key == "web" ? 60 : null
  force_new_deployment               = true
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
      condition     = !var.services_enabled || var.image_digest != null
      error_message = "Push an image and specify its digest before enabling ECS services."
    }
  }
  depends_on = [aws_lb_listener_rule.web, aws_secretsmanager_secret_version.app, aws_iam_role_policy.execution_secrets, aws_iam_role_policy.app, aws_route.outbound]
}
