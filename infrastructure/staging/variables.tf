variable "hosted_zone_id" {
  type        = string
  description = "Existing public Route 53 zone for mededbotswana.co.bw."
}
variable "vpc_cidr" {
  type    = string
  default = "10.43.0.0/16"
}
variable "services_enabled" {
  type        = bool
  default     = false
  description = "Start web and worker after image publication and migrations."
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
variable "backup_image_digest" {
  type     = string
  default  = null
  nullable = true
  validation {
    condition     = var.backup_image_digest == null ? true : can(regex("^sha256:[a-f0-9]{64}$", var.backup_image_digest))
    error_message = "Use an immutable ECR sha256 backup image digest."
  }
}
variable "mobile_callback_urls" {
  type = list(string)
  validation {
    condition     = length(var.mobile_callback_urls) > 0 && alltrue([for url in var.mobile_callback_urls : can(regex("^[a-z][a-z0-9+.-]*://", url)) && !strcontains(url, "*")])
    error_message = "Supply explicit native callback URIs without wildcards."
  }
}
variable "mobile_logout_urls" {
  type = list(string)
  validation {
    condition     = length(var.mobile_logout_urls) > 0 && alltrue([for url in var.mobile_logout_urls : can(regex("^[a-z][a-z0-9+.-]*://", url)) && !strcontains(url, "*")])
    error_message = "Supply explicit native logout URIs without wildcards."
  }
}
variable "email_identity_arn" {
  type        = string
  default     = ""
  description = "Optional verified SES identity for application and Cognito mail."
}
variable "email_from" {
  type    = string
  default = "noreply@mededbotswana.co.bw"
}
variable "deletion_protection" {
  type    = bool
  default = true
}
