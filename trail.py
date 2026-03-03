"""Trail script for testing the use_case module with simplified API.

This script demonstrates both the simplified function-based API and the
legacy PipedataProcessor class-based API.
"""

import logging

from pykorf import Model
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

KORF_FILE = r"pykorf/trail_files/Cooling Water Circuit-EES-IT-LT-00141.kdf"
PMS_JSON = r"pykorf/use_case/Input/Consolidated PMS.json"
HMB_JSON = r"pykorf/use_case/Input/Stream Data.json"


model = Model(KORF_FILE)

# Apply PMS data - directly applies schedule/material and returns list of updated pipes

try:
    pms_pipes = apply_pms(PMS_JSON, model, save=False)
    print(f"\nPMS updated {len(pms_pipes)} pipes: {pms_pipes}")
except (LineNumberParseError, PmsLookupError) as e:
    print(f"\nPMS processing stopped: {e}")
    print("(This is expected if some pipes have non-line-number NOTES)")

# Apply HMB data - directly applies fluid props and returns list of updated pipes

try:
    hmb_pipes = apply_hmb(HMB_JSON, model, save=False)
    print(f"\nHMB updated {len(hmb_pipes)} pipes: {hmb_pipes}")
except StreamNotFoundError as e:
    print(f"\nHMB processing stopped: {e}")

# Save the updated model
output_path = KORF_FILE.replace(".kdf", "_updated.kdf")
model.save(output_path)
print(f"\nSaved updated model to: {output_path}")
