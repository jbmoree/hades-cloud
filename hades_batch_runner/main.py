# hades_batch_runner/main.py

import argparse
import os
from run_hades import run_hades_job

parser = argparse.ArgumentParser()
parser.add_argument("--job-name", default=os.environ.get("HADES_JOB_NAME", "local-test"))
parser.add_argument("--input-file", default="test/hades.in")
parser.add_argument("--data-dir", default="test/hdevar")

args = parser.parse_args()

result = run_hades_job(
    job_name=args.job_name,
    input_file=args.input_file,
    data_dir=args.data_dir,
)

print(result)