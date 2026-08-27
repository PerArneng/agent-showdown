from datetime import datetime

from pydantic import BaseModel, ConfigDict

from agent_showdown.interfaces.log.log_level import LogLevel


class LogRecord(BaseModel):
    """A single log event, before it has been rendered to text."""

    model_config = ConfigDict(frozen=True)

    level: LogLevel
    message: str
    timestamp: datetime
