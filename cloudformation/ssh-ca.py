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
    Default="access-stack"
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

LAMBDA_ARN = "arn:aws:lambda:eu-west-1:486089510432:function:testrest"
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

        Sub("${AccessStack}-Vpc")

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

any = t.add_resource(apigateway.Method(
    "Any",
    ApiKeyRequired=False,
    AuthorizationType="AWS_IAM",
    HttpMethod="ANY",
    MethodResponses=[],
    Integration=apigateway.Integration(
        Type="AWS_PROXY",
        IntegrationHttpMethod="POST",
        Uri="arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/{}/invocations".format(LAMBDA_ARN),
        PassthroughBehavior="Never",
        IntegrationResponses= []



    ),
    ResourceId=Ref(proxy_resource),
    RestApiId=Ref(api)
))


get_cert = t.add_resource(apigateway.Method(
    "GetCert",
    ApiKeyRequired=False,
    AuthorizationType="AWS_IAM",
    HttpMethod="GET",
    Integration=apigateway.Integration(
        IntegrationHttpMethod="POST",
        PassthroughBehavior="WHEN_NO_MATCH",
        Type="AWS",
        Uri="arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/{}/invocations".format(LAMBDA_ARN),
        IntegrationResponses=[
            apigateway.IntegrationResponse(
                StatusCode="200",

            )],

    ),
    MethodResponses=[apigateway.MethodResponse(
        StatusCode="200"
    )],

    ResourceId=Ref(cert_resource),
    RestApiId=Ref(api)
))

t.add_output(Output(
    "RootResourceId",
    Value=GetAtt(api, "RootResourceId")
))

deployment = t.add_resource(apigateway.Deployment(
    "Deployment",
    DependsOn=[get_cert.title],
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
