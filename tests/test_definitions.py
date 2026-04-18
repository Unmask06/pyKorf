from pykorf.core.elements import PROPERTIES_BY_ELEMENT, Common, Element, Orifice, Pipe


def test_element_tokens_and_common_props():
    assert Element.PIPE == "PIPE"
    assert Element.ORIFICE == "FO"
    assert Common.NAME == "NAME"
    assert Common.NUM == "NUM"
    assert Pipe.XY == "XY"
    assert Orifice.XY == "XY"


def test_property_map_and_element_properties():
    assert Pipe.NAME == "NAME"
    assert Pipe.PRES == "PRES"
    assert "PRES" in Pipe.ALL
    assert Orifice.DP == "DP"
    assert "PRES" in PROPERTIES_BY_ELEMENT[Element.PIPE]
    assert "DP" in PROPERTIES_BY_ELEMENT[Element.ORIFICE]
