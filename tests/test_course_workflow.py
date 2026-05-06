"""Tests for the course-compatible Tracks workflow."""

from __future__ import annotations

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

MANUAL_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "tracks" / "manual"


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
