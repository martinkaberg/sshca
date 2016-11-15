#!/usr/bin/env bash
KMS_KEY_ARN=$1
function wait_for_stack()
{
  declare _stack_name=$1
  declare _status
  while sleep 2
  do
    _status=$(aws cloudformation describe-stacks --stack-name ${_stack_name} | jq -r '.Stacks[].StackStatus')
    if [[ ${_status} == "CREATE_COMPLETE" ]]
    then
      break
    fi
    if [[ ${_status} == "UPDATE_COMPLETE" ]]
    then
      break
    fi
    if [[ ${_status}  =~ .*FAILED.* ]]
    then
      return 1
    fi
    if [[ ${_status} =~ .*ROLLBACK.* ]]
    then
      return 1
    fi
    if [[ ${_status} =~ .*DELETE.* ]]
    then
      return 1
    fi
  done
}

function get_output_value()
{
  declare _stack_name
  declare _key
  _stack_name=$1
  _key=$2
  aws cloudformation describe-stacks --stack-name ${_stack_name} | jq -r '.Stacks[].Outputs[] | select(.OutputKey == "'${_key}'") | .OutputValue'

}
export AWS_DEFAULT_REGION=eu-west-1
sudo yum -y install gcc libffi-devel python-devel openssl-devel git jq
sudo pip install -r requirements.txt --upgrade
cd cloudformation
python access.py > access.template
aws cloudformation create-stack --stack-name access --template-body file://access.template --parameters  ParameterKey=KmsArn,ParameterValue=${KMS_KEY_ARN},UsePreviousValue=False --capabilities CAPABILITY_IAM

wait_for_stack access
LAMBDA_BUCKET=$(get_output_value access LambdaBucket)
CFN_BUCKET=$(get_output_value access CfnBucket)
cd ../lambda
make all
aws s3 cp build/publish/bless_lambda.zip s3://${LAMBDA_BUCKET}
make clean
cd ../cloudformation
python ssh-ca-api.py | aws s3 cp - s3://${CFN_BUCKET}
aws cloudformation create-stack --stack-name ssh-ca-api2 --template-url "https://s3.amazonaws.com/${CFN_BUCKET}/ssh-ca-api.py" --parameters  ParameterKey=AccessStack,ParameterValue=access,UsePreviousValue=False --capabilities CAPABILITY_IAM
wait_for_stack ssh-ca-api2