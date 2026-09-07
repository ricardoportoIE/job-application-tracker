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

# Networking

output "vpc_id" {
  description = "ID of the main VPC."
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets."
  value = [
    aws_subnet.public_a.id,
    aws_subnet.public_b.id,
  ]
}

output "private_subnet_ids" {
  description = "IDs of the private subnets."
  value = [
    aws_subnet.private_a.id,
    aws_subnet.private_b.id,
  ]
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway."
  value       = aws_internet_gateway.main.id
}

output "nat_gateway_id" {
  description = "ID of the NAT Gateway."
  value       = aws_nat_gateway.main.id
}

output "public_route_table_id" {
  description = "ID of the public route table."
  value       = aws_route_table.public.id
}

output "private_route_table_id" {
  description = "ID of the private route table."
  value       = aws_route_table.private.id
}

# Security Groups

output "alb_security_group_id" {
  description = "ID of the Application Load Balancer security group."
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ID of the ECS Fargate security group."
  value       = aws_security_group.ecs.id
}

output "rds_security_group_id" {
  description = "ID of the RDS PostgreSQL security group."
  value       = aws_security_group.rds.id
}

# Amazon ECR

output "ecr_repository_name" {
  description = "Name of the backend ECR repository."
  value       = aws_ecr_repository.backend.name
}

output "ecr_repository_arn" {
  description = "ARN of the backend ECR repository."
  value       = aws_ecr_repository.backend.arn
}

output "ecr_repository_url" {
  description = "URL of the backend ECR repository."
  value       = aws_ecr_repository.backend.repository_url
}
