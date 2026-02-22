#!/bin/bash
# Don't use set -e — we want the app to start even if Xvfb/apt fails

echo "=== MeeShip Startup Script ==="
echo "Working directory: $(pwd)"

# 1. Activate Python virtual environment (try relative path first, then absolute)
if [ -f antenv/bin/activate ]; then
    echo "Activating virtual environment (relative)..."
    source antenv/bin/activate
elif [ -f /home/site/wwwroot/antenv/bin/activate ]; then
    echo "Activating virtual environment (/home/site/wwwroot)..."
    source /home/site/wwwroot/antenv/bin/activate
else
    echo "WARNING: Virtual environment not found — trying system Python"
fi
echo "Python: $(which python) — $(python --version)"

# 3. Install Xvfb (virtual display for headed Chromium)
echo "Installing Xvfb..."
apt-get update -qq && apt-get install -y -qq xvfb > /dev/null 2>&1 || echo "⚠️ apt-get failed (non-fatal)"
echo "Xvfb installed."

# 4. Install Playwright browser + OS deps, and export path globally
export PLAYWRIGHT_BROWSERS_PATH=/home/playwright-browsers
echo "Installing Playwright dependencies (PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH)..."
playwright install chromium 2>/dev/null || true
playwright install-deps chromium 2>/dev/null || true
echo "Playwright ready."

# 5. Start Xvfb on display :99
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

# 6. Start the application (use Azure's PORT env var, default 8000)
echo "Starting uvicorn on port ${PORT:-8000}..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
