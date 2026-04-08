import pytest

from pykorf.core.exceptions import ExportError
from pykorf.core.model import Model
from pykorf.app.operation.config.config import get_pms_path, get_stream_path
from pykorf.app.operation.data_import.line_number import MAX_LINE_NUMBER_LENGTH, LineNumber
from pykorf.core.utils import MAX_FIELD_COUNT, MAX_LINE_LENGTH, parse_line


def test_path_traversal_sanitization():
    # Test that get_pms_path and get_stream_path sanitize filenames
    base_pms = get_pms_path("pms.json")
    traversal_pms = get_pms_path("../../etc/passwd")
    assert traversal_pms.name == "passwd"
    assert traversal_pms.parent == base_pms.parent

    base_stream = get_stream_path("stream_data.json")
    traversal_stream = get_stream_path("..\\..\\windows\\system32\\cmd.exe")
    assert traversal_stream.name == "cmd.exe"
    assert traversal_stream.parent == base_stream.parent


def test_parse_line_limits():
    # Test length limit
    long_line = "A" * (MAX_LINE_LENGTH + 1)
    with pytest.raises(ValueError, match="Line exceeds maximum length"):
        parse_line(long_line)

    # Test field count limit
    many_fields = ",".join(["1"] * (MAX_FIELD_COUNT + 1))
    with pytest.raises(ValueError, match="Line has too many fields"):
        parse_line(many_fields)


def test_line_number_limits():
    # Test LineNumber.parse with long input
    long_notes = "1" * (MAX_LINE_NUMBER_LENGTH + 1)
    assert LineNumber.parse(long_notes) is None

    # Test LineNumber.validate with long input
    result = LineNumber.validate(long_notes)
    assert result.is_valid is False
    assert result.error_message is not None and "exceeds maximum length" in result.error_message


def test_file_overwrite_protection(tmp_path):
    # Setup: create a dummy model and save it
    kdf_path = tmp_path / "test.kdf"
    model = Model()  # Creates blank from template
    model.save(kdf_path)
    assert kdf_path.exists()

    # Try to save again with overwrite=False
    with pytest.raises(ExportError, match="File already exists"):
        model.save(kdf_path, overwrite=False)

    # Try save_as with overwrite=False
    new_path = tmp_path / "another.kdf"
    model.save(new_path)
    with pytest.raises(ExportError, match="File already exists"):
        model.save_as(new_path, overwrite=False)


def test_export_overwrite_protection(tmp_path):
    kdf_path = tmp_path / "test.kdf"
    json_path = tmp_path / "test.json"
    yaml_path = tmp_path / "test.yaml"
    excel_path = tmp_path / "test.xlsx"
    csv_dir = tmp_path / "csv_export"

    model = Model()
    # Add a pump so there is something to export
    model.add_element("PUMP", "P1")

    # JSON
    json_path.write_text("{}")
    with pytest.raises(ExportError, match="File already exists"):
        model.io.export_to_json(json_path, overwrite=False)

    # YAML
    yaml_path.write_text("")
    with pytest.raises(ExportError, match="File already exists"):
        model.io.export_to_yaml(yaml_path, overwrite=False)

    # Excel
    excel_path.write_text("")
    with pytest.raises(ExportError, match="File already exists"):
        model.io.export_to_excel(excel_path, overwrite=False)

    # CSV
    csv_dir.mkdir(parents=True, exist_ok=True)
    pipe_csv = csv_dir / "pipes.csv"
    pipe_csv.write_text("")
    pump_csv = csv_dir / "pumps.csv"
    pump_csv.write_text("")
    with pytest.raises(ExportError, match="File already exists"):
        model.io.export_to_csv(csv_dir, overwrite=False)
