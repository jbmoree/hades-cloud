#!/bin/bash
set -e

input_file=$1
data_dir=$2
outdir=$3

srcdir="/app/hades"

mkdir -p "${outdir}"

workdir=$(mktemp -d)
echo "Working directory: ${workdir}"

echo "Input file: ${input_file}"
echo "Data dir: ${data_dir}"
echo "Output dir: ${outdir}"

cp "${input_file}" "${workdir}/hades.in"

mkdir -p "${workdir}/hdevar"
cp -r "${data_dir}/." "${workdir}/hdevar/"

echo "Descriptor files:"
find "${workdir}/hdevar/in" -maxdepth 1 -type f | sort

echo "Target files:"
find "${workdir}/hdevar/out" -maxdepth 1 -type f | sort

echo "Number of descriptor files:"
find "${workdir}/hdevar/in" -maxdepth 1 -type f | wc -l

echo "Number of target files:"
find "${workdir}/hdevar/out" -maxdepth 1 -type f | wc -l

echo "Workdir contents before run:"
find "${workdir}" -maxdepth 4 -type f | sort

cd "${workdir}"


echo "PWD before HADES:"
pwd

echo "Target dir absolute check:"
ls -la "$(pwd)/hdevar/out"

echo "Target dir relative check:"
ls -la ./hdevar/out/


"${srcdir}/hades.x" < ./hades.in > "${outdir}/hades.out" 2> "${outdir}/hades.err"

echo "Workdir contents after HADES:"
find "${workdir}" -maxdepth 3 -type f | sort

if [ -d "./out" ]; then
    cp -rv ./out "${outdir}/"
else
    echo "ERROR: ./out was not created"
    exit 1
fi