import os
import aws_cdk as cdk

from hades_stack import HadesCloudStack


app = cdk.App()

account = os.environ.get("CDK_DEFAULT_ACCOUNT")
region = os.environ.get("CDK_DEFAULT_REGION", "ap-northeast-1")

HadesCloudStack(
    app,
    "HadesCloudStack",
    env=cdk.Environment(account=account, region=region),
)

app.synth()