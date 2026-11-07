resource "aws_s3_bucket" "assets" {
  for_each      = toset(["static", "media"])
  bucket        = "${local.name}-${each.key}-${data.aws_caller_identity.current.account_id}"
  force_destroy = false
}
resource "aws_s3_bucket_public_access_block" "assets" {
  for_each                = aws_s3_bucket.assets
  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_server_side_encryption_configuration" "assets" {
  for_each = aws_s3_bucket.assets
  bucket   = each.value.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}
resource "aws_s3_bucket_ownership_controls" "assets" {
  for_each = aws_s3_bucket.assets
  bucket   = each.value.id
  rule { object_ownership = "BucketOwnerEnforced" }
}
# Media is intentionally unversioned so final evidence deletion removes the object.
resource "aws_s3_bucket_versioning" "static" {
  bucket = aws_s3_bucket.assets["static"].id
  versioning_configuration { status = "Enabled" }
}
resource "aws_cloudfront_origin_access_control" "static" {
  name                              = "${local.name}-static"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}
data "aws_cloudfront_cache_policy" "static" { name = "Managed-CachingOptimized" }
resource "aws_cloudfront_distribution" "static" {
  enabled         = true
  is_ipv6_enabled = true
  comment         = "${local.name} public static assets; media is excluded"
  price_class     = "PriceClass_All"
  origin {
    domain_name              = aws_s3_bucket.assets["static"].bucket_regional_domain_name
    origin_id                = "static"
    origin_access_control_id = aws_cloudfront_origin_access_control.static.id
  }
  default_cache_behavior {
    target_origin_id           = "static"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD", "OPTIONS"]
    cached_methods             = ["GET", "HEAD", "OPTIONS"]
    compress                   = true
    cache_policy_id            = data.aws_cloudfront_cache_policy.static.id
    response_headers_policy_id = aws_cloudfront_response_headers_policy.static.id
  }
  restrictions {
    geo_restriction { restriction_type = "none" }
  }
  viewer_certificate { cloudfront_default_certificate = true }
}
resource "aws_cloudfront_response_headers_policy" "static" {
  name = "${local.name}-static"
  cors_config {
    access_control_allow_credentials = false
    access_control_allow_headers { items = ["*"] }
    access_control_allow_methods { items = ["GET", "HEAD", "OPTIONS"] }
    access_control_allow_origins { items = [for domain in local.domains : "https://${domain}"] }
    origin_override = true
  }
  security_headers_config {
    content_type_options { override = true }
  }
}
resource "aws_s3_bucket_policy" "assets" {
  for_each = aws_s3_bucket.assets
  bucket   = each.value.id
  policy = jsonencode({ Version = "2012-10-17", Statement = concat([
    { Effect = "Deny", Principal = "*", Action = "s3:*", Resource = [each.value.arn, "${each.value.arn}/*"], Condition = { Bool = { "aws:SecureTransport" = "false" } } }
    ], each.key == "static" ? [
    { Effect = "Allow", Principal = { Service = "cloudfront.amazonaws.com" }, Action = "s3:GetObject", Resource = "${each.value.arn}/static/*", Condition = { StringEquals = { "AWS:SourceArn" = aws_cloudfront_distribution.static.arn } } }
  ] : []) })
  depends_on = [aws_s3_bucket_public_access_block.assets]
}
