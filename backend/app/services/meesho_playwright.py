"""
Meesho Playwright Service

Uses Playwright to automate browser login and capture credentials including HttpOnly cookies.
Runs Playwright in a separate subprocess to avoid asyncio conflicts with uvicorn on Windows.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)

# Path to the browser runner script
BROWSER_RUNNER_SCRIPT = os.path.join(os.path.dirname(__file__), "meesho_browser_runner.py")


class SessionStatus(str, Enum):
    """Status of a Playwright session."""
    PENDING = "pending"
    BROWSER_OPEN = "browser_open"
    LOGGED_IN = "logged_in"
    CAPTURING = "capturing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class CapturedCredentials:
    """Credentials captured from Meesho login."""
    supplier_id: str
    identifier: str
    connect_sid: str
    browser_id: Optional[str] = None
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PlaywrightSession:
    """Represents an active Playwright session."""
    session_id: str
    user_id: str
    status: SessionStatus = SessionStatus.PENDING
    credentials: Optional[CapturedCredentials] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    browser_task: Optional[asyncio.Task] = None


class MeeshoPlaywrightService:
    """
    Manages Playwright browser sessions for Meesho credential capture.
    
    Flow:
    1. User requests to link Meesho account
    2. We create a session and launch Playwright browser
    3. User logs into Meesho in the browser
    4. We intercept API calls to capture supplier_id and identifier
    5. We capture connect.sid cookie (HttpOnly)
    6. Browser closes, credentials returned
    """
    
    # Store active sessions (in production, use Redis)
    _sessions: Dict[str, PlaywrightSession] = {}
    
    @classmethod
    async def create_session(
        cls,
        user_id: str,
        email: str | None = None,
        password: str | None = None,
    ) -> str:
        """
        Create a new Playwright session and start the browser.

        If *email* and *password* are provided the login form is filled
        automatically (programmatic mode).  Otherwise the browser opens
        for manual login (legacy mode).

        Returns the session_id for polling.
        """
        session_id = str(uuid.uuid4())
        session = PlaywrightSession(
            session_id=session_id,
            user_id=user_id,
            status=SessionStatus.PENDING,
        )
        cls._sessions[session_id] = session

        # Start browser in background
        session.browser_task = asyncio.create_task(
            cls._run_browser_session(session, email=email, password=password)
        )

        return session_id
    
    @classmethod
    def get_session(cls, session_id: str) -> Optional[PlaywrightSession]:
        """Get session by ID."""
        return cls._sessions.get(session_id)
    
    @classmethod
    def get_session_status(cls, session_id: str) -> dict:
        """Get session status as dict."""
        session = cls._sessions.get(session_id)
        if not session:
            return {"status": "not_found", "error": "Session not found"}
        
        result = {
            "session_id": session.session_id,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
        }
        
        if session.error:
            result["error"] = session.error
        
        if session.credentials:
            result["credentials"] = {
                "supplier_id": session.credentials.supplier_id,
                "identifier": session.credentials.identifier,
                # Don't expose connect_sid in status
                "captured_at": session.credentials.captured_at.isoformat(),
            }
        
        return result
    
    @classmethod
    async def cancel_session(cls, session_id: str) -> bool:
        """Cancel an active session."""
        session = cls._sessions.get(session_id)
        if not session:
            return False
        
        session.status = SessionStatus.CANCELLED
        # Kill the subprocess if running
        if hasattr(session, '_process') and session._process:
            try:
                session._process.terminate()
            except Exception:
                pass
        
        return True
    
    @classmethod
    async def _run_browser_session(
        cls,
        session: PlaywrightSession,
        email: str | None = None,
        password: str | None = None,
    ):
        """
        Run the Playwright browser session in a subprocess.
        """
        # Create temp file for output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name

        try:
            session.status = SessionStatus.BROWSER_OPEN

            # Build command
            cmd = [sys.executable, BROWSER_RUNNER_SCRIPT, output_file]
            if email and password:
                cmd += ["--email", email, "--password", password]

            # Prepare environment with DISPLAY for Xvfb (Azure)
            import os
            env = os.environ.copy()
            if 'DISPLAY' not in env and os.getenv('DISPLAY'):
                env['DISPLAY'] = os.getenv('DISPLAY')
            # Fallback: if DISPLAY isn't set, use :99 (Xvfb default)
            if 'DISPLAY' not in env:
                env['DISPLAY'] = ':99'

            # Run the browser script as subprocess
            process = subprocess.Popen(
                cmd,
                env=env,
                # Don't capture output - let it print to terminal
            )
            session._process = process
            
            logger.info(f"Started browser subprocess (PID: {process.pid}) - check terminal for browser logs")
            
            # Poll for completion
            while process.poll() is None:
                if session.status == SessionStatus.CANCELLED:
                    process.terminate()
                    logger.info("Session cancelled, terminating browser")
                    return
                await asyncio.sleep(1)
            
            logger.info(f"Browser subprocess finished with code: {process.returncode}")
            
            # Process finished, read result
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    result = json.load(f)
                
                logger.info(f"Browser result: {result}")
                
                if result.get("success"):
                    session.credentials = CapturedCredentials(
                        supplier_id=result["supplier_id"],
                        identifier=result["identifier"],
                        connect_sid=result["connect_sid"],
                        browser_id=result.get("browser_id"),
                    )
                    session.status = SessionStatus.COMPLETED
                    logger.info(f"Successfully captured credentials for supplier {result['supplier_id']}")
                else:
                    session.status = SessionStatus.FAILED
                    session.error = result.get("error", "Unknown error")
                    logger.error(f"Browser session failed: {session.error}")
            else:
                session.status = SessionStatus.FAILED
                session.error = "No output from browser process"
                
        except Exception as e:
            session.status = SessionStatus.FAILED
            session.error = str(e)
            logger.error(f"Browser session error: {e}", exc_info=True)
        finally:
            # Cleanup temp file
            try:
                if os.path.exists(output_file):
                    os.unlink(output_file)
            except Exception:
                pass
    
    @classmethod
    def cleanup_old_sessions(cls, max_age_seconds: int = 600):
        """Remove sessions older than max_age_seconds."""
        now = datetime.now(timezone.utc)
        to_remove = []
        
        for session_id, session in cls._sessions.items():
            age = (now - session.created_at).total_seconds()
            if age > max_age_seconds:
                to_remove.append(session_id)
                if session.browser_task and not session.browser_task.done():
                    session.browser_task.cancel()
        
        for session_id in to_remove:
            del cls._sessions[session_id]
