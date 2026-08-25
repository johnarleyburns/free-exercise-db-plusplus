# ADR 0001: Single self-contained database JSON

Status: accepted

The release database remains one self-contained JSON artifact. Consumers can
load it without a service or secondary lookup store, while derived analyses and
interoperability mappings remain separate files.
