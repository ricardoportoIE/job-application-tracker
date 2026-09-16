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
  secret_string_wo_version = var.secrets_version
}

resource "aws_secretsmanager_secret" "application_db" {
  name        = "${var.project_name}/${var.environment}/application-database"
  description = "Least-privileged PostgreSQL credentials used by the backend API."

  recovery_window_in_days = 0

  tags = {
    Name = "${var.project_name}-${var.environment}-application-database"
  }
}

resource "aws_secretsmanager_secret_version" "application_db" {
  secret_id = aws_secretsmanager_secret.application_db.id

  secret_string_wo = jsonencode({
    username = var.db_app_username
    password = var.db_app_password
  })
  secret_string_wo_version = var.secrets_version
}

resource "aws_secretsmanager_secret" "metrics" {
  name        = "${var.project_name}/${var.environment}/metrics-bearer-token"
  description = "Bearer token required to scrape backend Prometheus metrics."

  recovery_window_in_days = 0

  tags = {
    Name = "${var.project_name}-${var.environment}-metrics-bearer-token"
  }
}

resource "aws_secretsmanager_secret_version" "metrics" {
  secret_id = aws_secretsmanager_secret.metrics.id

  secret_string_wo         = var.metrics_bearer_token
  secret_string_wo_version = var.secrets_version
}
