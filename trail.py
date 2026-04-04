"""Trail script for testing the sizing_criteria module.

This script demonstrates the sizing criteria loader and predictor functions
for liquid, gas, and two-phase fluid systems.
"""

import logging

from pykorf.use_case.sizing_criteria import (
    all_codes_by_type,
    get_codes,
    load_criteria,
    lookup_criteria,
    predict_criteria,
    predict_state,
)

# Configure logging to show INFO level and above
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

print("=" * 60)
print("Sizing Criteria Module Tests")
print("=" * 60)

# Test 1: Load criteria for all fluid types
print("\n[1/6] Loading criteria for all fluid types...")
for fluid_type in ["liquid", "gas", "two_phase"]:
    criteria = load_criteria(fluid_type)
    print(f"  {fluid_type}: {len(criteria)} entries loaded")
    if criteria:
        print(f"    Sample entry: {criteria[0]['code']} - {criteria[0]['service']}")

# Test 2: Get available codes
print("\n[2/6] Getting available codes...")
for fluid_type in ["liquid", "gas", "two_phase"]:
    codes = get_codes(fluid_type)
    print(f"  {fluid_type}: {len(codes)} unique codes")
    if codes:
        print(f"    First code: {codes[0][0]} - {codes[0][1][:50]}...")

# Test 3: Get all codes by type
print("\n[3/6] Getting all codes by type...")
all_codes = all_codes_by_type()
for fluid_type, codes in all_codes.items():
    print(f"  {fluid_type}: {len(codes)} codes available")

# Test 4: Predict fluid state from liquid fractions
print("\n[4/6] Predicting fluid states...")
test_cases = [
    ([1.0, 1.0, 0.99], "liquid (>= 0.99)"),
    ([0.0, 0.0, 0.01], "gas (<= 0.01)"),
    ([0.5, 0.6, 0.7], "two_phase (0.01 < avg < 0.99)"),
    ([0.99, 0.98, 1.0], "liquid (avg >= 0.99)"),
    ([], "None (empty list)"),
    ([None, None], "None (all None)"),
]
for fractions, description in test_cases:
    result = predict_state(fractions)
    print(f"  LF values {fractions} -> {result} ({description})")

# Test 5: Lookup specific criteria
print("\n[5/6] Looking up specific criteria entries...")
test_lookups = [
    ("liquid", "P-DIS-BUB", 6.0, 10.0),
    ("liquid", "P-DIS-BUB", 9999.0, 9999.0),
    ("gas", "C-OUT", 9999.0, 50.0),
    ("two_phase", "TWO-PHASE", 8.0, 20.0),
]
for fluid_type, code, pipe_size, pressure in test_lookups:
    result = lookup_criteria(fluid_type, code, pipe_size, pressure)
    if result:
        print(f"  {fluid_type}/{code} (size={pipe_size}, P={pressure})")
        print(f"    -> vel: {result.get('vel')}, dp: {result.get('dp')}")
    else:
        print(f"  {fluid_type}/{code} -> Not found")

# Test 6: Predict criteria for a pipe
print("\n[6/6] Testing criteria prediction...")
pipe_names = ["P-001", "C-101-SUC", "L-123", "TEST-LINE"]
for pipe_name in pipe_names:
    for fluid_type in ["liquid", "gas", "two_phase"]:
        criteria = predict_criteria(fluid_type, pipe_name)
        print(f"  {pipe_name} ({fluid_type}): {criteria}")

print("\n" + "=" * 60)
print("Sizing Criteria Tests Complete!")
print("=" * 60)
