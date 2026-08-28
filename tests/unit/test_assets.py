import pytest

from agent_showdown.web.assets import content_type, is_safe_name


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("index-abc123.js", "text/javascript"),
        ("index-abc123.css", "text/css"),
        ("index.html", "text/html"),
        ("data.json", "application/json"),
        ("icon.svg", "image/svg+xml"),
    ],
)
def test_known_extensions_get_a_content_type(name: str, expected: str) -> None:
    assert content_type(name) == expected


@pytest.mark.parametrize("name", ["secrets.env", "app.wasm", "noextension", "archive.tar.gz"])
def test_unknown_extensions_are_refused(name: str) -> None:
    assert content_type(name) is None


@pytest.mark.parametrize("name", ["app.js", "index-DEADBEEF.css"])
def test_plain_file_names_are_safe(name: str) -> None:
    assert is_safe_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "../../../etc/passwd",
        "..",
        "nested/app.js",
        "back\\slash.js",
        ".hidden.js",
        "",
        "null\0byte.js",
    ],
)
def test_anything_that_could_leave_the_directory_is_unsafe(name: str) -> None:
    assert not is_safe_name(name)
