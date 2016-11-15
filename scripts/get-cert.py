from awsrequests import AwsRequester
import boto3
import click
import subprocess


def get_mfa():
    iam = boto3.resource("iam")
    current_user = iam.CurrentUser()

    for mfa in current_user.mfa_devices.all():
        return mfa.serial_number


@click.command()
@click.option('--token-code', prompt="Enter your MFA token", hide_input=False,
              help="The 6 digit number from your MFA device")
@click.option('--host', help="Hostname of the api gateway")
@click.option('--stage', help="Deployment stage")
@click.option('--public-key-file', type=click.Path(exists=True), help="ssh public key file")
def main(token_code, host, stage, public_key_file):
    with open(public_key_file) as f:
        pub_key = f.read()
    f.close()
    sts_client = boto3.client('sts')
    token = sts_client.get_session_token(
        DurationSeconds=900,
        SerialNumber=mfa_serial,
        TokenCode=token_code
    )["Credentials"]

    req = AwsRequester(
        "eu-west-1",
        secret_key=token["SecretAccessKey"],
        access_key=token["AccessKeyId"],
        session_token=token["SessionToken"],
        session_expires=token["Expiration"]
    )
    click.echo(pub_key)
    response = req.post(
        "https://{}/{}/{}".format(host, stage, "cert"),
        json={
            "public_key_to_sign": pub_key
        },
        verify=True
    )
    click.echo(response.text)
    cert_file = '.'.join(public_key_file.split(".")[:-1]) + "-cert.pub"
    with open(cert_file, "w+") as f:
        f.write(response.text)
    f.close()

    key_gen_cmd = [
        "ssh-keygen",
        "-L",
        "-f",
        "id_rsa-cert.pub"
    ]
    subprocess.call(key_gen_cmd)


if __name__ == '__main__':
    mfa_serial = get_mfa()
    if mfa_serial is None:
        raise LookupError("No mfa serial found for user")
    main()
