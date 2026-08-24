# Interoperability mapping registry

The mapping registry is the declarative boundary between DB++ Workout observations and external formats. Each target is versioned independently in `mappings/*.json` and validated by [`interop-mapping.schema.json`](../interop-mapping.schema.json).

A registry has a target slug, semantic mapping version, lifecycle status, target specification, and entries. Each entry identifies a DB++ source path, a target field, a quality classification, and an explicit transform/notes value. The quality values are `exact`, `compatible`, `lossy`, `extension_required`, and `unsupported`.

`placeholder` registries deliberately contain no entries and are not claims of interoperability. `draft-reviewed` registries have reviewed field mappings but are not import/export implementations. `stable` is reserved for a future reviewed release.

The registry schema validates structure and controlled values. CI additionally rejects duplicate source/target pairs and requires every non-placeholder registry to contain at least one mapping entry. It does not assert that a target’s semantics are lossless; the target-specific document remains normative for limitations.
