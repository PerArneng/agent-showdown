"""Pure helpers for serving a built client directory. No IO, no framework."""

from pathlib import PurePosixPath

_CONTENT_TYPES = {
    ".css": "text/css",
    ".html": "text/html",
    ".js": "text/javascript",
    ".json": "application/json",
    ".map": "application/json",
    ".svg": "image/svg+xml",
}


def content_type(name: str) -> str | None:
    """Return the content type to serve `name` as, or `None` if we refuse to serve it at all."""
    return _CONTENT_TYPES.get(PurePosixPath(name).suffix)


def is_safe_name(name: str) -> bool:
    """Return whether `name` is a plain file name, and not an attempt to leave the directory."""
    if not name or name.startswith("."):
        return False
    return not any(character in name for character in ("/", "\\", "\0"))
