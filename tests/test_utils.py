"""Tests for pyKorf utility functions."""

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

    def test_is_numeric_str_true(self):
        assert _is_numeric_str("100")
        assert _is_numeric_str("2.22E-02")
        assert _is_numeric_str("-3.14")

    def test_is_numeric_str_false(self):
        assert not _is_numeric_str("")
        assert not _is_numeric_str("t/h")
        assert not _is_numeric_str("Steel")


class TestCaseHelpers:
    def test_split_multi(self):
        assert split_cases("50;55;20") == ["50", "55", "20"]

    def test_split_single(self):
        assert split_cases("100") == ["100"]

    def test_split_calculated(self):
        assert split_cases(";C") == [";C"]

    def test_join_ints(self):
        assert join_cases([50, 55, 20]) == "50;55;20"

    def test_join_strings(self):
        assert join_cases(["50", "55", "20"]) == "50;55;20"

    def test_is_calculated_true(self):
        assert is_calculated(";C")

    def test_is_calculated_false(self):
        assert not is_calculated("50")
        assert not is_calculated("")
