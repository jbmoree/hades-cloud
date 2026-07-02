from pathlib import Path
import shutil
import subprocess
import sys
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
CLIENT = ROOT_DIR / "hades_client" / "submit_hades.py"

FILES_TO_COMPARE = [
    "out/optparam_g001",
    "out/optparam_g002",
    "out/xopt_g002_aff_coeff",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def compare_reference_files(test_dir: Path, output_dir: Path) -> None:
    for relative_file in FILES_TO_COMPARE:
        actual = output_dir / relative_file
        reference = test_dir / "ref" / relative_file

        assert actual.is_file(), f"Missing output file: {actual}"
        assert reference.is_file(), f"Missing reference file: {reference}"

        assert read_text(actual) == read_text(reference), (
            f"File differs from reference: {relative_file}\n"
            f"Actual:    {actual}\n"
            f"Reference: {reference}"
        )


def run_hades_ci_case(case_name: str) -> None:
    test_dir = ROOT_DIR / "hades_tests" / case_name
    output_dir = ROOT_DIR / "downloaded_results" / case_name

    input_file = test_dir / "hades.in"
    data_dir = test_dir / "hdevar"

    assert input_file.is_file(), f"Missing input file: {input_file}"
    assert data_dir.is_dir(), f"Missing data directory: {data_dir}"

    if output_dir.exists():
        shutil.rmtree(output_dir)

    command = [
        sys.executable,
        str(CLIENT),
        "--job-name",
        case_name,
        "--input-file",
        str(input_file),
        "--data-dir",
        str(data_dir),
        "--output-dir",
        str(output_dir),
        "--cleanup",
    ]

    result = subprocess.run(
        command,
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, (
        f"HADES cloud job failed for {case_name}\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    compare_reference_files(test_dir, output_dir)


#def test_ci1():
#    run_hades_ci_case("ci1")
#def test_ci2():
#    run_hades_ci_case("ci2")

@pytest.mark.parametrize(
    "case",
    [
        "ci1",
        "ci2"
    ],
)
def test_hades(case):
    run_hades_ci_case(case)