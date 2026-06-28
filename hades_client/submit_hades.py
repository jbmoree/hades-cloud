import argparse
import json
import time
from pathlib import Path
import boto3


lambda_client = boto3.client("lambda")
batch_client = boto3.client("batch")
s3_client = boto3.client("s3")


def upload_file_to_s3(local_file, bucket, key):
    local_file = Path(local_file)

    if not local_file.is_file():
        raise FileNotFoundError(f"Input file not found: {local_file}")

    print(f"Uploading {local_file} -> s3://{bucket}/{key}")
    s3_client.upload_file(str(local_file), bucket, key)


def upload_directory_to_s3(local_dir, bucket, prefix):
    local_dir = Path(local_dir)

    if not local_dir.is_dir():
        raise NotADirectoryError(f"Data directory not found: {local_dir}")

    for path in local_dir.rglob("*"):
        if path.is_file():
            relative = path.relative_to(local_dir).as_posix()
            key = f"{prefix}/{relative}"
            print(f"Uploading {path} -> s3://{bucket}/{key}")
            s3_client.upload_file(str(path), bucket, key)


def upload_inputs_if_needed(bucket, job_name, input_file=None, data_dir=None):
    if input_file is None and data_dir is None:
        return None

    if input_file is None or data_dir is None:
        raise ValueError("Please provide both --input-file and --data-dir, or neither.")

    input_prefix = f"inputs/jobs/{job_name}"

    upload_file_to_s3(
        local_file=input_file,
        bucket=bucket,
        key=f"{input_prefix}/hades.in",
    )

    upload_directory_to_s3(
        local_dir=data_dir,
        bucket=bucket,
        prefix=f"{input_prefix}/hdevar",
    )

    return input_prefix


def invoke_lambda(function_name, job_name, input_prefix=None):
    payload = {
        "job_name": job_name,
    }

    if input_prefix is not None:
        payload["input_prefix"] = input_prefix

    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode("utf-8"),
    )

    data = json.loads(response["Payload"].read())

    if "FunctionError" in response:
        raise RuntimeError(data)

    body = data["body"]
    if isinstance(body, str):
        body = json.loads(body)

    return body


def wait_for_batch_job(job_id, poll_seconds=10):
    while True:
        response = batch_client.describe_jobs(jobs=[job_id])

        if not response["jobs"]:
            raise RuntimeError(f"Batch job not found: {job_id}")

        job = response["jobs"][0]
        status = job["status"]

        print(f"Batch job {job_id}: {status}")

        if status == "SUCCEEDED":
            return job

        if status == "FAILED":
            reason = job.get("statusReason", "Unknown reason")
            raise RuntimeError(f"Batch job failed: {reason}")

        time.sleep(poll_seconds)


def list_s3_prefix(bucket, prefix):
    keys = []
    paginator = s3_client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])

    return keys


def wait_for_s3_outputs(bucket, prefix, poll_seconds=5, max_wait_seconds=120):
    elapsed = 0

    while elapsed <= max_wait_seconds:
        keys = list_s3_prefix(bucket, prefix)

        if keys:
            print(f"Found {len(keys)} S3 output files.")
            return keys

        print(f"No S3 outputs yet under s3://{bucket}/{prefix}. Waiting...")
        time.sleep(poll_seconds)
        elapsed += poll_seconds

    raise RuntimeError(
        f"Batch job succeeded, but no S3 outputs appeared under "
        f"s3://{bucket}/{prefix} after {max_wait_seconds} seconds."
    )


def download_s3_keys(bucket, keys, prefix, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for key in keys:
        relative = key[len(prefix):].lstrip("/")
        local_path = output_dir / relative
        local_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Downloading s3://{bucket}/{key} -> {local_path}")
        s3_client.download_file(bucket, key, str(local_path))


def main():
    parser = argparse.ArgumentParser(
        description="Submit a HADES cloud job through AWS Lambda, AWS Batch, and S3."
    )
    parser.add_argument("--function-name", default="hades-submitter")
    parser.add_argument("--job-name", default=f"hades-{int(time.time())}")
    parser.add_argument("--bucket", default="hades-cloud-results")
    #parser.add_argument(
    #    "--bucket",
    #    default=None,
    #    help="S3 bucket containing the job results"
    #)
    parser.add_argument("--input-file", default=None)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--poll-seconds", type=int, default=10)
    args = parser.parse_args()

    output_dir = args.output_dir or f"downloaded_results/{args.job_name}"

    input_prefix = upload_inputs_if_needed(
        bucket=args.bucket,
        job_name=args.job_name,
        input_file=args.input_file,
        data_dir=args.data_dir,
    )

    body = invoke_lambda(
        function_name=args.function_name,
        job_name=args.job_name,
        input_prefix=input_prefix,
    )

    job_id = body["batch_job_id"]
    s3_prefix = f"jobs/{args.job_name}"

    print("Submitted:", body)

    wait_for_batch_job(job_id, poll_seconds=args.poll_seconds)

    keys = wait_for_s3_outputs(args.bucket, s3_prefix)

    download_s3_keys(args.bucket, keys, s3_prefix, output_dir)

    print(f"Done. Results downloaded to: {output_dir}")


if __name__ == "__main__":
    main()