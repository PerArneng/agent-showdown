from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class FileInfo(BaseModel):
    """Metadata about a single filesystem entry."""

    model_config = ConfigDict(frozen=True)

    path: Path
    size_bytes: int
    modified_at: datetime
    is_directory: bool
