resource "aws_instance" "foo" {
  ami           = "ami-005e54dee72cc1d00" # us-west-123
  instance_type = "m7i-flex.large"

  network_interface {
    network_interface_id = aws_network_interface.foo.id
    device_index         = 0
  }

  credit_specification {
    cpu_credits = "unlimited"
  }
}
