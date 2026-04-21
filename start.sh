#!/usr/bin/env bash
# Exit on error
set -o errexit

# Determine the data directory
# Render persistent disks are mounted at /data. If it exists and is writable, use it.
# Otherwise, fall back to the project root (same as local development).
if [ -d "/data" ] && [ -w "/data" ]; then
    echo "==> Using persistent storage at /data"
    export DATA_ROOT="/data"
else
    echo "==> /data not found or not writable. Using project root for storage."
    export DATA_ROOT="."
    # Cleanup accidental directory if it exists (fix for previous script bug)
    if [ -d "-p" ]; then rm -rf "-p"; fi
fi

# Create the directories
mkdir -p "$DATA_ROOT/drafts"
mkdir -p "$DATA_ROOT/memory"
mkdir -p logs

# Override environment variables to ensure the app uses the correct paths
# This ensures consistency even if render.yaml has different values
export LOCAL_DRAFTS_DIR="$DATA_ROOT/drafts"
export MEMORY_INDEX_PATH="$DATA_ROOT/memory/vectors.index"
export MEMORY_METADATA_PATH="$DATA_ROOT/memory/metadata.json"

# Start the application
# Ensure Playwright browsers are installed (Render UI build commands often miss this)
echo "==> Ensuring Playwright browsers are installed..."
playwright install chromium || echo "Playwright install skipped or failed"

# Port is automatically resolved from $PORT environment variable in main.py
python3 main.py run-server --host 0.0.0.0
