#!/bin/sh
set -e

echo "[Booting] Updating yt-dlp to the latest version..."
pip install --no-cache-dir -U --pre "yt-dlp[default]"

echo "[Booting] yt-dlp version:"
yt-dlp --version

echo "[Booting] Starting Uvicorn server..."
exec "$@"