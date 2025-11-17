terraform {
  required_version = ">= 1.1.0"

  backend "s3" {
    bucket         = "infra-state-blitz-2025"
    key            = "state/123.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = "us-east-1"
}
