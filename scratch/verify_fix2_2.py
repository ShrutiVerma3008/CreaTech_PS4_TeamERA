"""
scratch/verify_fix2_2.py
========================
Verification script for Fix 2.2 -- Cross-Site Data Timestamp Check.

Tests:
  1. ts_a and ts_b 10 minutes apart  -> is_stale=False, delta~10.0
  2. ts_a and ts_b 45 minutes apart  -> is_stale=True,  delta~45.0
  3. ts_a=None, ts_b=None            -> no crash, is_stale=False
  4. ts_a and ts_b exactly 30 min    -> is_stale=False (threshold exclusive)
  5. All 5 required keys present in every result

Academic basis:
  Dania et al. (2015) J.Eng.Design Tech. 13(3): cross-site reallocation
    only valid when site data is temporally consistent.
  PMI PMBOK 7th ed. S.4.3 (2021): procurement decisions require
    version-controlled inputs; stale data invalidates cross-site allocation.

Exit code 0 + "All assertions pass" on success.
"""
import sys
import os
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.cross_site import check_site_data_freshness

SEP = "=" * 60
REQUIRED_KEYS = {"is_stale", "delta_minutes", "threshold_minutes",
                 "site_a_loaded_at", "site_b_loaded_at"}


def assert_all_keys(result: dict, test_name: str):
    missing = REQUIRED_KEYS - set(result.keys())
    assert not missing, (
        f"FAIL {test_name}: missing keys {missing} in result {result}"
    )


# ══════════════════════════════════════════════════════════════════
# Test 1 -- 10 minutes apart -> is_stale=False
# ══════════════════════════════════════════════════════════════════
print(SEP)
print("TEST 1: 10 min apart -> is_stale=False, delta~10.0")
print(SEP)

now = datetime.datetime(2026, 5, 10, 10, 0, 0)
ts_a_1 = now
ts_b_1 = now + datetime.timedelta(minutes=10)

result_1 = check_site_data_freshness(ts_a_1, ts_b_1, threshold_minutes=30)
assert_all_keys(result_1, "Test 1")

assert result_1["is_stale"] == False, (
    f"FAIL Test 1: expected is_stale=False, got {result_1['is_stale']}"
)
assert abs(result_1["delta_minutes"] - 10.0) < 0.2, (
    f"FAIL Test 1: expected delta~10.0, got {result_1['delta_minutes']}"
)
assert result_1["threshold_minutes"] == 30

print(f"PASS: is_stale={result_1['is_stale']}, "
      f"delta_minutes={result_1['delta_minutes']}, "
      f"threshold={result_1['threshold_minutes']}")


# ══════════════════════════════════════════════════════════════════
# Test 2 -- 45 minutes apart -> is_stale=True
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 2: 45 min apart -> is_stale=True, delta~45.0")
print(SEP)

ts_a_2 = now
ts_b_2 = now + datetime.timedelta(minutes=45)

result_2 = check_site_data_freshness(ts_a_2, ts_b_2, threshold_minutes=30)
assert_all_keys(result_2, "Test 2")

assert result_2["is_stale"] == True, (
    f"FAIL Test 2: expected is_stale=True, got {result_2['is_stale']}"
)
assert abs(result_2["delta_minutes"] - 45.0) < 0.2, (
    f"FAIL Test 2: expected delta~45.0, got {result_2['delta_minutes']}"
)

print(f"PASS: is_stale={result_2['is_stale']}, "
      f"delta_minutes={result_2['delta_minutes']}")


# ══════════════════════════════════════════════════════════════════
# Test 3 -- Both None -> no crash, is_stale=False
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 3: ts_a=None, ts_b=None -> no crash, is_stale=False")
print(SEP)

try:
    result_3 = check_site_data_freshness(None, None, threshold_minutes=30)
except Exception as exc:
    print(f"FAIL Test 3: raised exception: {exc}")
    sys.exit(1)

assert_all_keys(result_3, "Test 3")
assert result_3["is_stale"] == False, (
    f"FAIL Test 3: expected is_stale=False, got {result_3['is_stale']}"
)
assert result_3["delta_minutes"] == 0.0, (
    f"FAIL Test 3: expected delta_minutes=0.0, got {result_3['delta_minutes']}"
)
assert result_3["site_a_loaded_at"] == "unknown"
assert result_3["site_b_loaded_at"] == "unknown"

print(f"PASS: no crash, is_stale={result_3['is_stale']}, "
      f"delta={result_3['delta_minutes']}, "
      f"site_a='{result_3['site_a_loaded_at']}', "
      f"site_b='{result_3['site_b_loaded_at']}'")


# ══════════════════════════════════════════════════════════════════
# Test 4 -- Exactly 30 min -> is_stale=False (threshold exclusive: > not >=)
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 4: Exactly 30 min apart -> is_stale=False (boundary: > not >=)")
print(SEP)

ts_a_4 = now
ts_b_4 = now + datetime.timedelta(minutes=30)

result_4 = check_site_data_freshness(ts_a_4, ts_b_4, threshold_minutes=30)
assert_all_keys(result_4, "Test 4")

assert result_4["is_stale"] == False, (
    f"FAIL Test 4: expected is_stale=False (boundary exclusive), "
    f"got {result_4['is_stale']}"
)
assert abs(result_4["delta_minutes"] - 30.0) < 0.2, (
    f"FAIL Test 4: expected delta~30.0, got {result_4['delta_minutes']}"
)

print(f"PASS: is_stale={result_4['is_stale']}, "
      f"delta_minutes={result_4['delta_minutes']} (boundary=30, exclusive)")


# ══════════════════════════════════════════════════════════════════
# Test 5 -- Mixed None: ts_a valid, ts_b None -> no crash, is_stale=False
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 5: ts_a valid, ts_b=None -> no crash, is_stale=False")
print(SEP)

try:
    result_5 = check_site_data_freshness(now, None, threshold_minutes=30)
except Exception as exc:
    print(f"FAIL Test 5: raised exception: {exc}")
    sys.exit(1)

assert_all_keys(result_5, "Test 5")
assert result_5["is_stale"] == False, (
    f"FAIL Test 5: expected is_stale=False, got {result_5['is_stale']}"
)
assert result_5["site_b_loaded_at"] == "unknown"

print(f"PASS: no crash, is_stale={result_5['is_stale']}, "
      f"site_b='{result_5['site_b_loaded_at']}'")


# ══════════════════════════════════════════════════════════════════
# Test 6 -- Custom threshold (5 min): 10 min apart -> is_stale=True
# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("TEST 6: Custom threshold 5 min, 10 min apart -> is_stale=True")
print(SEP)

result_6 = check_site_data_freshness(ts_a_1, ts_b_1, threshold_minutes=5)
assert_all_keys(result_6, "Test 6")
assert result_6["is_stale"] == True, (
    f"FAIL Test 6: expected is_stale=True with threshold=5, "
    f"got {result_6['is_stale']}"
)
assert result_6["threshold_minutes"] == 5

print(f"PASS: is_stale={result_6['is_stale']}, "
      f"threshold={result_6['threshold_minutes']} min, "
      f"delta={result_6['delta_minutes']} min")


# ══════════════════════════════════════════════════════════════════
print()
print(SEP)
print("All assertions pass")
print(SEP)
sys.exit(0)
