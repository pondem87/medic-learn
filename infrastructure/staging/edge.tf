resource "aws_lb" "app" {
  name                       = local.name
  internal                   = false
  load_balancer_type         = "application"
  subnets                    = aws_subnet.public[*].id
  security_groups            = [aws_security_group.alb.id]
  drop_invalid_header_fields = true
  enable_deletion_protection = var.deletion_protection
}
resource "aws_acm_certificate" "app" {
  domain_name               = local.domains[0]
  subject_alternative_names = slice(local.domains, 1, length(local.domains))
  validation_method         = "DNS"
  lifecycle { create_before_destroy = true }
}
resource "aws_route53_record" "app_certificate" {
  for_each = toset(local.domains)
  zone_id  = data.aws_route53_zone.existing.zone_id
  name     = one([for item in aws_acm_certificate.app.domain_validation_options : item if item.domain_name == each.key]).resource_record_name
  type     = one([for item in aws_acm_certificate.app.domain_validation_options : item if item.domain_name == each.key]).resource_record_type
  records  = [one([for item in aws_acm_certificate.app.domain_validation_options : item if item.domain_name == each.key]).resource_record_value]
  ttl      = 60
}
resource "aws_acm_certificate_validation" "app" {
  certificate_arn         = aws_acm_certificate.app.arn
  validation_record_fqdns = [for item in aws_route53_record.app_certificate : item.fqdn]
}
resource "aws_lb_target_group" "web" {
  name                 = local.name
  port                 = 8000
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = aws_vpc.main.id
  deregistration_delay = 30
  health_check {
    path                = "/health/"
    matcher             = "200"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.app.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.app.certificate_arn
  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "Unknown host"
      status_code  = "404"
    }
  }
}
resource "aws_lb_listener_rule" "web" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
  condition {
    host_header { values = local.domains }
  }
}
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}
resource "aws_route53_record" "app" {
  for_each = toset(local.domains)
  zone_id  = data.aws_route53_zone.existing.zone_id
  name     = each.value
  type     = "A"
  alias {
    name                   = aws_lb.app.dns_name
    zone_id                = aws_lb.app.zone_id
    evaluate_target_health = true
  }
}
# Cognito checks its immediate parent's public A record during domain creation.
resource "time_sleep" "parent_dns" {
  depends_on      = [aws_route53_record.app]
  create_duration = "90s"
  triggers        = { parent = aws_route53_record.app["api.staging.mededbotswana.co.bw"].fqdn }
}
resource "aws_acm_certificate" "cognito" {
  provider          = aws.us_east_1
  domain_name       = local.oidc_domain
  validation_method = "DNS"
  lifecycle { create_before_destroy = true }
}
resource "aws_route53_record" "cognito_certificate" {
  zone_id = data.aws_route53_zone.existing.zone_id
  name    = one(aws_acm_certificate.cognito.domain_validation_options).resource_record_name
  type    = one(aws_acm_certificate.cognito.domain_validation_options).resource_record_type
  records = [one(aws_acm_certificate.cognito.domain_validation_options).resource_record_value]
  ttl     = 60
}
resource "aws_acm_certificate_validation" "cognito" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.cognito.arn
  validation_record_fqdns = [aws_route53_record.cognito_certificate.fqdn]
}
