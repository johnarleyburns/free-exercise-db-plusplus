# Methodology

Free Exercise DB++ is an annotation layer over Free Exercise DB for resistance-training volume analysis.

## Set-credit model
For each performed set of a volume-eligible exercise: **direct = 1.0**, **indirect = 0.5**, **stabilizer = 0.0** effective sets. These are analytical credits, not claims that hypertrophy or fatigue is literally linear.

## Muscle roles
- **Direct:** principal target/prime contributor for the canonical movement as modeled by DB++.
- **Indirect:** materially contributes but is not credited as a full direct set.
- **Stabilizer:** meaningful stabilizing/isometric participation retained for biomechanics but given zero default set credit.

## Confidence
- `high`: deterministic mapping backed by targeted evidence or explicit reviewed override.
- `medium`: complex-event bookkeeping, indirect evidence, or deliberately retained ambiguous fallback.
- `low`: unresolved mapping; release CI should keep this at zero.

## Evidence status
- `supported`: targeted evidence for the movement family.
- `complex_supported`: evidence exists, but reducing a multi-phase/whole-body event to muscle roles remains an abstraction.
- `indirect_support`: relies partly on related movements/anatomy/extrapolation.
- `provisional`: insufficiently supported taxonomy entry; used provisional patterns fail CI.

Every record preserves the upstream source object. Evidence and pattern status are embedded in the single runtime JSON; Markdown/CSV audits are review aids only.
