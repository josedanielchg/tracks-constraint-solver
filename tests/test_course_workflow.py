"""Tests for the course-compatible Tracks workflow."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tracks_solver.course_workflow import (
    cplexSolve,
    displayGrid,
    displaySolution,
    generateDataSet,
    readInputFile,
    resultsArray,
    solveDataSet,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MANUAL_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "tracks" / "manual"


def run_course_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tracks_solver.course_workflow", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_course_instance_test_file_can_be_read() -> None:
    instance = readInputFile(MANUAL_DATA_DIR / "instanceTest.txt")

    assert instance.rows == 4
    assert instance.cols == 4
    assert instance.start == (0, 0)
    assert instance.end == (3, 3)


def test_course_display_wrappers_return_ascii_text(capsys) -> None:
    instance = readInputFile(MANUAL_DATA_DIR / "instanceTest.txt")
    is_optimal, _, solution = cplexSolve(instance)

    unresolved = displayGrid(instance)
    solved = displaySolution(instance, solution)
    captured = capsys.readouterr()

    assert is_optimal is True
    assert "A" in unresolved
    assert "B" in solved
    assert captured.out


def test_course_dataset_workflow_writes_result_files_and_table(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    result_dir = tmp_path / "res" / "cbc"
    csv_path = tmp_path / "res" / "summary.csv"
    table_path = tmp_path / "res" / "array.tex"

    generated = generateDataSet(
        data_dir,
        sizes=((3, 3),),
        count_per_size=2,
        seed=20,
        force=True,
    )
    rows = solveDataSet(
        data_dir,
        result_dir=result_dir,
        csv_output=csv_path,
        force=True,
    )
    latex_table = resultsArray(table_path, result_dir=result_dir)

    assert len(generated) == 2
    assert len(rows) == 2
    assert all((result_dir / path.name).exists() for path in generated)
    assert csv_path.exists()
    assert latex_table.exists()

    first_result = (result_dir / generated[0].name).read_text(encoding="utf-8")
    table_text = latex_table.read_text(encoding="utf-8")

    assert "solveTime =" in first_result
    assert "isOptimal =" in first_result
    assert "\\begin{tabular}" in table_text
    assert "instance\\_t3x3\\_1.txt" in table_text


def test_course_cli_generates_displays_and_solves_one_instance(tmp_path: Path) -> None:
    instance_path = tmp_path / "soutenance_3x3.txt"

    generated = run_course_cli(
        "generate-instance",
        "--rows",
        "3",
        "--cols",
        "3",
        "--seed",
        "203",
        "--output",
        str(instance_path),
    )
    displayed = run_course_cli("display-grid", str(instance_path))
    solved = run_course_cli(
        "solve-instance",
        str(instance_path),
        "--time-limit",
        "30",
        "--display-solution",
    )

    assert generated.returncode == 0, generated.stderr
    assert instance_path.exists()
    assert "instancePath =" in generated.stdout
    assert displayed.returncode == 0, displayed.stderr
    assert "A" in displayed.stdout
    assert solved.returncode == 0, solved.stderr
    assert "isOptimal =" in solved.stdout
    assert "solveTime =" in solved.stdout
    assert "B" in solved.stdout


def test_course_cli_dataset_and_results_table(tmp_path: Path) -> None:
    data_dir = tmp_path / "generated"
    result_dir = tmp_path / "results"
    csv_path = tmp_path / "summary.csv"
    table_path = tmp_path / "array.tex"

    generated = run_course_cli(
        "generate-dataset",
        "--output-dir",
        str(data_dir),
        "--sizes",
        "3x3,4x4",
        "--count-per-size",
        "1",
        "--seed",
        "203",
        "--force",
    )
    solved = run_course_cli(
        "solve-dataset",
        str(data_dir),
        "--result-dir",
        str(result_dir),
        "--csv-output",
        str(csv_path),
        "--time-limit",
        "30",
        "--force",
    )
    table = run_course_cli(
        "results-table",
        "--result-dir",
        str(result_dir),
        "--output",
        str(table_path),
    )

    assert generated.returncode == 0, generated.stderr
    assert len(list(data_dir.glob("*.txt"))) == 2
    assert solved.returncode == 0, solved.stderr
    assert len(list(result_dir.glob("*.txt"))) == 2
    assert csv_path.exists()
    assert "solveTime =" in next(result_dir.glob("*.txt")).read_text(encoding="utf-8")
    assert "isOptimal =" in next(result_dir.glob("*.txt")).read_text(encoding="utf-8")
    assert table.returncode == 0, table.stderr
    assert "\\begin{tabular}" in table_path.read_text(encoding="utf-8")


def test_course_cli_open_ui_help_is_available() -> None:
    result = run_course_cli("open-ui", "--help")

    assert result.returncode == 0
    assert "Pygame" in result.stdout
