from troposphere import (
    Template, GetAZs, Select, Ref, Parameter, Base64,
    Join, GetAtt, Output, Not, Equals, If, ec2, iam, awslambda, ImportValue, Sub, apigateway, Export
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

bless = t.add_resource(awslambda.Function(
    "Bless",
    Code=awslambda.Code(
        S3Bucket=ImportValue(
            Sub("${AccessStack}-LambdaBucket")
        ),
        S3Key="bless_lambda.zip"
    ),
    FunctionName="blessapi",
    Handler="lambda_handler.lambda_handler",
    MemorySize="128",
    Role=ImportValue(
        Sub("${AccessStack}-BlessRole")
    ),
    Runtime="python2.7",
    Timeout=300

))

t.add_output(Output(
    bless.title,
    Value=GetAtt(bless,"Arn"),
    Export=Export(
        Sub("${AWS::StackName}-" + bless.title)
    )
))