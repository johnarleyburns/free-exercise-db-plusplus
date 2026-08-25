# Project Session Workflow

Work on one roadmap phase at a time. A phase must be scoped so it can reasonably be completed in one session.

At the start of every session:

1. Read `current_status.md` first. Treat it as the local handoff for the current project state, recent work, future work, and the active phase.
2. Read the roadmap and any project files referenced by `current_status.md` that are relevant to the active phase.
3. Implement only the active phase. Preserve the v1.0 exercise-database consumer contract and follow the guardrails in `ROADMAP.md`.

Before finishing a phase:

1. Re-read the phase plan and audit the implementation for completeness and correctness.
2. Run the full relevant unit-test suite, not only newly added tests.
3. Add or update integration/CI validation when the phase changes behavior covered by those checks.
4. Review the final diff and working tree, preserving unrelated user changes.
5. Commit and push the completed implementation only after the audit and tests pass.
6. After the push, update `current_status.md` with the completed work, verification results, important decisions, remaining risks, and the next active phase.

`current_status.md` is a local working handoff file. Never stage, commit, or push it. Check the staged file list before every commit to enforce this rule.

