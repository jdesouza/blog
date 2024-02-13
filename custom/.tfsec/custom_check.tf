resource "aws_instance" "foo" {
  ami           = "ami-005e54dee72cc1d01" # us-west-1
  instance_type = "m7i-flex.large"

  network_interface {
    network_interface_id = aws_network_interface.foo.id
    device_index         = 1
  }

  credit_specification {
    cpu_credits = "unlimited"
  }
}
