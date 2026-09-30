"""DataMind entry point for 'datamind' command."""

import subprocess
import sys


def main() -> None:
    """Launch the DataMind Streamlit application."""
    from streamlit.web.cli import main as stcli

    sys.argv = ["streamlit", "run", "app.py"] + sys.argv[1:]
    stcli()


if __name__ == "__main__":
    main()
