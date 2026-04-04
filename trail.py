"""Trail script for testing center_layout."""

from pathlib import Path

from pykorf import KorfModel

LIBRARY = Path(__file__).parent / "pykorf" / "library"
CWC_KDF = LIBRARY / "Cooling Water Circuit.kdf"
PUMP_KDF = LIBRARY / "Pumpcases.kdf"
TEST_FILE = Path(
    r"C:\Users\PrasannaPalanivel\CC7\25002 TAZIZ SALT PVC - ADNOC UAE - 2A-PROCESS\08) Calculations\Hydraulics\EDC VCM\Prasanna\EV170-PS-010 VCM Offspec Pump\EV170-PS-010 - Copy.kdf"
)


def _bbox(model: KorfModel) -> tuple[float, float, float, float] | None:
    """Return (x_min, y_min, x_max, y_max) across all non-zero XY coords."""
    coords = [coord for elem in model.elements for coord in model.layout._all_nonzero_coords(elem)]
    if not coords:
        return None
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return min(xs), min(ys), max(xs), max(ys)


def test_model(label: str, kdf_path: Path) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"  {kdf_path.name}")
    print(f"{'=' * 60}")

    m = KorfModel.load(kdf_path)

    # Page info
    page = m.layout.page_size
    x_min, y_min, x_max, y_max = m.layout.boundary_coordinates
    page_cx = (x_min + x_max) / 2
    page_cy = (y_min + y_max) / 2
    print(f"\nPage  : {page}  bounds [{x_min:.0f},{y_min:.0f}] -> [{x_max:.0f},{y_max:.0f}]")
    print(f"Page centre : ({page_cx:.1f}, {page_cy:.1f})")

    # Before
    before = _bbox(m)
    if before is None:
        print("No placed elements found.")
        return
    bx_min, by_min, bx_max, by_max = before
    before_cx = (bx_min + bx_max) / 2
    before_cy = (by_min + by_max) / 2
    print(f"\nBefore center_layout()")
    print(f"  Bbox  : [{bx_min:.1f},{by_min:.1f}] -> [{bx_max:.1f},{by_max:.1f}]")
    print(f"  Centre: ({before_cx:.1f}, {before_cy:.1f})")
    print(f"  Offset from page centre: dx={page_cx - before_cx:.1f}, dy={page_cy - before_cy:.1f}")

    # Apply
    m.layout.center_layout()

    # After
    after = _bbox(m)
    if after is None:
        return
    ax_min, ay_min, ax_max, ay_max = after
    after_cx = (ax_min + ax_max) / 2
    after_cy = (ay_min + ay_max) / 2
    print(f"\nAfter  center_layout()")
    print(f"  Bbox  : [{ax_min:.1f},{ay_min:.1f}] -> [{ax_max:.1f},{ay_max:.1f}]")
    print(f"  Centre: ({after_cx:.1f}, {after_cy:.1f})")
    print(f"  Offset from page centre: dx={page_cx - after_cx:.1f}, dy={page_cy - after_cy:.1f}")

    # Verify
    ok = abs(after_cx - page_cx) < 1.0 and abs(after_cy - page_cy) < 1.0
    print(f"\n  {'PASS' if ok else 'FAIL'} — layout centred on page")
    #save
    m.save()


# test_model("Cooling Water Circuit", CWC_KDF)
# test_model("Pump Cases", PUMP_KDF)
#
test_model("", TEST_FILE)
