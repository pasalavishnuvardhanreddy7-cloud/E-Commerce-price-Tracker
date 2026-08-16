"""
Environment Verification Script
Tests imports, versions, database connectivity, and configuration loading.
"""

import os
import sys
import importlib
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


def test_python_version() -> bool:
    print(f"[*] Python Version: {sys.version.split()[0]}")
    if sys.version_info < (3, 11):
        print("[-] Warning: Recommended version is Python 3.12+")
        return False
    print("[+] Python version check passed.")
    return True


def test_package_imports() -> bool:
    packages = [
        "flask",
        "pandas",
        "numpy",
        "matplotlib",
        "requests",
        "bs4",
        "selenium",
        "sqlalchemy",
        "pymongo",
        "dotenv",
        "pytest",
    ]
    all_passed = True
    for pkg in packages:
        try:
            mod = importlib.import_module(pkg)
            version = getattr(mod, "__version__", "Installed")
            print(f"[+] Loaded {pkg:<15} (version: {version})")
        except ImportError as exc:
            print(f"[-] Failed to import {pkg}: {exc}")
            all_passed = False
    return all_passed


def test_env_variables() -> bool:
    secret_key = os.getenv("SECRET_KEY")
    db_url = os.getenv("DATABASE_URL")
    mongo_uri = os.getenv("MONGO_URI")

    if not secret_key or not db_url or not mongo_uri:
        print("[-] Environment variables missing from .env file.")
        return False

    print(f"[+] DATABASE_URL found: {db_url}")
    print(f"[+] MONGO_URI found:    {mongo_uri}")
    return True


def test_mongo_connection() -> bool:
    try:
        from pymongo import MongoClient

        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        client.server_info()
        print("[+] MongoDB connection successful.")
        client.close()
        return True
    except Exception as exc:
        print(f"[-] MongoDB connection failed: {exc}")
        return False


def main() -> None:
    print("=" * 55)
    print("      E-Commerce Price Tracker: Environment Test      ")
    print("=" * 55)

    py_ok = test_python_version()
    print("-" * 55)
    pkg_ok = test_package_imports()
    print("-" * 55)
    env_ok = test_env_variables()
    print("-" * 55)
    mongo_ok = test_mongo_connection()
    print("=" * 55)

    if py_ok and pkg_ok and env_ok and mongo_ok:
        print(">>> SUCCESS: Python environment is properly configured! <<<")
    else:
        print(">>> WARNING: Some environment checks failed. Review output above. <<<")


if __name__ == "__main__":
    main()

    