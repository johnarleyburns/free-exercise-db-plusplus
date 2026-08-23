# Methodology

Free Exercise DB++ is a reproducible annotation layer over Free Exercise DB for resistance-training volume analysis.

## Set-credit model

For each performed set of a `volumeEligible` exercise:

- **direct** muscle = **1.0** effective set
- **indirect** muscle = **0.5** effective set
- **stabilizer** muscle = **0.0** effective sets

These are analysis credits. They do not assert that hypertrophy, fatigue, or adaptation is literally linear.

## Muscle roles

**Direct** means the muscle is a principal target or prime contributor in the canonical movement as modeled by DB++.

**Indirect** means the muscle contributes materially but is not credited as a full direct set.

**Stabilizer** means meaningful stabilizing or isometric participation retained for biomechanical context but assigned zero default set credit.

## Confidence

- `high` — deterministic mapping backed by targeted evidence or an explicit reviewed override.
- `medium` — complex-event bookkeeping, indirect evidence, or a deliberately retained ambiguous fallback.
- `low` — unresolved mapping. Release CI is intended to keep this at zero.

Confidence describes confidence in the mapping, not exercise quality.

## Evidence status

- `supported` — targeted evidence supports the movement-family mapping.
- `complex_supported` — evidence supports the multi-phase/whole-body event, but direct/indirect bookkeeping remains an abstraction.
- `indirect_support` — the mapping relies partly on closely related movements, anatomy, or biomechanical extrapolation.
- `provisional` — insufficiently supported taxonomy entry. A used provisional pattern fails CI.

## Auditability

Every generated exercise preserves the complete upstream source object. Evidence references and pattern evidence are embedded in the single runtime JSON. Markdown and CSV audit files are reviewer/developer outputs only.

## Scope

DB++ is intended for training-log analytics, software interoperability, and research-oriented data processing. It is not a medical diagnostic model and does not estimate injury risk or individual muscle activation.
