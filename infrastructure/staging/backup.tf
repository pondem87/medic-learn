resource "aws_s3_bucket" "backup" {
  bucket        = "${local.name}-backup-${data.aws_caller_identity.current.account_id}"
  force_destroy = false
}
resource "aws_s3_bucket_public_access_block" "backup" {
  bucket                  = aws_s3_bucket.backup.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_server_side_encryption_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}
resource "aws_s3_bucket_ownership_controls" "backup" {
  bucket = aws_s3_bucket.backup.id
  rule { object_ownership = "BucketOwnerEnforced" }
}
resource "aws_s3_bucket_lifecycle_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id
  rule {
    id     = "expire-seven-days"
    status = "Enabled"
    filter { prefix = "postgres/" }
    expiration { days = 7 }
  }
}
resource "aws_s3_bucket_policy" "backup" {
  bucket     = aws_s3_bucket.backup.id
  policy     = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Deny", Principal = "*", Action = "s3:*", Resource = [aws_s3_bucket.backup.arn, "${aws_s3_bucket.backup.arn}/*"], Condition = { Bool = { "aws:SecureTransport" = "false" } } }] })
  depends_on = [aws_s3_bucket_public_access_block.backup]
}
resource "aws_iam_role" "backup" {
  name               = "${local.name}-backup"
  assume_role_policy = local.ecs_trust
}
resource "aws_iam_role_policy" "backup" {
  role   = aws_iam_role.backup.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["s3:PutObject"], Resource = "${aws_s3_bucket.backup.arn}/postgres/*" }] })
}
resource "aws_ecs_task_definition" "backup" {
  family                   = "${local.name}-backup"
  cpu                      = "256"
  memory                   = "512"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.execution["backup"].arn
  task_role_arn            = aws_iam_role.backup.arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  container_definitions = jsonencode([{
    name      = "backup"
    image     = local.backup_image
    essential = true
    environment = [
      { name = "PGHOST", value = "postgres.staging.internal" },
      { name = "PGDATABASE", value = "medic" },
      { name = "PGUSER", value = "medic_app" },
      { name = "PGSSLMODE", value = "disable" },
      { name = "BACKUP_BUCKET", value = aws_s3_bucket.backup.id }
    ]
    secrets          = [{ name = "PGPASSWORD", valueFrom = "${aws_secretsmanager_secret.app.arn}:DATABASE_PASSWORD::" }]
    logConfiguration = { logDriver = "awslogs", options = { awslogs-group = aws_cloudwatch_log_group.app.name, awslogs-region = "af-south-1", awslogs-stream-prefix = "backup" } }
  }])
}
resource "aws_iam_role" "backup_schedule" {
  name               = "${local.name}-backup-schedule"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "events.amazonaws.com" }, Action = "sts:AssumeRole" }] })
}
resource "aws_iam_role_policy" "backup_schedule" {
  role = aws_iam_role.backup_schedule.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Effect = "Allow", Action = ["ecs:RunTask"], Resource = aws_ecs_task_definition.backup.arn, Condition = { ArnEquals = { "ecs:cluster" = aws_ecs_cluster.main.arn } } },
    { Effect = "Allow", Action = ["iam:PassRole"], Resource = [aws_iam_role.execution["backup"].arn, aws_iam_role.backup.arn] }
  ] })
}
resource "aws_cloudwatch_event_rule" "backup" {
  name                = "${local.name}-postgres-backup"
  schedule_expression = "cron(0 2 * * ? *)"
  state               = var.services_enabled && var.backup_image_digest != null ? "ENABLED" : "DISABLED"
}
resource "aws_cloudwatch_event_target" "backup" {
  rule     = aws_cloudwatch_event_rule.backup.name
  arn      = aws_ecs_cluster.main.arn
  role_arn = aws_iam_role.backup_schedule.arn
  ecs_target {
    task_definition_arn = aws_ecs_task_definition.backup.arn
    task_count          = 1
    launch_type         = "FARGATE"
    platform_version    = "1.4.0"
    network_configuration {
      subnets          = aws_subnet.application[*].id
      security_groups  = [aws_security_group.tasks.id]
      assign_public_ip = false
    }
  }
  depends_on = [aws_iam_role_policy.backup_schedule, aws_iam_role_policy.backup, aws_iam_role_policy.execution_secrets, aws_ecs_service.data]
}
