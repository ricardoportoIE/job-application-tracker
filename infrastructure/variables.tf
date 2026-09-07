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
