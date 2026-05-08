#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

ensure_python() {
  if command -v python3 >/dev/null 2>&1; then
    return 0
  fi

  echo "Python 3 was not found. Attempting to install it..."

  if [[ "$(uname -s)" == "Darwin" ]]; then
    if command -v brew >/dev/null 2>&1; then
      brew install python
    else
      echo "Homebrew is not installed. Install Python from https://www.python.org/downloads/ or install Homebrew first."
      exit 1
    fi
  elif command -v apt-get >/dev/null 2>&1; then
    echo "Using apt-get. You may be prompted for your sudo password."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
  else
    echo "Could not auto-install Python. Install Python 3.11+ and rerun this script."
    exit 1
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    echo "Python installation did not make python3 available on PATH. Please restart your terminal or install Python manually."
    exit 1
  fi
}

ensure_python

if [ ! -d .venv ]; then
  echo "Creating virtual environment..."
  if ! python3 -m venv .venv; then
    echo "Could not create a virtual environment. On Ubuntu/WSL, run: sudo apt-get install python3-venv"
    exit 1
  fi
fi

. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
