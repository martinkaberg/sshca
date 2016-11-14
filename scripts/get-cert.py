from awsrequests import AwsRequester
import boto3
import click


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
@click.option('--resource', help="Api resource")
@click.option('--target', help="Target")
def main(token_code, host, stage, resource, target):
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
    response = req.get("http://{}/{}/{}/{}".format(host, stage, resource, target), verify=True)
    click.echo(response.status_code)

    click.echo(response.text)


if __name__ == '__main__':
    mfa_serial = get_mfa()
    if mfa_serial is None:
        raise LookupError("No mfa serial found for user")
    main()
