# Installation Guide

## 1. Project purpose

This repository contains the initial setup for a Python-based puzzle solver project.
The core logic will be written in Python, and the visual layer will use Pygame.

At this stage, the repository provides:

- a local virtual environment workflow,
- runtime and developer dependency files,
- a smoke entrypoint,
- and basic tests and lint configuration.

No Julia setup is required.

## 2. Required Python version

Use Python 3.11, 3.12, or 3.13.
Python 3.11 is the safest default for the initial setup because Pygame installs cleanly there.

Check your version with:

```powershell
python --version
```

If your default `python` command points to Python 3.14 or newer, switch to Python 3.11-3.13 before creating the virtual environment.

## 3. Clone the repository

```powershell
git clone <repo-url>
cd tracks-constraint-solver
```

## 4. Create the virtual environment

If `python --version` already shows Python 3.11-3.13:

```powershell
python -m venv .venv
```

If you need to force Python 3.11 on Windows and the Python launcher is available:

```powershell
py -3.11 -m venv .venv
```

Expected result: a local `.venv` directory is created in the repository root.

## 5. Activate the environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux or macOS:

```bash
source .venv/bin/activate
```

Expected result: your shell prompt shows the virtual environment is active.

## 6. Install runtime dependencies

Runtime dependencies are the packages needed to run the project itself.
For now, that means Python plus Pygame.

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Expected success: `pygame` installs without errors.

## 7. Install developer dependencies

Developer dependencies include the runtime packages plus tools used for testing and linting.

- `requirements.txt`: packages needed to run the project.
- `requirements-dev.txt`: runtime packages plus developer tools such as `pytest` and `ruff`.

```powershell
python -m pip install -r requirements-dev.txt
```

Expected success: `pygame`, `pytest`, and `ruff` are installed in the virtual environment.

## 8. Run the project smoke entrypoint

```powershell
python -m tracks_solver.main
```

Expected success: the command prints the Python version, the Pygame version, and a ready message.

## 9. Run tests

```powershell
python -m pytest
```

Expected success: the smoke tests pass.

## 10. Run lint checks

```powershell
python -m ruff check .
```

Expected success: Ruff completes without reporting errors.

## 11. Common issues

If `Activate.ps1` is blocked in PowerShell, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

If `python` points to the wrong interpreter, verify the active environment and retry the commands.

If dependency installation fails, confirm that your internet connection is available and that `pip` was upgraded inside the virtual environment.

If Pygame fails to install, check the Python version first. For the initial project setup, use Python 3.11-3.13 rather than Python 3.14+.

## 12. Deactivate the environment

```powershell
deactivate
```
