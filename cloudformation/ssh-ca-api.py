from troposphere import (
    Template, GetAZs, Select, Ref, Parameter, Base64,
    Join, GetAtt, Output, Not, Equals, If, ec2, iam, awslambda, ImportValue, Sub, apigateway
)
import json, os

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
dir = os.path.dirname(__file__)
with open(os.path.join(dir, "../swagger/dev.json")) as json_data:
    swagger = json.load(json_data)
swagger["info"]["title"] = "ssh-ca"
api = t.add_resource(apigateway.RestApi(
    "Api",
    Name="ssh-ca-cfn"
    # Body=swagger
))

bless = t.add_resource(awslambda.Function(
    "Bless",
    Code=awslambda.Code(
        S3Bucket=ImportValue(
            Sub("${AccessStack}-LambdaBucket")
        ),
        S3Key="bless_lambda.zip"
    ),
    FunctionName="bless-api",
    Handler="lambda_handler.lambda_handler",
    MemorySize="128",
    Role=ImportValue(
        Sub("${AccessStack}-BlessRole")
    ),
    Runtime="python2.7",
    Timeout=300

))
LAMBDA_ARN = GetAtt(bless, "Arn")
LAMBDA_URI = Join("", [
    "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/",
    LAMBDA_ARN,
    "invocations"
])
invoke_perm = t.add_resource(awslambda.Permission(
    "InvokePerm",
    Action="lambda:InvokeFunction",
    FunctionName=LAMBDA_ARN,
    Principal="apigateway.amazonaws.com",
))

account = t.add_resource(apigateway.Account(
    "Account",
    DependsOn=api.title,
    CloudWatchRoleArn=ImportValue(
        Sub("${AccessStack}-SshCaApiRole")
    )
))

cert_resource = t.add_resource(apigateway.Resource(
    "CertResource",
    ParentId=GetAtt(api, "RootResourceId"),
    PathPart="cert",
    RestApiId=Ref(api)

))

proxy_resource = t.add_resource(apigateway.Resource(
    "ProxyResource",
    ParentId=GetAtt(api, "RootResourceId"),
    PathPart="{proxy+}",
    RestApiId=Ref(api)

))

post = t.add_resource(apigateway.Method(
    "Post",
    ApiKeyRequired=False,
    AuthorizationType="AWS_IAM",
    HttpMethod="POST",
    Integration=apigateway.Integration(
        Type="AWS_PROXY",
        IntegrationHttpMethod="POST",
        Uri=LAMBDA_URI,
        #PassthroughBehavior="Never",


    ),
    ResourceId=Ref(proxy_resource),
    RestApiId=Ref(api)
))
get = t.add_resource(apigateway.Method(
    "Get",
    ApiKeyRequired=False,
    AuthorizationType="AWS_IAM",
    HttpMethod="GET",
    Integration=apigateway.Integration(
        Type="AWS_PROXY",
        IntegrationHttpMethod="POST",
        Uri=LAMBDA_URI,
        #PassthroughBehavior="Never",


    ),
    ResourceId=Ref(proxy_resource),
    RestApiId=Ref(api)
))

t.add_output(Output(
    "RootResourceId",
    Value=GetAtt(api, "RootResourceId")
))

deployment = t.add_resource(apigateway.Deployment(
    "Deployment",
    DependsOn=[get.title, post.title],
    RestApiId=Ref(api),
    StageDescription=apigateway.StageDescription(
        CacheClusterEnabled=False,
        StageName="dev"
    ),
    StageName="dev"

))

t.add_output(Output(
    "Deployment",
    Value=Ref(deployment)
))

t.add_output(Output(
    "Api",
    Value=Ref(api)
))

print t.to_json()
