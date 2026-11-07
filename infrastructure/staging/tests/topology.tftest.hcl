mock_provider "aws" {
  mock_data "aws_availability_zones" { defaults = { names = ["af-south-1a", "af-south-1b"] } }
  mock_data "aws_caller_identity" { defaults = { account_id = "123456789012" } }
  mock_data "aws_route53_zone" { defaults = { zone_id = "ZEXISTING", name = "mededbotswana.co.bw." } }
}
mock_provider "aws" { alias = "us_east_1" }
mock_provider "time" {}
mock_provider "random" {}
variables {
  hosted_zone_id       = "ZEXISTING"
  mobile_callback_urls = ["meded-staging://oauth/callback"]
  mobile_logout_urls   = ["meded-staging://oauth/logout"]
}
run "private_staging_topology" {
  command = plan
  assert {
    condition     = length(aws_subnet.public) == 2 && length(aws_subnet.application) == 2 && aws_ecs_service.data["postgres"].desired_count == 1 && aws_ecs_service.data["rabbit"].desired_count == 1
    error_message = "Staging needs two AZs and one of each private data service."
  }
  assert {
    condition     = alltrue([for service in aws_ecs_service.data : !service.network_configuration[0].assign_public_ip]) && alltrue([for service in aws_ecs_service.app : !service.network_configuration[0].assign_public_ip])
    error_message = "Fargate tasks must not get public IP addresses."
  }
  assert {
    condition     = alltrue([for service in aws_ecs_service.data : service.deployment_maximum_percent == 100 && service.deployment_minimum_healthy_percent == 0])
    error_message = "Data service deployments must not overlap access to their EFS data."
  }
  assert {
    condition     = length(aws_efs_access_point.data) == 2 && aws_cognito_user_pool_domain.main.domain == "oidc.api.staging.mededbotswana.co.bw" && aws_cognito_user_pool_domain.main.managed_login_version == 2
    error_message = "Persistent data and a separate staging login domain are required."
  }
  assert {
    condition     = length(aws_s3_bucket.assets) == 2 && !aws_s3_bucket.assets["media"].force_destroy && aws_cloudwatch_event_rule.backup.state == "DISABLED"
    error_message = "Private staging buckets and a gated backup schedule are required."
  }
  assert {
    condition     = aws_ecs_service.app["web"].desired_count == 0 && aws_ecs_service.app["worker"].desired_count == 0
    error_message = "App services must wait for image publication and migrations."
  }
}
run "published_staging" {
  command = plan
  variables {
    services_enabled    = true
    image_digest        = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    backup_image_digest = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  }
  assert {
    condition     = aws_ecs_service.app["web"].desired_count == 1 && aws_ecs_service.app["worker"].desired_count == 1 && aws_cloudwatch_event_rule.backup.state == "ENABLED"
    error_message = "Published staging starts web, worker and daily backups."
  }
}
run "reject_unpublished_service" {
  command = plan
  variables { services_enabled = true }
  expect_failures = [aws_ecs_service.app]
}
run "reject_missing_backup_image" {
  command = plan
  variables {
    services_enabled = true
    image_digest     = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }
  expect_failures = [aws_ecs_service.app]
}
