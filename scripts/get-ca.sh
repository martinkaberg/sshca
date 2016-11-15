#!/usr/bin/env bash

function get_output_value()
{
	set -eu
	declare _stack_name
	declare _key
	_stack_name=$1
	_key=$2
	aws cloudformation describe-stacks --stack-name ${_stack_name} | jq -r '.Stacks[].Outputs[] | select(.OutputKey == "'${_key}'") | .OutputValue'

}

API_HOST=$(get_output_value ssh-ca-api Host)
curl "https://${API_HOST}/$1/cert"
