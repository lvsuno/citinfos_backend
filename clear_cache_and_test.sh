#!/bin/bash

# Script to clear browser caches and reload the development environment

echo "🧹 Clearing browser cache and reloading development environment..."

# Kill any existing Chrome processes to clear cache completely
echo "Stopping Chrome processes..."
pkill -f "Google Chrome" 2>/dev/null || true
sleep 2

echo "Starting Chrome with clean cache..."
# Open Chrome with disabled web security and cleared cache
open -n -a "Google Chrome" --args \
  --disable-web-security \
  --user-data-dir="/tmp/chrome_dev_session" \
  --disable-features=VizDisplayCompositor \
  --disable-source-maps \
  --disable-extensions \
  "http://localhost:5173"

echo "✅ Chrome opened with development settings"
echo "📝 Navigate to: http://localhost:5173"
echo "🔧 Check the console - it should be much cleaner now!"
