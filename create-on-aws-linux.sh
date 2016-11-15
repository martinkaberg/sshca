#!/usr/bin/env bash
export AWS_DEFAULT_REGION=eu-west-1
aws s3 mb s3:// --region ${AWS_DEFAULT_REGION}
cd lambda



make all
