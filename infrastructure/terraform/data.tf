resource "aws_db_subnet_group" "main" {
  name       = local.name
  subnet_ids = aws_subnet.data[*].id
}
resource "aws_db_parameter_group" "main" {
  name_prefix = "${local.name}-"
  family      = "postgres17"
  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }
}
resource "aws_db_instance" "main" {
  identifier                      = local.name
  engine                          = "postgres"
  engine_version                  = "17"
  instance_class                  = var.db_instance_class
  allocated_storage               = 20
  max_allocated_storage           = 100
  storage_type                    = "gp3"
  storage_encrypted               = true
  db_name                         = "medic"
  username                        = "medic_admin"
  manage_master_user_password     = true
  db_subnet_group_name            = aws_db_subnet_group.main.name
  parameter_group_name            = aws_db_parameter_group.main.name
  vpc_security_group_ids          = [aws_security_group.database.id]
  publicly_accessible             = false
  multi_az                        = var.high_availability
  backup_retention_period         = 7
  backup_window                   = "01:00-02:00"
  maintenance_window              = "sun:02:30-sun:03:30"
  auto_minor_version_upgrade      = true
  deletion_protection             = var.deletion_protection
  skip_final_snapshot             = false
  final_snapshot_identifier       = "${local.name}-final"
  copy_tags_to_snapshot           = true
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
}
resource "random_password" "database" {
  length  = 40
  special = false
}
resource "random_password" "broker" {
  length  = 40
  special = false
}
resource "random_password" "django" {
  length  = 64
  special = false
}
resource "random_id" "session" { byte_length = 32 }
resource "aws_mq_broker" "main" {
  broker_name                = local.name
  engine_type                = "RabbitMQ"
  engine_version             = var.mq_engine_version
  host_instance_type         = var.mq_instance_type
  deployment_mode            = var.high_availability ? "CLUSTER_MULTI_AZ" : "SINGLE_INSTANCE"
  subnet_ids                 = var.high_availability ? aws_subnet.data[*].id : [aws_subnet.data[0].id]
  security_groups            = [aws_security_group.broker.id]
  publicly_accessible        = false
  auto_minor_version_upgrade = true
  apply_immediately          = false
  encryption_options { use_aws_owned_key = true }
  logs { general = true }
  user {
    username = "medic"
    password = random_password.broker.result
  }
  maintenance_window_start_time {
    day_of_week = "SUNDAY"
    time_of_day = "03:00"
    time_zone   = "UTC"
  }
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
    DATABASE_PASSWORD         = random_password.database.result
    RABBITMQ_URL              = "amqps://medic:${random_password.broker.result}@${trimprefix(aws_mq_broker.main.instances[0].endpoints[0], "amqps://")}/%2F"
    COGNITO_WEB_CLIENT_SECRET = aws_cognito_user_pool_client.web.client_secret
  })
}
