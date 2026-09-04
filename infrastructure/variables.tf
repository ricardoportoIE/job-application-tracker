variable "aws_region" {
  description = "AWS region where resources will be created."
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Name used to identify resources created for this project."
  type        = string
  default     = "job-application-tracker"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"
}
