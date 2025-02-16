#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create database directory if it doesn't exist
mkdir -p instance

# Initialize database
python init_db.py  # if you have this file 