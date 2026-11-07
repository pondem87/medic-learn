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
  region = "af-south-1"
  default_tags { tags = { Project = "meded-botswana", Environment = "staging", ManagedBy = "Terraform" } }
}
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
  default_tags { tags = { Project = "meded-botswana", Environment = "staging", ManagedBy = "Terraform" } }
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
  name         = "meded-staging"
  azs          = slice(data.aws_availability_zones.available.names, 0, 2)
  domains      = ["api.staging.mededbotswana.co.bw", "www.staging.mededbotswana.co.bw"]
  oidc_domain  = "oidc.api.staging.mededbotswana.co.bw"
  image        = var.image_digest == null ? "${aws_ecr_repository.app.repository_url}:unpublished" : "${aws_ecr_repository.app.repository_url}@${var.image_digest}"
  backup_image = var.backup_image_digest == null ? "${aws_ecr_repository.backup.repository_url}:unpublished" : "${aws_ecr_repository.backup.repository_url}@${var.backup_image_digest}"
}
