import uvicorn
from fastapi import FastAPI

# Only reached if a stream ignores `stopping()`. Without it, a browser still watching would hold
# the shutdown open forever.
_SHUTDOWN_BACKSTOP_SECONDS = 5


class WebServer:
    """Runs the web frontend, and says when it is on its way out.

    The event stream is endless by design, so a graceful shutdown would wait for a browser that is
    still watching. `stopping()` lets the stream end itself the moment Ctrl-C arrives, which is the
    difference between exiting cleanly and being cancelled mid-flight.
    """

    def __init__(self) -> None:
        self._server: uvicorn.Server | None = None

    def stopping(self) -> bool:
        return self._server is not None and self._server.should_exit

    def run(self, app: FastAPI, port: int) -> None:
        self._server = uvicorn.Server(
            uvicorn.Config(
                app,
                host="127.0.0.1",
                port=port,
                log_level="warning",
                timeout_graceful_shutdown=_SHUTDOWN_BACKSTOP_SECONDS,
            )
        )
        self._server.run()
