from troposphere import (
    Template, GetAZs, Select, Ref, Parameter, Base64,
    Join, GetAtt, Output, Not, Equals, If, ec2, iam, awslambda, ImportValue, Sub, apigateway, Export
)
import json, os
from swagger.dev import schema
from awacs.aws import Policy, Allow, Action, Statement, Principal

t = Template()

t.add_description("ssh ca API")
t.add_version("2010-09-09")
access_stack = t.add_parameter(Parameter(
    "AccessStack",
    Type="String",
    Description="Access stack name",
    Default="access"
))
lambda_stack = t.add_parameter(Parameter(
    "LambdaStack",
    Type="String",
    Description="Access stack name",
    Default="lambda"
))
dir = os.path.dirname(__file__)
#with open(os.path.join(dir, "../swagger/dev.json")) as json_data:
#    swagger = json.load(json_data)
#swagger["info"]["title"] = "ssh-ca"
api = t.add_resource(apigateway.RestApi(
    "Api",
    Name="ssh-ca-cfn",
    Body=schema
))

LAMBDA_ARN = ImportValue(
    Sub("${LambdaStack}-Bless")
)
LAMBDA_URI = Join("/", [
    "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/",
    LAMBDA_ARN,
    "invocations"
])

account = t.add_resource(apigateway.Account(
    "Account",
    DependsOn=api.title,
    CloudWatchRoleArn=ImportValue(
        Sub("${AccessStack}-SshCaApiRole")
    )
))

invoke_perm_get = t.add_resource(awslambda.Permission(
    "InvokePermGet",
    Action="lambda:InvokeFunction",
    FunctionName=LAMBDA_ARN,
    Principal="apigateway.amazonaws.com",
    SourceArn=Join(":", [
        "arn:aws:execute-api",
        Ref("AWS::Region"),
        Ref("AWS::AccountId"),
        Join("", [
            Ref(api),
            "/*/GET/*"
        ])])
))
invoke_perm_post = t.add_resource(awslambda.Permission(
    "InvokePermPost",
    Action="lambda:InvokeFunction",
    FunctionName=LAMBDA_ARN,
    Principal="apigateway.amazonaws.com",
    SourceArn=Join(":", [
        "arn:aws:execute-api",
        Ref("AWS::Region"),
        Ref("AWS::AccountId"),
        Join("", [
            Ref(api),
            "/*/POST/*"
        ])])
))

t.add_output(Output(
    "RootResourceId",
    Value=GetAtt(api, "RootResourceId")
))

deployment = t.add_resource(apigateway.Deployment(
    "Deployment",
    RestApiId=Ref(api),
    StageDescription=apigateway.StageDescription(
        CacheClusterEnabled=False,
        StageName="dev"
    ),
    StageName="dev"

))

invoke_policy = iam.ManagedPolicy(
    "InvokePolicy",
    PolicyDocument={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "CreateCert",
                "Effect": "Allow",
                "Action": [
                    "execute-api:Invoke"
                ],
                "Resource": [
                    Join(":", [
                        "arn:aws:execute-api",
                        Ref("AWS::Region"),
                        Ref("AWS::AccountId"),
                        Join("", [
                            Ref(api),
                            "/*/POST/*"
                        ])
                    ])
                ],
                "Condition": {
                    "Bool": {
                        "aws:MultiFactorAuthPresent": "true"
                    }
                }
            },
            {
                "Effect": "Allow",
                "Sid": "AllowIndividualUserToListTheirOwnMFA",
                "Action": [
                    "iam:ListVirtualMFADevices",
                    "iam:ListMFADevices"
                ],
                "Resource": [
                    "*"
                ]
            },
            {
                "Sid": "AllowAllUsersToListAccounts",
                "Effect": "Allow",
                "Action": [
                    "iam:ListAccountAliases",
                    "iam:ListUsers",
                    "iam:GetAccountSummary"
                ],
                "Resource": "*"
            },
        ]
    }
)
t.add_resource(invoke_policy)
t.add_output(Output(
    "Deployment",
    Value=Ref(deployment)
))

t.add_output(Output(
    "Api",
    Value=Ref(api)
))
t.add_output(Output(
    invoke_policy.title,
    Value=Ref(invoke_policy),
    Export=Export(
        Sub("${AWS::StackName}-" + invoke_policy.title)
    )
))

t.add_output(Output(
    "Host",
    Value=Join(".", [
        Ref(api),
        "execute-api",
        Ref("AWS::Region"),
        "amazonaws.com"
    ])
))
print t.to_json()
