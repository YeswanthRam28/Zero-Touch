"""Simple test harness for the `fuse` function in `backend/fus.py`.

Runs several cases (normal, out-of-sync, low-confidence, conflict)
using the sample JSON in `fusion/inputs` and prints results.
"""
import json
import os
import sys
from pprint import pprint

FUSION_INPUTS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "fusion", "inputs"))

sys.path.insert(0, os.path.dirname(__file__))
try:
    from fus import fuse
except Exception as e:
    print("Failed to import fuse from backend.fus:", e)
    raise


def load_json(name):
    path = os.path.join(FUSION_INPUTS, name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_vision(v):
    # fus.py expects keys: 'object', 'confidence', 'timestamp'
    return {
        "object": v.get("object") or v.get("object_detected"),
        "confidence": v.get("confidence", 0.0),
        "timestamp": v.get("timestamp", 0.0),
    }


def normalize_voice(v):
    # fus.py expects keys: 'transcript', 'intent', 'confidence', 'timestamp'
    return {
        "transcript": v.get("transcript", ""),
        "intent": v.get("intent", "UNKNOWN"),
        "confidence": v.get("confidence", 0.0),
        "timestamp": v.get("timestamp", 0.0),
    }


def run_case(name, vision, voice, expect_check):
    print(f"\n--- {name} ---")
    v = normalize_vision(vision)
    vo = normalize_voice(voice)
    print("Vision input:")
    pprint(v)
    print("Voice input:")
    pprint(vo)
    out = fuse(v, vo)
    print("Fusion output:")
    pprint(out)
    ok, msg = expect_check(out)
    print("Check:", "PASS" if ok else f"FAIL: {msg}")
    return ok


def main():
    # Load sample inputs provided in repo
    sample_v = load_json("vision_output.json")
    sample_vo = load_json("voice_output.json")

    all_ok = True

    # Case 1: canonical sample -> expect OPEN_PATIENT_FILE
    def expect1(out):
        a = out.get("action")
        return (a == "OPEN_PATIENT_FILE", f"expected OPEN_PATIENT_FILE, got {a}")

    all_ok &= run_case("Sample match", sample_v, sample_vo, expect1)

    # Case 2: out of sync timestamps -> expect IGNORE
    v2 = dict(sample_v)
    vo2 = dict(sample_vo)
    vo2["timestamp"] = v2["timestamp"] + 10.0

    def expect2(out):
        return (out.get("action") == "IGNORE", f"expected IGNORE, got {out}")

    all_ok &= run_case("Out of sync", v2, vo2, expect2)

    # Case 3: low confidence -> expect NONE/REJECTED
    v3 = dict(sample_v)
    vo3 = dict(sample_vo)
    v3["confidence"] = 0.5
    vo3["confidence"] = 0.4

    def expect3(out):
        return (out.get("action") == "NONE", f"expected NONE, got {out}")

    all_ok &= run_case("Low confidence", v3, vo3, expect3)

    # Case 4: conflict (object not person) -> expect NONE
    v4 = dict(sample_v)
    v4["object_detected"] = "chair"
    v4["object"] = "chair"

    def expect4(out):
        return (out.get("action") == "NONE", f"expected NONE, got {out}")

    all_ok &= run_case("Conflict object", v4, sample_vo, expect4)

    # Case 5: compare with pre-op -> expect COMPARE_WITH_PREOP
    v5 = dict(sample_v)
    vo5 = dict(sample_vo)
    vo5["transcript"] = "Compare with pre-op scan"

    def expect5(out):
        return (out.get("action") == "COMPARE_WITH_PREOP", f"expected COMPARE_WITH_PREOP, got {out}")

    all_ok &= run_case("Compare pre-op", v5, vo5, expect5)
    print('\nSummary:')
    print('ALL TESTS PASSED' if all_ok else 'SOME TESTS FAILED')
    if not all_ok:
        sys.exit(2)


if __name__ == "__main__":
    main()
