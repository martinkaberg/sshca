# sshca

## PoC Serverless SSH CA using a rest api and AWS IAM authentication.


# Installation


* create a kms key in eu-west-1 with the alias bless
* create an instance profile with admin privileges
* start up an aws linux ec2 instance with that profile
* ssh into it
* git clone https://github.com/martinkaberg/sshca.git
* cd sshca
* bash create-on-aws-linux.sh KMS_KEY_ARN



## on server

add too sshd config
<code>
TrustedUserCAKeys /etc/ssh/ca.pub
LogLevel VERBOSE
</code>
run this as root
<code>
bash scripts/get-ca.sh dev > /etc/ssh/ca.pub
chmod 0600 /etc/ssh/ca.pub
service sshd restart
</code>
## on client
Get a new cert
<code>
python scripts/get-cert.py --host $API_ID.execute-api.eu-west-1.amazonaws.com --public-key-file ~/.ssh/id_rsa.pub --stage dev
</code>

You could also create an alias
<code>
alias ssh='python scripts/get-cert.py --host $API_ID.execute-api.eu-west-1.amazonaws.com --stage dev --public-key-file ~/.ssh/id_rsa.pub; ssh'
</code>

To view the cert
<code>
ssh-keygen -L -f ~/.ssh/id_rsa-cert.pub
</code>

## Modifications to bless

### lambda_handler.py

* Removed all the metadata on the key id from original bless.
* I have instead added the iam user arn.
* Principal in cert is the iam user  + ubuntu and ec2-user
* Critical ip is removed

### configure.py

* Generate a 4096 bit key pair for the CA,  encrypting the private key with a 128 char long randomly pass phrase
* The pass phrase is encrypted with the KMS key and stored in the config file
* Certs are issued for 1 hour before and after they are issued

## Api gateway resource

* A greedy resource on root you can call whatever you want with two methods pointing to the same lambda
* GET does not require any auth. It returns the public key. This should be deployed on servers maybe on cron?
* POST requires IAM auth. It posts the public key you want a cert signed for to the CA valid for 1 hour.
	* The principal matches the iam user used for the request + ubuntu and ec2-user
	* A managed policy is that enforces MFA for invoking the method
* a stage called dev is deployed by default


## Cloudformation

### access.py

* Takes KmsArn as parameter
* Creates two buckets , one fore cfn and one for lambda packages
* Creates two roles,  one for Bless and one for the api gw
* Buckets and roles are exported

### lambda.py

* Takes AccessStack as parameter
* Creates a lambda function called blessapi using roles and code source from Imports in access
* Exports the lambda arn

### ssh-ca-api.py

* takes AccessStack and LambdaStack as parameters
* creates ssh-ca-cfn rest api from swagger/dev.json
* grants GET and POST access to lambda
* creates and InvokePolicy, that should be attached to iam users to enforce MFA
* creates a deployment stage called dev


## Scripts

### get-ca.sh
takes 1 positional param, being the stage. Gets outputs from ssh-ca-api stack to get the correct host name. It will then
do a simple get against the api to get the public key. This one should be installed on the servers

### get-cert.py
Will do a sign POST request against the api using MFA with the public key you want to get a cert signed for.
The cert will be created next to your key , ie id_rsa-cert.pub
<code>
Usage: get-cert.py [OPTIONS]

Options:
  --token-code TEXT       The 6 digit number from your MFA device
  --host TEXT             Hostname of the api gateway
  --stage TEXT            Deployment stage
  --public-key-file PATH  ssh public key file
  --help                  Show this message and exit.
<code>
If token-code is not passed it will be prompted for

Once you have the cert just do ssh user@host and ssh agent should pick up the cert.

### get-cert-no-mfa.py
Same as get-cert.py but without the mfa.  If you have added the InvokePolicy to your iam user this command will fail


## TODO
* This is just a PoC. It needs to be further tested.
* How to do with principals?
* Critical to ip ?
* How do to further improve security?
* Maintance ?
* Is one CA enough?
* Logging , both on servers as well lambda and api gw?
* Multiple regions




