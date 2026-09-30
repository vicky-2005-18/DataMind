# Contributing to DataMind

Thank you for your interest in contributing to DataMind!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/vicky-2005-18/DataMind.git
   cd DataMind
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Run tests:
   ```bash
   pytest -q
   ```

5. Run linter:
   ```bash
   ruff check .
   ruff format .
   ```

## Code Style

- Use 4-space indentation
- Follow PEP 8 (enforced by Ruff)
- Write docstrings for public functions
- Add type hints to public APIs
- Keep functions focused and small

## ML Correctness

Do not break these invariants:
- Target excluded from features
- Exact split/fold row IDs persisted
- Preprocessing fitted within CV training folds
- Champion fitted only on development rows
- Identical folds across models
- Selection by declared CV metric
- Dummy baseline included
- Holdout evaluation explicit and immutable
- Prediction uses saved fitted pipeline
- Config, seed, environment, dataset hashes recorded

## Submitting Changes

1. Create a branch for your feature
2. Make your changes
3. Run tests and linting
4. Commit with clear messages
5. Push and create a pull request

## Testing

- Unit tests should be fast and isolated
- Integration tests should use temporary directories
- UI tests should use Streamlit's AppTest
- Add tests for new features

## Questions?

Open an issue on GitHub for questions or discussion.
