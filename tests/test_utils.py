"""Tests for pyKorf utility functions."""

import pytest

from pykorf.core.utils import (
    _is_numeric_str,
    is_calculated,
    join_cases,
    parse_line,
    split_cases,
)


class TestParseFormatLine:
    def test_parse_simple(self):
        tokens = parse_line(r'"\PIPE",1,"TFLOW","50;55;20",20,"t/h"')
        assert tokens[0] == r"\PIPE"
        assert tokens[1] == "1"
        assert tokens[3] == "50;55;20"

    def test_parse_numeric(self):
        tokens = parse_line(r'"\PIPE",1,"LEN",100,"m"')
        assert tokens[3] == "100"

    @pytest.mark.parametrize("value", ["100", "2.22E-02", "-3.14"])
    def test_is_numeric_str_true(self, value):
        assert _is_numeric_str(value)

    @pytest.mark.parametrize("value", ["", "t/h", "Steel"])
    def test_is_numeric_str_false(self, value):
        assert not _is_numeric_str(value)


class TestCaseHelpers:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("50;55;20", ["50", "55", "20"]),
            ("100", ["100"]),
            (";C", [";C"]),
        ],
    )
    def test_split(self, raw, expected):
        assert split_cases(raw) == expected

    @pytest.mark.parametrize(
        "parts, expected",
        [
            ([50, 55, 20], "50;55;20"),
            (["50", "55", "20"], "50;55;20"),
        ],
    )
    def test_join(self, parts, expected):
        assert join_cases(parts) == expected

    @pytest.mark.parametrize(
        "value, expected",
        [
            (";C", True),
            ("50", False),
            ("", False),
        ],
    )
    def test_is_calculated(self, value, expected):
        assert is_calculated(value) is expected
