# Evidence and audit policy

The authoritative evidence registry is embedded in `free-exercise-db-plusplus.json`.

For every used canonical movement pattern:

1. the pattern must have an evidence registry entry;
2. its evidence status must not be `provisional`;
3. every referenced evidence ID must resolve in the embedded registry;
4. `supported` patterns must map at high confidence;
5. `complex_supported` and `indirect_support` patterns remain medium confidence.

The default effective-set model is direct `1.0`, indirect `0.5`, stabilizer `0.0`.

Generated audit files (`EVIDENCE-AUDIT.md`, `RULE-AUDIT.md`, `MAPPING-AUDIT.md`,
`FALLBACK-AUDIT.md`, and `REVIEW.md`) are review artifacts. They are not runtime dependencies.

For 1.0, evidence changes may change `converterVersion` without changing the JSON schema when the consumer contract is unchanged.
