resource "random_password" "database_admin" {
  length  = 40
  special = false
}
resource "random_password" "database_app" {
  length  = 40
  special = false
}
resource "random_password" "broker" {
  length  = 40
  special = false
}
resource "random_password" "erlang_cookie" {
  length  = 48
  special = false
}
resource "random_password" "django" {
  length  = 64
  special = false
}
resource "random_id" "session" { byte_length = 32 }

resource "aws_secretsmanager_secret" "data" {
  name_prefix             = "${local.name}-data-"
  recovery_window_in_days = 7
}
resource "aws_secretsmanager_secret_version" "data" {
  secret_id = aws_secretsmanager_secret.data.id
  secret_string = jsonencode({
    DATABASE_ADMIN_PASSWORD = random_password.database_admin.result
    RABBITMQ_PASSWORD       = random_password.broker.result
    RABBITMQ_ERLANG_COOKIE  = random_password.erlang_cookie.result
  })
}
resource "aws_secretsmanager_secret" "app" {
  name_prefix             = "${local.name}-application-"
  recovery_window_in_days = 7
}
resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    DJANGO_SECRET_KEY         = random_password.django.result
    COGNITO_SESSION_KEY       = "${random_id.session.b64_url}="
    DATABASE_PASSWORD         = random_password.database_app.result
    RABBITMQ_URL              = "amqp://medic:${random_password.broker.result}@rabbit.staging.internal:5672/%2F"
    COGNITO_WEB_CLIENT_SECRET = aws_cognito_user_pool_client.web.client_secret
  })
}

resource "aws_service_discovery_private_dns_namespace" "main" {
  name = "staging.internal"
  vpc  = aws_vpc.main.id
}
resource "aws_service_discovery_service" "data" {
  for_each = toset(["postgres", "rabbit"])
  name     = each.key
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id
    dns_records {
      ttl  = 10
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }
  health_check_custom_config {}
}

resource "aws_efs_file_system" "data" {
  encrypted        = true
  throughput_mode  = "bursting"
  performance_mode = "generalPurpose"
  tags             = { Name = "${local.name}-data" }
}
resource "aws_efs_mount_target" "data" {
  count           = 2
  file_system_id  = aws_efs_file_system.data.id
  subnet_id       = aws_subnet.application[count.index].id
  security_groups = [aws_security_group.efs.id]
}
resource "aws_efs_access_point" "data" {
  for_each       = toset(["postgres", "rabbit"])
  file_system_id = aws_efs_file_system.data.id
  posix_user {
    uid = 999
    gid = 999
  }
  root_directory {
    path = "/${each.key}"
    creation_info {
      owner_uid   = 999
      owner_gid   = 999
      permissions = "0750"
    }
  }
  tags = { Name = "${local.name}-${each.key}" }
}
