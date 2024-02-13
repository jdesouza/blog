resource "aws_instance" "foo" {
  ami           = "ami-005e54dee72cc1d21" # us-west-2
  instance_type = "m7i-flex.large"

  network_interface {
    network_interface_id = aws_network_interface.foo.id
    device_index         = 1
  }

  credit_specification {
    cpu_credits = "unlimited"
  }
}
