# Release checklist

- [ ] GitHub Actions is green on the release-preparation commit.
- [ ] `free-exercise-db-plusplus.json` validates against the JSON Schema.
- [ ] Release-contract tests pass.
- [ ] Golden-mapping tests pass.
- [ ] Medium-confidence policy tests pass.
- [ ] Reproducibility test produces byte-identical output.
- [ ] `Needs review` is zero.
- [ ] No used movement pattern has provisional evidence.
- [ ] Remaining medium-confidence mappings are explained by audit output.
- [ ] Upstream source count and SHA-256 are embedded in generated metadata.
- [ ] README examples match the current schema.
- [ ] `METHODOLOGY.md`, `COMPATIBILITY.md`, and `VERSIONING.md` are current.
- [ ] Generated outputs are committed before tagging a release.
- [ ] Tag a human release-preparation commit, not a bot commit containing `[skip ci]`.
- [ ] Verify the tag-triggered release workflow succeeds and publishes all expected assets.
