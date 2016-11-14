import boto3
import base64
import click
import subprocess
import os
import ConfigParser


@click.command()
@click.option('--password', prompt="Input pass phrase ", hide_input=False,
              help="very long and random pass phrase for the private key. $(pwgen -cnys 128) should do")
@click.option('--key-alias', default="bless", help="Alias of the kms key you want to use")
@click.option('--build-dir', default="build", help="Build dir relative to this file")
@click.option('--key-comment', default="bless-ca", help="comment for the public key")
def encrypt(password, key_alias, build_dir, key_comment):
    build_dir = os.path.join(os.path.dirname(__file__), build_dir)
    key_gen_cmd = [
        "ssh-keygen",
        "-t",
        "rsa",
        "-b",
        "4096",
        "-f"
        "{}/lambda_configs/ca.pem".format(build_dir),
        "-C",
        key_comment,
        "-N",
        password
    ]
    subprocess.call(key_gen_cmd)
    client = boto3.client('kms', )
    response = client.encrypt(
        KeyId='alias/{}'.format(key_alias),
        Plaintext=password,
    )
    cipher_text = response['CiphertextBlob']
    cipher_b64 = base64.b64encode(cipher_text)

    config = ConfigParser.ConfigParser()
    config.read("{}/bless/config/bless_deploy_example.cfg".format(build_dir))
    config.set("Bless Options", "certificate_validity_window_seconds", "3600")
    config.set("Bless CA", "kms_key_id", 'alias/{}'.format(key_alias))
    config.set("Bless CA", "eu-west-1_password", cipher_b64)
    config.set("Bless CA", "ca_private_key_file", "ca.pem")
    with open("{}/lambda_configs/bless_deploy.cfg".format(build_dir), 'wb') as configfile:
        config.write(configfile)


if __name__ == "__main__":
    encrypt()
