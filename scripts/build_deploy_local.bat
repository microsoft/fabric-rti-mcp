@echo off
setlocal

REM Check if version was provided as argument
if "%1"=="" (
    echo Error: Please provide version number as argument
    echo Usage: build_deploy_local.bat 1.0.0
    exit /b 1
)

REM Set version override
set SETUPTOOLS_SCM_PRETEND_VERSION=%1

REM Install dependencies and run quality checks
python -m pip install -e .[dev]

REM Run code quality checks
call scripts\fmt.bat || exit /b 1

REM Build distribution package
python -m pip install --upgrade build twine
python -m build

REM Upload to PyPI (will prompt for credentials)
echo Ready to upload version %1 to PyPI
set /p CONFIRM="Continue? [y/N] "
if /i "%CONFIRM%"=="y" (
    twine upload dist/*
) else (
    echo Upload cancelled
)
