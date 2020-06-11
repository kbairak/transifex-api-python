tests:
	pytest --cov=. --cov-report=term-missing

debugtests:
	pytest -s

watchtests:
	pytest-watch
