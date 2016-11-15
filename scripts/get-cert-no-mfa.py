from awsrequests import AwsRequester
import boto3
import click
import subprocess


@click.command()
@click.option('--host', help="Hostname of the api gateway")
@click.option('--stage', help="Deployment stage")
@click.option('--public-key-file', type=click.Path(exists=True), help="ssh public key file")
def main(host, stage, public_key_file):
    with open(public_key_file) as f:
        pub_key = f.read()
    f.close()

    req = AwsRequester(
        "eu-west-1",
    )

    response = req.post(
        "https://{}/{}/{}".format(host, stage, "cert"),
        json={
            "public_key_to_sign": pub_key
        },
        verify=True
    )
    if response.status_code is not 200:
        print response.text
        exit(1)

    cert_file = '.'.join(public_key_file.split(".")[:-1]) + "-cert.pub"
    with open(cert_file, "w+") as f:
        f.write(response.text)
    f.close()

    key_gen_cmd = [
        "ssh-keygen",
        "-L",
        "-f",
        cert_file
    ]
    subprocess.call(key_gen_cmd)


if __name__ == '__main__':
    main()
