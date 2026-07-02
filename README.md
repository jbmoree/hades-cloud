# HADES Cloud

**HADES Cloud** is a Python-based cloud workflow that executes HADES symbolic regression calculations on AWS using **AWS Lambda**, **AWS Batch**, **Docker**, and **Amazon S3**.

The repository contains the cloud execution framework used to launch HADES calculations on AWS. The proprietary HADES scientific engine itself is **not** included.

## Technologies

* Python 3
* Docker
* AWS Lambda
* AWS Batch
* Amazon S3
* AWS CLI
* boto3

---

# Architecture

```
              +----------------------+
              |   submit_hades.py    |
              +----------+-----------+
                         |
                         | Upload inputs
                         v
                   Amazon S3 (inputs)
                         |
                         | Invoke
                         v
                  AWS Lambda function
                         |
                         | Submit job
                         v
                    AWS Batch queue
                         |
                         v
                 Docker container
                         |
                         v
                    HADES program
                         |
                  Upload results
                         |
                         v
                  Amazon S3 (results)
                         |
                         |
                         v
              submit_hades.py downloads
                    the output files
```

The client automatically

1. uploads the input files to Amazon S3;
2. invokes an AWS Lambda function;
3. submits an AWS Batch job;
4. waits for the calculation to complete;
5. downloads the generated results.

> **Note**
>
> Running this workflow requires AWS credentials with permissions for AWS Lambda, AWS Batch, Amazon S3, and Amazon ECR.
>
> This repository is configured for the author's AWS deployment. Users wishing to reproduce the workflow should create their own AWS infrastructure (Lambda function, Batch queue, IAM roles, S3 bucket, Docker image, etc.) and update the corresponding configuration.

---

# Usage

## Prerequisites

* Python 3.10 or newer
* AWS CLI v2
* An AWS account with permissions for

  * AWS Lambda
  * AWS Batch
  * Amazon S3
  * Amazon ECR

Authenticate before running the client:

```bash
aws login
```

Install the required Python package:

```bash
pip install -r requirements.txt
```

---

## Running a calculation

```bash
python hades_client/submit_hades.py \
    --input-file path/to/hades.in \
    --data-dir path/to/hdevar
```

where

* `--input-file` specifies the HADES input file;
* `--data-dir` specifies the directory containing the descriptor and target variables.

After completion, the results are automatically downloaded to

```text
downloaded_results/<job_name>/
```

---

# Preparing the input data

## Directory structure

The data directory must have the following structure:

```text
hdevar/
├── in/
│   ├── var_x1
│   ├── var_x2
│   ├── ...
│   └── var_xM
└── out/
    └── var_y
```

where

* `in/` contains the descriptor variables;
* `out/` contains the target variable.

### Requirements

* `out/` **must contain exactly one variable file**.
* `in/` **must contain one or more variable files**.
* Every variable filename **must begin with** `var_`.

The remainder of the filename is arbitrary.

---

## Variable file format

Each variable is stored as a plain text file.

Example:

```text
a1
$a_1$
4
1.7
2.4
2.2
1.1
```

| Line | Meaning                  |
| ---- | ------------------------ |
| 1    | Variable name            |
| 2    | Variable name in LaTeX   |
| 3    | Number of samples, N     |
| 4... | Values for samples 1...N |

All descriptor and target variables must contain the same number of samples.

---

## Minimal input file

```text
&param_hde
ngen = 5
hdevar_in = './hdevar/in/'
hdevar_out = './hdevar/out/'
/
```

where

* `ngen` is the maximum number of HDE generations;
* `hdevar_in` specifies the descriptor directory;
* `hdevar_out` specifies the target directory.

Paths are interpreted relative to the HADES working directory.

---

# Output files

The downloaded results contain

```text
downloaded_results/
├── hades.out
├── hades.err
└── out/
    ├── optparam
    ├── xopt_g001_aff_coeff
    ├── xopt_g002_aff_coeff
    ├── ...
    └── score_gXXX
```

* `hades.out` contains the program output.
* `hades.err` contains error messages.
* `out/` contains the optimization results.

---

# Interpreting the optimization

The target variable is the single variable stored in

```text
hdevar/out/var_*
```

The descriptors are the variables stored in

```text
hdevar/in/var_*
```

HADES builds progressively more expressive symbolic expressions over successive generations.

## Generation 1

```
y_HDE(1) = a1 + b1 z1

z1 = (xopt1)^alpha1
```

where

* `xopt1` is the selected descriptor;
* `a1`, `b1`, and `alpha1` are optimized parameters.

---

## Generation g > 1

```
y_HDE(g) = ag + bg zg

zg = xopt(g-1) *
     [1 + zeta(g) * xopt(g)^alpha(g) /
          xopt(g-1)^beta(g)]
```

where

* `ag` is the affine offset;
* `bg` is the affine slope;
* `alpha(g)` is a real-valued exponent;
* `zeta(g)` is a real-valued scaling factor;
* `beta(g)` is either 0 or 1.

When

* `beta = 0`, the previous descriptor is multiplied by a nonlinear correction factor.
* `beta = 1`, a nonlinear correction is added to the previous descriptor.

---

# Optimization history

The file

```text
out/optparam_gXXX
```

contains one line:

```text
generation   descriptor   alpha   zeta   beta   rho
```

where

* `generation` is the generation number;
* `descriptor` is the selected descriptor;
* `alpha` is the optimized exponent;
* `zeta` is the optimized scaling factor;
* `beta` is either 0 or 1;
* `rho` is the Pearson correlation coefficient between the target variable and the HDE approximation.

Example:

```text
2   txp   1.8700000000   0.0999000000   1   0.9789174842
```

The affine coefficients are stored in

```text
out/xopt_gXXX_aff_coeff
```

Each file contains

```text
ag    bg
```

for the corresponding generation.

---

# Assessing convergence

For a calculation with

```text
ngen = 5
```

HADES produces five successive symbolic expressions.

The final generation corresponds to the final optimized expression.

Earlier generations document how the symbolic expression was progressively constructed.

The Pearson correlation coefficient `rho` generally increases with the generation number. In practice, the calculation can be considered converged once increasing `ngen` no longer produces a significant improvement in `rho`.

Choosing unnecessarily large values of `ngen` increases the computational cost while providing little improvement in the symbolic expression.

---

# Example

Suppose the project contains

```text
example/
├── hades.in
└── hdevar/
    ├── in/
    │   ├── var_txp
    │   ├── var_tpp
    │   └── ...
    └── out/
        └── var_tc
```

The calculation can then be launched with

```bash
python hades_client/submit_hades.py \
    --input-file example/hades.in \
    --data-dir example/hdevar
```

The results are automatically downloaded to

```text
downloaded_results/<job_name>/
```

## Branch protection [in progress]
