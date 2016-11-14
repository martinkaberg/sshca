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

    response = req.post(
        "http://{}/{}/{}/{}".format(host, stage, resource, target),
        data={
            "public_key_to_sign": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC3j8yMKRpL4Y5QwQeM94/1Rzav2dRRbEzyns1OMmG4l75KupqDb2vHWOnXy6he0Fc497BrKT0L00ZT7INQq7+bgClNMvZefN6UZgM9gVcWkz1nmCzhu1/WeieeHjFsplUAjH86npN59sk1RQEY8O8ZcIWHi7AIadN1Sx5rQWT41eO00Lb0bNIk0jPDJN5JmbA3R4zWisuf0D9D+68zkP7UNL4qJyD27+LSOiv6Y7RbdQ62H7MZvq2tC519+IMTsCDJCuGhrbumKvAv74VAi66fmnQKPZQzl+l++OLU9vz6SMKpttKHynxdW2Si7bJZ4UwEAburBP5uy+su6YaJt80Iav3Uyj0CGExU8s+9TNIrcXrTnKuaxO+bTlXRAmVVf0l0rKlmoDb4s++xba3WVFEYThO7MysgDcCte8Trg1mXNrYerWSZt3RLlqLYE+S9Clh6yBfHLDdKGWh1U5TLY6Elj++d3K5LRb4XDFevEEdWigcsEa8Uxwi9i+6DlMRUijk9wQeegrWOozEmvcJLBXQY+svIEElYqUeYkDQRpJQgHo9h75o7ewAOhId+QA+X2n/ItwZSto55IXj2gHMNDS5adzRzJLt3RZAp7oE2/yj3oqpLlJjZ152SKBEUulZ9uwKKnvxrwawc0AOMcRSnTIlduvTb90O6wJxzRpiKepGvTQ== fishdaemon"
        },
        verify=True
    )

    click.echo(response.status_code)

    click.echo(response.text)


if __name__ == '__main__':
    mfa_serial = get_mfa()
    if mfa_serial is None:
        raise LookupError("No mfa serial found for user")
    main()
