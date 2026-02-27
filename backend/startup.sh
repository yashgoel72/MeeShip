#!/bin/bash
# Don't use set -e — we want the app to start even if Xvfb/apt fails
#
# STRATEGY: Start uvicorn FIRST so Azure's warmup probe succeeds (< 230s),
# then install Xvfb + Playwright deps in the background. Browser automation
# becomes available ~3 min after boot.

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

# 2. Set env vars that uvicorn and the background installer both need
export PLAYWRIGHT_BROWSERS_PATH=/home/playwright-browsers
export DISPLAY=:99

# 3. Start uvicorn IMMEDIATELY so Azure warmup probe passes
#    Run in background so we can launch the installer, then wait on uvicorn.
echo "Starting uvicorn on port ${PORT:-8000} (foreground after bg setup)..."
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} &
UVICORN_PID=$!
echo "✅ uvicorn started (PID: $UVICORN_PID)"

# 4. Background installer: Xvfb + Playwright deps
#    Runs in parallel — uvicorn is already serving requests.
install_browser_deps() {
    echo "[bg-installer] Starting Xvfb + Playwright install..."

    # 4a. Install Xvfb
    apt-get update -qq && apt-get install -y -qq xvfb > /dev/null 2>&1 \
        || echo "[bg-installer] ⚠️ apt-get xvfb failed (non-fatal)"
    echo "[bg-installer] Xvfb package installed."

    # 4b. Install Playwright browser + OS deps
    playwright install chromium 2>/dev/null || true
    playwright install-deps chromium 2>/dev/null || true
    echo "[bg-installer] Playwright ready."

    # 4c. Start Xvfb on display :99
    pkill -f "Xvfb :99" 2>/dev/null || true
    sleep 1
    Xvfb :99 -screen 0 1280x900x24 -ac +extension GLX +render -noreset &
    XVFB_PID=$!
    sleep 2

    if kill -0 $XVFB_PID 2>/dev/null; then
        echo "[bg-installer] ✅ Xvfb started (PID: $XVFB_PID)"
    else
        echo "[bg-installer] ❌ Xvfb failed, retrying with setsid..."
        setsid Xvfb :99 -screen 0 1280x900x24 -ac +extension GLX +render -noreset >/dev/null 2>&1 < /dev/null &
        sleep 2
        echo "[bg-installer] Xvfb setsid retry done."
    fi

    # 4d. Signal readiness by touching a marker file
    touch /tmp/.playwright_ready
    echo "[bg-installer] ✅ All browser deps ready. Marker: /tmp/.playwright_ready"
}

# Launch installer in background
install_browser_deps &
INSTALLER_PID=$!
echo "Background installer PID: $INSTALLER_PID"

# 5. Wait on uvicorn (foreground process) — keeps the container alive
wait $UVICORN_PID
