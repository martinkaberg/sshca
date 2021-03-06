from troposphere import Join, Ref, ImportValue, Sub

schema = {
    "swagger": "2.0",
    "info": {
        "version": "2016-11-15T04:23:30Z",
        "title": "ssh-ca-cfn"
    },
    "host": "570qkeqvr9.execute-api.eu-west-1.amazonaws.com",
    "basePath": "/dev",
    "schemes": [
        "https"
    ],
    "paths": {
        "/{proxy+}": {
            "get": {
                "produces": [
                    "application/json"
                ],
                "parameters": [
                    {
                        "name": "proxy",
                        "in": "path",
                        "required": True,
                        "type": "string"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "200 response",
                        "schema": {
                            "$ref": "#/definitions/Empty"
                        }
                    }
                },
                "x-amazon-apigateway-integration": {
                    # "uri": "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-1:486089510432:function:blessapi/invocations",
                    "uri": Join(":", [
                        "arn:aws:apigateway",
                        Ref("AWS::Region"),
                        Join("/", [
                            "lambda:path/2015-03-31/functions",
                            ImportValue(
                                Sub("${LambdaStack}-Bless")
                            ),
                            "invocations"
                        ])
                    ]),
                    "responses": {
                        "default": {
                            "statusCode": "200"
                        }
                    },
                    "passthroughBehavior": "when_no_match",
                    "httpMethod": "POST",
                    "cacheNamespace": "fbs6bg",
                    "cacheKeyParameters": [
                        "method.request.path.proxy"
                    ],
                    "type": "aws_proxy"
                }
            },
            "post": {
                "produces": [
                    "application/json"
                ],
                "parameters": [
                    {
                        "name": "proxy",
                        "in": "path",
                        "required": True,
                        "type": "string"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "200 response",
                        "schema": {
                            "$ref": "#/definitions/Empty"
                        }
                    }
                },
                "security": [
                    {
                        "sigv4": []
                    }
                ],
                "x-amazon-apigateway-integration": {
                    "uri": Join(":", [
                        "arn:aws:apigateway",
                        Ref("AWS::Region"),
                        Join("/", [
                            "lambda:path/2015-03-31/functions",
                            ImportValue(
                                Sub("${LambdaStack}-Bless")
                            ),
                            "invocations"
                        ])
                    ]),
                    "responses": {
                        "default": {
                            "statusCode": "200"
                        }
                    },
                    "passthroughBehavior": "when_no_match",
                    "httpMethod": "POST",
                    "cacheNamespace": "fbs6bg",
                    "cacheKeyParameters": [
                        "method.request.path.proxy"
                    ],
                    "type": "aws_proxy"
                }
            }
        }
    },
    "securityDefinitions": {
        "sigv4": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "x-amazon-apigateway-authtype": "awsSigv4"
        }
    },
    "definitions": {
        "Empty": {
            "type": "object",
            "title": "Empty Schema"
        }
    }
}
