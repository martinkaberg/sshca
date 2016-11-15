#!/usr/bin/env bash

set -eu
KMS_KEY_ARN=$1
function wait_for_stack()
{
	set -eu
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
		if [[ ${_status} =~ .*FAILED.* ]]
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

function stack_exists()
{
	set -eu
	declare _stack_name=$1
	declare _filter=(
		CREATE_IN_PROGRESS
		CREATE_FAILED
		CREATE_COMPLETE
		ROLLBACK_IN_PROGRESS
		ROLLBACK_FAILED
		ROLLBACK_COMPLETE
		DELETE_IN_PROGRESS
		DELETE_FAILED
		UPDATE_IN_PROGRESS
		UPDATE_COMPLETE_CLEANUP_IN_PROGRESS
		UPDATE_COMPLETE
		UPDATE_ROLLBACK_IN_PROGRESS
		UPDATE_ROLLBACK_FAILED
		UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS
		UPDATE_ROLLBACK_COMPLETE
		REVIEW_IN_PROGRESS
	)


	aws cloudformation list-stacks --stack-status-filter ${_filter[@]} | jq -r '.StackSummaries[].StackName' | grep ${_stack_name}
	return $?


}


function get_output_value()
{
	set -eu
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

stack_exists access || aws cloudformation create-stack --stack-name access --template-body file://access.template --parameters ParameterKey=KmsArn,ParameterValue=${KMS_KEY_ARN},UsePreviousValue=False --capabilities CAPABILITY_IAM

wait_for_stack access
LAMBDA_BUCKET=$(get_output_value access LambdaBucket)
CFN_BUCKET=$(get_output_value access CfnBucket)
stack_exists lambda || {
	set -eu
	cd ../lambda
	make all
	aws s3 cp build/publish/bless_lambda.zip s3://${LAMBDA_BUCKET}
	make clean
}
cd ../cloudformation
python lambda.py | aws s3 cp - s3://${CFN_BUCKET}/lambda.template
stack_exists lambda || aws cloudformation create-stack --stack-name lambda --template-url "https://s3.amazonaws.com/${CFN_BUCKET}/lambda.template" --parameters ParameterKey=AccessStack,ParameterValue=access,UsePreviousValue=False --capabilities CAPABILITY_IAM
wait_for_stack lambda
python ssh-ca-api.py | aws s3 cp - s3://${CFN_BUCKET}/ssh-ca-api.template
stack_exists ssh-ca-api || aws cloudformation create-stack --stack-name ssh-ca-api --template-url "https://s3.amazonaws.com/${CFN_BUCKET}/ssh-ca-api.template" --parameters ParameterKey=AccessStack,ParameterValue=access,UsePreviousValue=False ParameterKey=LambdaStack,ParameterValue=lambda,UsePreviousValue=False --capabilities CAPABILITY_IAM
wait_for_stack ssh-ca-api
API_ID=$(get_output_value ssh-ca-api Api)
cd ..
API_HOST="${API_ID}.execute-api.eu-west-1.amazonaws.com"
echo "Testing pub CA: https://${API_HOST}/dev/cert"
curl -vvv "https://${API_HOST}/dev/cert"

echo "with an iam user run:"
echo "python scripts/get-cert.py --host ${API_HOST} --stage dev --public-key-file ~/.ssh/id_rsa.pub"
