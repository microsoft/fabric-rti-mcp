fmt:
	isort .
<<<<<<< HEAD
	black .
=======
	black . --line-length=120
>>>>>>> main

lint:
	flake8 .
	mypy . --explicit-package-bases 

test:
	pytest

precommit:
	isort .
	black .
	flake8 .
	mypy . --explicit-package-bases
	pytest
