import json
import os
import time
import boto3

batch = boto3.client("batch")

JOB_QUEUE = os.environ["HADES_JOB_QUEUE"]
JOB_DEFINITION = os.environ["HADES_JOB_DEFINITION"]
RESULT_BUCKET = os.environ["HADES_S3_BUCKET"]


def lambda_handler(event, context):
    print("Full event:", json.dumps(event))

    if "body" in event:
        body = event["body"]
        data = json.loads(body) if isinstance(body, str) else body
    else:
        data = event

    job_name = data.get("job_name", f"hades-{int(time.time())}")
    input_prefix = data.get("input_prefix")

    environment = [
        {"name": "HADES_S3_BUCKET", "value": RESULT_BUCKET},
        {"name": "HADES_JOB_NAME", "value": job_name},
    ]

    if input_prefix:
        environment.append(
            {"name": "HADES_INPUT_PREFIX", "value": input_prefix}
        )

    response = batch.submit_job(
        jobName=job_name,
        jobQueue=JOB_QUEUE,
        jobDefinition=JOB_DEFINITION,
        containerOverrides={
            "environment": environment
        }
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "HADES Batch job submitted",
            "job_name": job_name,
            "batch_job_id": response["jobId"],
            "input_prefix": input_prefix,
            "s3_prefix": f"s3://{RESULT_BUCKET}/jobs/{job_name}",
        }),
    }