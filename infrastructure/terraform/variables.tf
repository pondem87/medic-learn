variable "region" {
  type    = string
  default = "af-south-1"
  validation {
    condition     = var.region == "af-south-1"
    error_message = "This deployment is configured for Cape Town (af-south-1)."
  }
}
variable "environment" {
  type    = string
  default = "development"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,15}$", var.environment))
    error_message = "Use a short lowercase environment name."
  }
}
variable "hosted_zone_id" {
  type        = string
  description = "Existing public Route 53 hosted zone ID for mededbotswana.co.bw; never creates a zone."
}
variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}
variable "high_availability" {
  type        = bool
  default     = false
  description = "Enable three NATs, two web tasks, Multi-AZ RDS and three-node MQ. Worker remains singleton."
}
variable "services_enabled" {
  type        = bool
  default     = false
  description = "Enable only after pushing the image and successfully running the migration task."
}
variable "image_digest" {
  type     = string
  default  = null
  nullable = true
  validation {
    condition     = var.image_digest == null ? true : can(regex("^sha256:[a-f0-9]{64}$", var.image_digest))
    error_message = "Use an immutable ECR sha256 image digest."
  }
}
variable "mobile_callback_urls" {
  type        = list(string)
  description = "Exact native-mobile authorization-code callback URIs."
  validation {
    condition     = length(var.mobile_callback_urls) > 0 && alltrue([for url in var.mobile_callback_urls : can(regex("^[a-z][a-z0-9+.-]*://", url)) && !strcontains(url, "*")])
    error_message = "Supply explicit callback URIs, without wildcards."
  }
}
variable "mobile_logout_urls" {
  type        = list(string)
  description = "Exact native-mobile logout URIs."
  validation {
    condition     = length(var.mobile_logout_urls) > 0 && alltrue([for url in var.mobile_logout_urls : can(regex("^[a-z][a-z0-9+.-]*://", url)) && !strcontains(url, "*")])
    error_message = "Supply explicit logout URIs, without wildcards."
  }
}
variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}
variable "mq_instance_type" {
  type    = string
  default = "mq.m7g.medium"
}
variable "mq_engine_version" {
  type    = string
  default = "4.2"
}
variable "email_identity_arn" {
  type        = string
  default     = ""
  description = "Existing verified SES identity ARN. Blank keeps Cognito development email; application email requires SES setup."
}
variable "email_from" {
  type    = string
  default = "noreply@mededbotswana.co.bw"
}
variable "deletion_protection" {
  type    = bool
  default = true
}
