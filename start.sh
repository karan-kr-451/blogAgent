#!/usr/bin/env bash
# Exit on error
set -o errexit

# Create persistent directories if they don't exist
mkdir -p /data/drafts
mkdir -p /data/memory

# Start the application
python main.py run-server --host 0.0.0.0
