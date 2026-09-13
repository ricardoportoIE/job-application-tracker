resource "aws_secretsmanager_secret" "jwt" {
  name        = "${var.project_name}/${var.environment}/jwt-secret-key"
  description = "JWT signing secret used by the backend application."

  recovery_window_in_days = 0

  tags = {
    Name = "${var.project_name}-${var.environment}-jwt-secret-key"
  }
}

resource "aws_secretsmanager_secret_version" "jwt" {
  secret_id = aws_secretsmanager_secret.jwt.id

  secret_string_wo         = var.jwt_secret_value
  secret_string_wo_version = 1
}
