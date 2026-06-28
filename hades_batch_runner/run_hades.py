import os
import subprocess
from pathlib import Path
import boto3
import traceback
from botocore.exceptions import ClientError

def upload_directory_to_s3(local_dir, bucket, prefix):
    s3 = boto3.client("s3")
    local_dir = Path(local_dir)

    for path in local_dir.rglob("*"):
        if path.is_file():
            key = f"{prefix}/{path.relative_to(local_dir)}"

            print(f"Uploading {path} -> s3://{bucket}/{key}")

            try:
                s3.upload_file(str(path), bucket, key)
                print("Success")

            except ClientError as e:
                print("AWS ERROR")
                print(e.response)
                raise

            except Exception as e:
                print(type(e))
                print(e)
                raise


def download_s3_prefix(bucket, prefix, local_dir):
    s3 = boto3.client("s3")
    local_dir = Path(local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)

    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            relative = key[len(prefix):].lstrip("/")
            local_path = local_dir / relative
            local_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"Downloading s3://{bucket}/{key} -> {local_path}")
            s3.download_file(bucket, key, str(local_path))


def run_hades_job(job_name: str, input_file: str = "test/hades.in", data_dir: str = "test/hdevar"):
    runner_dir = Path("/app/hades_batch_runner")
    results_dir = Path("/app/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    bucket = os.environ.get("HADES_S3_BUCKET")
    input_prefix = os.environ.get("HADES_INPUT_PREFIX")

    if bucket and input_prefix:
        input_dir = runner_dir / "input"
        download_s3_prefix(bucket, input_prefix, input_dir)

        input_path = input_dir / "hades.in"
        data_path = input_dir / "hdevar"
    else:
        input_path = runner_dir / input_file
        data_path = runner_dir / data_dir

    print("Using input file:", input_path)
    print("Using data dir:", data_path)

    completed = subprocess.run(
        ["bash", "job.sh", str(input_path), str(data_path), str(results_dir)],
        cwd=runner_dir,
        capture_output=True,
        text=True,
        check=False
    )

    print("===== job.sh stdout =====")
    for line in completed.stdout.splitlines():
        print(line)

    print("===== job.sh stderr =====")
    for line in completed.stderr.splitlines():
        print(line)

    print("Environment variables:")
    print(os.environ)
    print("Bucket =", bucket)

    prefix = f"jobs/{job_name}"

    if bucket:
        print("Contents of results_dir:")
        for p in results_dir.rglob("*"):
            print(p)

        upload_directory_to_s3(results_dir, bucket, prefix)

    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "results_dir": str(results_dir),
        "s3_prefix": f"s3://{bucket}/{prefix}" if bucket else None
    }
