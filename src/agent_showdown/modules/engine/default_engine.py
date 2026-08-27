from agent_showdown.interfaces.log import Logger


class DefaultEngine:
    """The application facade. Gains one constructor parameter per module it needs."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def start(self) -> None:
        self._logger.info("started")
