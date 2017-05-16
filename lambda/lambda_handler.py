"""
.. module: bless.aws_lambda.bless_lambda
    :copyright: (c) 2016 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.
"""
import base64
import logging
import time
import json
import boto3
import os
from bless.config.bless_config import (
    BlessConfig,
    BLESS_OPTIONS_SECTION,
    CERTIFICATE_VALIDITY_BEFORE_SEC_OPTION,
    CERTIFICATE_VALIDITY_AFTER_SEC_OPTION,
    ENTROPY_MINIMUM_BITS_OPTION,
    RANDOM_SEED_BYTES_OPTION,
    BLESS_CA_SECTION,
    CA_PRIVATE_KEY_FILE_OPTION,
    LOGGING_LEVEL_OPTION
)
from bless.request.bless_request import BlessSchema, validate_ip, validate_user
from bless.ssh.certificate_authorities.ssh_certificate_authority_factory import \
    get_ssh_certificate_authority
from bless.ssh.certificates.ssh_certificate_builder import SSHCertificateType
from bless.ssh.certificates.ssh_certificate_builder_factory import get_ssh_certificate_builder

from marshmallow import Schema, fields, post_load, ValidationError
import ipaddress


class CustomSchema(Schema):
    iam_arn = fields.Str()
    public_key_to_sign = fields.Str()
    username = fields.Str(validate=validate_user)

    @post_load
    def make_bless_request(self, data):
        return CustomRequest(**data)


class CustomRequest:
    def __init__(self, username, public_key_to_sign, iam_arn):
        self.username = username
        self.public_key_to_sign = public_key_to_sign
        self.iam_arn = iam_arn

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


def respond(err, res=None):
    body = res
    content_type = "text/plain"
    if isinstance(res, dict):
        content_type = "application/json"
        body = json.dumps(res)

    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else body,
        'headers': {
            'Content-Type': content_type,
        },
    }


def dump_pub_ca(config, logger):
    ca_public_key_file = "{}.pub".format(config.get(BLESS_CA_SECTION, CA_PRIVATE_KEY_FILE_OPTION))
    with open(os.path.join(os.path.dirname(__file__), ca_public_key_file), 'r') as f:
        pub_file = f.read()

    return respond(None, pub_file)


def lambda_handler(event, context=None, ca_private_key_password=None,
                   entropy_check=True,
                   config_file=os.path.join(os.path.dirname(__file__), 'bless_deploy.cfg')):
    """
    This is the function that will be called when the lambda function starts.
    :param event: Dictionary of the json request.
    :param context: AWS LambdaContext Object
    http://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html
    :param ca_private_key_password: For local testing, if the password is provided, skip the KMS
    decrypt.
    :param entropy_check: For local testing, if set to false, it will skip checking entropy and
    won't try to fetch additional random from KMS
    :param config_file: The config file to load the SSH CA private key from, and additional settings
    :return: the SSH Certificate that can be written to id_rsa-cert.pub or similar file.
    """
    # AWS Region determines configs related to KMS
    region = os.environ['AWS_REGION']

    config = BlessConfig(region, config_file=config_file)
    logging_level = config.get(BLESS_OPTIONS_SECTION, LOGGING_LEVEL_OPTION)
    numeric_level = getattr(logging, logging_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(logging_level))

    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    if event["httpMethod"] == "GET":
        return dump_pub_ca(config, logger)
    payload = json.loads(event["body"])
    certificate_validity_before_seconds = config.getint(BLESS_OPTIONS_SECTION,
                                                        CERTIFICATE_VALIDITY_BEFORE_SEC_OPTION)
    certificate_validity_after_seconds = config.getint(BLESS_OPTIONS_SECTION,
                                                       CERTIFICATE_VALIDITY_AFTER_SEC_OPTION)
    entropy_minimum_bits = config.getint(BLESS_OPTIONS_SECTION, ENTROPY_MINIMUM_BITS_OPTION)
    random_seed_bytes = config.getint(BLESS_OPTIONS_SECTION, RANDOM_SEED_BYTES_OPTION)
    ca_private_key_file = config.get(BLESS_CA_SECTION, CA_PRIVATE_KEY_FILE_OPTION)
    password_ciphertext_b64 = config.getpassword()

    # read the private key .pem
    with open(os.path.join(os.path.dirname(__file__), ca_private_key_file), 'r') as f:
        ca_private_key = f.read()

    # decrypt ca private key password
    if ca_private_key_password is None:
        kms_client = boto3.client('kms', region_name=region)
        ca_password = kms_client.decrypt(
            CiphertextBlob=base64.b64decode(password_ciphertext_b64))
        ca_private_key_password = ca_password['Plaintext']

    # if running as a Lambda, we can check the entropy pool and seed it with KMS if desired
    if entropy_check:
        with open('/proc/sys/kernel/random/entropy_avail', 'r') as f:
            entropy = int(f.read())
            logger.debug(entropy)
            if entropy < entropy_minimum_bits:
                logger.info(
                    'System entropy was {}, which is lower than the entropy_'
                    'minimum {}.  Using KMS to seed /dev/urandom'.format(
                        entropy, entropy_minimum_bits))
                response = kms_client.generate_random(
                    NumberOfBytes=random_seed_bytes)
                random_seed = response['Plaintext']
                with open('/dev/urandom', 'w') as urandom:
                    urandom.write(random_seed)

    # Modify the payload
    params = {}
    params["iam_arn"] = event["requestContext"]["identity"]["userArn"]
    if event["requestContext"]["identity"]["userArn"] == "arn:aws:iam::{}:root".format( event["requestContext"]["identity"]["accountId"]) :
        params["username"] = "test"
    else:
        if "@" in params["iam_arn"]:
            params["username"] = params["iam_arn"].split("/")[1].split("@")[0]
        else:
            params["username"] = params["iam_arn"].split("/")[1]

    params["public_key_to_sign"] = payload["public_key_to_sign"]
    # Process cert request
    schema = CustomSchema(strict=True)
    request = schema.load(params).data

    # cert values determined only by lambda and its configs
    current_time = int(time.time())
    valid_before = current_time + certificate_validity_after_seconds
    valid_after = current_time - certificate_validity_before_seconds

    # Build the cert
    ca = get_ssh_certificate_authority(ca_private_key, ca_private_key_password)
    cert_builder = get_ssh_certificate_builder(ca, SSHCertificateType.USER,
                                               request.public_key_to_sign)
    cert_builder.add_valid_principal(request.username)
    cert_builder.add_valid_principal("ubuntu")
    cert_builder.add_valid_principal("ec2-user")
    cert_builder.set_valid_before(valid_before)
    cert_builder.set_valid_after(valid_after)

    # cert_builder is needed to obtain the SSH public key's fingerprint
    key_id = 'request[{}] for[{}] ssh_key:[{}]  ca:[{}] valid_to[{}]'.format(
        context.aws_request_id, request.username,
        cert_builder.ssh_public_key.fingerprint, context.invoked_function_arn,
        time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(valid_before)))
    # Removed the crit options
    # cert_builder.set_critical_option_source_address(request.bastion_ip)
    cert_builder.set_key_id(key_id)
    cert = cert_builder.get_cert_file()

    #logger.info(
    #    'Issued a cert to bastion_ip[{}] for the remote_username of [{}] with the key_id[{}] and '
    #    'valid_from[{}])'.format(
    #        request.bastion_ip, request.remote_username, key_id,
    #        time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(valid_after))))
    return respond(None, cert)
