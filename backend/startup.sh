#!/bin/bash
set -e

echo "=== MeeShip Startup Script ==="

# 1. Activate Python virtual environment
if [ -f /home/site/wwwroot/antenv/bin/activate ]; then
    echo "Activating virtual environment..."
    source /home/site/wwwroot/antenv/bin/activate
else
    echo "WARNING: Virtual environment not found at /home/site/wwwroot/antenv"
fi

# 2. Install Xvfb (virtual display for headed Chromium)
echo "Installing Xvfb..."
apt-get update -qq && apt-get install -y -qq xvfb > /dev/null 2>&1
echo "Xvfb installed."

# 3. Install Playwright browser dependencies
echo "Installing Playwright dependencies..."
PLAYWRIGHT_BROWSERS_PATH=/home/playwright-browsers playwright install chromium 2>/dev/null || true
PLAYWRIGHT_BROWSERS_PATH=/home/playwright-browsers playwright install-deps chromium 2>/dev/null || true
echo "Playwright ready."

# 4. Start Xvfb on display :99
echo "Starting Xvfb on :99..."
# Kill any existing Xvfb first
pkill -f "Xvfb :99" 2>/dev/null || true
sleep 1

# Start Xvfb as a background daemon with setsid so it survives
Xvfb :99 -screen 0 1280x900x24 -ac +extension GLX +render -noreset &
XVFB_PID=$!
sleep 2

# Verify Xvfb is running
if kill -0 $XVFB_PID 2>/dev/null; then
    echo "✅ Xvfb started successfully (PID: $XVFB_PID)"
else
    echo "❌ Xvfb failed to start, retrying with setsid..."
    setsid Xvfb :99 -screen 0 1280x900x24 -ac +extension GLX +render -noreset >/dev/null 2>&1 < /dev/null &
    sleep 2
    echo "Xvfb retry done."
fi

export DISPLAY=:99
echo "DISPLAY=$DISPLAY"

# 5. Start the application
echo "Starting uvicorn..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
