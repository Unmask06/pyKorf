"""
Tests for individual element classes.
Run with:  pytest tests/
"""

from pathlib import Path

from pykorf.model import KorfModel

SAMPLES_DIR = Path(__file__).parent.parent / "pykorf" / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
CRANE_KDF = SAMPLES_DIR / "crane10.kdf"


class TestPipe:
    def _model(self, kdf=PUMP_KDF):
        return KorfModel.load(kdf)

    def test_pipe_name(self):
        m = self._model()
        assert m.pipes[1].name == "L1"

    def test_pipe_diameter(self):
        m = self._model()
        assert m.pipes[1].diameter_inch == "6"

    def test_pipe_schedule(self):
        m = self._model()
        # Pumpcases.kdf pipe 1 has schedule "STD"
        assert m.pipes[1].schedule == "STD"

    def test_pipe_length(self):
        m = self._model()
        assert m.pipes[1].length_m == 100.0

    def test_pipe_material(self):
        m = self._model()
        assert m.pipes[1].material == "Steel"

    def test_pipe_velocity(self):
        m = self._model()
        v = m.pipes[1].velocity
        assert isinstance(v, list)
        assert len(v) > 0

    def test_pipe_summary(self):
        m = self._model()
        s = m.pipes[1].summary()
        assert "name" in s
        assert "dP_kPa_100m" in s


class TestPump:
    def _pump(self):
        return KorfModel.load(PUMP_KDF).pumps[1]

    def test_pump_name(self):
        assert self._pump().name == "P1"

    def test_pump_type(self):
        assert self._pump().pump_type == "Centrifugal"

    def test_pump_head(self):
        assert self._pump().head_m > 0

    def test_pump_power(self):
        assert self._pump().power_kW > 0

    def test_pump_efficiency(self):
        e = self._pump().efficiency
        assert 0 < e <= 1

    def test_pump_has_curve(self):
        assert self._pump().has_curve

    def test_pump_curve_lengths(self):
        p = self._pump()
        assert len(p.curve_q) == len(p.curve_h) == len(p.curve_eff)

    def test_set_efficiency(self):
        m = KorfModel.load(PUMP_KDF)
        # Set efficiency override (stored at index 0)
        m.pumps[1].set_efficiency(0.75)
        # Verify it was set correctly by checking the raw value
        rec = m.pumps[1]._get("EFFP")
        assert rec is not None
        assert rec.values[0] == "0.75"
        # Note: efficiency property reads calculated value at index 1,
        # which may differ from the override value

    def test_pump_summary(self):
        s = self._pump().summary()
        assert "power_kW" in s
        assert "efficiency" in s


class TestFeedProduct:
    def _model(self):
        return KorfModel.load(PUMP_KDF)

    def test_feed_pressure(self):
        m = self._model()
        feed = m.feeds[1]
        assert "50" in feed.pressure_string

    def test_set_feed_pressure(self):
        m = self._model()
        m.feeds[1].set_pressure("80;90;60")
        assert "80" in m.feeds[1].pressure_string

    def test_product_pressure(self):
        m = self._model()
        prod = m.products[1]
        assert prod.pressure_string == "1000"


class TestValveOrifice:
    def _model(self):
        return KorfModel.load(PUMP_KDF)

    def test_valve_exists(self):
        m = self._model()
        assert 1 in m.valves

    def test_valve_dp(self):
        m = self._model()
        assert m.valves[1].dp_kPag > 0

    def test_orifice_beta(self):
        m = self._model()
        assert 0 < m.orifices[1].beta < 1


class TestHeatExchanger:
    def _model(self):
        return KorfModel.load(PUMP_KDF)

    def test_hx_exists(self):
        m = self._model()
        assert 1 in m.exchangers

    def test_hx_type(self):
        m = self._model()
        assert m.exchangers[1].hx_type == "S-T"

    def test_hx_dp(self):
        m = self._model()
        assert m.exchangers[1].dp_kPag > 0
