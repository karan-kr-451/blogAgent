#!/usr/bin/env bash
# exit on error
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Install Playwright browsers and their system dependencies
playwright install chromium
playwright install-deps chromium
