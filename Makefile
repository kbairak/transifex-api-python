test_nocapture:
	pytest --cov=. --cov-report=term-missing

test:
	pytest -s --cov=. --cov-report=term-missing

