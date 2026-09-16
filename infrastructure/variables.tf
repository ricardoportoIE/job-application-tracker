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

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_a_cidr" {
  description = "CIDR block for the public subnet in Availability Zone A."
  type        = string
  default     = "10.0.1.0/24"
}

variable "public_subnet_b_cidr" {
  description = "CIDR block for the public subnet in Availability Zone B."
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_subnet_a_cidr" {
  description = "CIDR block for the private subnet in Availability Zone A."
  type        = string
  default     = "10.0.11.0/24"
}

variable "private_subnet_b_cidr" {
  description = "CIDR block for the private subnet in Availability Zone B."
  type        = string
  default     = "10.0.12.0/24"
}

variable "availability_zone_a" {
  description = "Primary Availability Zone."
  type        = string
  default     = "eu-west-1a"
}

variable "availability_zone_b" {
  description = "Secondary Availability Zone."
  type        = string
  default     = "eu-west-1b"
}

variable "db_name" {
  description = "Name of the PostgreSQL database."
  type        = string
  default     = "jobtracker"
}

variable "db_username" {
  description = "Master username for the PostgreSQL database."
  type        = string
  default     = "jobtracker"
}

variable "db_app_username" {
  description = "Least-privileged PostgreSQL username used by the running API."
  type        = string
  default     = "jobtracker_app"
}

variable "db_app_password" {
  description = "Password stored in Secrets Manager for the application database role."
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "db_instance_class" {
  description = "RDS instance class used for the PostgreSQL database."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage for the PostgreSQL database in GiB."
  type        = number
  default     = 20
}

variable "backend_image_tag" {
  description = "Immutable image tag used by the backend ECS task definition."
  type        = string
  default     = "bootstrap"
}

variable "jwt_secret_value" {
  description = "JWT signing secret injected into AWS Secrets Manager."
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "metrics_bearer_token" {
  description = "Bearer token required to scrape the production metrics endpoint."
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "secrets_version" {
  description = "Increment to rotate write-only application secret versions."
  type        = number
  default     = 1
}

variable "api_domain_name" {
  description = "Public DNS name used by the HTTPS API endpoint."
  type        = string
}

variable "route53_zone_id" {
  description = "Route 53 hosted zone used to validate the certificate and publish the API record."
  type        = string
}

variable "frontend_origin" {
  description = "HTTPS origin allowed to call the production API from a browser."
  type        = string

  validation {
    condition     = startswith(var.frontend_origin, "https://")
    error_message = "frontend_origin must use HTTPS."
  }
}

variable "backend_desired_count" {
  description = "Desired number of backend ECS tasks."
  type        = number
  default     = 0
}
