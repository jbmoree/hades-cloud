from aws_cdk import (
    CfnOutput,
    Stack,
)
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_lambda as lambda_
from constructs import Construct


class HadesCloudStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Existing resources created manually for now.
        bucket = s3.Bucket.from_bucket_name(
            self,
            "HadesResultsBucket",
            bucket_name="hades-cloud-results",
        )

        repository = ecr.Repository.from_repository_name(
            self,
            "HadesEcrRepository",
            repository_name="hades-cloud",
        )

        submitter = lambda_.Function.from_function_name(
            self,
            "HadesSubmitterLambda",
            function_name="hades-submitter",
        )

        CfnOutput(
            self,
            "ResultsBucketName",
            value=bucket.bucket_name,
        )

        CfnOutput(
            self,
            "EcrRepositoryName",
            value=repository.repository_name,
        )

        CfnOutput(
            self,
            "LambdaFunctionName",
            value=submitter.function_name,
        )