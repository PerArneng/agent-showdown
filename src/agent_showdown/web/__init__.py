from pathlib import Path

from agent_showdown.web.app import create_app, stream_events
from agent_showdown.web.server import WebServer

INDEX_PATH = Path(__file__).parent / "static" / "index.html"

__all__ = ["INDEX_PATH", "WebServer", "create_app", "stream_events"]
