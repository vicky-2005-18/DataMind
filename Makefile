.PHONY: setup run test lint clean help

# Windows users: use PowerShell scripts in scripts/ directory instead
# On Windows with Git Bash or WSL, these commands will work

setup:
	pip install -e ".[dev]"

run:
	python -m streamlit run app.py

test:
	pytest -q

lint:
	ruff check .
	ruff format --check .

clean:
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .ruff_cache
	rm -rf .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

help:
	@echo "Available targets:"
	@echo "  setup   - Install dependencies"
	@echo "  run     - Launch the application"
	@echo "  test    - Run tests"
	@echo "  lint    - Run linter"
	@echo "  clean   - Remove build artifacts"
	@echo ""
	@echo "Windows users: Use scripts/setup.ps1 and scripts/run.ps1 instead"
