output "aws_region" {
  description = "AWS region configured for this Terraform project."
  value       = var.aws_region
}

output "project_name" {
  description = "Project name used for resource identification."
  value       = var.project_name
}

output "environment" {
  description = "Deployment environment."
  value       = var.environment
}
