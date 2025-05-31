@echo off
echo Running code quality checks...

echo.
echo Running isort...
isort . --skip-glob=**/_version.py --extend-skip-glob=__init__.py || exit /b

echo.
echo Running Black...
black . || exit /b

echo.
echo Running Flake8...
flake8 . || exit /b

echo.
echo Running MyPy...
mypy . --explicit-package-bases || exit /b

echo.
echo All checks passed successfully!
