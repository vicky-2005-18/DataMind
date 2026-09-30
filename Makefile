.PHONY: setup run test lint clean help

# Windows users: use PowerShell scripts in scripts/ directory instead
# On Windows with Git Bash or WSL, these commands will work
# On Windows CMD, use the scripts in the scripts/ folder

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
	-python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('*.egg-info')]"
	-python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	-python -c "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"
	-python -c "import shutil; shutil.rmtree('.pytest_cache', ignore_errors=True)"
	-python -c "import shutil; shutil.rmtree('.ruff_cache', ignore_errors=True)"
	-python -c "import shutil; shutil.rmtree('.coverage', ignore_errors=True)"
	-python -c "import shutil; shutil.rmtree('htmlcov', ignore_errors=True)"
	-python -c "import shutil; shutil.rmtree('build', ignore_errors=True)"
	-python -c "import shutil; shutil.rmtree('dist', ignore_errors=True)"

help:
	@echo "Available targets:"
	@echo "  setup   - Install dependencies"
	@echo "  run     - Launch the application"
	@echo "  test    - Run tests"
	@echo "  lint    - Run linter"
	@echo "  clean   - Remove build artifacts"
	@echo ""
	@echo "Windows users: Use scripts/setup.ps1 and scripts/run.ps1 instead"
