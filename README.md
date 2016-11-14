# sshca
Serverless SSH CA

apt-get install build-essential libssl-dev libffi-dev python-dev git
yum install gcc libffi-devel python-devel openssl-devel git

pip install -r requirments.txt

make sure you have a kms key that your iam user can use Encrypt with. The alias of the key must be bless

cd lambda


export AWS_DEFAULT_REGION=eu-west-1

make all





