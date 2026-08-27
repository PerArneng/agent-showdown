class InMemoryConsole:
    """Test fake. Collects written lines instead of touching a terminal."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.error_lines: list[str] = []

    def write_line(self, text: str) -> None:
        self.lines.append(text)

    def write_error_line(self, text: str) -> None:
        self.error_lines.append(text)
