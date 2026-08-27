# Cross-language engine parity

The Python package is the semantic oracle for the v1.11 engine fixtures under
`fixtures/cross-language/{evaluation,history,progression,generation,adaptation}`.
Native implementations compare their serialized result with the corresponding
`expected.json` using one strict policy.

## Normalization policy

The comparison ignores only:

- JSON object member order;
- JSON whitespace; and
- integer versus floating-point representation when both values are
  mathematically equal and the schema permits numeric values.

The comparison preserves and therefore requires equality for every other
value. In particular, it does not sort or otherwise normalize arrays, and it
does not treat a missing member as equivalent to an explicit `null`.

The following are semantic and must compare exactly:

- session, exercise, prescription, and set ordering;
- day offsets and counts;
- target ranges and coverage values;
- policy IDs and versions;
- status values and reason codes, including their array order;
- provenance members and values; and
- complete CoachDecision before/after, evidence, and decision contents.

The reference implementation is
`tools/compare_canonical_json.py`. It recursively compares objects by key,
compares arrays by index, and reports the first differing JSON path. It is
intended for fixture gates and does not alter either document.

Examples:

```bash
python3 tools/compare_canonical_json.py \
  fixtures/cross-language/evaluation/expected.json \
  native-evaluation.json
```

Exit status `0` means semantic equality; `1` means a mismatch; `2` means an
invalid invocation. A JSON parse failure is a fixture/test failure.

This policy is deliberately stricter than a similarity or tolerance check.
If Python and a native implementation disagree, the differing path identifies
the parity gap; the native implementation must be aligned with the Python
oracle unless the repository records a corrected oracle defect.
