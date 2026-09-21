"""Verify environment, package dependencies, SQLite, and directory access for DataMind."""

from __future__ import annotations

import platform
import sqlite3
import sys


def verify_environment() -> int:
    print("=" * 60)
    print("DataMind Environment Verification")
    print("=" * 60)

    # 1. Python version check
    py_version = sys.version_info
    print(f"Python Version: {py_version.major}.{py_version.minor}.{py_version.micro} ({platform.platform()})")
    if py_version < (3, 11):
        print("[-] ERROR: Python 3.11 or higher is required.")
        return 1
    print("[+] Python version check passed.")

    # 2. Check standard library sqlite3
    sqlite_ver = sqlite3.sqlite_version
    print(f"[+] SQLite standard library version: {sqlite_ver}")

    # 3. Check core dependencies
    packages = [
        ("streamlit", "Streamlit"),
        ("pandas", "pandas"),
        ("numpy", "NumPy"),
        ("sklearn", "scikit-learn"),
        ("plotly", "Plotly"),
        ("joblib", "joblib"),
        ("pydantic", "Pydantic"),
        ("filelock", "filelock"),
        ("dotenv", "python-dotenv"),
        ("jinja2", "Jinja2"),
        ("pytest", "pytest"),
        ("ruff", "ruff"),
    ]

    failed = False
    for module_name, display_name in packages:
        try:
            mod = __import__(module_name)
            ver = getattr(mod, "__version__", "installed")
            print(f"[+] {display_name}: {ver}")
        except ImportError as exc:
            print(f"[-] ERROR: Failed to import {display_name} ({module_name}): {exc}")
            failed = True

    # 4. Check datamind package import
    try:
        import datamind
        from datamind.config import get_settings
        from datamind.storage.database import run_migrations
        settings = get_settings()
        print(f"[+] datamind package version: {datamind.__version__}")
        print(f"[+] storage root configured: {settings.storage_dir}")
        settings.ensure_directories()
        run_migrations(settings.db_path)
        print(f"[+] SQLite database initialized at: {settings.db_path}")
    except Exception as exc:
        print(f"[-] ERROR initializing datamind: {exc}")
        failed = True

    if failed:
        print("\nEnvironment verification FAILED.")
        return 1

    print("\nAll environment checks PASSED successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(verify_environment())
