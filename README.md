# sshca
Serverless SSH CA

* create a kms key in eu-west-1 with the alias bless
* create an instance profile with admin privileges
* start up an aws linux ec2 instance with that profile
* ssh into it
* git clone https://github.com/martinkaberg/sshca.git
* cd sshca
* bash create-on-aws-linux.sh KMS_KEY_ARN



** on server **

add too sshd config

TrustedUserCAKeys /etc/ssh/ca.pub
LogLevel VERBOSE


curl https://joxcu5vyr0.execute-api.eu-west-1.amazonaws.com/dev2/cert > /etc/ssh/ca.pub
chmod 0600 /etc/ssh/ca.pub
service sshd restart

** on client **

python scripts/get-cert.py --host $API_ID.execute-api.eu-west-1.amazonaws.com --public-key-file ~/.ssh/id_rsa.pub --stage dev


