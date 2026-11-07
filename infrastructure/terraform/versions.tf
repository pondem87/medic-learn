terraform {
  required_version = ">= 1.10, < 2.0"
  backend "s3" {}
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 6.0" }
    random = { source = "hashicorp/random", version = "~> 3.7" }
    time   = { source = "hashicorp/time", version = "~> 0.13" }
  }
}
provider "aws" {
  region = var.region
  default_tags { tags = { Project = "meded-botswana", Environment = var.environment, ManagedBy = "Terraform" } }
}
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
  default_tags { tags = { Project = "meded-botswana", Environment = var.environment, ManagedBy = "Terraform" } }
}
data "aws_availability_zones" "available" { state = "available" }
data "aws_caller_identity" "current" {}
data "aws_route53_zone" "existing" {
  zone_id      = var.hosted_zone_id
  private_zone = false
  lifecycle {
    postcondition {
      condition     = trimsuffix(self.name, ".") == "mededbotswana.co.bw"
      error_message = "Select the existing public mededbotswana.co.bw hosted zone."
    }
  }
}
locals {
  name        = "meded-${var.environment}"
  azs         = slice(data.aws_availability_zones.available.names, 0, 3)
  domains     = ["api.mededbotswana.co.bw", "www.mededbotswana.co.bw"]
  oidc_domain = "oidc.api.mededbotswana.co.bw"
  nat_count   = var.high_availability ? 3 : 1
  image       = var.image_digest == null ? "${aws_ecr_repository.app.repository_url}:unpublished" : "${aws_ecr_repository.app.repository_url}@${var.image_digest}"
}
