#!/usr/bin/env python3
"""Quick review script to test specific concerns."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pykorf.model import KorfModel, Model

SAMPLES_DIR = Path(__file__).parent / "library"
PUMP_KDF = SAMPLES_DIR / "Pumpcases.kdf"
CWC_KDF = SAMPLES_DIR / "Cooling Water Circuit.kdf"

print("=" * 60)
print("Testing KorfModel backward compatibility")
print("=" * 60)

# Test 1: KorfModel is alias for Model
print("\n1. KorfModel is Model:", KorfModel is Model)

# Test 2: KorfModel.load() works
try:
    m = KorfModel.load(PUMP_KDF)
    print("2. KorfModel.load() works: ✓")
    print(f"   Loaded {m.num_pipes} pipes, {m.num_pumps} pumps")
except Exception as e:
    print(f"2. KorfModel.load() FAILED: {e}")

# Test 3: Model(path) constructor works
try:
    m2 = Model(PUMP_KDF)
    print("3. Model(path) constructor works: ✓")
except Exception as e:
    print(f"3. Model(path) FAILED: {e}")

# Test 4: Model() with no args works
try:
    m3 = Model()
    print("4. Model() no args works: ✓")
    print(f"   Created blank model: {m3.num_pipes} pipes")
except Exception as e:
    print(f"4. Model() FAILED: {e}")

print("\n" + "=" * 60)
print("Testing name map with empty names")
print("=" * 60)

# Test 5: Name map handles elements with empty names
try:
    m = Model(PUMP_KDF)
    print("\n5. Testing name map...")

    # Check if any element has empty name
    empty_name_count = 0
    for collection in m._all_collections():
        for idx, elem in collection.items():
            if idx >= 1 and not elem.name:
                empty_name_count += 1

    print(f"   Found {empty_name_count} elements with empty names")
    print(f"   Name map has {len(m._name_map)} entries")

    # Try to get an element that exists
    if "L1" in m:
        print("   ✓ Can get element 'L1' by name")
    else:
        print("   ✗ FAILED: 'L1' not in name map")

except Exception as e:
    print(f"5. Name map test FAILED: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
print("Testing CRUD operations and NUM counts")
print("=" * 60)

# Test 6: Add element updates NUM
try:
    m = Model(PUMP_KDF)
    orig_count = m.num_pipes
    orig_num = m._parser.num_instances("PIPE")

    new_pipe = m.add_element("PIPE", "L_TEST", {"LEN": "50"})

    new_count = m.num_pipes
    new_num = m._parser.num_instances("PIPE")

    print("\n6. Add element:")
    print(f"   Before: NUM={orig_num}, count={orig_count}")
    print(f"   After:  NUM={new_num}, count={new_count}")

    if new_num == orig_num + 1:
        print("   ✓ NUM correctly incremented")
    else:
        print(f"   ✗ FAILED: NUM should be {orig_num + 1}, got {new_num}")

    if new_count == orig_count + 1:
        print("   ✓ Count correctly incremented")
    else:
        print(f"   ✗ FAILED: Count should be {orig_count + 1}, got {new_count}")

except Exception as e:
    print(f"6. Add element FAILED: {e}")
    import traceback

    traceback.print_exc()

# Test 7: Delete element updates NUM
try:
    m = Model(PUMP_KDF)
    orig_count = m.num_pipes
    orig_num = m._parser.num_instances("PIPE")

    # Delete first pipe
    first_pipe_name = m.get_elements_by_type("PIPE")[0].name
    m.delete_element(first_pipe_name)

    new_count = m.num_pipes
    new_num = m._parser.num_instances("PIPE")

    print("\n7. Delete element:")
    print(f"   Before: NUM={orig_num}, count={orig_count}")
    print(f"   After:  NUM={new_num}, count={new_count}")

    if new_num == orig_num - 1:
        print("   ✓ NUM correctly decremented")
    else:
        print(f"   ✗ FAILED: NUM should be {orig_num - 1}, got {new_num}")

    if new_count == orig_count - 1:
        print("   ✓ Count correctly decremented")
    else:
        print(f"   ✗ FAILED: Count should be {orig_count - 1}, got {new_count}")

except Exception as e:
    print(f"7. Delete element FAILED: {e}")
    import traceback

    traceback.print_exc()

# Test 8: Copy element updates NUM
try:
    m = Model(PUMP_KDF)
    orig_count = m.num_pipes
    orig_num = m._parser.num_instances("PIPE")

    # Copy a pipe
    m.copy_element("L1", "L_COPY")

    new_count = m.num_pipes
    new_num = m._parser.num_instances("PIPE")

    print("\n8. Copy element:")
    print(f"   Before: NUM={orig_num}, count={orig_count}")
    print(f"   After:  NUM={new_num}, count={new_count}")

    if new_num == orig_num + 1:
        print("   ✓ NUM correctly incremented")
    else:
        print(f"   ✗ FAILED: NUM should be {orig_num + 1}, got {new_num}")

    if new_count == orig_count + 1:
        print("   ✓ Count correctly incremented")
    else:
        print(f"   ✗ FAILED: Count should be {orig_count + 1}, got {new_count}")

except Exception as e:
    print(f"8. Copy element FAILED: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
print("Testing connectivity module with v3.6 NOZL vs v2.0 NOZ")
print("=" * 60)

# Test 9: Connectivity handles v2.0 NOZ
try:
    m = Model(PUMP_KDF)
    print(f"\n9. Testing v2.0 (NOZ) - {PUMP_KDF.name}")
    print(f"   Version: {m.version}")

    # Get a FEED element
    if m.feeds:
        feed = list(m.feeds.values())[0]
        if feed.index >= 1:
            noz_rec = feed._get("NOZ")
            nozl_rec = feed._get("NOZL")
            print(f"   FEED has NOZ: {noz_rec is not None}")
            print(f"   FEED has NOZL: {nozl_rec is not None}")

            if noz_rec:
                print("   ✓ v2.0 NOZ detected correctly")
            elif nozl_rec:
                print("   ! Found NOZL in v2.0 file (unexpected)")
            else:
                print("   ? No NOZ or NOZL found")
        else:
            print("   No real FEED elements")
    else:
        print("   No FEED elements in model")

except Exception as e:
    print(f"9. v2.0 connectivity test FAILED: {e}")
    import traceback

    traceback.print_exc()

# Test 10: Connectivity handles v3.6 NOZL
try:
    m = Model(CWC_KDF)
    print(f"\n10. Testing v3.6 (NOZL) - {CWC_KDF.name}")
    print(f"    Version: {m.version}")

    # Get a FEED element
    if m.feeds:
        feed = list(m.feeds.values())[0]
        if feed.index >= 1:
            noz_rec = feed._get("NOZ")
            nozl_rec = feed._get("NOZL")
            print(f"    FEED has NOZ: {noz_rec is not None}")
            print(f"    FEED has NOZL: {nozl_rec is not None}")

            if nozl_rec:
                print("    ✓ v3.6 NOZL detected correctly")
            elif noz_rec:
                print("    ! Found NOZ in v3.6 file (unexpected)")
            else:
                print("    ? No NOZ or NOZL found")
        else:
            print("    No real FEED elements")
    else:
        print("    No FEED elements in model")

except Exception as e:
    print(f"10. v3.6 connectivity test FAILED: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
print("Testing circular import prevention")
print("=" * 60)

# Test 11: Lazy imports work
try:
    print("\n11. Testing lazy imports...")
    from pykorf import Model

    # These should not cause circular imports at import time
    m = Model(PUMP_KDF)

    # Now trigger the lazy imports
    issues = m.check_connectivity()
    print("    ✓ check_connectivity() imported successfully")

    issues = m.check_layout()
    print("    ✓ check_layout() imported successfully")

    issues = m.validate()
    print("    ✓ validate() imported successfully")

except Exception as e:
    print(f"11. Lazy import test FAILED: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
print("All tests completed")
print("=" * 60)
