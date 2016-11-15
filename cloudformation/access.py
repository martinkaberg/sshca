from troposphere import (
    Template, GetAZs, Select, Ref, Parameter, Base64, Export,
    Join, GetAtt, Output, Not, Equals, If, ec2, iam, awslambda, ImportValue, Sub, s3
)
from awacs.aws import (Allow, Policy, Principal, Statement)
from awacs.sts import (AssumeRole)

t = Template()

t.add_description("Access stack")
t.add_version("2010-09-09")
kms_arn = t.add_parameter(Parameter(
    "KmsArn",
    Type="String",
    Description="arn of KMS key",
    Default="arn:aws:kms:eu-west-1:486089510432:key/3704248a-2168-4d0c-937a-344e0ecdcbb2"
))
lambda_bucket = t.add_resource(s3.Bucket(
    "LambdaBucket"
))
cfn_bucket = t.add_resource(s3.Bucket(
    "CfnBucket"
))

t.add_output(Output(
    cfn_bucket.title,
    Value=Ref(cfn_bucket),
    Export=Export(
        Sub("${AWS::StackName}-" + cfn_bucket.title)
    )
))
t.add_output(Output(
    lambda_bucket.title,
    Value=Ref(lambda_bucket),
    Export=Export(
        Sub("${AWS::StackName}-" + lambda_bucket.title)
    )
))
bless_role = t.add_resource(iam.Role(
    "BlessRole",
    AssumeRolePolicyDocument=Policy(
        Version="2012-10-17",
        Statement=[
            Statement(
                Effect=Allow,
                Action=[AssumeRole],
                Principal=Principal("Service", ["lambda.amazonaws.com"])
            )
        ]
    ),
    Policies=[
        iam.Policy(
            PolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "KmsDecrypt",
                        "Effect": "Allow",
                        "Action": [
                            "kms:decrypt"
                        ],
                        "Resource": [
                            Ref(kms_arn)
                        ]
                    }
                ]
            },
            PolicyName="KmsDecrypt"
        )
    ],
    ManagedPolicyArns=[
        "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
    ]
))
t.add_output(Output(
    bless_role.title,
    Value=Ref(bless_role),
    Export=Export(
        Sub("${AWS::StackName}-" + bless_role.title)
    )
))
ssh_ca_api_role = t.add_resource(iam.Role(
    "SshCaApiRole",
    AssumeRolePolicyDocument={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "apigateway.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    },
    Path="/",
    ManagedPolicyArns=["arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"]
))

t.add_output(Output(
    ssh_ca_api_role.title,
    Value=Ref(ssh_ca_api_role),
    Export=Export(
        Sub("${AWS::StackName}-" + ssh_ca_api_role.title)
    )
))