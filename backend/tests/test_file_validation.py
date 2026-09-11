from app.services.file_validator import validate_file


def test_rejects_unsupported_file():
    result = validate_file("notes.txt", b"hello")
    assert result.error_code == "UNSUPPORTED_FILE_TYPE"


def test_rejects_empty_file():
    result = validate_file("invoice.pdf", b"")
    assert result.error_code == "EMPTY_FILE"

