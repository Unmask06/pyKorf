from pykorf.definitions import Common, PROPERTIES_BY_ELEMENT, Element, Orifice, Pipe


def test_element_tokens():
    assert Element.PIPE == "PIPE"
    assert Element.ORIFICE == "FO"


def test_pipe_properties():
    assert Pipe.NAME == "NAME"
    assert Pipe.PRES == "PRES"
    assert "PRES" in Pipe.ALL


def test_property_map_has_pipe_and_orifice():
    assert "PRES" in PROPERTIES_BY_ELEMENT[Element.PIPE]
    assert "DP" in PROPERTIES_BY_ELEMENT[Element.ORIFICE]
    assert Orifice.DP == "DP"


def test_common_properties():
    assert Common.NAME == "NAME"
    assert Common.XY == "XY"
