resource "aws_cognito_user_pool" "main" {
  name                     = local.name
  user_pool_tier           = "ESSENTIALS"
  deletion_protection      = var.deletion_protection ? "ACTIVE" : "INACTIVE"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]
  mfa_configuration        = "OPTIONAL"
  username_configuration { case_sensitive = false }
  software_token_mfa_configuration { enabled = true }
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }
  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }
  verification_message_template { default_email_option = "CONFIRM_WITH_CODE" }
  user_attribute_update_settings { attributes_require_verification_before_update = ["email"] }
  email_configuration {
    email_sending_account = var.email_identity_arn == "" ? "COGNITO_DEFAULT" : "DEVELOPER"
    source_arn            = var.email_identity_arn == "" ? null : var.email_identity_arn
    from_email_address    = var.email_identity_arn == "" ? null : var.email_from
  }
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true
    string_attribute_constraints {
      min_length = 1
      max_length = 2048
    }
  }
  schema {
    name                = "name"
    attribute_data_type = "String"
    required            = false
    mutable             = true
    string_attribute_constraints {
      min_length = 0
      max_length = 2048
    }
  }
}
resource "aws_cognito_resource_server" "api" {
  user_pool_id = aws_cognito_user_pool.main.id
  identifier   = "medic-api"
  name         = "MedEd API"
  scope {
    scope_name        = "access"
    scope_description = "Access account and verified-role APIs"
  }
}
resource "aws_cognito_user_pool_client" "web" {
  name                          = "django-bff"
  user_pool_id                  = aws_cognito_user_pool.main.id
  generate_secret               = true
  explicit_auth_flows           = ["ALLOW_USER_PASSWORD_AUTH"]
  prevent_user_existence_errors = "ENABLED"
  enable_token_revocation       = true
  access_token_validity         = 5
  id_token_validity             = 5
  refresh_token_validity        = 7
  read_attributes               = ["email", "email_verified", "name"]
  write_attributes              = ["email", "name"]
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
  refresh_token_rotation {
    feature                    = "ENABLED"
    retry_grace_period_seconds = 10
  }
}
resource "aws_cognito_user_pool_client" "mobile" {
  name                                 = "native-mobile"
  user_pool_id                         = aws_cognito_user_pool.main.id
  generate_secret                      = false
  explicit_auth_flows                  = ["ALLOW_USER_SRP_AUTH"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile", "aws.cognito.signin.user.admin", "${aws_cognito_resource_server.api.identifier}/access"]
  supported_identity_providers         = ["COGNITO"]
  callback_urls                        = var.mobile_callback_urls
  logout_urls                          = var.mobile_logout_urls
  prevent_user_existence_errors        = "ENABLED"
  enable_token_revocation              = true
  access_token_validity                = 5
  id_token_validity                    = 5
  refresh_token_validity               = 7
  read_attributes                      = ["email", "email_verified", "name"]
  write_attributes                     = ["email", "name"]
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
  refresh_token_rotation {
    feature                    = "ENABLED"
    retry_grace_period_seconds = 10
  }
}
resource "aws_cognito_user_pool_domain" "main" {
  domain                = local.oidc_domain
  user_pool_id          = aws_cognito_user_pool.main.id
  certificate_arn       = aws_acm_certificate_validation.cognito.certificate_arn
  managed_login_version = 2
  depends_on            = [time_sleep.parent_dns]
}
resource "aws_cognito_managed_login_branding" "mobile" {
  user_pool_id                = aws_cognito_user_pool.main.id
  client_id                   = aws_cognito_user_pool_client.mobile.id
  use_cognito_provided_values = true
  depends_on                  = [aws_cognito_user_pool_domain.main]
}
resource "aws_route53_record" "cognito" {
  zone_id = data.aws_route53_zone.existing.zone_id
  name    = local.oidc_domain
  type    = "A"
  alias {
    name                   = aws_cognito_user_pool_domain.main.cloudfront_distribution
    zone_id                = aws_cognito_user_pool_domain.main.cloudfront_distribution_zone_id
    evaluate_target_health = false
  }
}
