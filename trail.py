"""Trail script for testing the use_case module with simplified API.

This script demonstrates both the simplified function-based API and the
legacy PipedataProcessor class-based API.
"""

import logging
from pathlib import Path

from pykorf import Model
from pykorf.use_case.config import get_pms_path
from pykorf.use_case.exceptions import (
    LineNumberParseError,
    PmsLookupError,
    StreamNotFoundError,
)
from pykorf.use_case.hmb import apply_hmb
from pykorf.use_case.pms import apply_pms

# Configure logging to show INFO level and above
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

KORF_FILE = r"pykorf/trail_files/Cooling Water Circuit.kdf"

# Try to get PMS path from config (like TUI does), fallback to hardcoded
pms_path = get_pms_path()
if pms_path is None or not pms_path.exists():
    # Fallback for debugging
    pms_path = Path(r"pykorf/use_case/Input/Consolidated PMS.json")
    print(f"[INFO] PMS path from config not found, using fallback: {pms_path}")
else:
    print(f"[INFO] Using PMS path from config: {pms_path}")

# HMB path - in TUI this comes from user input
hmb_path = Path(r"pykorf/use_case/Input/Stream Data.json")

print(f"\n{'=' * 60}")
print("DEBUG: Starting use_case processing")
print(f"{'=' * 60}")
print(f"KORF file: {KORF_FILE}")
print(f"PMS file:  {pms_path}")
print(f"HMB file:  {hmb_path}")
print(f"{'=' * 60}\n")

# Load model
print("[1/4] Loading KORF model...")
model = Model(KORF_FILE)
print(f"      Loaded model with {len(model.pipes)} pipes")

# Apply PMS data - directly applies schedule/material and returns list of updated pipes
print("\n[2/4] Applying PMS specifications...")
if not pms_path.exists():
    print(f"      [ERROR] PMS file not found: {pms_path}")
    print("      Skipping PMS application.")
    pms_pipes = []
else:
    try:
        pms_pipes = apply_pms(pms_path, model, save=False)
        print(f"      [OK] PMS updated {len(pms_pipes)} pipes:")
        for name in pms_pipes[:10]:  # Show first 10
            print(f"           - {name}")
        if len(pms_pipes) > 10:
            print(f"           ... and {len(pms_pipes) - 10} more")
    except (LineNumberParseError, PmsLookupError) as e:
        print(f"      [ERROR] PMS processing stopped: {e}")
        print("      (This is expected if some pipes have non-line-number NOTES)")
        pms_pipes = []

# Apply HMB data - directly applies fluid props and returns list of updated pipes
print("\n[3/4] Applying HMB fluid properties...")
if not hmb_path.exists():
    print(f"      [ERROR] HMB file not found: {hmb_path}")
    print("      Skipping HMB application.")
    hmb_pipes = []
else:
    try:
        hmb_pipes = apply_hmb(hmb_path, model, save=False)
        print(f"      [OK] HMB updated {len(hmb_pipes)} pipes:")
        for name in hmb_pipes[:10]:  # Show first 10
            print(f"           - {name}")
        if len(hmb_pipes) > 10:
            print(f"           ... and {len(hmb_pipes) - 10} more")
    except StreamNotFoundError as e:
        print(f"      [ERROR] HMB processing stopped: {e}")
        hmb_pipes = []

# Summary
print(f"\n{'=' * 60}")
print("SUMMARY:")
print(f"  - PMS pipes updated: {len(pms_pipes)}")
print(f"  - HMB pipes updated: {len(hmb_pipes)}")
print(f"{'=' * 60}")

# Save the updated model
print("\n[4/4] Saving updated model...")
output_path = KORF_FILE.replace(".kdf", "_updated.kdf")
model.save(output_path)
print(f"      [OK] Saved to: {output_path}")

print("\nDone!")
