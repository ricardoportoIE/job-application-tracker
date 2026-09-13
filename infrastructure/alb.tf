resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    aws_security_group.alb.id,
  ]

  subnets = [
    aws_subnet.public_a.id,
    aws_subnet.public_b.id,
  ]

  enable_deletion_protection = false

  tags = {
    Name = "${var.project_name}-${var.environment}-alb"
  }
}
resource "aws_lb_target_group" "backend" {
  name        = "jobtracker-${var.environment}-backend-tg"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 30
    timeout             = 5

    path     = "/live"
    protocol = "HTTP"
    matcher  = "200"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-tg"
  }

}
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}
