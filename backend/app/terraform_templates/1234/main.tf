module "ec2" {
  source        = "../../backend/modules/ec2"
  ami           = "ami-0c02fb55956c7d316"
  instance_type = "t3.micro"
  instance_name = "test-instance"
  device_id     = "1234"
}
