mock_provider "aws" {
  mock_data "aws_availability_zones" { defaults = { names = ["af-south-1a", "af-south-1b", "af-south-1c"] } }
  mock_data "aws_caller_identity" { defaults = { account_id = "123456789012" } }
  mock_data "aws_route53_zone" { defaults = { zone_id = "ZEXISTING", name = "mededbotswana.co.bw." } }
}
mock_provider "aws" { alias = "us_east_1" }
mock_provider "time" {}
mock_provider "random" {}
variables {
  hosted_zone_id       = "ZEXISTING"
  mobile_callback_urls = ["meded://oauth/callback"]
  mobile_logout_urls   = ["meded://oauth/logout"]
}
run "development_private_topology" {
  command = plan
  assert {
    condition     = length(aws_subnet.public) == 3 && length(aws_subnet.application) == 3 && length(aws_subnet.data) == 3
    error_message = "Public, private application and isolated data tiers must span three AZs."
  }
  assert {
    condition     = length(aws_nat_gateway.main) == 1 && !aws_db_instance.main.multi_az && aws_mq_broker.main.deployment_mode == "SINGLE_INSTANCE"
    error_message = "Development must use one NAT, Single-AZ RDS and a single broker."
  }
  assert {
    condition     = !aws_db_instance.main.publicly_accessible && !aws_mq_broker.main.publicly_accessible && alltrue([for service in aws_ecs_service.app : !service.network_configuration[0].assign_public_ip])
    error_message = "Database, broker and Fargate tasks must not be public."
  }
  assert {
    condition     = aws_cognito_user_pool_domain.main.domain == "oidc.api.mededbotswana.co.bw" && aws_cognito_user_pool_domain.main.managed_login_version == 2
    error_message = "Use the specified Cognito managed-login custom domain."
  }
  assert {
    condition     = length(aws_s3_bucket.assets) == 2 && alltrue([for bucket in aws_s3_bucket_public_access_block.assets : bucket.block_public_policy && bucket.block_public_acls])
    error_message = "Static and media buckets must both remain private."
  }
  assert {
    condition     = aws_ecs_service.app["web"].desired_count == 0 && aws_ecs_service.app["worker"].desired_count == 0
    error_message = "Services must remain stopped until a real image and migrations are ready."
  }
  assert {
    condition     = aws_ecs_service.app["worker"].deployment_maximum_percent == 100 && aws_ecs_service.app["worker"].deployment_minimum_healthy_percent == 0
    error_message = "Worker deployments must not overlap publishers."
  }
}
run "enabled_high_availability" {
  command = plan
  variables {
    high_availability = true
    services_enabled  = true
    image_digest      = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }
  assert {
    condition     = length(aws_nat_gateway.main) == 3 && aws_db_instance.main.multi_az && aws_mq_broker.main.deployment_mode == "CLUSTER_MULTI_AZ" && aws_ecs_service.app["web"].desired_count == 2 && aws_ecs_service.app["worker"].desired_count == 1
    error_message = "HA must enable AZ-local NAT, Multi-AZ data services, two web tasks and one worker."
  }
}
run "reject_unpublished_service" {
  command = plan
  variables { services_enabled = true }
  expect_failures = [aws_ecs_service.app]
}
